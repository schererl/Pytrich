from copy import copy, deepcopy
import logging
import sys
import time

from pyperplan.model import Operator, AbstractTask
import pyperplan.FLAGS as FLAGS


def clean_tdg(
    model    
):
    """
    Compresses the model representation to optimize memory usage and performance.

    simple TDG cleaning: It filters out unachieved operators and decompositions based on the initial task network,
    and updates the model with only the necessary elements.
    It also logs the memory usage before and after the compression for profiling purposes.
    """
    # profilling stuff
    count_op_before     = len(model.operators)
    count_decomp_before = len(model.decompositions)
    count_abs_task_before = len(model.abstract_tasks)

    used_operators      = []
    used_decompositions = []
    used_abstract_tasks = []
    visited_tasks = set()
    used_facts    = set()
    
    tasks = model.initial_tn[:]
    for l in model.initial_state:
        used_facts.add(l)
    
    while len(tasks)>0:
        task = tasks.pop()
        if task in visited_tasks:
            continue
        visited_tasks.add(task)
        if type(task) == Operator:
            used_operators.append(task)
            used_facts.update(task.pos_precons) 
            used_facts.update(task.neg_precons)
            used_facts.update(task.add_effects)
            used_facts.update(task.del_effects)
        else:
            used_abstract_tasks.append(task)
            for method in model.methods(task):
                used_facts.update(method.pos_precons)
                used_facts.update(method.neg_precons)
                used_decompositions.append(method)
                tasks+= model.decompose(method)[:]
                

    # profilling stuff
    model.operators      = used_operators
    model.decompositions = used_decompositions
    model.facts          = used_facts
    model.abstract_tasks = used_abstract_tasks
    count_op_after     = len(model.operators)
    count_decomp_after = len(model.decompositions)
    count_abs_task_after = len(model.abstract_tasks)
    
    if FLAGS.LOG_GROUNDER:
        print(f"used facts: {len(used_facts)}")
        print(f"cleaning operators: before {count_op_before} un ==> after {count_op_after} un")
        print(f"cleaning decompositions: before {count_decomp_before} un ==> after {count_decomp_after} un")
        print(f"cleaning tasks: before {count_abs_task_before} un ==> after {count_abs_task_after} un")


def remove_negative_precons(model):
    neg_facts = set()
    # convert negative preconditions into 'neg literals'
    for o in model.operators:
        new_pos_precons = set(o.pos_precons)
        for n_p in o.neg_precons:
            new_fact = '(not_' + n_p[1:]
            new_pos_precons.add(new_fact)
            model.facts.add(new_fact)
        neg_facts.update(o.neg_precons)
        o.pos_precons = frozenset(new_pos_precons)

    for d in model.decompositions:
        new_pos_precons = set(d.pos_precons)
        for n_p in d.neg_precons:
            new_fact = '(not_' + n_p[1:]
            new_pos_precons.add(new_fact)
            model.facts.add(new_fact)
        neg_facts.update(d.neg_precons)
        d.pos_precons = frozenset(new_pos_precons)
    
    # change effects to turns a not literals true when modified
    for o in model.operators:
        for fact in o.add_effects:
            if fact in neg_facts:
                o.del_effects.add('(not_' + fact[1:])
        for fact in o.del_effects:
            if fact in neg_facts:
                o.add_effects.add('(not_' + fact[1:])
    
    # update initial state
    for fact in neg_facts:
        new_initial_state = set()
        if not fact in model.initial_state:
            new_initial_state.add('(not_' + fact[1:])
        new_initial_state.update(model.initial_state)
        model.initial_state = frozenset(new_initial_state)
    
    #clear all negative precons
    for o in model.operators:
        o.neg_precons=frozenset()
    for d in model.decompositions:
        d.neg_precons=frozenset()
    



