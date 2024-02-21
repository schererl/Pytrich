"""
Classes and methods for grounding a schematic PDDL task to a STRIPS planning
task.
"""

from collections import defaultdict
from copy import deepcopy
import itertools
import logging
import re


from .grounder import Grounder
from ..model import Operator, Model, AbstractTask, Decomposition


# controls mass log output
verbose_logging = False


class TDGGround(Grounder):


    def __init__(self,
        problem, remove_statics_from_initial_state=True, remove_irrelevant_operators=True
    ):
        super().__init__(problem, remove_statics_from_initial_state, remove_irrelevant_operators)
        
        
    def groundify(self):
        self.grounded_init  = self._get_partial_state(self.problem.initial_state)
        self.grounded_goals = self._get_partial_state(self.problem.goal)

        for g_it in self._ground_initial_tn(self.lifted_itn):
            task = g_it[0]
            rechable_objects = g_it[1]
            
            self.grounded_itn.append(task)
            self._ground_methods(task, rechable_objects)
        
        self.grounded_tasks   = [ t for t in self.grounded_tasks.values()]
        self.grounded_methods = [ m for m in self.grounded_methods.values()]
        self.grounded_actions = [ a for a in self.grounded_actions.values()]
        
        return super().groundify()


    def _ground_methods(self, compound_task, assignment, debug=False):
        for l_m in self.lifted_methods:
            if not l_m.compound_task.name in compound_task.name:
                continue
            
            lifted_to_ground_map = {}
            # the parameters used in the compound task will be assigned to the method
            for idx, dt_s in enumerate(l_m.compound_task.signature):
                lifted_to_ground_map[dt_s[0]] = assignment[idx]
            
            assignments =self._assign_objects(l_m, self.type_map, already_facts = lifted_to_ground_map)
            
            for assign in assignments:
                grounded_method = self._reach_method(l_m, compound_task, dict(assign)) 
                if not grounded_method is None:
                    compound_task.decompositions.append(grounded_method)
        
    def _reach_method(self, lifted_method, compound_task, assignment):
        args = [a for a in assignment.values()]
        grounded_name = self._get_grounded_string(lifted_method.name, args)
        # reach method preconditions
        if lifted_method.precondition is None:
            pos_precons = []
            neg_precons = []
        else:
            # Check for '=' preconditions, in this case 'not =' restriction
            if len(lifted_method.precondition.neqlist) > 0:
                for t in lifted_method.precondition.neqlist:
                    if assignment[t[0].name] == assignment[t[1].name]:
                        return None
            pos_precons = self._ground_atoms(lifted_method.precondition.poslist, assignment)
            neg_precons = self._ground_atoms(lifted_method.precondition.neglist, assignment)
        decomposition= Decomposition(grounded_name, pos_precons, neg_precons, compound_task, [])    
        self.grounded_methods[decomposition.name] = decomposition
        self._reach_task_network(decomposition, lifted_method, assignment)
        return decomposition
        

    def _reach_task_network(self, decomposition, lifted_method, assignment):
        # reach task network
        for subt in lifted_method.ordered_subtasks:
            subtask_name = subt.name
            subtask_sig  = subt.signature
            task_type    = subt.task_type

            subt_params = []
            for param_sig in subtask_sig:
                subt_params.append(assignment[param_sig[0]])
                    
            
            if task_type == 'primitive':
                l_a = self.lifted_actions[subtask_name]
                new_operator = self._reach_action(l_a, subt_params)
                decomposition.task_network.append(new_operator)
            else:
                l_t = self.lifted_tasks[subtask_name]
                new_task = self._reach_task(l_t, subt_params)
                decomposition.task_network.append(new_task)
                
                
    def _reach_task(self, lifted_task, parameters):
        grounded_name = self._get_grounded_string(lifted_task.name, parameters)
        task = self.grounded_tasks.get(grounded_name)
        if task is None:
            task = AbstractTask(grounded_name) 
            self.grounded_tasks[grounded_name] = task
            self._ground_methods(task, parameters, debug=False)
        return task

    def _reach_action(self, lifted_action, parameters):
        
        grounded_name = self._get_grounded_string(lifted_action.name, parameters)
        
        operator = self.grounded_actions.get(grounded_name)
        if operator is None:
            action_signature = {}
            for i, var in enumerate(lifted_action.signature):
                action_signature[var[0]] = parameters[i]
            pos_precons = self._ground_atoms(lifted_action.precondition.poslist, action_signature)
            neg_precons = self._ground_atoms(lifted_action.precondition.neglist, action_signature)
            add_effects = self._ground_atoms(lifted_action.effect.addlist, action_signature)
            del_effects = self._ground_atoms(lifted_action.effect.dellist, action_signature)
            operator = Operator(grounded_name, pos_precons, neg_precons, add_effects, del_effects)
            self.grounded_actions[grounded_name] = operator

        return operator

    def _ground_initial_tn(self, lifted_itn):
        '''
            for each task into the initial task network
            return a map of task name as key, and task instance and parameters as values
        '''
        gr_itn_map = []
        for task in lifted_itn:
            parameters     = [str(ptype[0]) for ptype in task.signature]
            grounded_name  = self._get_grounded_string(task.name, parameters)
            task           = AbstractTask(grounded_name)
            self.grounded_tasks[task.name] = task
            gr_itn_map.append((task, parameters))
        return gr_itn_map

    def _assign_objects(self, lifted_structure, type_map, already_facts = {}):
        '''
            Given a lifted structure get every possible assignment based on its parameters.
            For TDGGrounder we are grounding while exploring the TDG, 
                some parameters maybe were already defined (already facts), so we use them.
            
            Example:
                Let B be a set of objects {block1, block2, block3, block4, block4}
                let g_TA be a grounded compound task of task 'TA ?a ?b' using parameters block1 block2
                let MTA be a lifted structure of a method that decomposes TA with the following signature:
                    
                    Method: MTA ?x -block ?y -block ?z -block
                        Task: TA ?x ?z
                
                we get from type_map for each value the list of block objets
                    and we already now that g_TA use ?x=block1 ?z=block2
                
                The possible assignments for MTA will be:
                    [block1] * B * [block2]
                leading to:
                    MTA block1, block1, block2
                    MTA block1, block2, block2
                    MTA block1, block3, block2
                    MTA block1, block4, block2
                    MTA block1, block5, block2

        '''
        
        param_to_objects = {}
        for param_name, param_types in lifted_structure.signature:
            # If there is already an assignment for the variable, use it
            if param_name in already_facts:
                param_to_objects[param_name] = [already_facts[param_name]]
                continue

            # If not, get every object respecting type constraint
            objects = [type_map[type] for type in param_types]
            objects = set(itertools.chain(*objects))
            param_to_objects[param_name] = objects
            
        domain_lists = [
            [(name, obj) for obj in objects] for name, objects in param_to_objects.items()
        ]
        
        assignments = itertools.product(*domain_lists)
        
        return assignments
