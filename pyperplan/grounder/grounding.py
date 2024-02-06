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

from collections import defaultdict
from copy import deepcopy
import itertools
import logging
import re
from ..utils import LogicalOperator


from ..model import Operator, Model, AbstractTask, Decomposition
from .optimize_model import clean_tdg, remove_negative_precons, convert_bitwise_repr, del_relax_rechability

# controls mass log output
verbose_logging = False


def ground(
    problem, remove_statics_from_initial_state=True, remove_irrelevant_operators=True
):
    """
    This is the main method that grounds the PDDL task and returns an
    instance of the task.Task class.

    @note Assumption: only HDDL problems with types at the moment.

    @param problem A hddl.Problem instance describing the parsed problem
    @return A model.Model instance with the grounded problem
    """

    """
    Overview of variable names in hddl.py, grounding.py and task.py:
    Problem.initial_state       -> init                 -> Model.initial_state
    Problem.goal                -> goal                 -> Model.goal
    Problem.htn                 -> initial task network -> Model.goal
    Problem.domain.actions      -> operators            -> Model.operators
    Problem.domain.methods      -> decompositions       -> Model.operators
    Problem.domain.tasks        -> groundedTasks        -> Model.operators
    Problem.domain.predicates   -> variables            -> Model.facts
    """
    domain = problem.domain
    actions = domain.actions.values()
    methods =  domain.methods.values()
    tasks = domain.tasks.values()
    initial_tn = problem.htn
    
    # Objects
    objects = problem.objects
    objects.update(domain.constants)
    
    if verbose_logging:
        logging.debug("Objects:\n%s" % objects)

    # Create a map from types to objects
    type_map = _create_type_map(objects)
    
    if verbose_logging:
        logging.debug("Type to object map:\n%s" % type_map)

    # Transform initial state into a specific
    init = _get_partial_state(problem.initial_state)
    if verbose_logging:
        logging.debug("Initial state with statics:\n%s" % init)
    
                          
    # Ground tasks
    grounded_tasks  = _ground_tasks(tasks, type_map)
    
    # Ground initial task network
    grounded_initial_tn = _ground_initial_tn(initial_tn, grounded_tasks)
    
    # Ground actions
    operators = _ground_actions(actions, type_map)
    
    # Ground methods
    decompositions = _ground_methods(methods, operators, grounded_tasks, type_map) 
    
    if verbose_logging:
        logging.debug("Operators:\n%s" % "\n".join(map(str, operators)))
        logging.debug("Grounded Tasks:\n%s" % "\n".join(map(str, grounded_tasks)))
        logging.debug("Decompositions:\n%s" % "\n".join(map(str, decompositions)))
    
    # Ground goal
    goals = _get_partial_state(problem.goal)
    if verbose_logging:
        logging.debug("Goal:\n%s" % goals)

    facts = [] #NOTE: check here about facts and how they are used in the 'Task/Model'

    
    model = Model(problem.name, facts, init, grounded_initial_tn, goals, operators, decompositions, grounded_tasks)
    # remove operators and tasks not achievable from initial task network
    clean_tdg(model)
    # remove negative preconditions converting it into negated facts 'not_<literal>'
    remove_negative_precons(model)
    # convert facts representation to bitwise
    convert_bitwise_repr(model)
    # remove non delete relaxed tdg operators, tasks and methods
    del_relax_rechability(model) #NOTE: works only using bitwise representation
    
    
    return model


def _create_type_map(objects):
    """
    Create a map from each type to its objects.

    For each object we know the type. This returns a dictionary
    from each type to a set of objects (of this type). We also
    have to care about type hierarchy. An object
    of a subtype is a specialization of a specific type. We have
    to put this object into the set of the supertype, too.
    """
    type_map = defaultdict(set)
    
    # for every type we append the corresponding object
    for object_name, object_type in objects.items():
        parent_type = object_type.parent
        while True:
            type_map[object_type].add(object_name)
            object_type, parent_type = parent_type, object_type.parent
            if parent_type is None:
                # if object_type is None:
                break

    # TODO sets in map should be ordered lists
    return type_map

