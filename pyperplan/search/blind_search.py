from collections import deque
import logging

from . import htn_node
from ..model import Operator
import time

import heapq

#!/usr/bin/env python
import psutil

from .heuristic import BlindHeuristic, FactCountHeuristic, TaskCountHeuristic
from utils import UNSOLVABLE
from .htn_node import BlindNode, AstarNode

'''
NOTE: Victor SP 14.01.21: Made some optimizations defining Strategy pattern.
*  observed  a significant improve if we diretly call the operation -applicable, apply, decompose, etc..- 
directly from the task, instead of using the model function calls, but this would compromise code readability.
'''

class Bucket:
    def __init__(self, size):
        self.size = size+1
        self.bucket = [deque() for _ in range(self.size)]
        self.current = UNSOLVABLE
        
    
    def push_bucket(self, key, element):
        self.bucket[key].append(element)
        if self.current>key:
            self.current = key
    
    def pop_bucket(self):
        if self.is_empty():
            raise IndexError("Pop from empty bucket")

        element = self.bucket[self.current].popleft()
        
        if not self.bucket[self.current]:
            self._update_current()

        return element

    def _update_current(self):
        next_non_empty = next((idx for idx in range(self.current + 1, self.size) if self.bucket[idx]), None)
        self.current = next_non_empty if next_non_empty is not None else UNSOLVABLE
    
    def is_empty(self):
        return self.current == UNSOLVABLE
    
    def __str__(self):
        _str = 'bucket: '
        for i in range(self.size):
            _str += f"b{i}: {len(self.bucket[i])} element(s) |"
        _str += '\n'
        return _str

    
#def blind_search(model, heuristic_type = BlindHeuristic, node_type = BlindNode):
def blind_search(model, heuristic_type = TaskCountHeuristic, node_type = AstarNode):
    print('Staring solver')
    print(model)
    time.sleep(1)
    h = heuristic_type()
    
    start_time = time.time()  # Initialize the start time
    control_time = start_time

    #NOTE: loop control
    iteration = 0
    count_revisits=0
    seq_num=0
    #visited = set()
    node = node_type(None, None, model.initial_state, model.initial_tn, seq_num=seq_num, g_value=0, heuristic=0)
    h.compute_heuristic(model, None, node)
    initial_heuristic_value=node.heuristic
    h_sum=node.heuristic
    
    #pq = []
    #heapq.heappush(pq, node)

    bucket = Bucket(node.heuristic)
    bucket.push_bucket(node.heuristic, node)
    
    #while pq:
    while not bucket.is_empty():
        iteration += 1
        current_time = time.time()      
        
        
        #node = heapq.heappop(pq)
        node = bucket.pop_bucket()
        
        h_sum+=node.heuristic
        #print(node.heuristic, end = ' ')
        # time and memory control
        if current_time - control_time > 1:
            psutil.cpu_percent()
            print(f"(Elapsed Time: {current_time - start_time:.2f} seconds, Nodes/second: {iteration/float(current_time - start_time):.2f} n/s, h-avg {h_sum/iteration:.2f}, Expanded Nodes: {iteration}. Revists Avoided: {count_revisits}, Used Memory: {psutil.virtual_memory().percent}")
            control_time = time.time()
            if psutil.virtual_memory().percent > 85:
                logging.info('OUT OF MEMORY')
                logging.info("%d Nodes expanded" % iteration)
                logging.info(f"Elapsed Time: {current_time - start_time:.2f} seconds, Nodes/second: {iteration/float(current_time - start_time):.2f} n/s, Expanded Nodes: {iteration}. Revists Avoided: {count_revisits}, Used Memory: {psutil.virtual_memory().percent}")
                logging.info(f"h-init: {initial_heuristic_value}, h-avg {h_sum/iteration:.2f}, heuristic type: {heuristic_type}")
                return None
            if current_time - start_time > 60:
                logging.info("TIMEOUT.")
                logging.info("%d Nodes expanded" % iteration)
                logging.info(f"Elapsed Time: {current_time - start_time:.2f} seconds, Nodes/second: {iteration/float(current_time - start_time):.2f} n/s, Expanded Nodes: {iteration}. Revists Avoided: {count_revisits}, Used Memory: {psutil.virtual_memory().percent}")
                logging.info(f"h-init: {initial_heuristic_value}, h-avg {h_sum/iteration:.2f}, heuristic type: {heuristic_type}")
                return None
            
        #print(f'\n:FRINGE({len(queue)}): {node}')
        if model.goal_reached(node.state, node.task_network):
            logging.info("Goal reached. Start extraction of solution.")
            logging.info("%d Nodes expanded" % iteration)
            logging.info(f"Elapsed Time: {current_time - start_time:.2f} seconds, Nodes/second: {iteration/float(current_time - start_time):.2f} n/s, Expanded Nodes: {iteration}. Revists Avoided: {count_revisits}, Used Memory: {psutil.virtual_memory().percent}")
            logging.info(f"h-init: {initial_heuristic_value}, h-avg {h_sum/iteration:.2f}, heuristic type: {heuristic_type}")
            return node.extract_solution()
        
        elif len(node.task_network) == 0: #task network empty but goal wasnt achieved
            continue
        task = node.task_network[0]
        
        # check if task is primitive
        if type(task) is Operator:
            #print(f'\n:APPLY: {task}')
            if not model.applicable(task, node.state):
                #print(f':NOT APPLICABLE:')
                continue
            
            seq_num += 1
            new_node = node_type(node, task, task.apply_bitwise(node.state), node.task_network[1:], seq_num=seq_num, g_value = node.g_value+1, heuristic=0)
            h.compute_heuristic(model, node, new_node)
             
            # if new_node in visited:
            #     count_revisits+=1
            #     continue
            
            #heapq.heappush(pq, new_node)
            bucket.push_bucket(new_node.heuristic, new_node)
            
        # otherwise its abstract
        else:
            for method in model.methods(task):
                if not model.applicable(method, node.state):
                    #print(f':NOT APPLICABLE:')
                    continue

                #print(f'\n:APPLY: {method}')        
                seq_num += 1
                new_node = node_type(node, task, node.state,  model.decompose(method)+node.task_network[1:], seq_num = seq_num, g_value = node.g_value+1, heuristic=0)
                h.compute_heuristic(model, node, new_node)
                
                # if new_node in visited:
                #     count_revisits+=1
                #     continue
                
                #heapq.heappush(pq, new_node)
                bucket.push_bucket(new_node.heuristic, new_node)
        #visited.add(node)
     
    #NOTE: INTERESTING, when using '<' in prio queue it expands more nodes using less time:
    # python3 pyperplan/__main__.py benchmarks/Blocksworld-GTOHP/domain.hddl benchmarks/Blocksworld-GTOHP/p12.hddl                   
    logging.info("No operators left. Task unsolvable.")
    logging.info("%d Nodes expanded" % iteration)
    return None

#         #visited.add(node)
     
#     #NOTE: INTERESTING, when using '<' in prio queue it expands more nodes using less time:
#     # python3 pyperplan/__main__.py benchmarks/Blocksworld-GTOHP/domain.hddl benchmarks/Blocksworld-GTOHP/p12.hddl                   
#     if RELAXED:
#         return UNSOLVABLE      
#     logging.info("No operators left. Task unsolvable.")
#     logging.info("%d Nodes expanded" % iteration)
#     return None

