from copy import deepcopy
import pulp 

from pyperplan.heuristics.heuristic import Heuristic
from pyperplan.heuristics.landmarks.landmark import Landmarks
from pyperplan.model import AbstractTask, Decomposition, Operator
from pyperplan.search.htn_node import AstarNode
from pyperplan.tools import InvalidArgumentException

class TDGLmHeuristic(Heuristic):
    """
    TDGLM uses an IP formulation to compute the minimal number of tasks 
    needed to clear the task network while completing all landmarks extracted using bidirectional landmarks.

    Important IP variables:
        - UN_var: Number of occurrences of task variables.
        - M_var: Number of occurrences of method variables.
        - TNI_const: Number of occurrences of tasks in the current task network.
        - LM_var: Reference to UN variables that are landmarks.

    Parameters:
        @param model: Contains the instantiated problem.
        @param initial_node: Initial node, starting point with a heuristic value of 0.
        @param use_landmarks: Flag to toggle landmark usage (default: True).
        @param use_bid: Flag to use bidirectional landmarks (default: True).
    """
    def __init__(self, model, initial_node, use_landmarks=True, use_bid = True, var_category = "Integer", compute_reachability = False, name="tdg-ip"):
        super().__init__(model, initial_node, name=name)
        if var_category not in ["Integer", "Continuous"]:
            raise InvalidArgumentException(f"Invalid variable category '{var_category}', types allowed are Integer or Continuous")
        self.name = name
        self.var_category = var_category
        self.compute_reachability = compute_reachability
        self.use_landmarks = use_landmarks
        self.use_bid = use_bid
        self.read_parameters()

        # auxiliar: maps each subtask to each corresponding method that uses it (can appear more than once)
        self.mst = {n.global_id: [] for n in self.model.operators + self.model.abstract_tasks}
        
        self.landmarks = None
        if self.use_landmarks:
            # generate bidirectional landmarks
            self.landmarks = Landmarks(self.model)
            self.landmarks.bottom_up_lms()
            self.landmarks.classical_lms(self.model, initial_node.state, initial_node.task_network)
            if self.use_bid:
                self.landmarks.top_down_lms()
                self.landmarks.bidirectional_lms(self.model, initial_node.state, initial_node.task_network)
        # self.landmarks.clear_structures() # clear memory
        self.total_lms = len(self.landmarks.task_lms) + len(self.landmarks.method_lms) + len(self.landmarks.fact_lms)
        
        # IP/LP model variables
        self.uan_vars = {}
        self.mm_vars = {}
        self.tni_constants = {}
        self.fact_vars = {} # only considering fact landmarks

        # LM model variables
        self.lm_method_vars = {}
        self.lm_task_vars = {}
        self.achiever_fact = {} # which operator has f as effect (disjuntive action constraint)

        # Preare IP/LP model
        self.ipmodel = pulp.LpProblem("TaskDecomposition", pulp.LpMinimize)
        self._build_ip_model()

        # Compute initial node
        lm_triple_set = (
            deepcopy(self.landmarks.task_lms),
            deepcopy(self.landmarks.method_lms),
            deepcopy(self.landmarks.fact_lms)
        )
        initial_node.lm_node = lm_triple_set #TODO: this is not ok, it suppose to get landmarkNode, here Im passing a set(), different purpose
        super().set_hvalue(initial_node, self._solve_ip())
        self.initial_h = initial_node.h_value

    def read_parameters(self):
        print(f'Heuristic {self.name} set with the following parameters: \n\tvariable category:{self.var_category}\n\tuse landmarks:{self.use_landmarks}\n\tuse bidirectional landmarks:{self.use_bid}\n\tcompute reachability:{self.compute_reachability}')

    def compute_heuristic(self, parent_node, node):
        """
        Update model:
            - Check and update node's unachieved landmarks.
            - Reset variable bounds.
            - Update TNI and landmark variables.
        """
        # update unachieved landmarks
        unachieved_task_lms, unachieved_method_lms, unachieved_fact_lms = deepcopy(parent_node.lm_node)
        
        # if is an operator, update landmarks but avoid recomputing a new lp    
        if isinstance(node.task, Operator):
            if node.task.global_id in unachieved_task_lms:
                unachieved_task_lms.remove(node.task.global_id)
            for fact_lm in unachieved_fact_lms.copy():
                if node.state & (1 << fact_lm):
                    unachieved_fact_lms.remove(fact_lm)
            node.lm_node = (unachieved_task_lms, unachieved_method_lms, unachieved_fact_lms)
            #discount from parent node the operation
            super().set_hvalue(node, parent_node.h_value-1)
            return
        
        if node.task.global_id in unachieved_task_lms:
            unachieved_task_lms.remove(node.task.global_id)
        if node.decomposition and node.decomposition.global_id in unachieved_method_lms:
            unachieved_method_lms.remove(node.decomposition.global_id)
        node.lm_node = (unachieved_task_lms, unachieved_method_lms, unachieved_fact_lms)
        
        # reset fact variables
        for var in self.fact_vars.values():
            var.lowBound=0
            var.upBound=0
        # reset and update tni constants
        for tni_const in self.tni_constants.values():
            tni_const.lowBound = 0
            tni_const.upBound = 0
        # update tni
        for task in node.task_network:
            tv = self.tni_constants[task.global_id]
            tv.lowBound+=1
            tv.upBound+=1

        if self.compute_reachability:
            # reset uan variables
            for var in self.uan_vars.values():
                var.lowBound= 0
                var.upBound = 0
            # reset mm variables
            for var in self.mm_vars.values():
                var.lowBound = 0
                var.upBound = 0
            for task in node.task_network:
                self._calculate_reachability(task)
        else:
            # reset uan variables
            for var in self.uan_vars.values():
                var.lowBound= 0
                var.upBound = None
            # reset mm variables
            for var in self.mm_vars.values():
                var.lowBound = 0
                var.upBound = None
        
        lm_unreachable=False
        # mark task landmarks
        for lm_id in node.lm_node[0]:
            var = self.lm_task_vars[lm_id]
            if var.upBound == 0:
                lm_unreachable = True
            var.lowBound=1
        # mark method landmarks
        for lm_id in node.lm_node[1]:
            var = self.lm_method_vars[lm_id]
            if var.upBound == 0:
                lm_unreachable = True
            var.lowBound=1
        # mark fact landmarks for activating disjuncitve action constraints
        for lm_id in node.lm_node[2]: #NOTE: for now I won't consider fact lm reachability
            var = self.fact_vars[lm_id]
            var.lowBound=1
            var.upBound=1
        
        if lm_unreachable:
            super().set_hvalue(node, 100000000)
        else:
            super().set_hvalue(node, self._solve_ip())
            
        #print([self.landmarks.bu_AND_OR.nodes[idx] for idx in node.lm_node])
    def _calculate_reachability(self, current_task):
        task_var = self.uan_vars[current_task.global_id]
        # check task already visited
        if task_var.upBound is None:
            return
        # mark task as reachable
        task_var.upBound = None
        if isinstance(current_task, AbstractTask):
            for d in current_task.decompositions:
                method_var = self.mm_vars[d.global_id]
                method_var.upBound = None
                for subt in d.task_network:
                    self._calculate_reachability(subt)

    def _calculate_fact_achievers(self):
        """
            mark for each fact landmark the operators that make it true (disjuntive action landmarks)
        """
        for o in self.model.operators:
            for f in self.fact_vars.keys():
                if o.add_effects_bitwise & (1 << f):
                    self.achiever_fact[f].append(o.global_id)

    def _build_ip_model(self):
        """
        Instantiate variables and constraints, 
        similar to the "Delete- and Ordering-Relaxation Heuristics for HTN Planning" paper.
        """
        # initialize auxiliary structure
        for d in self.model.decompositions:
            for subt in d.task_network:
                self.mst[subt.global_id].append(d)
        
        # INITIALIZE VARIABLES
        self.uan_vars = {
            n.global_id:
            pulp.LpVariable(f"UN_{n.name}", lowBound=0, cat=self.var_category)
            for n in self.model.abstract_tasks + self.model.operators
        }
        
        self.mm_vars  = {
            m.global_id:
            pulp.LpVariable(f"M_{m.name}", lowBound=0, cat=self.var_category)
            for m in self.model.decompositions
        }

        self.tni_constants = {
            n.global_id:
            pulp.LpVariable(f"TNC_{n.name}", lowBound=0, upBound=0, cat=self.var_category)
            for n in self.model.abstract_tasks + self.model.operators
        }
        
        self.fact_vars = {
            f_id:
            pulp.LpVariable(f"F_{self.model.get_fact_name(f_id)}", lowBound=0, upBound=0, cat=self.var_category)
            for f_id in self.landmarks.fact_lms
        }

        # PREPARE LANDMARK VARIABLES
        # set task landmarks
        for lm_id in self.landmarks.task_lms:
            lm_var = self.uan_vars.get(lm_id)
            lm_var.lowBound=1
            self.lm_task_vars[lm_id]=lm_var
        # set method landmarks
        for lm_id in self.landmarks.method_lms:
            lm_var = self.mm_vars.get(lm_id)
            lm_var.lowBound=1
            self.lm_method_vars[lm_id]=lm_var
        # set fact landmark and action disjunction constraints
        self.achiever_fact = {f:[] for f in self.landmarks.fact_lms}
        self._calculate_fact_achievers()
        for lm_id in self.landmarks.fact_lms:
            # instantiate fact landmark variables
            lm_var = self.fact_vars[lm_id]
            lm_var.lowBound = 1
            lm_var.upBound = 1
            # if a fact landmark is not in the initial state, at least one action containing it as effect should be activated
            if ~self.model.initial_state & (1 << lm_id) and len(self.achiever_fact[lm_id])>1:
                self.ipmodel += pulp.lpSum([self.uan_vars[o_id] for o_id in self.achiever_fact[lm_id]]) >= lm_var
        
        # PREPARE CURRENT TASK NETWORK VARIABLES
        for t in self.model.initial_tn:
            self.tni_constants[t.global_id].lowBound+=1
            self.tni_constants[t.global_id].upBound+=1

        # PREPARE TDG CONSTRAINTS
        #self.ipmodel += pulp.lpSum([self.uan_vars[n.global_id] for n in self.model.abstract_tasks] + [self.uan_vars[n.global_id] for n in self.model.operators])
        self.ipmodel += pulp.lpSum([self.uan_vars[n.global_id] for n in self.model.operators])
        for abt in self.model.abstract_tasks:
            #every abstract task should use a method
            mm_lst = [self.mm_vars[d.global_id] for d in abt.decompositions]
            self.ipmodel += self.uan_vars[abt.global_id] == pulp.lpSum(mm_lst), f"Decomposition_{abt.name}"
        
        for n in self.model.abstract_tasks + self.model.operators:
            #every task should appear the same number of times it appears into method's subtask plus their initial task network
            mm_lst = [self.mm_vars[m.global_id] for m in self.mst.get(n.global_id, [])]
            self.ipmodel += self.uan_vars[n.global_id] == self.tni_constants[n.global_id] + pulp.lpSum(mm_lst), f"Task_{n.name}"
        
        return True
    
    def _solve_ip(self):
        self.ipmodel.solve(pulp.PULP_CBC_CMD(msg=False))
        objective_value = pulp.value(self.ipmodel.objective)
        return objective_value
    
    def print_variables_and_constraints(self):
        print("Variables:")
        for v in self.ipmodel.variables():
            if v.varValue is not None and v.varValue >= 1:
                print(f"name={v.name} bounds=({v.lowBound}, {v.upBound}) value={v.varValue}")

    def test_model(self, initial_node):
        """
            handmade test for debugging
        """
        print(initial_node)
        do_put_on = initial_node.task_network[0]
        self.print_variables_and_constraints()
        print(initial_node.lm_node)
        print(f'h: {initial_node.h_value}')
        
        # m1 child
        method_m1 = do_put_on.decompositions[0]
        m1_child_node = AstarNode(initial_node, do_put_on, method_m1, initial_node.state, method_m1.task_network, 0, 0)
        print(m1_child_node)
        self.compute_heuristic(initial_node, m1_child_node)
        self.print_variables_and_constraints()
        print(m1_child_node.lm_node)
        print(f'h: {m1_child_node.h_value}')
        

        method_m2 = do_put_on.decompositions[1]
        m2_child_node = AstarNode(initial_node, do_put_on, method_m2, initial_node.state, method_m2.task_network, 0, 0)
        print(m2_child_node)
        self.compute_heuristic(initial_node, m2_child_node)
        self.print_variables_and_constraints()
        print(m2_child_node.lm_node)
        print(f'h: {m2_child_node.h_value}')
        
        do_clear = m1_child_node.task_network[0]
        method_m7 = do_clear.decompositions[0]
        m3_child_node = AstarNode(m1_child_node, do_clear, method_m7, m1_child_node.state, method_m7.task_network+m1_child_node.task_network[1:], 0, 0)
        self.compute_heuristic(m1_child_node, m3_child_node)
        self.print_variables_and_constraints()
        print(m2_child_node.lm_node)
        print(f'h: {m3_child_node.h_value}')
        exit()