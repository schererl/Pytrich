from . import relaxed_search
from ..model import Operator, AbstractTask
class Heuristic:
    def __init__(self):
        pass
    
    def compute_heuristic(self, model, parent_node, task, state, task_network):
        pass

class BlindHeuristic(Heuristic):
    def __init__(self):
        super().__init__()
    
    def compute_heuristic(self, model, parent_node, task, state, task_network):
        return 0

# class RelaxedHeuristic(Heuristic):
#     def __init__(self):
#         super().__init__()
#     @staticmethod
#     def compute_heuristic(model, parent_node, node):
#         return relaxed_search.relaxed_search(model, node)

class TaskCountHeuristic(Heuristic):
    def __init__(self):
        super().__init__()
    
    def compute_heuristic(self, model, parent_node, task, state, task_network):
        if parent_node:
            if type(task) is Operator:
                return parent_node.h_val
            
            return parent_node.h_val-task.h_val
        else:
            
            return len(model.initial_tn)

class FactCountHeuristic(Heuristic):
    def __init__(self):
        super().__init__()

    
    def compute_heuristic(self, model, parent_node, task, state, task_network):
        if parent_node:
            if not type(task) is Operator:
                return parent_node.h_val
            
            goal_count = 0
            bit_state = state
            bit_goal = model.goals
            #NOTE: here goal facts should be the k-first bits positions, otherwise won't work
            while bit_goal:
                if (bit_state & 1) and (bit_goal & 1):
                    goal_count += 1
                bit_state >>= 1
                bit_goal >>= 1
            
            
            return model.goal_facts_count - goal_count
        else:
            
            return model.goal_facts_count

##### EXPERIMENTAL HEURISTICS ########
'''
    * I think this is a better way for computing Task Count:
        instead of counting the number of completed tasks from initial task network,
        use the lowest number of subtasks required for completing the initial task netwrok;
'''        
class TaskDecompositionHeuristic(Heuristic):
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

    def compute_heuristic(self, model, parent_node, task, state, task_network):
        if parent_node:
            return sum([t.h_val for t in task_network])
        else:
            h_sum = sum([self._compute_tdg_values(t) for t in model.initial_tn])
            self.visited.clear()
            return h_sum


class DoubleCountHeuristic(Heuristic):
    def __init__(self):
        self.fact_h = FactCountHeuristic()
        self.task_h = TaskCountHeuristic()
        super().__init__()
    
    def compute_heuristic(self, model, parent_node, task, state, task_network):
        #compute h1
        h1=0
        if parent_node:
            if not type(task) is Operator:
                h1= parent_node.h_val[0]
            else:
                goal_count = 0
                bit_state = state
                bit_goal = model.goals
                while bit_goal:
                    if (bit_state & 1) and (bit_goal & 1):
                        goal_count += 1
                    bit_state >>= 1
                    bit_goal >>= 1
                h1=model.goal_facts_count - goal_count
        else:
            h1=model.goal_facts_count
        #compute h2
        h2=0
        if parent_node:
            if type(task) is Operator:
                h2=parent_node.h_val[1]
            else:
                h2=parent_node.h_val[1]-task.is_goal_task
        else:
            
            h2=len(model.initial_tn)
        return [h1, h2] 


class MaxCountHeuristic(Heuristic):
    def __init__(self):
        self.fact_h = FactCountHeuristic()
        self.task_h = TaskCountHeuristic()
        super().__init__()
    
    
    def compute_heuristic(self, model, parent_node, task, state, task_network):
        return max(self.fact_h.compute_heuristic(model, parent_node, task, state), self.task_h.compute_heuristic(model, parent_node, task, state))