def _collect_facts(operators):
    """
    Collect all facts from grounded operators (precondition, add
    effects and delete effects).
    """
    facts = set()
    for op in operators:
        facts |= op.pos_precons | op.neg_precons | op.add_effects | op.del_effects
    return facts

def _assign_objects(lifted_structure, type_map):
    param_to_objects = {}
    for param_name, param_types in lifted_structure.signature:
        # List of sets of objects for this parameter
        objects = [type_map[type] for type in param_types]
        # Combine the sets into one set
        objects = set(itertools.chain(*objects))
        param_to_objects[param_name] = objects
        #print("Parameter {}: Possible Objects -> {}".format(param_name, objects))
    domain_lists = [
        [(name, obj) for obj in objects] for name, objects in param_to_objects.items()
    ]
    
    assignments = itertools.product(*domain_lists)
    return assignments

def _ground_initial_tn(initial_tn, grounded_tasks):
    """
    Get the initial task network instances from the grounded tasks.
    @param initial_tn: List of initial tasks
    @param grounded_tasks: List of grounded tasks
    """
    grounded_itn = []
    grounded_task_dict = {gt.name:gt for gt in grounded_tasks}
    for tsksig in initial_tn.signature:
        task_name = tsksig[0]
        task_args = [literal for literal, _ in tsksig[1]]
        task_id =_get_grounded_string(task_name, task_args)
        grounded_task = grounded_task_dict.get(task_id)
        if grounded_task:
            grounded_itn.append(grounded_task)
        
    return grounded_itn
      
   

def _ground_methods(methods, primitive, abstract, type_map):
    """
    Ground a list of methods and return the resulting list of decompositions.

    @param methods: List of methods
    @param type_map: Mapping from type to objects of that type
    @param primitive: List of primitive tasks (Operators)
    @param abstract: List of abstract tasks (GroundedTasks)
    """
    decompositions = []
    # NOTE: for now we need those dictionaries to avoid iterating over lists multiple times
    primitive_dict = {p.name:p for p in primitive}
    abstract_dict = {ab.name:ab for ab in abstract}
    decomp_lists = [_ground_method(m, primitive_dict, abstract_dict, type_map) for m in methods]
    decompositions = list(itertools.chain(*decomp_lists))
    return decompositions

def _ground_tasks(tasks, type_map):
    """
    Ground a list of tasks and return the resulting list of grounded tasks.

    @param tasks: List of tasks
    @param type_map: Mapping from type to objects of that type
    """
    ground_task_lst =  [_ground_task(task, type_map) for task in tasks]
    grounded_tasks = list(itertools.chain(*ground_task_lst))
    return grounded_tasks

def _ground_actions(actions, type_map):
    """
    Ground a list of actions and return the resulting list of operators.

    @param actions: List of actions
    @param type_map: Mapping from type to objects of that type
    @param statics: Names of the static predicates
    @param init: Grounded initial state
    """
    op_lists = [_ground_action(action, type_map) for action in actions]
    operators = list(itertools.chain(*op_lists))
    return operators

def _ground_task(task, type_map):
    assignments = _assign_objects(task, type_map)
    
    ops = [
        _create_grounded_task(task, dict(assign)) for assign in assignments
    ]
    
    ops = filter(bool, ops)
    return ops


def _ground_method(method, primitive, abstract, type_map):
    assignments = _assign_objects(method, type_map)
    
    ops = [
        _create_grounded_method(method, primitive, abstract, dict(assign)) for assign in assignments
    ]
    ops = filter(bool, ops)
    return ops

def _ground_action(action, type_map):
    """
    Ground the action and return the resulting list of operators.
    """
    import time
    logging.debug("Grounding %s" % action.name)
    assignments = _assign_objects(action,type_map)
    ops = [
        _create_operator(action, dict(assign)) for assign in assignments
    ]
    ops = filter(bool, ops)
    return ops


