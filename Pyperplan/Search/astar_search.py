import time
import heapq
import psutil
from Pyperplan.model import Operator
from Pyperplan.Search.htn_node import AstarNode
from Pyperplan.Heuristics.blind_heuristic import BlindHeuristic
from Pyperplan.tools import parse_heuristic_params
import Pyperplan.FLAGS as FLAGS
def search(model, h_params=None, heuristic_type=BlindHeuristic, node_type=AstarNode):
    print('Staring solver')
    start_time   = time.time()
    control_time = start_time
    STATUS = 'UNSOLVABLE'
    expansions      = 0
    count_revisits = 0
    seq_num        = 0
    
    closed_list = {}
    node = node_type(None, None, None, model.initial_state, model.initial_tn, seq_num, 0)
    h = None
    if not h_params is None:
        h  = heuristic_type(model, node, **(parse_heuristic_params(h_params)))
    else:
        h  = heuristic_type(model, node)
    
    if FLAGS.LOG_HEURISTIC:
        print(h.__output__())
    

    pq = []
    
    heapq.heappush(pq, node)
    memory_usage = psutil.virtual_memory().percent
    current_time = time.time()
    while pq:
        expansions += 1
        node = heapq.heappop(pq)
        
        closed_list[hash(node)]=node.g_value
        
        # time and memory control
        if FLAGS.MONITOR_SEARCH_RESOURCES and expansions%100 == 0:
            current_time = time.time()
            if current_time - control_time > 1:
                control_time = current_time
                memory_usage = psutil.virtual_memory().percent
                elapsed_time = current_time - start_time
                nodes_second = expansions/float(current_time - start_time)
                h_avg        = h.total_hvalue/h.calls
                h_best       = h.min_hvalue
                print(f"(Elapsed Time: {elapsed_time:.2f} seconds, Nodes/second: {nodes_second:.2f} n/s, h-avg {h_avg:.2f}, h-best {h_best} Expanded Nodes: {expansions}, Fringe Size: {len(pq)} Revists Avoided: {count_revisits}, Used Memory: {memory_usage}")
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
        task = node.task_network[0]
        # check if task is primitive
        if isinstance(task, Operator):
            if not model.applicable(task, node.state):
                continue
            
            seq_num += 1
            new_state        = model.apply(task, node.state)
            new_task_network = node.task_network[1:]
            new_node         = node_type(node, task, None, new_state, new_task_network, seq_num, node.g_value+1)
            
            try_get_node_g_val = closed_list.get(hash(new_node))
            if try_get_node_g_val and try_get_node_g_val <= new_node.g_value:
                count_revisits+=1
            else:
                h(node, new_node)
                heapq.heappush(pq, new_node)
            
        # otherwise its abstract
        else:
            for method in model.methods(task):
                if not model.applicable(method, node.state):
                    continue

                seq_num += 1
                new_task_network  = model.decompose(method)+node.task_network[1:]
                new_node          = node_type(node, task, method, node.state, new_task_network, seq_num, node.g_value)
                
                try_get_node_g_val = closed_list.get(hash(new_node))
                if try_get_node_g_val and try_get_node_g_val <= new_node.g_value:
                    count_revisits+=1
                else:
                    h(node, new_node)
                    heapq.heappush(pq, new_node)

    current_time = time.time()
    elapsed_time = current_time - start_time
    nodes_second = expansions/float(current_time - start_time)
    _, op_sol, goal_dist_sol = node.extract_solution()
    if FLAGS.LOG_SEARCH:
        print( "Status: {}\nElapsed Time: {:.2f} seconds\nNodes/second: {:.2f} n/s\nSolution size: {}\nExpanded Nodes: {}\nFringe Size: {}\nRevisits Avoided: {}\nUsed Memory: {}".format(STATUS, elapsed_time, nodes_second, len(op_sol), expansions, len(pq), count_revisits, memory_usage) )

    
    