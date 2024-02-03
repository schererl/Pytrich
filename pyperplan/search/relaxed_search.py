from collections import deque
import logging

from . import htn_node
from ..model import Operator
import time

import heapq

#!/usr/bin/env python
import psutil
from utils import UNSOLVABLE

#TODO: CODE IS NOT WORKING

#NOTE: solving relaxed htn problems seem to become harder when getting only add effects
def relaxed_search(model, init_node):
    visited = set()
    node = htn_node.make_node(None, None, init_node.state, init_node.task_network[:])
    queue = deque() # faster than priority queue
    queue.append(node)

    start_time = time.time()  # Initialize the start time
    control_time = start_time
    iteration = 0

    while queue:
        node = queue.popleft()
        iteration += 1
        current_time = time.time()  
        # if current_time - control_time > 1:
        #     psutil.cpu_percent()
        #     print(f"(Elapsed Time: {current_time - start_time:.2f} seconds, Fringe Size: {len(queue)}, Expanded Nodes: {iteration}. Used Memory: {psutil.virtual_memory().percent}")
        #     control_time = time.time()
        psutil.cpu_percent()
        if psutil.virtual_memory().percent > 85:
            raise Exception('OUT OF MEMORY')
            
        if model.goal_reached(node.state, node.task_network):
            return node.g_value
        elif len(node.task_network) == 0:
            continue
        
        task = node.task_network[0]
        # check if task is primitive
        if type(task) is Operator:
            if not model.applicable(task, node.state):
                continue
            new_node = htn_node.make_node(node, task, model.relaxed_apply(task, node.state), node.task_network[1:])
            
            if new_node in visited:
                continue
            queue.append(new_node)
            
        # otherwise its abstract
        else:
            for method in model.methods(task):
                if not model.applicable(method, node.state):
                    continue
                
                new_node = htn_node.make_node(node, task, node.state,  model.decompose(method)+node.task_network[1:])
                if new_node in visited:
                    continue
                queue.append(new_node)
                
        visited.add(node)
    return UNSOLVABLE      
    

