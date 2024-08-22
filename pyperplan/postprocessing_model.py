from copy import deepcopy
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
    Calculate the achievers for each action.
    The achievers are those that came before the action using Total-Order constraint
    """
    predecessors = {a.global_id: set() for a in model.operators}
    for decomposition in model.decompositions:
        subtasks = decomposition.task_network
        for i in range(len(subtasks)):
            task_i = subtasks[i].global_id
            for action_id in reachable[task_i]:
                for j in range(i - 1, -1, -1):
                    task_j = subtasks[j].global_id
                    predecessors[action_id].update(reachable[task_j])
    
    subtasks = model.initial_tn
    for i in range(len(subtasks)):
        task_i = subtasks[i].global_id
        for action_id in reachable[task_i]:
            for j in range(i - 1, -1, -1):
                task_j = subtasks[j].global_id
                predecessors[action_id].update(reachable[task_j])

    achivers_set = {a.global_id: set() for a in model.operators}
    for o in model.operators:
        if o.relaxed_applicable_bitwise(model.initial_state):
            achivers_set[o.global_id] = {-1}
            continue
        
        preconditions = o.get_precons_bitfact()
        o_achievers = set()
        for pre in preconditions:
            o_achievers.update(
                o_id for o_id in predecessors[o.global_id] if ((model.get_component(o_id).add_effects_bitwise) & (1 << pre) != 0)
            )
        achivers_set[o.global_id] = o_achievers
        
    return achivers_set

def _calculate_TO_reachable(model):
    """
    Calculate the reachable set of actions for each task, both primitive and compound.
    """
    
    reachable = {task.global_id: set() for task in model.abstract_tasks}
    for action in model.operators:
        reachable[action.global_id] = {action.global_id}
    
    for task in model.abstract_tasks:
        r_task = set()
        _dfs(model, task, reachable, r_task, visited=set())
        reachable[task.global_id] = deepcopy(r_task)
    return reachable
        

def _dfs(model, task, R, r, visited):
    """
    Perform a depth-first search to find all reachable tasks for a compound task.
    
    Args:
        task (int): The task ID for which to compute the reachable set.
        visited (set): Set of visited tasks to prevent cycles.
    """
    if task in visited:
        return
    
    visited.add(task)

    # if reachable set of a given task was already computed, use it
    r_task = R.get(task.global_id)
    if r_task:
        r.update(r_task)
    
    for decomposition in task.decompositions:
        for subtask in decomposition.task_network:
            if subtask in model.operators:
                r.add(subtask.global_id)
            else:
                _dfs(model, subtask, R, r, visited)

def _TOreachable_operators(model, operators):
    '''
        Based on the available operators, get TO achievers and remove those that cannot be TO achievable.
    '''
    reachable =  _calculate_TO_reachable(model)
    achievers =  _calculate_TO_achievers(model, reachable)
    achievable_op = set()
    
    for o in operators:
        # check if operator is applicable
        achiever_state  = model.initial_state
        for a_id in achievers[o.global_id]:
            if a_id == -1:
                continue
            achiever_state = model.get_component(a_id).relaxed_apply_bitwise(achiever_state)
        if o.applicable_bitwise(achiever_state):
            achievable_op.add(o) # achievable
        
    
    
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
    
    changed = True
    while changed:
        changed = False
        remove_op = set()
        for op in operators:
            if not op in reachable_operators and op.applicable_bitwise(reachable_facts):
                reachable_operators.append(op)
                reachable_facts = op.relaxed_apply_bitwise(reachable_facts)
                remove_op.add(op)
                changed = True
        operators-=remove_op
    return reachable_operators, reachable_facts

def TO_relax_reachability(model):
    start_time   = time.time()
    # TODO: already assigned IDs
    changed=True
    i=0
    number_o_before   = len(model.operators)
    number_abt_before = len(model.abstract_tasks)
    number_m_before   = len(model.decompositions)
    while True:
        i+=1
        changed=False
        count_curr_O   = len(model.operators)
        D_Rops_set = _Dreachable_operators(model.initial_tn) # operators reachable by decomposition space
        count_DRops_set = len(D_Rops_set)
        E_Rops, reachable_facts = _Ereachable_operators(D_Rops_set, model.initial_state) # operators reachable by executability space
        count_ERops = len(E_Rops)
        TO_Rops = _TOreachable_operators(model, E_Rops) # operators reachable by total-order constraints
        count_TORops = len(TO_Rops)
        
        if FLAGS.LOG_GROUNDER:   
            print(f'OPERATORS: {len(model.operators)}')
            print(f'\tDecomposition Space removed {number_o_before-count_DRops_set} operators.')
            print(f'\tExecutability Space removed {count_DRops_set-count_ERops} operators.')
            print(f'\tTO Ordering Constraints removed {count_ERops-count_TORops} operators.')
            print(f'Result: {len(TO_Rops)}')

        if count_curr_O - count_TORops == 0:
            break    

        # Clean TDG
        cleaned=True
        while cleaned:
            cleaned = False
            decompositions = []
            for d in model.decompositions:
                valid=True
                if not d.applicable_bitwise(reachable_facts):
                    valid=False
                else:
                    for t in d.task_network:
                        if isinstance(t, Operator) and t not in TO_Rops:
                            #print(f'TP {t.global_id} not found, D {d.global_id} will be removed')
                            valid=False
                            break
                        elif isinstance(t, AbstractTask) and t not in model.abstract_tasks:
                            #print(f'TA {t.global_id} not found, D {d.global_id} will be removed')
                            valid=False
                            break

                if valid:
                    decompositions.append(d)
                else:
                    #print(f'removing D {d.global_id} from TA {d.compound_task.global_id}')
                    d.compound_task.decompositions.remove(d)
                    cleaned=True
            
            abstract_tasks = []
            for abt in model.abstract_tasks:
                if len(abt.decompositions) > 0:
                    abstract_tasks.append(abt)
                else:
                    cleaned=True
                    #print(f'removing TA {abt.global_id} D empty')
            model.decompositions = decompositions
            model.abstract_tasks = abstract_tasks    

        model.operators      = TO_Rops
        model.assign_global_ids()
    
    if FLAGS.LOG_GROUNDER:   
        print(f'number of abstract tasks removed {number_abt_before - len(model.abstract_tasks)} of {number_abt_before}')
        print(f'number of operators removed: {number_o_before - len(model.operators)} of {number_o_before}')
        print(f'number of methods removed: {number_m_before-len(model.decompositions)} of {number_m_before}')
    
    print(f'TO reachability elapsed time: {time.time()-start_time:.4f} s')

#TODO:  fixing it 
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
    
        
