
import time
import heapq
import psutil

from typing import Optional, Type, Union, List, Dict

from Pytrich.DESCRIPTIONS import Descriptions
from Pytrich.Heuristics.blind_heuristic import BlindHeuristic
from Pytrich.Heuristics.heuristic import Heuristic
from Pytrich.Heuristics.lm_heuristic import LandmarkHeuristic
from Pytrich.Search.htn_node import AstarNode, GreedyNode, HTNNode
from Pytrich.model import Operator, AbstractTask, Model
import Pytrich.FLAGS as FLAGS

def search(
        model: Model,
        heuristic: Type[BlindHeuristic] = BlindHeuristic,
        node_type: Type[AstarNode] = AstarNode,
        n_params: Optional[Dict] = None,
        use_early=False

    ) -> None:
    node_type =  GreedyNode
    print('Staring solver')
    start_time   = time.time()
    control_time = start_time
    STATUS = 'UNSOLVABLE'
    expansions      = 0
    count_revisits = 0
    seq_num        = 0
    
    closed_list = {}
    node= None
    node = node_type(None, None, None,
                     model.initial_state,
                     model.initial_tn,
                     seq_num,
                     **n_params)
    
    print(node.__output__())
    node.update_g_h(0, heuristic.initialize(model, node))
    print(heuristic.__output__())
    pq = []
    
    heapq.heappush(pq, node)
    memory_usage = psutil.virtual_memory().percent
    init_search_time = time.time()
    current_time = time.time()
    while pq:
        expansions += 1
        node:HTNNode = heapq.heappop(pq)
        # print(node.h_value, end = ' ')
        closed_list[hash(node)]=node.g_value
        # time and memory control
        if FLAGS.MONITOR_SEARCH_RESOURCES and expansions%100 == 0:
            current_time = time.time()
            if current_time - control_time > 1:
                control_time = current_time
                memory_usage = psutil.virtual_memory().percent
                elapsed_time = current_time - start_time
                nodes_second = expansions/float(current_time - start_time)
                if isinstance(heuristic, Heuristic):
                    h_avg        = heuristic.total_hvalue/heuristic.calls
                    h_best       = heuristic.min_hvalue
                else:
                    h_avg        = -1
                    h_best       = -1
                print(f"(Elapsed Time: {elapsed_time:.2f} seconds, \
                    Nodes/second: {nodes_second:.2f} n/s, h-avg {h_avg:.2f}, \
                    h-best {h_best} \
                    Expanded Nodes: {expansions}, \
                    Fringe Size: {len(pq)} \
                    Revists Avoided: {count_revisits}, \
                    Used Memory: {memory_usage}")
                psutil.cpu_percent()
                if psutil.virtual_memory().percent > 85:
                    STATUS = 'OUT OF MEMORY'
                    break
                elif current_time - start_time > 60:
                    STATUS = 'TIMEOUT'
                    break
                
        if model.goal_reached(node.state, node.task_network):
            STATUS = 'GOAL'
            psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            elapsed_time = current_time - start_time
            break    
        elif len(node.task_network) == 0: #task network empty but goal wasnt achieved
            continue
        task:Union[AbstractTask, Operator] = node.task_network[0]
        # check if task is primitive
        if isinstance(task, Operator):
            #print(f'o', end= '  ')
            if not task.applicable(node.state):
                continue
            
            seq_num += 1
            new_state        = task.apply(node.state)
            new_task_network = node.task_network[1:]
            new_node         = node_type(node, task, None, new_state, new_task_network, seq_num)

            if use_early and model.goal_reached(new_node.state, new_node.task_network):
                STATUS = 'GOAL'
                psutil.cpu_percent()
                memory_usage = psutil.virtual_memory().percent
                elapsed_time = current_time - start_time
                break

            try_get_node_g_val = closed_list.get(hash(new_node))
            if try_get_node_g_val and try_get_node_g_val <= node.g_value+1:
                count_revisits+=1
            else:
                new_node.update_g_h(node.g_value+1, heuristic(node, new_node))
                heapq.heappush(pq, new_node)
            
        # otherwise its abstract
        else:
            for method in task.decompositions:
                if not method.applicable(node.state):
                    continue
                seq_num += 1
                refined_task_network  = method.task_network+node.task_network[1:]
                new_node          = node_type(node, task, method, node.state, refined_task_network, seq_num)
                if use_early and model.goal_reached(new_node.state, new_node.task_network):
                    STATUS = 'GOAL'
                    psutil.cpu_percent()
                    memory_usage = psutil.virtual_memory().percent
                    elapsed_time = current_time - start_time
                    break 


                try_get_node_g_val = closed_list.get(hash(new_node))
                if try_get_node_g_val and try_get_node_g_val <= node.g_value:
                    count_revisits+=1
                else:
                    new_node.update_g_h(node.g_value, heuristic(node, new_node))
                    heapq.heappush(pq, new_node)

    current_time = time.time()
    elapsed_time = current_time - start_time
    nodes_second = expansions/float(current_time - init_search_time)
    _, op_sol, goal_dist_sol = node.extract_solution()
    if isinstance(heuristic, LandmarkHeuristic):
        if node.lm_node.lm_value():
            if node.lm_node.get_unreached_landmarks() == 0:
                print(f'({node.lm_node.get_unreached_landmarks()}) invalid landamarks')

    if FLAGS.LOG_SEARCH:
        desc = Descriptions()
        print(f"{desc('search_status', STATUS)}\n"
              f"{desc('search_elapsed_time', elapsed_time)}\n"
              f"{desc('nodes_per_second', nodes_second)}\n"
              f"{desc('solution_size', len(op_sol))}\n"
              f"{desc('nodes_expanded', expansions)}\n"
              f"{desc('fringe_size', len(pq))}\n"
              f"Revisits Avoided: {count_revisits}\n"
              f"Used Memory: {memory_usage}%")
