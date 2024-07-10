import logging
import time
import heapq
import psutil


from pyperplan.model import Operator
from pyperplan.search.utils import create_result_dict
from pyperplan.search.htn_node import AstarNode
from pyperplan.heuristics.blind_heuristic import BlindHeuristic
#from pyperplan.DOT_output import DotOutput

from pyperplan.tools import parse_heuristic_params
def search(model, h_params=None, heuristic_type=BlindHeuristic, node_type=AstarNode):
    
    #graph_dot = DotOutput()

    print('Staring solver')
    start_time   = time.time()
    control_time = start_time

    iteration      = 0
    count_revisits = 0
    seq_num        = 0
    
    closed_list = {}
    node = node_type(None, None, None, model.initial_state, model.initial_tn, seq_num, 0)
    h = None
    if not h_params is None:
        h  = heuristic_type(model, node, **(parse_heuristic_params(h_params)))
    else:
        h  = heuristic_type(model, node)
    
    
    #graph_dot.add_node(node, model)
    
    STATUS = ''
    pq = []
    heapq.heappush(pq, node)
    current_time = time.time()
    while pq:
        iteration += 1
        if iteration%100 == 0:
            current_time = time.time()
        
        node = heapq.heappop(pq)
        #graph_dot.open(node)
        
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
            h_avg        = h.total_hvalue/h.calls
            h_best       = h.min_hvalue
            print(f"(Elapsed Time: {elapsed_time:.2f} seconds, Nodes/second: {nodes_second:.2f} n/s, h-avg {h_avg:.2f}, h-best {h_best} Expanded Nodes: {iteration}, Fringe Size: {len(pq)} Revists Avoided: {count_revisits}, Used Memory: {memory_usage}")
            psutil.cpu_percent()
            if psutil.virtual_memory().percent > 85:
                STATUS = 'OUT OF MEMORY'
                break
            elif current_time - start_time > 60:
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
        if isinstance(task, Operator):
            if not model.applicable(task, node.state):
                #graph_dot.not_applicable(":APPLY:"+str(task.name))
                continue
            
            seq_num += 1
            new_state        = model.apply(task, node.state)
            new_task_network = node.task_network[1:]
            new_node         = node_type(node, task, None, new_state, new_task_network, seq_num, node.g_value+1)
            h.compute_heuristic(node, new_node)
            if new_node.h_value == 100000000:
                continue
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
                new_node          = node_type(node, task, method, node.state, new_task_network, seq_num, node.g_value)
                h.compute_heuristic(node, new_node)
                if new_node.h_value == 100000000:
                    continue
                heapq.heappush(pq, new_node)

                #graph_dot.add_node(new_node, model)
                #graph_dot.add_relation(new_node, ":DECOMPOSE:"+str(method.name)+str(model.count_positive_binary_facts(method.pos_precons_bitwise)))
        
                
        #graph_dot.close()
        closed_list[hash(node)]=node.g_value
    
    if STATUS == 'GOAL':
        nodes_second = iteration/float(current_time - start_time)
        h_avg        = h.total_hvalue/h.calls
        h_best       = h.min_hvalue
        h_init        = h.initial_h
        _, op_sol, goal_dist_sol = node.extract_solution()
        logging.info(
            "Goal reached!"
            "\nstatus info>    \tElapsed Time: %.2f seconds, Nodes/second: %.2f n/s,"
            "\nheap info>      \tSolution size: %d, Expanded Nodes: %d, Revists Avoided: %d, Used Memory: %s"
            "\nheuristic info> \tname: %s, initial value: %.2f, average value %.2f",
            elapsed_time, nodes_second, len(op_sol), iteration, count_revisits, memory_usage,
            h.name, 0, h_avg
        )
        #graph_dot.to_graphviz()
        
        return create_result_dict(h.name, 'GOAL', iteration, h_init, h_avg, start_time, current_time, memory_usage, len(goal_dist_sol), len(op_sol), None)
    elif STATUS =='OUT OF MEMORY' or STATUS == 'TIMEOUT':
        logging.info(
            "%s \nElapsed Time: %.2f seconds, Nodes/second: %.2f n/s," 
            "Expanded Nodes: %d. Revists Avoided: %d, Used Memory: %s\n"
            "h-init: %.2f, h-avg %.2f, heuristic name: %s",
            STATUS, elapsed_time, nodes_second, iteration, count_revisits, memory_usage,
            0, h_avg, h.name
        )
        return create_result_dict(h.name, STATUS, iteration, -1, -1, start_time, current_time, memory_usage, -1, -1)
    else:
        logging.info("No operators left. Task unsolvable.")
        #graph_dot.to_graphviz()
        return create_result_dict(
            h.name, 'UNSOLVABLE', iteration, 0, 
            h_avg, start_time, current_time, 
            psutil.virtual_memory().percent, -1, -1
        )