def convert_bitwise_repr(model):
    def map_explicit_to_int(model):
        """
        Maps each fact to a unique integer, creating a mapping for bitwise operations.
        This method is part of the process to convert states and operations to a bitwise format.
        """
        cont = 0

        model.facts = sorted(model.facts)
        model.goals = sorted(model.goals)
        # NOTE: this is essential for fact count heuristic works faster
        for g in model.goals:
                model._explicit_to_int[g]    = cont
                model._int_to_explicit[cont] = g
                cont+=1
        
        for f in model.facts:
            if f in model.goals:
                continue
            model._explicit_to_int[f]    = cont
            model._int_to_explicit[cont] = f
            cont+=1
    
    def convert_to_bitwise(model, facts_set):
        bitwise_representation = 0
        for fact in facts_set:
            bit_position = model._explicit_to_int[fact]
            bitwise_representation |= 1 << bit_position
        return bitwise_representation
    
    """
    Compresses fact representations by mapping facts to bit positions and converting
    states to integer representations.
    """
    # map facts to bit position for bit representation
    map_explicit_to_int(model)
    
    # convert initial and goal state to int
    si_bitwise_repr = convert_to_bitwise(model, model.initial_state)
    sf_bitwise_repr = convert_to_bitwise(model, model.goals)
    model.initial_state = si_bitwise_repr
    model._goal_bit_pos = [model._explicit_to_int[g] for g in model.goals]
    model.goals = sf_bitwise_repr
    
    # convert preconditions and effects to integers for bitwise operations
    for o in model.operators:
        o.pos_precons_bitwise = convert_to_bitwise(model, o.pos_precons)
        o.neg_precons_bitwise = convert_to_bitwise(model, o.neg_precons)
        o.add_effects_bitwise = convert_to_bitwise(model, o.add_effects)
        o.del_effects_bitwise = convert_to_bitwise(model, o.del_effects)
        o.pos_precons = frozenset()
        o.neg_precons = frozenset()
        o.add_effects = frozenset()
        o.del_effects = frozenset()
    for d in model.decompositions:
        d.pos_precons_bitwise = convert_to_bitwise(model, d.pos_precons)
        d.neg_precons_bitwise = convert_to_bitwise(model, d.neg_precons)
        d.pos_precons = frozenset()
        d.neg_precons = frozenset()

def _calculate_TO_achievers(model, reachable):
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
        
    shift_offset_id = model.ifacts_end+1
    predecessors = [set() for _ in range(len(model.operators))]
    # compute predecessors mapping global->local ids
    for decomposition in model.decompositions:
        subtasks = decomposition.task_network
        for sub_i, subtask in enumerate(subtasks, start=1):
            taski_id = subtask.global_id
            taski_local_id = taski_id - shift_offset_id # shift left: global->local
                             
            for operator_local_id in reachable[taski_local_id]:
                for j in range(sub_i - 1, -1, -1):
                    taskj_id = subtasks[j].global_id
                    taskj_local_id = taskj_id - shift_offset_id # shift left: global->local
                    r = reachable[taskj_local_id]
                    predecessors[operator_local_id].update(r)
    
    subtasks = model.initial_tn
    for sub_i, subtask in enumerate(subtasks):
        taski_id = subtask.global_id
        taski_local_id = taski_id - shift_offset_id # shift left: global->local
                             
        for operator_local_id in reachable[taski_local_id]:
            for j in range(sub_i - 1, -1, -1):
                taskj_id = subtasks[j].global_id
                taskj_local_id = taskj_id - shift_offset_id # shift left: global->local
                predecessors[operator_local_id].update(reachable[taskj_local_id])

    # compute achievers mappping local->global ids
    achivers_group = {a.global_id: set() for a in model.operators}
    for o in model.operators:
        if o.relaxed_applicable_bitwise(model.initial_state):
            achivers_group[o.global_id] = {-1} # mark trivial applicable operators
            continue
        
        o_achievers = set()
        o_local_id = o.global_id - shift_offset_id
        o_predecessors = predecessors[o_local_id]
        for pred_loc_id in o_predecessors:
            pred_global_id = pred_loc_id + shift_offset_id # shift RIGHT: local -> global
            pred_instance = model.get_component(pred_global_id)
            if pred_instance.add_effects_bitwise & o.pos_precons_bitwise != 0:
                o_achievers.add(pred_global_id)
        achivers_group[o.global_id] = o_achievers
        
    return achivers_group

