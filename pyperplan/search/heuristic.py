from . import relaxed_search
from ..model import Operator
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
            if type(node.action) is Operator:
                node.heuristic = parent_node.heuristic
                return
            
            node.heuristic= parent_node.heuristic-node.action.is_goal_task
        else:
            node.heuristic= len(node.task_network)

class FactCountHeuristic(Heuristic):
    def __init__(self):
        super().__init__()
    @staticmethod
    def compute_heuristic(model, parent_node, node):
        if parent_node:
            if not type(node.action) is Operator:
                node.heuristic = parent_node.heuristic
                return
            
            goal_count = 0
            # for s in node.state:
            #     if s in model.goals:
            #         goal_count+=1

            bit_state = node.state
            bit_goal = model.goals
            #NOTE: here goal facts should be the k-first bits positions, otherwise won't work
            while bit_goal:
                if (bit_state & 1) and (bit_goal & 1):
                    goal_count += 1
                bit_state >>= 1
                bit_goal >>= 1
            
            node.heuristic= model.goal_facts_count - goal_count
        else:
            node.heuristic= model.goal_facts_count
