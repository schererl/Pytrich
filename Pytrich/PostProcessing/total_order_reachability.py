
from copy import copy, deepcopy
import time
from typing import List, Set, Dict, NewType, Tuple, Union

import Pytrich.FLAGS as FLAGS
from Pytrich.model import Decomposition, Model, Operator, AbstractTask

GlobalID = NewType('GlobalID', int)
LocalID  = NewType('LocalID', int)

def _calculate_TO_achievers(model: Model, reachable: List[Set[int]]) -> Dict[int, Set[int]]:
    """
    Calculate the achievers for each operator.
    The achievers are those that came before (predecessors) based on Total-Order reachability
        and enable an operator (have at least one of its preconditions as effect).

    NOTE: shift_offset_id (int): The offset used to map global task IDs to local task IDs.
    NOTE: predecessors (List[Set[int]]): A list where each index corresponds to a local operator ID, 
        and each element is a set of local IDs that can achieve the operator based on TO constraints.
    NOTE: achivers_group (Dict[int, Set[int]]): A dictionary mapping each operator's global ID to a set of 
        global IDs of operators that can achieve it.

    """
        
    shift_offset_id: int = model.ifacts_end + 1
    predecessors: List[Set[LocalID]] = [set() for _ in range(len(model.operators))]
    
    # compute predecessors mapping global->local ids
    for decomposition in model.decompositions:
        subtasks = decomposition.task_network
        
        for sub_i, subtask in enumerate(subtasks, start=1):
            taski_id: GlobalID = subtask.global_id
            taski_local_id: LocalID = taski_id - shift_offset_id  # shift left: global->local
            for operator_local_id in reachable[taski_local_id]:
                for j in range(sub_i - 1, -1, -1):
                    taskj_id: GlobalID = subtasks[j].global_id
                    taskj_local_id: LocalID = taskj_id - shift_offset_id  # shift left: global->local
                    r: Set[int] = reachable[taskj_local_id]
                    predecessors[operator_local_id].update(r)
    
    subtasks = model.initial_tn
    for sub_i, subtask in enumerate(subtasks):
        taski_id: GlobalID = subtask.global_id
        taski_local_id: LocalID = taski_id - shift_offset_id  # shift left: global->local
        for operator_local_id in reachable[taski_local_id]:
            for j in range(sub_i - 1, -1, -1):
                taskj_id: GlobalID = subtasks[j].global_id
                taskj_local_id: LocalID = taskj_id - shift_offset_id  # shift left: global->local
                predecessors[operator_local_id].update(reachable[taskj_local_id])
                
    # compute achievers mappping local->global ids
    achivers_group: Dict[GlobalID, Set[GlobalID]] = {a.global_id: set() for a in model.operators}
    for o in model.operators:
        if o.applicable_bitwise(model.initial_state):
            achivers_group[o.global_id] = {-1}  # mark trivial applicable operators
            continue
        
        o_achievers: Set[GlobalID] = set()
        o_local_id: LocalID = o.global_id - shift_offset_id
        o_predecessors: Set[LocalID] = predecessors[o_local_id]
        
        for pred_loc_id in o_predecessors:
            pred_global_id: GlobalID = pred_loc_id + shift_offset_id  # shift RIGHT: local -> global
            pred_instance: Operator = model.get_component(pred_global_id)
            if pred_instance.add_effects_bitwise & o.pos_precons_bitwise != 0:
                o_achievers.add(pred_global_id)
        achivers_group[o.global_id] = o_achievers

    return achivers_group

def _calculate_TO_reachable(model: Model) -> List[Set[int]]:
    """
    Calculate the reachable set of operators for each task.

    NOTE: R_set : A list where each index corresponds to a task's local ID, 
         and each element is a set of reachable task local IDs.
    NOTE: visited : A list to track which tasks have been 
        visited during the depth-first search (DFS).
    NOTE: v_it : A visit marker that increments with each DFS 
        run to avoid resetting the `visited` list.
    NOTE: shift_offset_ids: The offset used to map global task IDs to local task IDs.
    
    TODO: Use Dijkstra for updating nodes instead of DFS; not sure if it compensates.
    """
    
    len_operators = len(model.operators)
    len_abstract_tasks = len(model.abstract_tasks)
    shift_offset_ids = model.ifacts_end + 1
    
    R_set: List[Set[LocalID]] = [set() for _ in range(len_operators + len_abstract_tasks)]
    visited: List[LocalID] = [0] * (len_operators + len_abstract_tasks)
    v_it: int = 1

    # Operators are trivially reachable
    for i in range(len_operators):
        R_set[i] = {i}

    for task in model.abstract_tasks:
        r_task: Set[LocalID] = set()
        _dfs_iterative(model, task, R_set, r_task, v_it, visited, shift_offset_ids)
        
        # Shift left to get task local IDs
        task_local_id: LocalID = task.global_id - shift_offset_ids
        R_set[task_local_id] = r_task
        v_it += 1

    return R_set
        

