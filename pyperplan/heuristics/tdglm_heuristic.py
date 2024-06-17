from copy import deepcopy
import pulp 

from pyperplan.heuristics.heuristic import Heuristic
from pyperplan.heuristics.landmarks.landmark import Landmarks
from pyperplan.search.htn_node import AstarNode

class TDGLmHeuristic(Heuristic):
    """
    TDG Count use an IP formulation to compute the minimal number of tasks to clear the task network
    which completes all landmarks extracting using the 'bidirectional landmarks'.
    - Each new node should 'know' the number of pending landmarks
    - Each new node should update variable bounds
     (1) We have to update the counting on TNI variables, 
        this indicates the number of times each task appears into the current task network
     (2) Each node should update variable bounds according to the pending landmarks
    """
    def __init__(self, model, initial_node, use_landmarks=True, use_bid = True):
        super().__init__(model, initial_node)
        # auxiliar: maps each subtask to each corresponding method that uses it (can appear more than once)
        self.mst = {n.global_id: [] for n in self.model.operators + self.model.abstract_tasks}

        # generate bidirectional landmarks
        self.landmarks = Landmarks(self.model)
        self.landmarks.bottom_up_lms()
        self.lm_set = set()
        if use_landmarks and use_bid:
            self.landmarks.top_down_lms()
            self.lm_set = self.landmarks.bidirectional_lms(self.model, initial_node.state, initial_node.task_network)
        elif use_landmarks:
            self.lm_set = self.landmarks.classical_lms(self.model, initial_node.state, initial_node.task_network)
        # after getting lm_set, clear memory
        # self.landmarks.clear_structures()
        
        # IP/LP model variables
        self.uan_vars = {}
        self.mm_vars = {}
        self.tni_constants = {}
        self.lm_vars = {}

        # Preare IP/LP model
        self.ipmodel = pulp.LpProblem("TaskDecomposition", pulp.LpMinimize)
        self._build_ip_model()

        # Compute initial node
        initial_node.lm_node = deepcopy(self.lm_set)
        initial_node.h_value = self._solve_ip()
        initial_node.f_value = initial_node.h_value
        #self.test_model(initial_node)

    def test_model(self, initial_node):
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

    def compute_heuristic(self, parent_node, node):
        unachieved_landmarks = deepcopy(parent_node.lm_node)
        #print(f'{node.task.name} ==> {node.decomposition.name} ({node.decomposition.global_id})')
        if node.task.global_id in unachieved_landmarks:
            unachieved_landmarks.remove(node.task.global_id)
        if node.decomposition and node.decomposition.global_id in unachieved_landmarks:
            unachieved_landmarks.remove(node.decomposition.global_id)
        node.lm_node = unachieved_landmarks
        #print(node.lm_node)

        # reset uan variables
        for var in self.uan_vars.values():
            var.lowBound= 0
            var.upBound = None
        # reset mm variables
        for var in self.mm_vars.values():
            var.lowBound = 0
            var.upBound = None
        # update landmarks
        for lm_id in node.lm_node:
            var = self.lm_vars[lm_id]
            var.lowBound=1

        # reset and update tni constants
        for tni_const in self.tni_constants.values():
            tni_const.lowBound = 0
            tni_const.upBound = 0
        for task in node.task_network:
            tv = self.tni_constants[task.global_id]
            tv.lowBound+=1
            tv.upBound+=1

        node.h_value = self._solve_ip()
        node.f_value = node.h_value + node.g_value
        
    def _build_ip_model(self):
        # initialize auxiliary structure
        for d in self.model.decompositions:
            for subt in d.task_network:
                self.mst[subt.global_id].append(d)
        
        # initialize variables
        self.uan_vars = {
            n.global_id:
            pulp.LpVariable(f"UN_{n.name}", lowBound=0, cat='Integer')
            for n in self.model.abstract_tasks + self.model.operators
        }
        self.mm_vars  = {
            m.global_id: 
            pulp.LpVariable(f"M_{m.name}", lowBound=0, cat='Integer')
            for m in self.model.decompositions
        }
        self.tni_constants = {
            n.global_id: 
            pulp.LpVariable(f"TNC_{n.name}", lowBound=0, upBound=0, cat='Integer')
            for n in self.model.abstract_tasks + self.model.operators
        }
        
        # set landmarks
        for lm_id in self.lm_set:
            # check if is method or task landmarks
            lm_var = self.uan_vars.get(lm_id, None)
            if lm_var is None:
                lm_var = self.mm_vars.get(lm_id, None)
            lm_var.lowBound=1
            self.lm_vars[lm_id]=lm_var
                 
        # set TNI counting
        for t in self.model.initial_tn:
            self.tni_constants[t.global_id].lowBound+=1
            self.tni_constants[t.global_id].upBound+=1

        # constraints
        self.ipmodel += pulp.lpSum([self.uan_vars[n.global_id] for n in self.model.abstract_tasks] + [self.uan_vars[n.global_id] for n in self.model.operators])
        for abt in self.model.abstract_tasks:
            #every abstract task should use a method
            self.ipmodel += self.uan_vars[abt.global_id] == pulp.lpSum([self.mm_vars[d.global_id] for d in abt.decompositions]), f"Decomposition_{abt.name}"
        for n in self.model.abstract_tasks + self.model.operators:
            #every task should appear the same number of times it appears into method's subtask plus their initial task network
            self.ipmodel += self.uan_vars[n.global_id] == self.tni_constants[n.global_id] + pulp.lpSum([self.mm_vars[m.global_id] for m in self.mst.get(n.global_id, [])]), f"Task_{n.name}"
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