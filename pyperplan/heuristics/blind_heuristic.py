from .heuristic import Heuristic

class BlindHeuristic(Heuristic):
    def compute_heuristic(self, parent_node, node):
        return 0