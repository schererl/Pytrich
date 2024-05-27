from collections import deque
import logging

from pyperplan.heuristics.lm_heuristic import LandmarkHeuristic

from . import htn_node
from ..model import Operator
import time

import heapq

#!/usr/bin/env python
import psutil

from .utils import create_result_dict
from ..DOT_output import DotOutput
from .htn_node import AstarNode

from ..heuristics.tdglm_heuristic import TDGLmHeuristic

def search(model, heuristic_type, node_type=AstarNode):
    graph_dot = DotOutput()

    print('Staring solver')
    start_time   = time.time()  
    control_time = start_time

    iteration      = 0
    count_revisits = 0
    seq_num        = 0
    
    closed_list = {}
    node = node_type(None, None, None, model.initial_state, model.initial_tn, seq_num, 0)
    h    = heuristic_type(model, node)
    
    h_sum = node.h_value
    initial_heuristic_value=node.h_value
    
    #graph_dot.add_node(node, model)
    
    STATUS = ''
    pq = []
    heapq.heappush(pq, node)
    while pq:
        iteration += 1
        current_time = time.time()      
        
        node = heapq.heappop(pq)
        #graph_dot.open(node)
        h_sum+=node.h_value
        try_get_node_g_val = closed_list.get(hash(node))
        if try_get_node_g_val and try_get_node_g_val <= node.g_value:
            count_revisits+=1
            #graph_dot.already_visited("")
            continue 
        
        # time and memory control
        if current_time - control_time > 1:
            control_time = time.time()
            memory_usage = psutil.virtual_memory().percent
            elapsed_time = current_time - start_time
            nodes_second = iteration/float(current_time - start_time)
            h_avg        = h_sum/iteration
            print(f"(Elapsed Time: {elapsed_time:.2f} seconds, Nodes/second: {nodes_second:.2f} n/s, h-avg {h_avg:.2f}, Expanded Nodes: {iteration}, Fringe Size: {len(pq)} Revists Avoided: {count_revisits}, Used Memory: {memory_usage}")
            psutil.cpu_percent()
            if psutil.virtual_memory().percent > 85:
                STATUS = 'OUT OF MEMORY'
                break
            elif current_time - start_time > 300:
                STATUS = 'TIMEOUT'
                break
                
        if model.goal_reached(node.state, node.task_network):
            psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            elapsed_time = current_time - start_time
            STATUS = 'GOAL'
            break    
        elif len(node.task_network) == 0: #task network empty but goal wasnt achieved
            continue
        task = node.task_network[0]
        
        # check if task is primitive
        if type(task) is Operator:
            if not model.applicable(task, node.state):
                #graph_dot.not_applicable(":APPLY:"+str(task.name))
                continue
            
            seq_num += 1
            new_state        = model.apply(task, node.state)
            new_task_network = node.task_network[1:]
            new_node         = node_type(node, task, None, new_state, new_task_network, seq_num, node.g_value+1)
            h.compute_heuristic(node, new_node)
            #graph_dot.add_node(new_node, model)
            #graph_dot.add_relation(new_node, ":APPLY:"+str(task.name))
            heapq.heappush(pq, new_node)
            
            
        # otherwise its abstract
        else:
            for method in model.methods(task):
                if not model.applicable(method, node.state):
                    #graph_dot.not_applicable(":DECOMPOSE:"+str(method.name))
                    continue

                seq_num += 1
                new_task_network  = model.decompose(method)+node.task_network[1:]
                new_node          = node_type(node, task, method, node.state, new_task_network, seq_num, node.g_value+1)
                h.compute_heuristic(node, new_node)
                
                #if result != new_node.h_value:
                #    test.print_variables_and_constraints()
                #    print(method.task_network)
                #    print(new_node.task_network)
                #    exit()
                heapq.heappush(pq, new_node)

                #graph_dot.add_node(new_node, model)
                #graph_dot.add_relation(new_node, ":DECOMPOSE:"+str(method.name)+str(model.count_positive_binary_facts(method.pos_precons_bitwise)))
        
                
        #graph_dot.close()
        closed_list[hash(node)]=node.g_value
    
    if STATUS == 'GOAL':
        nodes_second = iteration/float(current_time - start_time)
        h_avg        = h_sum/iteration
        logging.info(f"Goal reached!\n\tElapsed Time: {elapsed_time:.2f} seconds, Nodes/second: {nodes_second:.2f} n/s, Expanded Nodes: {iteration}, Revists Avoided: {count_revisits}, Used Memory: {memory_usage}\nh-init: {initial_heuristic_value}, h-avg {h_avg:.2f}, h_val type: {heuristic_type}")
        #graph_dot.to_graphviz()
        solution, operators = node.extract_solution()
        #print(solution)
        return create_result_dict('GOAL', iteration, initial_heuristic_value, h_sum, start_time, current_time, memory_usage, len(solution), len(operators), solution)
    elif STATUS =='OUT OF MEMORY' or STATUS == 'TIMEOUT':
        logging.info(f"{STATUS} \nElapsed Time: {elapsed_time:.2f} seconds, Nodes/second: {nodes_second:.2f} n/s, Expanded Nodes: {iteration}. Revists Avoided: {count_revisits}, Used Memory: {memory_usage}\nh-init: {initial_heuristic_value}, h-avg {h_avg:.2f}, h_val type: {heuristic_type}")
        return create_result_dict(STATUS, iteration, -1, -1, start_time, current_time, memory_usage, -1, -1)
    else:
        logging.info("No operators left. Task unsolvable.")
        #graph_dot.to_graphviz()
        return create_result_dict('UNSOLVABLE', iteration, initial_heuristic_value, h_sum, start_time, current_time, psutil.virtual_memory().percent, -1, -1)