def _calculate_TO_reachable(model):
    """
    Calculate the reachable set of operators for each task.

    NOTE: R_set (List[Set[int]]): A list where each index corresponds to a task's local ID, 
         and each element is a set of reachable task local IDs.
    NOTE: visited (List[int]): A list to track which tasks have been 
        visited during the depth-first search (DFS).
    NOTE: v_it (int): A visit marker that increments with each DFS 
        run to avoid resetting the `visited` list.
    NOTE: shift_offset_ids (int): The offset used to map global task IDs to local task IDs.
    
    TODO: Use Dijkstra for updating nodes instead of dfs not sure if compensate
    """
    
    len_operators      = len(model.operators)
    len_abstract_tasks = len(model.abstract_tasks)
    shift_offset_ids = model.ifacts_end+1
    
    R_set = [set() for _ in range(len_operators + len_abstract_tasks)]
    visited = [0] * (len_operators + len_abstract_tasks)
    v_it = 1

    for task in model.abstract_tasks:
        r_task = set()
        _dfs_iterative(model, task, R_set, r_task, v_it, visited, shift_offset_ids)
        
        # shift left to get task local ids
        task_local_id = task.global_id - shift_offset_ids
        R_set[task_local_id] = r_task
        v_it += 1

    return R_set
        

def _dfs_iterative(model, task, R, r, v_it, visited, soid):
    stack = [task]
    
    while stack:
        current_task = stack.pop()
        task_id = current_task.global_id
        
        # shift left to get task local ids
        task_local_id = task_id - soid
        
        if visited[task_local_id] == v_it:
            continue
        
        visited[task_local_id] = v_it
        r_task = R[task_local_id]
        if r_task:
            r.update(r_task)

        for decomposition in current_task.decompositions:
            for subtask in decomposition.task_network:
                if subtask in model.operators:
                    r.add(subtask.global_id - soid) # use local id
                else:
                    stack.append(subtask)


def _TOreachable_operators(model, O, achievers):
    """
        Get Total-Order achievers and remove those that cannot be reachable (not available).
        @param model: Model class
        @param O: Set of operators available
        @param achivers: Dict(key:operator_id, value:Set(operator_id))
        NOTE: shift_offset_id maps global ids to local ids, for indexing them into an array.
        NOTE: Instead of checking wheter an operator is in 'achivers' set, we verify in the 'available' set.
    """
    achievable_op = set()
    available = [0] * len(model.operators)
    shift_left_id = len(model.facts)
    for o in O:
        available[o.global_id-len(model.facts)] = 1 #shift left operators IDS

    # check if operator is applicable (achievers satisfy all operator preconditions)  
    for o in O:
        achiever_state  = model.initial_state
        removed_achievers = set()
        op_achievers = achievers[o.global_id]
        for a_id in op_achievers:
            if a_id == -1:
                continue
            if available[a_id-shift_left_id] == 0:
                removed_achievers.add(a_id)
                continue
            o_a = model.get_component(a_id)
            achiever_state = o_a.relaxed_apply_bitwise(achiever_state)
        
        op_achievers = op_achievers - removed_achievers
        if o.applicable_bitwise(achiever_state):
            achievable_op.add(o) # operator achievable
        
    return list(achievable_op)


def _Dreachable_operators(initial_task_network):
    def _dfs_reachable(task_node, R, visited):
        visited.add(task_node)
        for d in task_node.decompositions:
            for t in d.task_network:
                if isinstance(t, Operator):
                    R.add(t)
                else:
                    if t not in visited:
                        _dfs_reachable(t, R, visited)
                
    visited = set()
    tdg_reachable_operators = set()
    for t in initial_task_network:
        if isinstance(t, Operator):
            tdg_reachable_operators.add(t)
            continue
        _dfs_reachable(t, tdg_reachable_operators, visited)
    
    return tdg_reachable_operators

