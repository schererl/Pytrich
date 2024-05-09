from .heuristic import Heuristic
class TaskCountHeuristic(Heuristic):
    def __init__(self):
        super().__init__()
    
    def compute_heuristic(self, model, parent_node, node):
        return len(node.task_network)
        # if parent_node:
        #     if type(task) is Operator:
        #         return parent_node.h_val
            
        #     return parent_node.h_val-task.h_val
        # else:
            
        #     return len(model.initial_tn)