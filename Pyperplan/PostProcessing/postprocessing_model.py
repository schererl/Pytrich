
import logging
import sys


from Pyperplan.model import Operator, AbstractTask
import Pyperplan.FLAGS as FLAGS


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
    
        
