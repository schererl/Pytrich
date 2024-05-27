from copy import deepcopy
from .heuristic import Heuristic
from landmarks.landmark import Landmarks
import pulp 
'''
    TDG Count use an IP formulation to compute the minimal number of tasks to clear the task network
    which completes all landmarks extracting using the 'bidirectional landmarks'.
    - Each new node should 'know' the number of pending landmarks
     (1) landmark uses integers to store extracted landmarks 'lms' and reached landmarks 'marked'
        So we need to iterate over the binary representation of both checking wheter there
        is a landmark not marked yet.
    
    - Each new node should update variable bounds
     (1) We have to update the counting on TNI variables, 
        this indicate the number of times each task appears into the current task network
     (2) Each node should update variable bounds according to the pending landmarks

    - How to compute efficiently?
     * As we cannot use a incremental approach -otherwise every node should store their own variable dictionary
        We store a 'zero_model' containing all node variables having its initial bounds,
        then for each new node create, we make a copy of zero model, so we update bounds
        based on current task network 'TNI', and pending landmarks.
    
    - Personal Opinion:
     * This should be more memory efficient than storing all variables, tn_count and pending landmarks,
     the problem is that we have to compute landmarks all over again.
'''

class TDGLmHeuristic(Heuristic):
    def __init__(self, model, initial_node):
        super().__init__(model)
        self.mst = {}  # maps each subtask to each corresponding method that uses it (can appear more than once)
        self.ua_vars = {}
        self.mm_vars = {}
        self.tni_constants = {}
        
        # prepare IP/LP model
        self.zero_lpmodel = pulp.LpProblem("TaskDecomposition", pulp.LpMinimize)
        self._build_ip_model()

        # generate landmarks
        self.landmarks = Landmarks(self.model)
        self.landmarks.bottom_up_lms()
        self.landmarks.top_down_lms()
        # fix this
        initial_node.lm_node.update_lms(self.landmarks._bidirectional_lms(self.model, initial_node.state, initial_node.task_network))
    
    def compute_heuristic(self, parent_node, node):
        # calculate landmarks unachieved
        pending_landmarks = self._get_pending_landmarks(node)
        # make a copy of zero_model
        new_ip_problem = self.copy_lp_problem(self.zero_lpmodel)
        # update variable bounds
        self.update_var_bounds(new_ip_problem, pending_landmarks, node.task_network)

    def _get_pending_landmarks(self, node):
        pending_landmarks = []
        for bit_pos in range(len(bin(node.lm_node.lms)-2)):
            if node.lm_node.lms & (1 << bit_pos) and ~node.lm_node.marked & (1 << bit_pos):
                pending_landmarks.append(bit_pos)
        return pending_landmarks
    
    def update_var_bounds(self, new_ip_problem, pending_landmarks, TNI):
        # get variables from problem
        var_dict = new_ip_problem.lp_problem.variablesDict()
        #update tni variables (TNI is an array of task nodes)
        for TNI_node in TNI:
            var_dict[f'TNC_{TNI_node.name}'].lowBound += 1
            var_dict[f'TNC_{TNI_node.name}'].upBound  += 1
        #set lower bound of '1' to every pending landmark (need to be reached at least 1 time)
        for node_id in pending_landmarks:
            node = self.landmarks.bu_AND_OR.nodes[node_id]
            if f'UN_{node.name}' in var_dict:
                var_dict[f'UN_{node.name}'].lowBound = 1
            else:
                var_dict[f'M_{node.name}'].lowBound = 1
        
    def _build_ip_model(self):
        # initialize auxiliary structure
        self.mst = {n.global_id: [] for n in self.model.operators + self.model.abstract_tasks}
        for d in self.model.decompositions:
            for subt in d.task_network:
                self.mst[subt.global_id].append(d)

        # initialize variables
        self.UAn_vars = {n.global_id: pulp.LpVariable(f"UN_{n.name}", lowBound=0, cat='Integer') for n in self.model.abstract_tasks + self.model.operators}
        self.mm_vars = {m.global_id: pulp.LpVariable(f"M_{m.name}", lowBound=0, cat='Integer') for m in self.model.decompositions}
        self.tni_constants = {n.global_id: pulp.LpVariable(f"TNC_{n.name}", lowBound=0, upBound=0, cat='Integer') for n in self.model.abstract_tasks + self.model.operators}
        
        # constraints
        self.zero_lpmodel += pulp.lpSum([self.UAn_vars[n.global_id] for n in self.model.abstract_tasks] + [self.UAn_vars[n.global_id] for n in self.model.operators])
        for abt in self.model.abstract_tasks:
            self.zero_lpmodel += self.UAn_vars[abt.global_id] == pulp.lpSum([self.mm_vars[d.global_id] for d in abt.decompositions]), f"Decomposition_{abt.name}"
        for n in self.model.abstract_tasks + self.model.operators:
            self.zero_lpmodel += self.UAn_vars[n.global_id] == self.tni_constants[n.global_id] + pulp.lpSum([self.mm_vars[m.global_id] for m in self.mst.get(n.global_id, [])]), f"Task_{n.name}"
    
        # starting model
        self.solve_ip(self.zero_lpmodel)

    def solve_ip(self, lp_problem):
        lp_problem.solve(pulp.PULP_CBC_CMD(msg=False))        
        objective_value = pulp.value(self.lp_problem.objective)
        return objective_value 
        #return self.lp_problem.status, pulp.LpStatus[self.lp_problem.status]
      
    def copy_lp_problem(self, lp_problem):
        new_lp_problem = pulp.LpProblem("TaskDecomposition", pulp.LpMinimize)
        
        for var in lp_problem.variables():
            new_var = pulp.LpVariable(var.name, lowBound=var.lowBound, upBound=var.upBound, cat=var.cat)
            if var.varValue is not None:
                new_var.setInitialValue(var.varValue)
            new_lp_problem.variablesDict()[var.name] = new_var
        
        new_lp_problem += lp_problem.objective
        for name, constraint in lp_problem.constraints.items():
            new_lp_problem += constraint, name
        
        return new_lp_problem


    def print_variables_and_constraints(self, lp_problem):
        print("Variables:")
        for v in lp_problem.variables():
            if v.varValue >= 1:
                print(f"name={v.name} bounds=({v.lowBound}, {v.upBound}) value={v.varValue}")
        # print("\nConstraints:")
        # for name, constraint in self.lp_problem.constraints.items():
        #     print(f"{name}: {constraint}")



        # remove executed_task from TN count
        #etask_id = executed_task.global_id
        #etask_constraint_name = f"TNC({executed_task.name})"
        #self.tn_count[etask_id]-=1
        #var_dict[etask_constraint_name].upBound = self.tn_count[etask_id]
        #var_dict[etask_constraint_name].lowBound = self.tn_count[etask_id]
        
        # change bound for landmark task '0'
        #if etask_id in self.lm_set:
        #    var_dict[f'UN({executed_task.name})'].lowBound = 0
        
        # if not executed_method:
        #     return

        # add new tasks into the constraint changing the TN count (rhs constraint)
        # for task in executed_method.task_network:
        #     task_id = task.global_id
        #     self.tn_count[task_id]+=1
        #     task_constraint_name = f"TNC({task.name})"
        #     var_dict[task_constraint_name].upBound = self.tn_count[task_id]
        #     var_dict[task_constraint_name].lowBound = self.tn_count[task_id]
            
            
        # if executed_method.global_id in self.lm_set:
        #     var_dict[f'M_{executed_method.name}'].lowBound = 0