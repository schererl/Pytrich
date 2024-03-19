from .heuristic import Heuristic
from ..model import Operator, AbstractTask
from ..utils import UNSOLVABLE
class TaskDecompositionPlusHeuristic(Heuristic):
    def __init__(self):
        super().__init__()
        self.visited = set()
        
    def _compute_tdg_values(self, task):
        if task in self.visited:
            return task.h_val
        
        self.visited.add(task)
        if isinstance(task, Operator):
            heuristic_value = 1
        else:
            heuristic_values = []
            for decomposition in task.decompositions:
                h_sum=0
                for subtask in decomposition.task_network:
                    self._compute_tdg_values(subtask) 
                    h_sum+=subtask.h_val
                heuristic_values.append(h_sum)
            heuristic_value = min(heuristic_values)+1 if heuristic_values else 1 

        task.h_val = heuristic_value
        return heuristic_value
    
    def _compute_opreach(self, task):
        if isinstance(task, Operator):
            return {task}
        else:
            self.visited.add(task)
            for decomposition in task.decompositions:
                for subtask in decomposition.task_network:
                    if subtask in self.visited and type(subtask) is AbstractTask:
                        task.op_reach.update(subtask.op_reach)
                    else:
                        task.op_reach.update(self._compute_opreach(subtask))
        return task.op_reach

    def _reachable_operators(self, visited, reachable_op, task):
        stack = [task]
        while stack:
            current_task = stack.pop()
            if current_task not in visited:
                visited.add(current_task)
                if isinstance(current_task, Operator):
                    reachable_op.add(current_task)
                else:
                    for decomposition in current_task.decompositions:
                        for subtask in decomposition.task_network:
                            stack.append(subtask)
    
    def del_relax_count(self, model, task_network, state):
        curr_state = state
        op_available = set()
        visited=set()
        sum_h = 0
        
        for task in task_network:
            sum_h+=task.h_val
            #self._reachable_operators(visited, op_available, task)
            if type(task) is AbstractTask:
                op_available.update(task.op_reach)
            else:
                op_available.add(task)
        it_count = 0
        changed = True
        goal_reached = False
        
        while changed:
            changed = False
            to_remove = set()
            
            if (curr_state & model.goals) == (model.goals):
                goal_reached = True
                break

            for o in op_available:
                if o.applicable_bitwise(curr_state):
                    curr_state |= o.relaxed_apply_bitwise(curr_state)
                    to_remove.add(o) 
                    changed = True
            
            op_available-=to_remove 
            it_count += 1
        
        if not goal_reached:
            return UNSOLVABLE
        return sum_h
    
    def compute_heuristic(self, model, parent_node, task, state, task_network):
        if parent_node:
            return self.del_relax_count(model, task_network, state)
        else:
            h_sum = sum([self._compute_tdg_values(t) for t in model.initial_tn])
            self.visited.clear()
            for t in model.initial_tn:
                self._compute_opreach(t)
            

            self.visited.clear()
            return h_sum