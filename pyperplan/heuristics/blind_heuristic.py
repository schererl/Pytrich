from .heuristic import Heuristic

class BlindHeuristic(Heuristic):
    def __init__(self):
        super().__init__()
    
    def compute_heuristic(self, model, parent_node, task, state, task_network):
        return 0