def _Ereachable_operators(operators, initial_state):
    reachable_operators = []
    reachable_facts = initial_state
    O = set()
    for o in operators:
        O.add(o)
    changed = True
    while changed:
        changed = False
        remove_op = set()
        for op in O:
            if not op in reachable_operators and op.applicable_bitwise(reachable_facts):
                reachable_operators.append(op)
                reachable_facts = op.relaxed_apply_bitwise(reachable_facts)
                remove_op.add(op)
                changed = True
        O-=remove_op
    return reachable_operators, reachable_facts

def _compute_achievers_set(model):
    reachable =  _calculate_TO_reachable(model)
    achievers =  _calculate_TO_achievers(model, reachable)
    return achievers

def _bottom_up_removal(R_decompositions, R_operators, R_abstract_tasks, reachable_facts):
    """
    Performs a bottom-up removal process on the reachable decompositions, operators, and abstract tasks
    to eliminate those that cannot be achieved or are invalid due to the absence of their required components.

    Decompositions are removed:
        (1) not applicable based on the current set of delete-relaxed reachable facts
        (2) some subtask (operator or abstract) was pruned
    
    Abstract tasks are removed when no longer have valid decompositions.

    The process repeats until any decomposition or task is removed.
    
    @param R_decompositions (List[Decomposition]): List of decompositions to be pruned.
    @param R_operators (List[Operator]): List of operators to be pruned.
    @param R_abstract_tasks (List[AbstractTask]): List of abstract tasks to be pruned.
    @param reachable_facts (Set[Fact]): Set of facts that are currently reachable.
    """
    
    cleaned=True
    #print(f'BEGIN {[d.global_id for d in R_decompositions]}')
    while cleaned:
        cleaned = False
        decompositions = []
        abstract_tasks = []
        # remove decompositions
        for d in R_decompositions:
            valid=True
            if not d.applicable_bitwise(reachable_facts):
                valid=False
            else:
                for t in d.task_network:
                    if isinstance(t, Operator) and t not in R_operators:
                        #print(f'TP {t.global_id} not found, D {d.global_id} will be removed')
                        valid=False
                        break
                    elif isinstance(t, AbstractTask) and t not in R_abstract_tasks:
                        #print(f'TA {t.global_id} not found, D {d.global_id} will be removed')
                        valid=False
                        break
            if valid:
                decompositions.append(d)
            else:
                d.compound_task.decompositions.remove(d)
                cleaned=True
            
        # remove abstract tasks
        for abt in R_abstract_tasks:
            if len(abt.decompositions) > 0:
                abstract_tasks.append(abt)
            else:
                cleaned=True
                #print(f'removing TA {abt.global_id} D empty')'
        
        R_decompositions.clear()
        R_decompositions.extend(decompositions)
        R_abstract_tasks.clear()
        R_abstract_tasks.extend(abstract_tasks)
    
    #print(f'END {[d.global_id for d in R_decompositions]}')

def TO_relax_reachability(model):
    start_time   = time.time()
    number_o_before   = len(model.operators)
    number_abt_before = len(model.abstract_tasks)
    number_m_before   = len(model.decompositions)

    R_abstract_tasks = model.abstract_tasks[:]
    R_operators      = model.operators[:]
    R_decompositions = model.decompositions[:]
    
    
    start_achievers = time.time()
    achiever_set = _compute_achievers_set(model)
    elapsed_achievers = time.time() - start_achievers
    if FLAGS.LOG_GROUNDER:   
        print(f'TO achievers after {elapsed_achievers:.2f} seconds.')
    
    i=0
    print(f'Starting Removal')
    while True:
        i=i+1
        count_curr_O   = len(R_operators)
        
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
        count_ERops     = len(E_Rops)
        count_TORops    = len(R_operators)
        if count_curr_O - count_TORops == 0:
            break    
          
        start_bur = time.time()                    
        _bottom_up_removal(R_decompositions, R_operators, R_abstract_tasks, reachable_facts)
        elapsed_bur = time.time() - start_bur
        if FLAGS.LOG_GROUNDER:   
            count_burRops = len(R_operators)
            print(f'\t({i}) Bottom up removal after {elapsed_bur:.2f} seconds.')
            print(f'\t\t({i}) Decomposition Space removed {count_curr_O-count_DRops_set} operators.')
            print(f'\t\t({i}) Executability Space removed {count_DRops_set-count_ERops} operators.')
            print(f'\t\t({i}) TO Ordering Constraints removed {count_ERops-count_TORops} operators.')
            print(f'\t\t({i}) Bottom up removed {count_TORops-count_burRops} operators.')
    
    model.decompositions = R_decompositions
    model.abstract_tasks = R_abstract_tasks
    model.operators      = R_operators
    model.assign_global_ids()
    
    if FLAGS.LOG_GROUNDER:   
        print(f'number of abstract tasks removed {number_abt_before - len(model.abstract_tasks)} of {number_abt_before}')
        print(f'number of operators removed: {number_o_before - len(model.operators)} of {number_o_before}')
        print(f'number of methods removed: {number_m_before-len(model.decompositions)} of {number_m_before}')
        
    print(f'TO reachability elapsed time: {time.time()-start_time:.4f} s')
    print(f'\n\n')

