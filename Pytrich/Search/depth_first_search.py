import time
import psutil
from typing import Optional, List
import Pytrich.FLAGS as FLAGS

from Pytrich.model import Model, Operator, AbstractTask
from Pytrich.Search.htn_node import HTNNode
from Pytrich.DESCRIPTIONS import Descriptions

# If your NoveltyHeuristic is in a separate module, e.g.:
# from Pytrich.Heuristics.novelty_heuristic import NoveltyHeuristic
# Adjust this import as needed; the code snippet you gave suggests it's in the same directory or package
from Pytrich.Heuristics.novelty_heuristic import NoveltyHeuristic

def search(
    model: Model,
    heuristic=None,
    node_type=None,
    n_params=None,
    use_novelty: bool = False
) -> None:
    """
    Iterative DFS with a global visited set. If 'use_novelty' is True, we instantiate
    NoveltyHeuristic(novelty_type="lazyft") and maintain two stacks:
       - preferred_stack: for nodes with novelty == 0
       - normal_stack: for nodes with novelty != 0
    We pop from preferred_stack first if it has nodes, ensuring novelty=0 expansions get priority.

    HTNNode is created using positional arguments only:
        HTNNode(parent, task, method, state, task_network, g_value)
    """

    print("Starting DFS solver...")
    start_time   = time.time()
    control_time = start_time
    expansions   = 0
    count_revisits = 0

    # Root node
    seq_num = 0
    root = HTNNode(None, None, None, model.initial_state, model.initial_tn, seq_num)

    # If using novelty, instantiate and initialize the "lazyft" novelty heuristic
    novelty_h = None
    if use_novelty:
        novelty_h = NoveltyHeuristic(novelty_type="lazyft")
        novelty_h.initialize(model, root)

    # We'll have two stacks if novelty is used
    preferred_stack = []
    normal_stack    = []

    # Start by putting the root in normal_stack
    normal_stack.append(root)
    
    visited = set()
    found_solution = False
    solution_node = None
    final_status = "UNSOLVABLE"

    def resource_check(expanded_count: int):
        """
        Periodically check time and memory usage, returning a status if we must stop.
        """
        nonlocal control_time, start_time
        current_time = time.time()
        if current_time - control_time > 1:  # e.g. check every 1 second
            control_time = current_time
            memory_usage = psutil.virtual_memory().percent
            elapsed_time = current_time - start_time
            if elapsed_time > 0:
                nodes_second = expanded_count / float(elapsed_time)
            else:
                nodes_second = expanded_count

            print(f"(Elapsed Time: {elapsed_time:.2f}s, "
                  f"Nodes/sec: {nodes_second:.2f}, "
                  f"Expanded: {expanded_count}, "
                  f"Used Memory: {memory_usage}%)")

            psutil.cpu_percent()  # update CPU stats
            if memory_usage > 85:
                return "OUT OF MEMORY"
            if elapsed_time > 60:  # example cutoff
                return "TIMEOUT"
        return None

    # Main DFS loop
    while preferred_stack or normal_stack:
        # Always pop from preferred_stack first if it has nodes
        if preferred_stack:
            node = preferred_stack.pop()
        else:
            node = normal_stack.pop()

        expansions += 1

        # Resource check every 100 expansions
        if FLAGS.MONITOR_SEARCH_RESOURCES and expansions % 100 == 0:
            status = resource_check(expansions)
            if status in ["OUT OF MEMORY", "TIMEOUT"]:
                final_status = status
                found_solution = False
                solution_node = None
                break

        # Check visited
        h_node = hash(node)
        if h_node in visited:
            count_revisits += 1
            continue
        visited.add(h_node)

        # Check goal
        if model.goal_reached(node.state, node.task_network):
            found_solution = True
            final_status = "GOAL"
            solution_node = node
            break

        # If no tasks but not a goal => dead end
        if len(node.task_network) == 0:
            continue

        # Expand the first task
        task = node.task_network[0]

        # CASE 1: Primitive operator
        if isinstance(task, Operator):
            if task.applicable(node.state):
                new_state = task.apply(node.state)
                new_tn = node.task_network[1:]
                child = HTNNode(node, task, None, new_state, new_tn, node.g_value + 1)

                if use_novelty and novelty_h(node, child)==0:
                    preferred_stack.append(child)
                else:
                    normal_stack.append(child)

        # CASE 2: Abstract Task => expand each method
        else:  # AbstractTask
            for method in task.decompositions:
                if method.applicable(node.state):
                    refined_tn = method.task_network + node.task_network[1:]
                    child = HTNNode(node, task, method, node.state, refined_tn, node.g_value + 1)

                    if use_novelty and novelty_h(node, child)==0:
                        preferred_stack.append(child)
                    else:
                        normal_stack.append(child)

    # Done exploring or ended early
    end_time = time.time()
    elapsed_time = end_time - start_time

    # If no solution found, see if we timed out or OOM
    if not found_solution and final_status not in ["OUT OF MEMORY", "TIMEOUT"]:
        final_status = "UNSOLVABLE"

    # Extract solution if found
    sol_size = 0
    if found_solution and solution_node:
        _, op_sol, goal_dist_sol = solution_node.extract_solution()
        sol_size = len(op_sol)

    # Logging
    if FLAGS.LOG_SEARCH:
        desc = Descriptions()
        memory_usage = psutil.virtual_memory().percent
        nodes_second = expansions / float(elapsed_time) if elapsed_time > 0 else expansions
        fringe_size = len(preferred_stack) + len(normal_stack)
        print(f"{desc('search_status', final_status)}\n"
              f"{desc('search_elapsed_time', elapsed_time)}\n"
              f"{desc('nodes_per_second', nodes_second)}\n"
              f"{desc('solution_size', sol_size)}\n"
              f"{desc('nodes_expanded', expansions)}\n"
              f"{desc('fringe_size', fringe_size)}\n"
              f"Revisits Avoided: {count_revisits}\n"
              f"Used Memory: {memory_usage}%")

    print(f"DFS finished. Status: {final_status}, expansions: {expansions}, solution size: {sol_size}")
