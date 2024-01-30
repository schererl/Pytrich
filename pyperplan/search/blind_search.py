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

#def blind_search(model, heuristic_type = BlindHeuristic, node_type = BlindNode):
def blind_search(model, heuristic_type = BlindHeuristic, node_type = AstarNode):
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
    visited = set()
    node = node_type(None, None, model.initial_state, model.initial_tn, seq_num=seq_num, g_value=0, heuristic=0)
    h.compute_heuristic(model, None, node)
    print(node.task_network)
    print(node.heuristic)
    pq = []
    
    heapq.heappush(pq, node)
    while pq:
        iteration += 1
        current_time = time.time()      
        node = heapq.heappop(pq)
        #print(node.heuristic, end = ' ')
        # time and memory control
        if current_time - control_time > 1:
            psutil.cpu_percent()
            print(f"(Elapsed Time: {current_time - start_time:.2f} seconds, Expanded Nodes: {iteration}. Revists Avoided: {count_revisits}, Used Memory: {psutil.virtual_memory().percent}")
            control_time = time.time()
            if psutil.virtual_memory().percent > 85:
                raise Exception('OUT OF MEMORY')
            
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
            new_node = node_type(node, task, model.apply(task, node.state), node.task_network[1:], seq_num=seq_num, g_value = node.g_value+1, heuristic=0)
            h.compute_heuristic(model, node, new_node)
            if new_node.heuristic == UNSOLVABLE:
                #visited.add(node)
                continue 
            # if new_node in visited:
            #     count_revisits+=1
            #     continue
            heapq.heappush(pq, new_node)
            
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
                if new_node.heuristic == UNSOLVABLE:
                    #visited.add(node)
                    continue
                
                # if new_node in visited:
                #     count_revisits+=1
                #     continue
                
                heapq.heappush(pq, new_node)
        #visited.add(node)
     
    #NOTE: INTERESTING, when using '<' in prio queue it expands more nodes using less time:
    # python3 pyperplan/__main__.py benchmarks/Blocksworld-GTOHP/domain.hddl benchmarks/Blocksworld-GTOHP/p12.hddl                   
    logging.info("No operators left. Task unsolvable.")
    logging.info("%d Nodes expanded" % iteration)
    return None





















# from collections import deque
# import logging

# from . import htn_node
# from ..model import Operator
# import time

# import heapq

# #!/usr/bin/env python
# import psutil


# UNSOLVABLE = 123456789123
# def blind_search(model, INIT_NODE = None, RELAXED=False):
    
#     if not RELAXED:
#         print('Staring solver')
#         print(model)
#         time.sleep(1)
    
#     start_time = time.time()  # Initialize the start time
#     control_time = start_time

#     #NOTE: loop control
#     iteration = 0
#     count_revisits=0
#     seq_num=0
#     visited = set()
    
#     if RELAXED:
#         node = htn_node.make_node(None, None, INIT_NODE.state, INIT_NODE.task_network[:], seq_num=seq_num, g_value=0, heuristic=0)
#     else:
#         node = htn_node.make_node(None, None, model.initial_state, model.initial_tn, seq_num=seq_num, g_value=0, heuristic=0)
#         node.heuristic=0#blind_search(model, INIT_NODE=node,RELAXED=True)
        
#     #queue = deque()
#     #queue.append(node)
#     pq = []
#     heapq.heappush(pq, node)

#     #while queue:
#     while pq:
#         iteration += 1
#         current_time = time.time()  
        
#         #node = queue.popleft()
#         #node = pq.get()
#         node = heapq.heappop(pq)
#         #print(f'\n:FRINGE({len(queue)}): {node}')
#         if not RELAXED and current_time - control_time > 1:
#             psutil.cpu_percent()
#             print(f"(Elapsed Time: {current_time - start_time:.2f} seconds, Expanded Nodes: {iteration}. Revists Avoided: {count_revisits}, Used Memory: {psutil.virtual_memory().percent}")
#             control_time = time.time()
#             if psutil.virtual_memory().percent > 85:
#                 raise Exception('OUT OF MEMORY')
#             # if count_revisits == 0:
#             #     visited = set()

#         # if not RELAXED:
#         #     print(node.heuristic)
        
        
#         if model.goal_reached(node.state, node.task_network):
#             if RELAXED:
#                 return node.g_value
            
#             logging.info("Goal reached. Start extraction of solution.")
#             logging.info("%d Nodes expanded" % iteration)
#             logging.info(f"Elapsed Time: {current_time - start_time:.2f} seconds, Expanded Nodes: {iteration}. Revists Avoided: {count_revisits}, Used Memory: {psutil.virtual_memory().percent}")
#             return node.extract_solution()
#         elif len(node.task_network) == 0: #task network empty but goal wasnt achieved
#             continue
#         task = node.task_network[0]
        
#         # check if task is primitive
#         if type(task) is Operator:
#             #print(f'\n:APPLY: {task}')
#             if RELAXED and not model.relaxed_applicable(task, node.state):
#                 continue
#             elif not model.applicable(task, node.state):
#                 #print(f':NOT APPLICABLE:')
#                 continue
            
#             seq_num += 1
#             if RELAXED:
#                 new_node = htn_node.make_node(node, task, model.relaxed_apply(task, node.state), node.task_network[1:], seq_num=seq_num, g_value = node.g_value+1, heuristic=0)
#             else:
#                 new_node = htn_node.make_node(node, task, model.apply(task, node.state), node.task_network[1:], seq_num=seq_num, g_value = node.g_value+1, heuristic=0)
#                 new_node.heuristic=0#blind_search(model, INIT_NODE=new_node, RELAXED=True)
#                 if new_node.heuristic == UNSOLVABLE:
#                     continue 
            
#             if new_node in visited:
#                 count_revisits+=1
#                 continue
#             #queue.append(new_node)
#             #pq.put(new_node)
#             heapq.heappush(pq, new_node)
            
        
#         # otherwise its abstract
#         else:
#             for method in model.methods(task):
#                 #print(f'\n:APPLY: {method}')
#                 if RELAXED and not model.relaxed_applicable(method, node.state):
#                     continue
#                 elif not model.applicable(method, node.state):
#                     #print(f':NOT APPLICABLE:')
#                     continue

#                 seq_num += 1
#                 if RELAXED:
#                     new_node = htn_node.make_node(node, task, node.state,  model.decompose(method)+node.task_network[1:], seq_num = seq_num, g_value = node.g_value+1, heuristic=0)
#                 else:
#                     new_node = htn_node.make_node(node, task, node.state,  model.decompose(method)+node.task_network[1:], seq_num = seq_num, g_value = node.g_value+1, heuristic=0)
#                     new_node.heuristic=0#blind_search(model, INIT_NODE=new_node, RELAXED=True)
#                     if new_node.heuristic == UNSOLVABLE:
#                         continue
                
#                 if new_node in visited:
#                     count_revisits+=1
#                     continue
#                 #queue.append(new_node)
#                 #pq.put(new_node)
#                 heapq.heappush(pq, new_node)
                

#         #visited.add(node)
     
#     #NOTE: INTERESTING, when using '<' in prio queue it expands more nodes using less time:
#     # python3 pyperplan/__main__.py benchmarks/Blocksworld-GTOHP/domain.hddl benchmarks/Blocksworld-GTOHP/p12.hddl                   
#     if RELAXED:
#         return UNSOLVABLE      
#     logging.info("No operators left. Task unsolvable.")
#     logging.info("%d Nodes expanded" % iteration)
#     return None