#TODO:  Need code refactoring for efficiency and readability
def del_relax_reachability(model):
    """
    Performs delete relaxation to identify reachable operators, tasks, and decompositions.
    It iteratively prunes elements not reachable from the task decomposition graph.

    Args:
        model (Model): The planning model to optimize.
    """
    initial_op_len = len(model.operators)
    initial_decomp_len = len(model.decompositions)
    initial_task_len = len(model.abstract_tasks)

    removed_tasks     = set()
    removed_operators = set()
    initial_operators = {op for op in model.initial_tn if isinstance(op, Operator)} #in case there are operators into the initial task network
    # TODO: problem here is to updated used_operators based on TDG, it generates invalid plans
    changed=True
    while changed:
        changed=False
        reachable_ops, positive_facts = _applicable_operators(model, model.initial_state)
        
        htn_reachable_operators = set(initial_operators)
        removed_operators |= set(model.operators) - reachable_ops
        for t in model.abstract_tasks[:]:
            if t in removed_tasks:
                continue

            
            # NOTE: remove decompositions: (1) not applicable (2) containing removed subtask
            d_removal = False  # indicate if at least one decomposition 'd' was removed from task 't' 
            for d in t.decompositions:
                if not model.applicable(d, positive_facts) or any(subtask in removed_operators or subtask in removed_tasks for subtask in d.task_network):
                # if not model.applicable(d, positive_facts):
                   t.decompositions.remove(d)
                   d_removal=True
            
            if d_removal and len(t.decompositions) == 0:
                removed_tasks.add(t)
                model.abstract_tasks.remove(t)
            
        reachable_decompositions = set()
        for t in model.abstract_tasks:
            if t in removed_tasks:
               continue
            for d in t.decompositions:
                reachable_decompositions.add(d)
                for subt in d.task_network:
                    if isinstance(subt, Operator) and not subt in removed_operators:
                        htn_reachable_operators.add(subt)
                    
        reachable_tasks = set(model.abstract_tasks) -  removed_tasks
        if FLAGS.LOG_GROUNDER:
            print(f" op ({len(model.operators)}=>{len(htn_reachable_operators)})|tsks ({len(model.abstract_tasks)}=>{len(reachable_tasks)})|decompo ({len(model.decompositions)}=>{len(reachable_decompositions)})")
        if len(reachable_tasks) != len(model.abstract_tasks) or len(htn_reachable_operators) != len(model.operators) or len(model.decompositions) != len(reachable_decompositions):
            model.operators = list(htn_reachable_operators)  
            model.decompositions = list(reachable_decompositions)
            model.abstract_tasks = list(reachable_tasks) 
            changed=True
    
    if FLAGS.LOG_GROUNDER:   
        print(f"Delete Relaxation Reachability: Operators {initial_op_len} to {len(model.operators)}, Decompositions {initial_decomp_len} to {len(model.decompositions)}, Tasks {initial_task_len} to {len(model.abstract_tasks)}")    #correctness_check(model)
    

