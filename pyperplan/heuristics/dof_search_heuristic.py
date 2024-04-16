import heapq
import psutil

from .heuristic import Heuristic
from ..model import Operator
from ..search.htn_node import AstarNode, HTNNode, DofNode
from ..utils import UNSOLVABLE
from .task_decomposition_heuristic import TaskDecompositionHeuristic

import random
class DofSearchHeuristic(Heuristic):
    def __init__(self):
        super().__init__()
    def compute_heuristic(self, model, parent_node, task, state, task_network):
        if parent_node:
            return self.relaxed_search(model, HTNNode(parent_node, task, state, task_network[:], 0, 0, 0))
        else:
            return self.relaxed_search(model, HTNNode(None, None, state, task_network[:], 0, 0, 0))

    
    def relaxed_search(self, model, init_node, node_type = DofNode):
        seq_num = 0
        visited = set()

        h = TaskDecompositionHeuristic()
        node = node_type(init_node.parent, init_node.action, init_node.state, init_node.task_network[:], 0, 0, h.compute_heuristic(model, init_node.parent, init_node.action, init_node.state, init_node.task_network))
        pq = []
        heapq.heappush(pq, node)
        
    
        while pq:
            node = heapq.heappop(pq)
            if psutil.virtual_memory().percent > 85:
                return UNSOLVABLE
            if model.goal_reached(node.state, node.task_network):
                return node.g_value

            elif len(node.task_network) == 0:
                continue
            

            task = random.choice(node.task_basket)
            node.task_basket.remove(task)
            if node.task_basket:
                node.reinsertions+=1
                heapq.heappush(pq, node)
            
            if type(task) is Operator:
                if not task.applicable_bitwise(node.state):
                    continue
                
                seq_num += 1
                new_state = task.relaxed_apply_bitwise(node.state)
                new_task_network = node.task_network[1:]
                new_node = node_type(node, task, new_state, new_task_network, seq_num, node.g_value+1, h.compute_heuristic(model, node, task, new_state, new_task_network))
                if new_node in visited:
                    continue 
                
                heapq.heappush(pq, new_node)
                
            else:
                for method in task.decompositions:
                    if not method.applicable_bitwise(node.state):
                        continue
                    seq_num += 1
                    new_task_network= method.task_network+node.task_network[1:]
                    new_node = node_type(node, task, node.state, new_task_network, seq_num, node.g_value+1, h.compute_heuristic(model, node, task, node.state, new_task_network))
                    if new_node in visited:
                        continue
                    
                    heapq.heappush(pq, new_node)
            
            
            visited.add(node)
        return UNSOLVABLE