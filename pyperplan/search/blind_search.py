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
#NOTE: testing bucket search
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

def blind_search(model, heuristic_type = TaskCountHeuristic, node_type = AstarNode):
    print('Staring solver')
    print(model)
    time.sleep(1)
    h = heuristic_type()
    
    start_time = time.time()  
    control_time = start_time

    iteration = 0
    count_revisits=0
    seq_num=0
    
    closed_list = {}
    node = node_type(None, None, model.initial_state, model.initial_tn, seq_num, 0, h.compute_heuristic(model, None, None, model.initial_state, model.initial_tn))
    initial_heuristic_value=node.h_val
    print(f'initial task heuristic: {initial_heuristic_value}')
    h_sum=node.h_val
    
    pq = []
    heapq.heappush(pq, node)

    #bucket = Bucket(node.h_val)
    #bucket.push_bucket(node.h_val, node)
    
    while pq:
    #while not bucket.is_empty():
        iteration += 1
        current_time = time.time()      
        
        node = heapq.heappop(pq)
        
        #node = bucket.pop_bucket()
        h_sum+=node.h_val
        
        try_get_node = closed_list.get(hash(node))
        if try_get_node and try_get_node.g_value < node.g_value:
            count_revisits+=1
            continue 
        
        
        # time and memory control
        if current_time - control_time > 1:
            psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            elapsed_time = current_time - start_time
            nodes_second = iteration/float(current_time - start_time)
            h_avg=h_sum/iteration
            print(f"(Elapsed Time: {elapsed_time:.2f} seconds, Nodes/second: {nodes_second:.2f} n/s, h-avg {h_avg:.2f}, Expanded Nodes: {iteration}. Revists Avoided: {count_revisits}, Used Memory: {memory_usage}")
            control_time = time.time()
            if psutil.virtual_memory().percent > 85:
                logging.info('OUT OF MEMORY')
                logging.info(f"Elapsed Time: {elapsed_time:.2f} seconds, Nodes/second: {nodes_second:.2f} n/s, Expanded Nodes: {iteration}. Revists Avoided: {count_revisits}, Used Memory: {memory_usage}\nh-init: {initial_heuristic_value}, h-avg {h_avg:.2f}, h_val type: {heuristic_type}")
                return create_result_dict('MEMORY', iteration, initial_heuristic_value, h_sum, start_time, current_time, memory_usage, -1)
            
            if current_time - start_time > 60:
                logging.info("TIMEOUT.")
                logging.info(f"Elapsed Time: {elapsed_time:.2f} seconds, Nodes/second: {nodes_second:.2f} n/s, Expanded Nodes: {iteration}. Revists Avoided: {count_revisits}, Used Memory: {memory_usage}\nh-init: {initial_heuristic_value}, h-avg {h_avg:.2f}, h_val type: {heuristic_type}")
                return create_result_dict('TIMEOUT', iteration, initial_heuristic_value, h_sum, start_time, current_time, memory_usage, -1)
            
        
        if model.goal_reached(node.state, node.task_network):
            psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            elapsed_time = current_time - start_time
            nodes_second = iteration/float(current_time - start_time)
            h_avg=h_sum/iteration
            logging.info("Goal reached. Start extraction of solution.")
            logging.info(f"Elapsed Time: {elapsed_time:.2f} seconds, Nodes/second: {nodes_second:.2f} n/s, Expanded Nodes: {iteration}. Revists Avoided: {count_revisits}, Used Memory: {memory_usage}\nh-init: {initial_heuristic_value}, h-avg {h_avg:.2f}, h_val type: {heuristic_type}")
            solution = node.extract_solution()
            return create_result_dict('GOAL', iteration, initial_heuristic_value, h_sum, start_time, current_time, memory_usage, len(solution), solution)


        
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
            new_state = model.apply(task, node.state)
            new_task_network = node.task_network[1:]
            new_node = node_type(node, task, new_state, new_task_network, seq_num, node.g_value+1, h.compute_heuristic(model, node, task, new_state, new_task_network))
            heapq.heappush(pq, new_node)
            #bucket.push_bucket(new_node.h_val, new_node)
            
        # otherwise its abstract
        else:
            for method in model.methods(task):
                if not model.applicable(method, node.state):
                    #print(f':NOT APPLICABLE:')
                    continue

                #print(f'\n:APPLY: {method}')        
                seq_num += 1
                new_task_network= model.decompose(method)+node.task_network[1:]
                new_node = node_type(node, task, node.state, new_task_network, seq_num, node.g_value+1, h.compute_heuristic(model, node, task, node.state, new_task_network))
                heapq.heappush(pq, new_node)
                #bucket.push_bucket(new_node.h_val, new_node)
        closed_list[hash(node)]=node
     
    logging.info("No operators left. Task unsolvable.")
    logging.info("%d Nodes expanded" % iteration)
    return create_result_dict('UNSOLVABLE', iteration, initial_heuristic_value, h_sum, start_time, current_time, psutil.virtual_memory().percent, -1)


def create_result_dict(status, iterations, initial_heuristic, h_sum, start_time, end_time, memory_usage, s_size, solution=None):
    elapsed_time = end_time - start_time
    h_avg = h_sum / iterations if iterations > 0 else 0
    nodes_per_second = iterations / elapsed_time if elapsed_time > 0 else 0

    result = {
        'status': status,
        'nodes_expanded': iterations,
        'h_init': initial_heuristic,
        'h_avg': h_avg,
        'elapsed_time': elapsed_time,
        'nodes_per_second': nodes_per_second,
        's_size': s_size,
        'memory_usage': memory_usage
    }
    
    if solution is not None:
        result['solution'] = solution

    return result