def _applicable_operators(model, initial_facts):
    reachable_operators = set()
    reachable_facts = initial_facts
    
    changed = True
    while changed:
        changed = False
        valid_operators =  set(model.operators) - reachable_operators
        for op in valid_operators:
            if not op in reachable_operators and model.applicable(op, reachable_facts):
                reachable_operators.add(op)
                reachable_facts = op.relaxed_apply_bitwise(reachable_facts)
                changed = True
    return reachable_operators, reachable_facts

def correctness_check(model):
    ab_set = set(model.abstract_tasks)
    op_set = set(model.operators)

    tn_errors=[]
    for d in model.decompositions:
        for t in d.task_network:
            if type(t) is AbstractTask and not t in ab_set:
                tn_errors.append(f"ABTASK {d.name} -> {t.name}")
            elif type(t) is Operator and not t in op_set:
                tn_errors.append(f"OPERATOR {d.name} -> {t.name}")

    if len(tn_errors)>0:
        print("MODEL INCONSISTENCIES FOUND")
        print(tn_errors)
        exit(0)
    

def pullup(model):
    if FLAGS.LOG_GROUNDER:
        print('initializing pullup')
    ctask_map = {} # map each decomposition to its compound task
    for abtask_idx, ab_task in enumerate(model.abstract_tasks):
        for decomp in ab_task.decompositions:
            ctask_map[decomp] = abtask_idx

    # Progression and done pullup control
    decomp_progression = [0] * len(model.decompositions)
    task_progression   = [0] * len(model.abstract_tasks)
    decomp_done = [False] * len(model.decompositions)
    task_done   = [False] * len(model.abstract_tasks)

    #check for empty decompositions:
    for m_idx, decomp in enumerate(model.decompositions):
        if len(decomp.task_network) == 0:
            decomp_done[m_idx] = True
    
    decomp_pullup_eff = [0] * len(model.decompositions)
    changed=True
    iterations=0
    while changed:
        iterations += 1
        count_op_pus = 0
        count_m_pus = 0
        count_t_pus = 0
        changed=False
        for m_idx, decomp in enumerate(model.decompositions):
            if decomp_done[m_idx]:
                continue
            
            next_task = decomp.task_network[decomp_progression[m_idx]]
            # if operator, pullup facts that are not effects of some previous task
            if type(next_task) is Operator:
                pullup_precons = next_task.pos_precons_bitwise & ~decomp_pullup_eff[m_idx]
                decomp_pullup_eff[m_idx] |= next_task.add_effects_bitwise
                decomp.pos_precons_bitwise |= pullup_precons
                count_op_pus+=1
                
            # if abstract task and its done, pullup common facts from task's decompositions
            else:
                ctask_idx = ctask_map[decomp]
                if not task_done[ctask_idx]:
                    continue
                precons_intersec = next_task.decompositions[0]
                for d in next_task.decompositions:
                    precons_intersec &= d.pos_precons_bitwise
                pullup_precons = precons_intersec & ~decomp_pullup_eff[m_idx]
                decomp.pos_precons_bitwise |= pullup_precons
                count_t_pus+=1
                #print(f'>>> ABSTRACT task pullup {decomp.name}')


            # check if decomposition and task are done
                # decomposition pullup over all task network
                # abstract task pullup over all decompositions
            decomp_progression[m_idx]+=1
            if decomp_progression[m_idx] >= len(decomp.task_network):
                decomp_done[m_idx]=True
                #print(f'({decomp_progression[m_idx]}) decomposition pullup {decomp.name}')
                count_m_pus+=1
                ctask_idx = ctask_map[decomp]
                task_progression[ctask_idx]+=1
                compound_task = model.abstract_tasks[ctask_idx]
                if task_progression[ctask_idx] >= len(compound_task.decompositions):
                    task_done[ctask_idx] = True
            changed=True    
        if FLAGS.LOG_GROUNDER:
            print(f"it ({iterations}) Pullup Op {count_op_pus} Pullup Methods {count_m_pus} Pullup Tasks {count_t_pus}")
    
    if FLAGS.LOG_GROUNDER:
        print(f'Pullup ended')
    
        
