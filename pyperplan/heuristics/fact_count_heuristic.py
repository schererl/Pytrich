from .heuristic import Heuristic
from ..model import Operator

class FactCountHeuristic(Heuristic):
    def __init__(self):
        super().__init__()

    
    def compute_heuristic(self, model, parent_node, task, state, task_network):
        import time
        if parent_node:
            if not type(task) is Operator:
                return parent_node.h_val
            
            #NOTE: here goal facts should be the k-last bits positions, otherwise won't work
            count_zeros = 0
            for i in bin(state)[len(bin(state))-len(bin(model.goals))-2:]:
                if int(i) == 0:
                    count_zeros+=1
            return count_zeros
        else:
            
            return model.goal_facts_count