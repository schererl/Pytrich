from collections import deque
import logging
import time
import psutil

from ..model import Operator
from ..DOT_output import DotOutput

from .htn_node import HTNNode
from .utils import create_result_dict

def search(model, heuristic_type, node_type=HTNNode):
    print('Staring solver')
    print(model)
    time.sleep(1)
    start_time   = time.time()  
    control_time = start_time

    iteration      = 0
    count_revisits = 0
    seq_num        = 0
    
    closed_list = set()
    node  = node_type(None, None, model.initial_state, model.initial_tn, seq_num, 0, 0)
    
    
    #graph_dot.add_node(node, model)
    queue = deque()
    queue.append(node)

    goal_reached=False
    while queue:
        iteration += 1
        current_time = time.time()      
        node = queue.popleft()
        
        #graph_dot.open(node)
        
        # time and memory control
        if current_time - control_time > 1:
            psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            elapsed_time = current_time - start_time
            nodes_second = iteration/float(current_time - start_time)
            print(f"(Elapsed Time: {elapsed_time:.2f} seconds, Nodes/second: {nodes_second:.2f} n/s, h-avg {0:.2f}, Expanded Nodes: {iteration}, Fringe Size: {len(queue)} Revists Avoided: {count_revisits}, Used Memory: {memory_usage}")
            control_time = time.time()
            if psutil.virtual_memory().percent > 85:
                logging.info('OUT OF MEMORY')
                logging.info(f"Elapsed Time: {elapsed_time:.2f} seconds, Nodes/second: {nodes_second:.2f} n/s, Expanded Nodes: {iteration}. Revists Avoided: {count_revisits}, Used Memory: {memory_usage}\nh-init: {0}, h-avg {0:.2f}, h_val type: {heuristic_type}")
                return create_result_dict('MEMORY', iteration, -1, -1, start_time, current_time, memory_usage, -1, -1)
            
            if current_time - start_time > 300:
                logging.info("TIMEOUT.")
                logging.info(f"Elapsed Time: {elapsed_time:.2f} seconds, Nodes/second: {nodes_second:.2f} n/s, Expanded Nodes: {iteration}. Revists Avoided: {count_revisits}, Used Memory: {memory_usage}\nh-init: {0}, h-avg {0:.2f}, h_val type: {heuristic_type}")
                return create_result_dict('TIMEOUT', iteration, -1, -1, start_time, current_time, memory_usage, -1, -1)
            
        
        elif len(node.task_network) == 0:
            continue
        task = node.task_network[0]
        
        # check if task is primitive
        if type(task) is Operator:
            #print(f'\n:APPLY: {task}')
            if not model.applicable(task, node.state):
                #print(f':NOT APPLICABLE: {task.name}')
                ##graph_dot.not_applicable(":APPLY:"+str(task.name))
                continue
            
            seq_num += 1
            new_state = model.apply(task, node.state)
            new_task_network = node.task_network[1:]
            new_node = node_type(node, task, new_state, new_task_network, seq_num, node.g_value+1, 0)
            #graph_dot.add_node(new_node, model)
            #graph_dot.add_relation(new_node, ":APPLY:"+str(task.name))
            if model.goal_reached(node.state, node.task_network):
                goal_reached=True
                break
            if new_node in closed_list:
                continue

            queue.append(new_node)
            
            
            
        # otherwise its abstract
        else:
            for method in model.methods(task):
                if not model.applicable(method, node.state):
                    #print(f':NOT APPLICABLE:')
                    ##graph_dot.not_applicable(":DECOMPOSE:"+str(method.name))
                    continue

                #print(f'\n:APPLY: {method}')        
                seq_num += 1
                new_task_network= model.decompose(method)+node.task_network[1:]
                new_node = node_type(node, task, node.state, new_task_network, seq_num, node.g_value+1, 0)
                #graph_dot.add_node(new_node, model)
                #graph_dot.add_relation(new_node, ":DECOMPOSE:"+str(method.name)+str(model.count_positive_binary_facts(method.pos_precons_bitwise)))
                if model.goal_reached(node.state, node.task_network):
                    goal_reached=True
                    break

                if new_node in closed_list:
                    continue
                queue.append(new_node)
                        
                
        #graph_dot.close()
        closed_list.add(node)
    
    if goal_reached:
        psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        elapsed_time = current_time - start_time
        nodes_second = iteration/float(current_time - start_time)
        logging.info("Goal reached. Start extraction of solution.")
        logging.info(f"Elapsed Time: {elapsed_time:.2f} seconds, Nodes/second: {nodes_second:.2f} n/s, Expanded Nodes: {iteration}, Revists Avoided: {count_revisits}, Used Memory: {memory_usage}\nh-init: {0}, h-avg {0:.2f}, h_val type: {heuristic_type}")
        solution, operators = node.extract_solution()
        #graph_dot.to_graphviz()
        print(operators)
        print(f'operators count: {len(operators)}')
        return create_result_dict('GOAL', iteration, 0, 0, start_time, current_time, memory_usage, len(solution), len(operators), solution)

    logging.info("No operators left. Task unsolvable.")
    #graph_dot.to_graphviz()
    return create_result_dict('UNSOLVABLE', iteration, 0, 0, start_time, current_time, psutil.virtual_memory().percent, -1, -1)