def _create_grounded_method(method, primitive, abstract, assignment):
    args = [assignment[name] for name, types in method.signature]
    method_name = _get_grounded_string(method.name, args)
    
    if method.precondition is None:
        pos_precons = []
        neg_precons = []
    else:
        # Check for '=' preconditions, in this case 'not =' restriction
        if len(method.precondition.neqlist) > 0:
            for t in method.precondition.neqlist:
                if assignment[t[0].name] == assignment[t[1].name]:
                    return None
        pos_precons = _ground_atoms(method.precondition.poslist, assignment)
        neg_precons = _ground_atoms(method.precondition.neglist, assignment)
        

    # grounding decomposed task according to its signature and method literals
    task_args = [assignment[dt_sig[0]] for dt_sig in method.decomposed_task.signature]
    decomposed_task_id = _get_grounded_string(method.decomposed_task.name, task_args)
        
    # grounding task network according to its signature and method literals
    task_network = [] 
    for subt_sig  in method.ordered_subtasks.signature:
        
        subtask_name = subt_sig[0]
        task_type = subt_sig[2]
        subtask_args = []
        for param_sig in subt_sig[1]:
            subtask_args.append(assignment[param_sig[0]])
        
        task_id = _get_grounded_string(subtask_name, subtask_args)
        
        if task_type == 'primitive':
            primitive_task = primitive.get(task_id)
            if primitive_task:
                task_network.append(primitive_task)
           

        elif task_type == 'abstract':
            abstract_task = abstract.get(task_id)
            if abstract_task:
                task_network.append(abstract_task)
            
    
    decomposition= Decomposition(method_name, pos_precons, neg_precons, decomposed_task_id, task_network)    
    if decomposed_task_id in abstract:
        abstract[decomposed_task_id].decompositions.append(decomposition)
        
    return decomposition 

def _create_grounded_task(task, assignment):
    args = [assignment[name] for name, types in task.signature]
    name = _get_grounded_string(task.name, args)
    return AbstractTask(name)

def _create_operator(action, assignment):
    """Create an operator for "action" and "assignment".
    @param assignment: mapping from predicate name to object name
    """
    #print("\n--- Creating Operator ---")
    #print(f"Action: {action.name}")
    #print(f"Assignment: {assignment}")
    #precons = _ground_preconditions(action.precondition, assignment)
    pos_precons = _ground_atoms(action.precondition.poslist, assignment)
    neg_precons = _ground_atoms(action.precondition.neglist, assignment)
    add_effects = _ground_atoms(action.effect.addlist, assignment)
    del_effects = _ground_atoms(action.effect.dellist, assignment)
    args = [assignment[name] for name, types in action.signature]
    name = _get_grounded_string(action.name, args)
    return Operator(name, pos_precons, neg_precons, add_effects, del_effects)


def _get_grounded_string(name, args):
    """We use the lisp notation (e.g. "(unstack c e)")."""
    args_string = " " + " ".join(args) if args else ""
    return f"({name}{args_string})"


def _ground_atom(atom, assignment):
    """
    Return a string with the grounded representation of "atom" with respect
    to "assignment".
    """
    names = []
   
    for name, types in atom.signature:
        if name in assignment:
            names.append(assignment[name])
        else:
            names.append(name)
    return _get_grounded_string(atom.name, names)


def _ground_atoms(atoms, assignment):
    """Return a set of the grounded representation of the atoms."""
    return {_ground_atom(atom, assignment) for atom in atoms}

def _get_fact(atom):
    """Return the string representation of the grounded atom."""
    args = [name for name, types in atom.signature]
    return _get_grounded_string(atom.name, args)

def _get_partial_state(atoms):
    """Return a set of the string representation of the grounded atoms."""
    return frozenset(_get_fact(atom) for atom in atoms)