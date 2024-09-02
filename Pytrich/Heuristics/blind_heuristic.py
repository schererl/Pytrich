from Pytrich.Heuristics.heuristic import Heuristic

class BlindHeuristic(Heuristic):
    def __call__(self, parent_node, node):
        return 0