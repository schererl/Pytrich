from collections import deque
import logging

from . import htn_node
from ..model import Operator
import time

import heapq

#!/usr/bin/env python
import psutil

from ..utils import PriorityQueueNode

def blind_search(model):
    print('Staring solver')
    print(model)
    time.sleep(1)
    
    start_time = time.time()  # Initialize the start time
    control_time = start_time

    #NOTE: loop control
    iteration = 0
    count_revisits=0
    seq_num=0
    visited = set()
    
    node = htn_node.make_node(None, None, model.initial_state, model.initial_tn, seq_num=seq_num, g_value=0, heuristic=h_value)
    
    #queue = deque()
    #queue.append(node)
    pq = []
    heapq.heappush(pq, node)

    #while queue:
    while pq:
        iteration += 1
        current_time = time.time()  
        
        #node = queue.popleft()
        #node = pq.get()
        node = heapq.heappop(pq)
        h_value = node.heuristic
        
        if current_time - control_time > 1:
            psutil.cpu_percent()
            print(f"({h_value} of {model.number_goals}) Elapsed Time: {current_time - start_time:.2f} seconds, Expanded Nodes: {iteration}. Revists Avoided: {count_revisits}, Used Memory: {psutil.virtual_memory().percent}")
            control_time = time.time()
            if psutil.virtual_memory().percent > 85:
                raise Exception('OUT OF MEMORY')
            # if count_revisits == 0:
            #     visited = set()

        
        
        #print(f'\n:FRINGE({len(queue)}): {node}')
        if model.goal_reached(node.state, node.task_network):
            logging.info("Goal reached. Start extraction of solution.")
            logging.info("%d Nodes expanded" % iteration)
            logging.info(f"Elapsed Time: {current_time - start_time:.2f} seconds, Expanded Nodes: {iteration}. Revists Avoided: {count_revisits}, Used Memory: {psutil.virtual_memory().percent}")
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
            new_node = htn_node.make_node(node, task, model.apply(task, node.state), node.task_network[1:], seq_num=seq_num, g_value = node.g_value+1, heuristic=h_value)
            
            if new_node in visited:
                count_revisits+=1
                continue
            
            #queue.append(new_node)
            #pq.put(new_node)
            heapq.heappush(pq, new_node)
            
        
        # otherwise its abstract
        else:
            for method in model.methods(task):
                #print(f'\n:APPLY: {method}')
                if not model.applicable(method, node.state):
                    #print(f':NOT APPLICABLE:')
                    continue

                seq_num += 1
                new_node = htn_node.make_node(node, task, node.state,  model.decompose(method)+node.task_network[1:], seq_num = seq_num, g_value = node.g_value+1, heuristic=h_value)
                
                if new_node in visited:
                    count_revisits+=1
                    continue
                #queue.append(new_node)
                #pq.put(new_node)
                heapq.heappush(pq, new_node)
                

        visited.add(node)
     
    #NOTE: INTERESTING, when using '<' in prio queue it expands more nodes using less time:
    # python3 pyperplan/__main__.py benchmarks/Blocksworld-GTOHP/domain.hddl benchmarks/Blocksworld-GTOHP/p12.hddl                   
            
    logging.info("No operators left. Task unsolvable.")
    logging.info("%d Nodes expanded" % iteration)
    return None

