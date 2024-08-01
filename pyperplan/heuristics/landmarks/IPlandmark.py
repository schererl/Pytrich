from collections import deque
from copy import deepcopy
import gc
import pulp

class IPLandmarks:
    def __init__(self, model):
        self.model = model
        self.nodes_lenght = len(model.facts) + len(model.operators) + len(model.abstract_tasks) + len(model.decompositions)
        self.nodes = ["none"] * self.nodes_lenght
        self.node_type = [-1] * self.nodes_lenght
        self.node_predecessors = [[] for _ in range(self.nodes_lenght)]
        self.node_reachable = [1] * self.nodes_lenght
        
        
        self.ip_model = []
        self._initialize_graph(model)
        self.initialize_ilp_model()
        self.solve_ilp_model()
        

    def _initialize_graph(self, model):
        
        # set facts
        number_facts = len(model.facts)
        for fact_pos in range(number_facts):
            self.nodes[fact_pos] = model._int_to_explicit[fact_pos]
            print(f'{self.nodes[fact_pos]}: {fact_pos}')
            self.node_type[fact_pos] = 1 # OR
            if model.initial_state & (1 << fact_pos):
                self.node_type[fact_pos] = 0 # INIT
                
        for t_i, t in enumerate(model.abstract_tasks):
            self.nodes[t.global_id] = t.name
            self.node_type[t.global_id] = 1 # OR
            
            
        # set primitive tasks -operators
        for op_i, op in enumerate(model.operators):  
            self.nodes[op.global_id] = op.name
            self.node_type[op.global_id] =  2 # AND
            for fact_pos in range(number_facts):
                if op.pos_precons_bitwise & (1 << fact_pos):
                    self.add_predecessor(op.global_id, fact_pos)
                
                if op.add_effects_bitwise & (1 << fact_pos):
                    self.add_predecessor(fact_pos, op.global_id)
                    

        # set methods
        for d_i, d in enumerate(model.decompositions):
            self.nodes[d.global_id]=d.name
            self.add_predecessor(d.compound_task.global_id, d.global_id)
            self.node_type[d.global_id] = 2 # AND
            
            for subt in d.task_network:
                self.add_predecessor(d.global_id, subt.global_id)
            
            for fact_pos in range(number_facts):
                if d.pos_precons_bitwise & (1 << fact_pos):
                    self.add_predecessor(d.global_id, fact_pos)
                    
        
    def add_predecessor(self, node, pred):
        if not pred in self.node_predecessors[node]:
            self.node_predecessors[node].append(pred)


    def initialize_ilp_model(self):
        self.lp_problem = pulp.LpProblem("Landmark_Propagation", pulp.LpMinimize)
        self.landmarks = {n1: {n2: pulp.LpVariable(f"L_({self.nodes[n1]},{self.nodes[n2]})", 0, 1, pulp.LpBinary) for n2 in range(self.nodes_lenght)} for n1 in range(self.nodes_lenght)}
        
        #print(self.landmarks)
        for lm_dict in self.landmarks.values():
            for lm_var in lm_dict.values():
                lm_var.setInitialValue(1, check=True)

        # Initialization: Nodes with no predecessors
        for node in range(self.nodes_lenght):
            if len(self.node_predecessors[node]) == 0:
                for lm in range(self.nodes_lenght):
                    self.landmarks[node][lm].upBound = 0
                    self.landmarks[node][lm].lowBound = 0
            self.landmarks[node][node].upBound = 1
            self.landmarks[node][node].lowBound = 1

        # Initialization: Unreachable nodes
        for n1 in range(self.nodes_lenght):
            if self.node_reachable[n1] == 0:
                for n2 in range(self.nodes_lenght):
                    self.landmarks[n1][n2].lowBound = 0
                    self.landmarks[n1][n2].upBound = 0
            else:
                for n2 in range(self.nodes_lenght):
                    if self.node_reachable[n2] == 0:
                        self.landmarks[n1][n2].lowBound = 0
                        self.landmarks[n1][n2].upBound = 0

        M = 1000
        # Add AND-OR landmarks
        for node in range(self.nodes_lenght):
            if self.node_reachable[node] == 0:
                continue
            valid_predecessors = [p for p in self.node_predecessors[node]  if self.node_reachable[p] == 1]
            for lm in range(self.nodes_lenght):
                if lm == node:
                    continue

                if self.node_type[node] == 1:
                    if len(valid_predecessors) > 0:
                        constraint = self.landmarks[node][lm] >= pulp.lpSum([self.landmarks[pred][lm] for pred in valid_predecessors]) - len(valid_predecessors) + 1
                        self.lp_problem += constraint
                    
                    for pred in valid_predecessors:
                        constraint = self.landmarks[node][lm] <= self.landmarks[pred][lm]  + M * (1 - self.node_reachable[pred])
                        self.lp_problem += constraint
                
                elif self.node_type[node] == 2:  # AND node
                    if len(valid_predecessors) > 0:
                        constraint = self.landmarks[node][lm] <= pulp.lpSum([self.landmarks[pred][lm] for pred in valid_predecessors])
                        self.lp_problem += constraint
                    
                    for pred in valid_predecessors:
                        constraint = self.landmarks[node][lm] >= self.landmarks[pred][lm]  - M * (1 - self.node_reachable[pred])
                        self.lp_problem += constraint
                else:
                    constraint = self.landmarks[node][lm] == 0
                    self.lp_problem += constraint

        self.lp_problem += -pulp.lpSum([self.landmarks[n1][n2] for n2 in range(self.nodes_lenght) for n1 in range(self.nodes_lenght)])

    def solve_ilp_model(self):
        result = self.lp_problem.solve()
        if self.lp_problem.status == pulp.LpStatusOptimal:
            self.print_variables_and_constraints()
        else:
            print("The problem is not solvable.")
            
    
    def print_variables_and_constraints(self):
        for t in self.model.initial_tn:
            n1 = t.global_id
            for n2 in range(self.nodes_lenght):
                v = self.landmarks[n1][n2]
                if v.varValue is not None and v.varValue >= 1:
                    print(f"name={v.name} bounds=({v.lowBound}, {v.upBound}) value={v.varValue}")
        
        for fact in range(len(bin(self.model.goals))-2):
            if self.model.goals & (1 << fact):
                for n2 in range(self.nodes_lenght):
                    v = self.landmarks[fact][n2]
                    if v.varValue is not None and v.varValue >= 1:
                        print(f"name={v.name} bounds=({v.lowBound}, {v.upBound}) value={v.varValue}")


