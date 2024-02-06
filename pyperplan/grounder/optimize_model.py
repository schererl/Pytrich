#
# This file is part of pyperplan.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#

"""
Classes and methods for grounding a schematic PDDL task to a STRIPS planning
task.
"""

from ..model import Operator, Model, AbstractTask, Decomposition
import logging
import sys
def clean_tdg(
    model    
):
    """
    Compresses the model representation to optimize memory usage and performance.

    simple TDG cleaning: It filters out unachivabçe operators and decompositions based on the initial task network,
    and updates the model with only the necessary elements.
    It also logs the memory usage before and after the compression for profiling purposes.
    """

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
    op_before            = sys.getsizeof(model.operators) 
    decomp_before        = sys.getsizeof(model.decompositions) 
    abs_tasks_before     = sys.getsizeof(model.abstract_tasks) 
    model.operators      = used_operators
    model.decompositions = used_decompositions
    model.facts          = used_facts
    model.abstract_tasks = used_abstract_tasks
    op_after     = sys.getsizeof(model.operators) 
    decomp_after = sys.getsizeof(model.decompositions)
    tasks_after  = sys.getsizeof(model.abstract_tasks)
    logging.info(f"cleaning operators: before {op_before} bytes ==> after {op_after} bytes")
    logging.info(f"cleaning decompositions: before {decomp_before} bytes ==> after {decomp_after} bytes")
    logging.info(f"cleaning tasks: before {abs_tasks_before} bytes ==> after {tasks_after} bytes")
    logging.info(f"used facts: {len(used_facts)}")

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
    
def del_relax_rechability(model):
    """
    Performs delete relaxation to identify reachable operators, tasks, and decompositions.
    It iteratively prunes elements not rechable from the TDG.

    **UNDER DEVELOPMENT**
    Args:
        model (Model): The planning model to optimize.
    """
    # profilling stuff
    op_before     = sys.getsizeof(model.operators) 
    decomp_before = sys.getsizeof(model.decompositions) 
    abs_tasks_before = sys.getsizeof(model.abstract_tasks) 

    it= 0
    changed=True
    used_operators, positive_facts = rechable_operators(model, model.initial_state)
    removable_operators      = set(model.operators)-(used_operators)
    
    while changed:
        it+=1
        changed, used_operators, used_abstract_tasks, used_decompositions =  relaxed_tdg_rechability(model, removable_operators, positive_facts)
        model.operators      = list(used_operators)
        model.abstract_tasks = list(used_abstract_tasks)
        model.decompositions = list(used_decompositions)
        
    # profilling stuff
    op_after         = sys.getsizeof(list(used_operators) )
    decomp_after     = sys.getsizeof(list(used_decompositions))
    tasks_after      = sys.getsizeof(list(used_abstract_tasks))

    logging.info(f"cleaning operators: before {op_before} bytes ==> after {op_after} bytes")
    logging.info(f"cleaning decompositions: before {decomp_before} bytes ==> after {decomp_after} bytes")
    logging.info(f"cleaning tasks: before {abs_tasks_before} bytes ==> after {tasks_after} bytes")
                

def rechable_operators(model, initial_facts):
    # Initialize reachable facts from the initial state
    reachable_operators = set()
    reachable_facts = initial_facts
    changed = True
    while changed:
        changed = False
        for op in model.operators:
            if not op in reachable_operators and model.applicable(op, reachable_facts):
                reachable_operators.add(op)
                reachable_facts = op.relaxed_apply_bitwise(reachable_facts)
                changed = True
    return reachable_operators, reachable_facts



def relaxed_tdg_rechability(model, removable_operators, positive_facts):
    changed=False
    
    used_abstract_tasks      = set()
    used_operators           = set()
    used_decompositions      = set()
    
    removable_tasks          = set()
    removable_decompositions = set()
    
    visited_tasks            = set()
    tasks = model.initial_tn[:]
    while len(tasks)>0:
        task = tasks.pop(0)
        if task in visited_tasks:
            continue
        visited_tasks.add(task)

        # If operador is applicable, use it
        if type(task) == Operator:
            if task.applicable_bitwise(positive_facts):
                if not task in removable_operators:
                        used_operators.add(task)
                else: 
                    removable_operators.add(task)
        else:
            # Each method should be relaxed applicable, but also should have every subtask available, otherwise, remove method.
            for method in model.methods(task):
                if not method.applicable_bitwise(positive_facts) or any((subtask in removable_tasks or subtask in removable_operators) for subtask in method.task_network):
                    removable_decompositions.add(method)
                    task.decompositions.remove(method)
                    changed=True
                    continue
                tasks+= model.decompose(method)[:]
                if not method in used_decompositions:
                    used_decompositions.add(method)
                    
            
            # removed_methods = prev_decompositions-len(task.decompositions)
            # if removed_methods > 0:
            #    changed=True
                #logging.info(f"Task {task} has {removed_methods} of {prev_decompositions} removable decompositions")
            if len(task.decompositions)==0:
                #logging.info(f"Task {task} removed")
                removable_tasks.add(task)
            elif len(task.decompositions)>0 and not task in used_abstract_tasks:
                    used_abstract_tasks.add(task)

    print(f'AFTER ({len(model.abstract_tasks)}) removable task removed {len(removable_tasks)} used {len(used_abstract_tasks)}')
    print(f'AFTER ({len(model.decompositions)}) removable decompositions removed {len(removable_decompositions)} used {len(used_decompositions)}')
    print(f'AFTER ({len(model.operators)}) operators used {len(used_operators)} removed {len(removable_operators)}\n')
    return changed, used_operators, used_abstract_tasks, used_decompositions

