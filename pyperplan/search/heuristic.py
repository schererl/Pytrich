from . import relaxed_search

class Heuristic:
    def __init__(self):
        pass
    @staticmethod
    def compute_heuristic(model, parent_node, node):
        pass
class BlindHeuristic(Heuristic):
    def __init__(self):
        super().__init__()
    @staticmethod
    def compute_heuristic(model, parent_node, node):
        node.heuristic = 0
class RelaxedHeuristic(Heuristic):
    def __init__(self):
        super().__init__()
    @staticmethod
    def compute_heuristic(model, parent_node, node):
        node.heuristic=relaxed_search.relaxed_search(model, node)
class TaskCountHeuristic(Heuristic):
    def __init__(self):
        super().__init__()
    @staticmethod
    def compute_heuristic(model, parent_node, node):
        if parent_node:
            return parent_node.heuristic-node.task.h_goal_val
        else:
            len(node.task_network)
