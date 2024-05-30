from .heuristic import Heuristic
from ..model import Operator


class TaskDecompositionHeuristic(Heuristic):
    def __init__(self, model, initial_node):
        super().__init__(model, initial_node)
        self.visited = set()
        for t in self.model.initial_tn:
            self._compute_tdg_values(t) 
        self.visited = None  # clear memory

        initial_node.h_value = sum([t.h_val for t in initial_node.task_network])
        initial_node.f_value = initial_node.h_value + initial_node.g_value

    def _compute_tdg_values(self, task):
        if task in self.visited:
            return task.h_val

        self.visited.add(task)
        if isinstance(task, Operator):
            heuristic_value = 1
        else:
            heuristic_values = []
            for decomposition in task.decompositions:
                h_sum = 0
                for subtask in decomposition.task_network:
                    self._compute_tdg_values(subtask) 
                    h_sum += subtask.h_val
                heuristic_values.append(h_sum)
            heuristic_value = min(heuristic_values)+1 if heuristic_values else 1 

        task.h_val = heuristic_value
        return heuristic_value

    def compute_heuristic(self, parent_node, node):
        node.h_value = sum([t.h_val for t in node.task_network])
        node.f_value = node.h_value+node.g_value
