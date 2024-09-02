"""
Classes and methods for grounding a schematic PDDL task to a STRIPS planning
task.
"""
from collections import defaultdict
from copy import deepcopy
import itertools
import logging
import re


from Pytrich.Grounder.grounder import Grounder
from Pytrich.model import Operator, Model, AbstractTask, Decomposition

# controls mass log output
verbose_logging = False

class FullGrounder(Grounder):
    def __init__(self,
        problem
    ):
        super().__init__(problem)



    def groundify(self):
        self.grounded_init   = self._get_partial_state(self.problem.initial_state)
        self.grounded_goals  = self._get_partial_state(self.problem.goal)
        self.grounded_tasks  = self._ground_tasks(self.lifted_tasks, self.type_map)
        self.grounded_itn    = self._ground_initial_tn(self.lifted_itn, self.grounded_tasks)
        self.grounded_actions = self._ground_actions(self.lifted_actions, self.type_map)
        self.grounded_methods = self._ground_methods(self.lifted_methods, self.grounded_actions, self.grounded_tasks, self.type_map) 
        
        
        return super().groundify()

    def _assign_objects(self, lifted_structure, type_map):
        param_to_objects = {}
        
        for param_name, param_types in lifted_structure.signature:
            # List of sets of objects for this parameter
            objects = [type_map[type] for type in param_types]
            # Combine the sets into one set
            objects = set(itertools.chain(*objects))
            param_to_objects[param_name] = objects
            
        domain_lists = [
            [(name, obj) for obj in objects] for name, objects in param_to_objects.items()
        ]
        
        assignments = itertools.product(*domain_lists)
        return assignments

    def _ground_initial_tn(self, initial_tn, grounded_tasks):
        """
        Get the initial task network instances from the grounded tasks.
        @param initial_tn: List of initial tasks
        @param grounded_tasks: List of grounded tasks
        """
        grounded_itn = []
        grounded_task_dict = {gt.name:gt for gt in grounded_tasks}
        for tsk in initial_tn:
            task_name = tsk.name
            task_args = [literal for literal, _ in tsk.signature]
            task_id =self._get_grounded_string(task_name, task_args)
            grounded_task = grounded_task_dict.get(task_id)
            if grounded_task:
                grounded_itn.append(grounded_task)
            
        return grounded_itn
        
    

    def _ground_methods(self, methods, primitive, abstract, type_map):
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
        decomp_lists = [self._ground_method(m, primitive_dict, abstract_dict, type_map) for m in methods]
        decompositions = list(itertools.chain(*decomp_lists))
        return decompositions

    def _ground_tasks(self, tasks, type_map):
        """
        Ground a list of tasks and return the resulting list of grounded tasks.

        @param tasks: List of tasks
        @param type_map: Mapping from type to objects of that type
        """
        ground_task_lst =  [self._ground_task(task, type_map) for task in tasks.values()]
        grounded_tasks = list(itertools.chain(*ground_task_lst))
        return grounded_tasks

    def _ground_actions(self, actions, type_map):
        """
        Ground a list of actions and return the resulting list of operators.

        @param actions: List of actions
        @param type_map: Mapping from type to objects of that type
        @param statics: Names of the static predicates
        @param init: Grounded initial state
        """
        op_lists = [self._ground_action(action, type_map) for action in actions.values()]
        operators = list(itertools.chain(*op_lists))
        return operators

    def _ground_task(self, task, type_map):
        assignments = self._assign_objects(task, type_map)
        
        ops = [
            self._create_grounded_task(task, dict(assign)) for assign in assignments
        ]
        
        ops = filter(bool, ops)
        return ops


    def _ground_method(self, method, primitive, abstract, type_map):
        assignments = self._assign_objects(method, type_map)
        
        ops = [
            self._create_grounded_method(method, primitive, abstract, dict(assign)) for assign in assignments
        ]
        ops = filter(bool, ops)
        return ops

    def _ground_action(self, action, type_map):
        """
        Ground the action and return the resulting list of operators.
        """
        import time
        logging.debug("Grounding %s" % action.name)
        assignments = self._assign_objects(action, type_map)
        ops = [
            self._create_operator(action, dict(assign)) for assign in assignments
        ]
        ops = filter(bool, ops)
        return ops


    def _create_grounded_method(self, method, primitive, abstract, assignment):
        args = [assignment[name] for name, types in method.signature]
        method_name = self._get_grounded_string(method.name, args)
        
        if method.precondition is None:
            pos_precons = []
            neg_precons = []
        else:
            # Check for '=' preconditions, in this case 'not =' restriction
            if len(method.precondition.neqlist) > 0:
                for t in method.precondition.neqlist:
                    if assignment[t[0].name] == assignment[t[1].name]:
                        return None
            pos_precons = self._ground_atoms(method.precondition.poslist, assignment)
            neg_precons = self._ground_atoms(method.precondition.neglist, assignment)
            

        # grounding decomposed task according to its signature and method literals
        task_args = [assignment[dt_sig[0]] for dt_sig in method.compound_task.signature]
        decomposed_task_id = self._get_grounded_string(method.compound_task.name, task_args)
            
        # grounding task network according to its signature and method literals
        task_network = [] 
        for subt in method.ordered_subtasks:
            subtask_name = subt.name
            subt_sig     = subt.signature
            task_type    = subt.task_type
            
            subtask_args = []
            for param_sig in subt_sig:
                subt_assign = assignment.get(param_sig[0])
                
                if subt_assign is None: # its a constant
                    subt_assign = self.objects.get(param_sig[0]).name
                
                subtask_args.append(subt_assign)
            
            task_id = self._get_grounded_string(subtask_name, subtask_args)
            
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

    def _create_grounded_task(self, task, assignment):
        args = [assignment[name] for name, types in task.signature]
        name = self._get_grounded_string(task.name, args)
        return AbstractTask(name)

    def _create_operator(self, action, assignment):
        """Create an operator for "action" and "assignment".
        @param assignment: mapping from predicate name to object name
        """
        pos_precons = self._ground_atoms(action.precondition.poslist, assignment)
        neg_precons = self._ground_atoms(action.precondition.neglist, assignment)
        add_effects = self._ground_atoms(action.effect.addlist, assignment)
        del_effects = self._ground_atoms(action.effect.dellist, assignment)
        args = [assignment[name] for name, types in action.signature]
        name = self._get_grounded_string(action.name, args)
        return Operator(name, pos_precons, neg_precons, add_effects, del_effects)
