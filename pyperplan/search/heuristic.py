
from ..model import Operator, AbstractTask
#from .relaxed_search import relaxed_search
from .htn_node import HTNNode
import numpy as np
from .htn_node import AstarNode
from utils import UNSOLVABLE
from .htn_node import AstarNode
from collections import deque
import heapq
import psutil
import time
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

class TaskCountHeuristic(Heuristic):
    def __init__(self):
        super().__init__()
    
    def compute_heuristic(self, model, parent_node, task, state, task_network):
        return len(task_network)
        # if parent_node:
        #     if type(task) is Operator:
        #         return parent_node.h_val
            
        #     return parent_node.h_val-task.h_val
        # else:
            
        #     return len(model.initial_tn)

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

class DellEffHeuristic(Heuristic):
    def __init__(self):
        super().__init__()
    def compute_heuristic(self, model, parent_node, task, state, task_network):
        if parent_node:
            return self.relaxed_search(model, HTNNode(parent_node, task, state, task_network[:], 0, 0, 0))
        else:
            return self.relaxed_search(model, HTNNode(None, None, state, task_network[:], 0, 0, 0))

    
    #NOTE: solving relaxed htn problems seem to become harder when getting only add effects
    def relaxed_search(self, model, init_node, node_type = AstarNode):
        seq_num = 0
        visited = set()

        h = TaskDecompositionHeuristic()
        #node = HTNNode(init_node.parent, init_node.action, init_node.state, init_node.task_network[:], 0, 0, 0)
        node = node_type(init_node.parent, init_node.action, init_node.state, init_node.task_network[:], 0, 0, h.compute_heuristic(model, init_node.parent, init_node.action, init_node.state, init_node.task_network))
        queue = deque()
        
        pq = []
        heapq.heappush(pq, node)
        
        #queue.append(node)

        #while queue:
        while pq:
            #node = queue.popleft()
            node = heapq.heappop(pq)
            if psutil.virtual_memory().percent > 85:
                return UNSOLVABLE
            if model.goal_reached(node.state, node.task_network):
                return node.g_value

            elif len(node.task_network) == 0:
                continue
            task = node.task_network[0]
            
            # check if task is primitive
            if type(task) is Operator:
                if not task.applicable_bitwise(node.state):
                    continue
                
                seq_num += 1
                new_state = task.relaxed_apply_bitwise(node.state)
                new_task_network = node.task_network[1:]
                new_node = node_type(node, task, new_state, new_task_network, seq_num, node.g_value+1, h.compute_heuristic(model, node, task, new_state, new_task_network))
                if new_node in visited:
                    continue 
                #queue.append(new_node)
                heapq.heappush(pq, new_node)
                
            # otherwise its abstract
            else:
                for method in task.decompositions:
                    if not method.applicable_bitwise(node.state):
                        continue
                    seq_num += 1
                    new_task_network= method.task_network+node.task_network[1:]
                    new_node = node_type(node, task, node.state, new_task_network, seq_num, node.g_value+1, h.compute_heuristic(model, node, task, node.state, new_task_network))
                    if new_node in visited:
                        continue
                    #queue.append(new_node)
                    heapq.heappush(pq, new_node)
            
            
            visited.add(node)
        return UNSOLVABLE

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

    def _rechable_operators(self, visited, rechable_op ,task):
        if task in visited:
            return 
        
        visited.add(task)
        if isinstance(task, Operator):
            rechable_op.add(task)
            return
        else:
            for decomposition in task.decompositions:
                for subtask in decomposition.task_network:
                    self._rechable_operators(visited, rechable_op, subtask)
        

    
    def del_relax_count(self, model, task_network, state):
        curr_state = state
        op_available = set()
        visited=set()
        for task in task_network:
           self._rechable_operators(visited, op_available, task)
        
        it_count = 0
        changed = True
        goal_reached = False
        
        while changed:
            changed = False
            new_state = curr_state
            if (new_state & model.goals) == (model.goals):
                goal_reached = True
                break
            
            to_remove = set()  
            for o in op_available:
                if o.applicable_bitwise(new_state):
                    curr_state |= o.relaxed_apply_bitwise(curr_state)
                    to_remove.add(o) 
                    changed = True
                    
            
            op_available-=to_remove 
            it_count += 1
        
        if not goal_reached:
            return UNSOLVABLE
        return it_count



    def compute_heuristic(self, model, parent_node, task, state, task_network):
        if parent_node:
            return sum([t.h_val for t in task_network]) + self.del_relax_count(model, task_network, state)
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

