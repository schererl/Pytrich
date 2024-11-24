from collections import deque
import time
import psutil
from typing import Optional, Type, Union, List, Dict
from Pytrich.model import Operator, AbstractTask, Model
from Pytrich.Search.htn_node import HTNNode
import Pytrich.FLAGS as FLAGS

def search(model: Model, 
           h_params: Optional[Dict] = None, s_params: Optional[Dict] = None,
           heuristic_type=None,
           node_type: Type[HTNNode] = HTNNode) -> None:
    print('Starting blind search')
    start_time = time.time()
    control_time = start_time
    STATUS = 'UNSOLVABLE'
    expansions = 0
    count_revisits = 0
    seq_num = 0

    closed_list = set()
    node = node_type(None, None, None, model.initial_state, model.initial_tn, seq_num, 0)

    print(node.__output__())

    queue = deque()
    queue.append(node)
    memory_usage = psutil.virtual_memory().percent
    init_search_time = time.time()
    current_time = time.time()

    while queue:
        expansions += 1
        node: HTNNode = queue.popleft()  # FIFO for BFS

        # Time and memory control
        if FLAGS.MONITOR_SEARCH_RESOURCES and expansions % 100 == 0:
            current_time = time.time()
            if current_time - control_time > 1:
                control_time = current_time
                memory_usage = psutil.virtual_memory().percent
                elapsed_time = current_time - start_time
                nodes_second = expansions / float(current_time - start_time)
                print(f"(Elapsed Time: {elapsed_time:.2f} seconds, Nodes/second: {nodes_second:.2f} n/s, "
                      f"Expanded Nodes: {expansions}, Fringe Size: {len(queue)} "
                      f"Revisits Avoided: {count_revisits}, Used Memory: {memory_usage}%")
                psutil.cpu_percent()
                if psutil.virtual_memory().percent > 85:
                    STATUS = 'OUT OF MEMORY'
                    break
                elif current_time - start_time > 60:
                    STATUS = 'TIMEOUT'
                    break

        # Add the node to the closed list
        closed_list.add(hash(node))

        # Check if the current node is the goal
        if model.goal_reached(node.state, node.task_network):
            STATUS = 'GOAL'
            psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            elapsed_time = current_time - start_time
            break
        elif len(node.task_network) == 0:  # Task network empty but goal wasn't achieved
            continue

        task = node.task_network[0]
        # Check if task is primitive
        if isinstance(task, Operator):
            if not task.applicable(node.state):
                continue

            seq_num += 1
            new_state = task.apply(node.state)
            new_task_network = node.task_network[1:]
            new_node = node_type(node, task, None, new_state, new_task_network, seq_num, node.g_value + 1)

            # Eager goal detection
            if model.goal_reached(new_node.state, new_node.task_network):
                node = new_node  # Update node to the goal node
                STATUS = 'GOAL'
                psutil.cpu_percent()
                memory_usage = psutil.virtual_memory().percent
                elapsed_time = current_time - start_time
                break

            # Check for repeated nodes
            if hash(new_node) in closed_list:
                count_revisits += 1
            else:
                queue.append(new_node)
        # Otherwise, it's abstract
        else:
            for method in task.decompositions:
                if not method.applicable(node.state):
                    continue
                seq_num += 1
                refined_task_network = method.task_network + node.task_network[1:]
                new_node = node_type(node, task, method, node.state, refined_task_network, seq_num, node.g_value)
                # Check for repeated nodes
                if hash(new_node) in closed_list:
                    count_revisits += 1
                else:
                    queue.append(new_node)
            

    current_time = time.time()
    elapsed_time = current_time - start_time
    nodes_second = expansions / float(current_time - init_search_time)
    _, op_sol, goal_dist_sol = node.extract_solution()
    if FLAGS.LOG_SEARCH:
        print(f"Search status: {STATUS}\n"
              f"Elapsed time: {elapsed_time}\n"
              f"Nodes per second: {nodes_second}\n"
              f"Solution size: {len(op_sol)}\n"
              f"Nodes expanded: {expansions}\n"
              f"Fringe size: {len(queue)}\n"
              f"Revisits avoided: {count_revisits}\n"
              f"Used memory: {memory_usage}%")