def _dfs_iterative(model: Model, task: AbstractTask, R: List[Set[LocalID]], 
                   r: Set[LocalID], v_it: int, visited: List[LocalID], soid: int) -> None:
    stack = [task]
    
    while stack:
        current_task = stack.pop()
        task_id = current_task.global_id
        
        # Shift left to get task local IDs
        task_local_id: LocalID = LocalID(task_id - soid)
        
        if visited[task_local_id] == v_it:
            continue
        
        visited[task_local_id] = v_it
        r_task = R[task_local_id]
        if r_task:
            r.update(r_task)

        for decomposition in current_task.decompositions:
            for subtask in decomposition.task_network:
                if subtask in model.operators:
                    r.add(LocalID(subtask.global_id - soid))  # use local ID
                else:
                    stack.append(subtask)


def _TOreachable_operators(model: Model, O: List[Operator], achievers: Dict[GlobalID, Set[GlobalID]]) -> List[Operator]:
    """
    Get Total-Order achievers and remove those that cannot be reachable (not available).
    
    @param model: Model class
    @param O: List of available operators
    @param achievers: Dict mapping operator global IDs to sets of global IDs of operators that can achieve it.
    
    NOTE: shift_offset_id maps global IDs to local IDs for indexing them into an array.
    NOTE: Instead of checking whether an operator is in the 'achievers' set, we verify in the 'available' set.
    """
    achievable_op: Set[Operator] = set()
    available: List[int] = [0] * len(model.operators)
    shift_offset_id: int = len(model.facts)

    # mark available operators in the 'available' array
    for o in O:
        available[o.global_id - shift_offset_id] = 1  # shift left operators IDs

    # check if each operator is applicable (achievers satisfy all operator preconditions)
    for o in O:
        achiever_state = model.initial_state
        removed_achievers: Set[GlobalID] = set()
        op_achievers = achievers[o.global_id]
        
        for a_id in op_achievers:
            if a_id == GlobalID(-1):  # Skip trivial achievers
                continue
            if available[a_id - shift_offset_id] == 0:
                removed_achievers.add(a_id)
                continue
            o_a = model.get_component(a_id)
            achiever_state = o_a.relaxed_apply_bitwise(achiever_state)
        
        op_achievers -= removed_achievers
        if o.applicable_bitwise(achiever_state):  # Check if the operator is achievable
            achievable_op.add(o)
        
    return list(achievable_op)

def _Dreachable_operators(initial_task_network: List[Union[AbstractTask, Operator]]) -> Set[Operator]:
    def _dfs_reachable(task_node: Union[AbstractTask, Operator],
                       R: Set[Operator],
                       visited: Set[Union[AbstractTask, Operator]]) -> None:
        visited.add(task_node)
        for d in task_node.decompositions:
            for t in d.task_network:
                if isinstance(t, Operator):
                    R.add(t)
                else:
                    if t not in visited:
                        _dfs_reachable(t, R, visited)
                
    visited: Set[Union[AbstractTask, Operator]] = set()
    tdg_reachable_operators: Set[Operator] = set()
    
    for t in initial_task_network:
        if isinstance(t, Operator):
            tdg_reachable_operators.add(t)
            continue
        _dfs_reachable(t, tdg_reachable_operators, visited)
    
    return tdg_reachable_operators

def _Ereachable_operators(operators: List[Operator], initial_state: int) -> Tuple[List[Operator], int]:
    reachable_operators: List[Operator] = []
    reachable_facts: int = initial_state
    O: Set[Operator] = set(operators)
    
    changed: bool = True
    while changed:
        changed = False
        remove_op: Set[Operator] = set()
        for op in O:
            if op not in reachable_operators and op.applicable_bitwise(reachable_facts):
                reachable_operators.append(op)
                reachable_facts = op.relaxed_apply_bitwise(reachable_facts)
                remove_op.add(op)
                changed = True
        O -= remove_op
    
    return reachable_operators, reachable_facts

def _compute_achievers_set(model: Model) -> Dict[int, Set[int]]:
    reachable: List[Set[int]] = _calculate_TO_reachable(model)
    achievers: Dict[int, Set[int]] = _calculate_TO_achievers(model, reachable)
    return achievers

