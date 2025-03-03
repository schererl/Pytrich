import time
import psutil
from typing import Optional, List
import Pytrich.FLAGS as FLAGS

from Pytrich.model import Model, Operator, AbstractTask
from Pytrich.Search.htn_node import HTNNode
from Pytrich.DESCRIPTIONS import Descriptions
from Pytrich.Heuristics.novelty_heuristic import NoveltyHeuristic
import sys
sys.setrecursionlimit(100000)  # for example

def search(
    model: Model,
    heuristic=None,
    node_type=None,
    n_params=None,
    use_novelty: bool = False
) -> None:
    """
    Recursive DFS for HTN planning.
    
    If use_novelty is True, a NoveltyHeuristic (with novelty_type "lazyft") is
    instantiated and initialized with (model, root). When expanding a node, we
    partition its children into two groups: those with novelty value 0 (novel)
    and the remainder. Novel children are recursed on first.
    
    HTNNode is created with positional arguments only:
       HTNNode(parent, task, method, state, task_network, g_value)
       
    A global "in_path" set is used to avoid cycles (nodes are added upon entry
    and removed upon backtracking).
    """
    print("Starting recursive DFS solver...")
    start_time = time.time()
    expansions = 0
    count_revisits = 0
    in_path = set()
    solution_node = [None]  # container for solution node
    found_solution = [False]
    
    # Create root node using positional arguments only
    seq_num = 0
    root = HTNNode(None, None, None, model.initial_state, model.initial_tn, seq_num)
    
    # If novelty is enabled, instantiate and initialize the novelty heuristic
    novelty_h = None
    if use_novelty:
        novelty_h = NoveltyHeuristic(novelty_type="ft")
        novelty_h.initialize(model, root)
    def resource_check(expanded_count: int):
        nonlocal start_time
        current_time = time.time()
        if current_time - start_time > 1:
            memory_usage = psutil.virtual_memory().percent
            elapsed_time = current_time - start_time
            nodes_second = expanded_count / float(elapsed_time) if elapsed_time > 0 else expanded_count
            print(f"(Elapsed Time: {elapsed_time:.2f} s, "
                  f"Nodes/sec: {nodes_second:.2f}, "
                  f"Expanded: {expanded_count}, "
                  f"Used Memory: {memory_usage}%)")
            psutil.cpu_percent()  # update CPU stats
            if memory_usage > 85:
                return "OUT OF MEMORY"
            if elapsed_time > 60:
                return "TIMEOUT"
        return None

    def dfs_recursive(node: HTNNode) -> Optional[str]:
        nonlocal expansions, count_revisits
        expansions += 1

        # Resource check every 100 expansions
        if FLAGS.MONITOR_SEARCH_RESOURCES and expansions % 100 == 0:
            status = resource_check(expansions)
            if status in ["OUT OF MEMORY", "TIMEOUT"]:
                return status

        # Cycle detection: if already in the current recursion path, skip
        h_node = hash(node)
        if h_node in in_path:
            count_revisits += 1
            return None
        in_path.add(h_node)

        # Goal check
        if model.goal_reached(node.state, node.task_network):
            solution_node[0] = node
            found_solution[0] = True
            in_path.remove(h_node)
            return "GOAL"

        # If the task network is empty but not a goal, dead end
        if len(node.task_network) == 0:
            in_path.remove(h_node)
            return None

        # Expand the first task
        task = node.task_network[0]
        children: List[HTNNode] = []
        # CASE 1: Primitive operator
        if isinstance(task, Operator):
            if task.applicable(node.state):
                new_state = task.apply(node.state)
                new_tn = node.task_network[1:]
                child = HTNNode(node, task, None, new_state, new_tn, node.g_value + 1)
                children.append(child)
        # CASE 2: Abstract Task: expand each applicable method
        else:
            for method in task.decompositions:
                if method.applicable(node.state):
                    refined_tn = method.task_network + node.task_network[1:]
                    child = HTNNode(node, task, method, node.state, refined_tn, node.g_value + 1)
                    children.append(child)
        
        # Partition children into "novel" and "remaining" if novelty is used.
        if use_novelty and novelty_h is not None:
            remaining_children = []
            for child in children:
                if novelty_h(node, child) == 0:
                    result = dfs_recursive(child)
                    if result == "GOAL":
                        in_path.remove(h_node)
                        return "GOAL"
                else:
                    remaining_children.append(child)
        else:
            remaining_children = children

        for child in remaining_children:
            result = dfs_recursive(child)
            if result == "GOAL":
                in_path.remove(h_node)
                return "GOAL"

        # Backtrack: remove this node from the current path
        #in_path.remove(h_node)
        return None

    # Start the recursive DFS from the root
    result = dfs_recursive(root)
    end_time = time.time()
    elapsed_time = end_time - start_time

    final_status = "GOAL" if found_solution[0] else (result if result in ["OUT OF MEMORY", "TIMEOUT"] else "UNSOLVABLE")
    sol_size = 0
    if found_solution[0] and solution_node[0] is not None:
        _, op_sol, goal_dist_sol = solution_node[0].extract_solution()
        sol_size = len(op_sol)

    if FLAGS.LOG_SEARCH:
        desc = Descriptions()
        memory_usage = psutil.virtual_memory().percent
        nodes_second = expansions / float(elapsed_time) if elapsed_time > 0 else expansions
        print(f"{desc('search_status', final_status)}\n"
              f"{desc('search_elapsed_time', elapsed_time)}\n"
              f"{desc('nodes_per_second', nodes_second)}\n"
              f"{desc('solution_size', sol_size)}\n"
              f"{desc('nodes_expanded', expansions)}\n"
              f"{desc('fringe_size', 0)}\n"  # fringe size is 0 for recursive DFS
              f"Revisits Avoided: {count_revisits}\n"
              f"Used Memory: {memory_usage}%")
    print(f"Recursive DFS finished. Status: {final_status}, expansions: {expansions}, solution size: {sol_size}")

