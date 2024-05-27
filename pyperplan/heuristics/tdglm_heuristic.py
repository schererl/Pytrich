from copy import deepcopy
from .heuristic import Heuristic
from .landmarks.landmark import Landmarks
import pulp 

'''
    TDG Count use an IP formulation to compute the minimal number of tasks to clear the task network
    which completes all landmarks extracting using the 'bidirectional landmarks'.
    - Each new node should 'know' the number of pending landmarks
    - Each new node should update variable bounds
     (1) We have to update the counting on TNI variables, 
        this indicates the number of times each task appears into the current task network
     (2) Each node should update variable bounds according to the pending landmarks

'''
class TDGLmHeuristic(Heuristic):
    def __init__(self, model, initial_node):
        super().__init__(model, initial_node)
        # auxiliar: maps each subtask to each corresponding method that uses it (can appear more than once)
        self.mst = {n.global_id: [] for n in self.model.operators + self.model.abstract_tasks} 

        # generate bidirectional landmarks
        self.landmarks = Landmarks(self.model)
        self.landmarks.bottom_up_lms()
        self.landmarks.top_down_lms()
        self.lm_set = self.landmarks.bidirectional_lms(self.model, initial_node.state, initial_node.task_network)
        
        # IP/LP model variables
        self.ua_vars = {}
        self.mm_vars = {}
        self.tni_constants = {}

        # Preare IP/LP model
        self.ipmodel = pulp.LpProblem("TaskDecomposition", pulp.LpMinimize)
        self._build_ip_model()

        # Compute initial node
        initial_node.h_value = self._solve_ip()
        initial_node.f_value = initial_node.h_value
        initial_node.lp_vars = self._store_lpvars()
         
    def compute_heuristic(self, parent_node, node):
        self._retrieve_ipmodel(parent_node.lp_vars)
        self._update_ipmodel(self.ipmodel.variablesDict(), node.task, node.decomposition)
        node.h_value = self._solve_ip()
        node.f_value = node.h_value + node.g_value
        node.lp_vars = self._store_lpvars()
        
    def _store_lpvars(self):
        # make a copy of each variable's bound and current objective value
        lp_var_cpy = {}
        for name, var in self.ipmodel.variablesDict().items():
            var_info = (var.lowBound, var.upBound, var.varValue)
            lp_var_cpy[name] = var_info
        return lp_var_cpy

    def _retrieve_ipmodel(self, ipnode_vars):
        # get variable values from parent node
        for name, info in ipnode_vars.items():
            model_var = self.ipmodel.variablesDict()[name]
            model_var.lowBound, model_var.upBound, var_varValue = info
            model_var.setInitialValue(var_varValue)

    def _update_ipmodel(self, ipmodel_vars, executed_task, executed_method):
        # update tni variables (TNI is an array of task nodes)
        var_name = f"TNC_{executed_task.name}"
        if executed_task.global_id in self.lm_set:
            ipmodel_var = ipmodel_vars[var_name]
            ipmodel_var.lowBound = ipmodel_var.lowBound - 1
            ipmodel_var.upBound  = ipmodel_var.upBound  - 1
            
        # remove landmark bound if the executed task is a landmark
        # var_name = f"UN_{executed_task.name}"
        # if executed_task.global_id in self.lm_set:
        #     ipmodel_var = ipmodel_vars[var_name]
        #     ipmodel_var.lowBound = 0
            
        if not executed_method:
            return
        
        # update tni variables (add new tasks from method's task network)
        for task in executed_method.task_network:
            var_name = f"TNC_{task.name}"
            ipmodel_var = ipmodel_vars[var_name]
            ipmodel_var.lowBound = ipmodel_var.lowBound + 1
            ipmodel_var.upBound  = ipmodel_var.upBound + 1

        # remove landmark bound if the executed method is a landmark
        # if executed_method.global_id in self.lm_set:
        #     var_name = f'M_{executed_method.name}'
        #     ipmodel_var = ipmodel_vars[var_name]
        #     ipmodel_var.lowBound = 0
        
    def _build_ip_model(self):
        # initialize auxiliary structure
        for d in self.model.decompositions:
            for subt in d.task_network:
                self.mst[subt.global_id].append(d)

        # initialize variables
        self.UAn_vars = {n.global_id: pulp.LpVariable(f"UN_{n.name}", lowBound=0, cat='Integer') for n in self.model.abstract_tasks + self.model.operators}
        self.mm_vars = {m.global_id: pulp.LpVariable(f"M_{m.name}", lowBound=0, cat='Integer') for m in self.model.decompositions}
        self.tni_constants = {n.global_id: pulp.LpVariable(f"TNC_{n.name}", lowBound=0, upBound=0, cat='Integer') for n in self.model.abstract_tasks + self.model.operators}
        
        # set landmark bounds
        # for lm_id in self.lm_set:
        #     if lm_id in self.UAn_vars:
        #         self.UAn_vars[lm_id].lowBound=1
        #     elif lm_id in self.mm_vars:
        #         self.mm_vars[lm_id].lowBound=1

        # set TNI counting
        for t in self.model.initial_tn:
            self.tni_constants[t.global_id].lowBound+=1
            self.tni_constants[t.global_id].upBound+=1

        # constraints
        self.ipmodel += pulp.lpSum([self.UAn_vars[n.global_id] for n in self.model.abstract_tasks] + [self.UAn_vars[n.global_id] for n in self.model.operators])
        for abt in self.model.abstract_tasks:
            self.ipmodel += self.UAn_vars[abt.global_id] == pulp.lpSum([self.mm_vars[d.global_id] for d in abt.decompositions]), f"Decomposition_{abt.name}"
        for n in self.model.abstract_tasks + self.model.operators:
            self.ipmodel += self.UAn_vars[n.global_id] == self.tni_constants[n.global_id] + pulp.lpSum([self.mm_vars[m.global_id] for m in self.mst.get(n.global_id, [])]), f"Task_{n.name}"
    
    def _solve_ip(self):
        self.ipmodel.solve(pulp.PULP_CBC_CMD(msg=False))        
        objective_value = pulp.value(self.ipmodel.objective)
        return objective_value 
      
    def print_variables_and_constraints(self):
        print("Variables:")
        for v in self.ipmodel.variables():
            if v.varValue is not None and v.varValue >= 1:
                print(f"name={v.name} bounds=({v.lowBound}, {v.upBound}) value={v.varValue}")