def _bottom_up_removal(R_decompositions: List[Decomposition],
                       R_operators: List[Operator], 
                       R_abstract_tasks: List[AbstractTask],
                       reachable_facts: int) -> None:
    """
    Performs a bottom-up removal process on the reachable decompositions, operators, and abstract tasks
    to eliminate those that cannot be achieved or are invalid due to the absence of their required components.

    Decompositions are removed:
        (1) Not applicable based on the current set of delete-relaxed reachable facts.
        (2) If some subtask (operator or abstract) was pruned.
    
    Abstract tasks are removed when they no longer have valid decompositions.

    The process repeats until any decomposition or task is removed.
    
    @param R_decompositions: List of decompositions to be pruned.
    @param R_operators: List of operators to be pruned.
    @param R_abstract_tasks: List of abstract tasks to be pruned.
    @param reachable_facts: Set of facts that are currently reachable.
    """
    
    cleaned: bool = True
    while cleaned:
        cleaned = False
        decompositions: List[Decomposition] = []
        abstract_tasks: List[AbstractTask] = []

        # Remove decompositions
        for d in R_decompositions:
            valid: bool = True
            if not d.applicable_bitwise(reachable_facts):
                valid = False
            else:
                for t in d.task_network:
                    if isinstance(t, Operator) and t not in R_operators:
                        valid = False
                        break
                    elif isinstance(t, AbstractTask) and t not in R_abstract_tasks:
                        valid = False
                        break
            if valid:
                decompositions.append(d)
            else:
                d.compound_task.decompositions.remove(d)
                cleaned = True
            
        # Remove abstract tasks
        for abt in R_abstract_tasks:
            if len(abt.decompositions) > 0:
                abstract_tasks.append(abt)
            else:
                cleaned = True
        
        R_decompositions.clear()
        R_decompositions.extend(decompositions)
        R_abstract_tasks.clear()
        R_abstract_tasks.extend(abstract_tasks)

def TO_relax_reachability(model: Model) -> None:
    print(f'Starting TO reachability.')
    start_time = time.time()
    number_o_before = len(model.operators)
    number_abt_before = len(model.abstract_tasks)
    number_m_before = len(model.decompositions)

    R_abstract_tasks: List[AbstractTask] = model.abstract_tasks[:]
    R_operators: List[Operator] = model.operators[:]
    R_decompositions: List[Decomposition] = model.decompositions[:]
    
    start_achievers = time.time()
    achiever_set = _compute_achievers_set(model)
    elapsed_achievers = time.time() - start_achievers

    if FLAGS.LOG_GROUNDER:   
        print(f'TO achievers after {elapsed_achievers:.2f} seconds.')
    
    i = 0
    
    while True:
        i += 1
        count_curr_O = len(R_operators)
        
        # Measure time for _Dreachable_operators
        start_D_reachable = time.time()
        D_Rops_set = _Dreachable_operators(model.initial_tn)  # operators reachable by decomposition space
        elapsed_D_reachable = time.time() - start_D_reachable
        if FLAGS.LOG_GROUNDER:   
            print(f'\t({i}) Decomposition reachability after {elapsed_D_reachable:.2f} seconds.')

        # Measure time for _Ereachable_operators
        start_E_reachable = time.time()
        E_Rops, reachable_facts = _Ereachable_operators(D_Rops_set, model.initial_state)  # operators reachable by executability space
        elapsed_E_reachable = time.time() - start_E_reachable
        if FLAGS.LOG_GROUNDER:   
            print(f'\t({i}) Executability reachability after {elapsed_E_reachable:.2f} seconds.')

        # Measure time for _TOreachable_operators
        start_TO_reachable = time.time()
        R_operators = _TOreachable_operators(model, E_Rops, achiever_set)  # operators reachable by total-order constraints
        elapsed_TO_reachable = time.time() - start_TO_reachable
        if FLAGS.LOG_GROUNDER:   
            print(f'\t({i}) TO constraints reachability after {elapsed_TO_reachable:.2f} seconds.')

        count_DRops_set = len(D_Rops_set)
        count_ERops = len(E_Rops)
        count_TORops = len(R_operators)
        
        if count_curr_O - count_TORops == 0:
            break    
          
        start_bur = time.time()                    
        _bottom_up_removal(R_decompositions, R_operators, R_abstract_tasks, reachable_facts)
        elapsed_bur = time.time() - start_bur
        if FLAGS.LOG_GROUNDER:   
            count_burRops = len(R_operators)
            print(f'\t({i}) Bottom up removal after {elapsed_bur:.2f} seconds.')
            print(f'\t\t({i}) Decomposition Space removed {count_curr_O - count_DRops_set} operators.')
            print(f'\t\t({i}) Executability Space removed {count_DRops_set - count_ERops} operators.')
            print(f'\t\t({i}) TO Ordering Constraints removed {count_ERops - count_TORops} operators.')
            print(f'\t\t({i}) Bottom up removed {count_TORops - count_burRops} operators.')
        break
    
    model.decompositions = R_decompositions
    model.abstract_tasks = R_abstract_tasks
    model.operators = R_operators
    
    if FLAGS.LOG_GROUNDER:   
        print(f'number of abstract tasks removed {number_abt_before - len(model.abstract_tasks)} of {number_abt_before}')
        print(f'number of operators removed: {number_o_before - len(model.operators)} of {number_o_before}')
        print(f'number of methods removed: {number_m_before - len(model.decompositions)} of {number_m_before}')
    
    model.assign_global_ids()
    print(f'TO reachability elapsed time: {time.time() - start_time:.4f} s')