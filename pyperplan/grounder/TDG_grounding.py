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
verbose_logging = False


import psutil
import time
from .errors import OutOfMemoryError, OutOfTimeError


class TDGGround(Grounder):

    def __init__(self,
        problem
    ):
        super().__init__(problem)
        self.start_time   =  time.time()
        self.heart_time   = time.time()
        self.heart_memory = time.time()
        self.status = 'EMPTY'

    def monitor_memory(self):
        if time.time() - self.heart_memory > 0.1:
            self.heart_memory = time.time()
            psutil.cpu_percent()
            if psutil.virtual_memory().percent > 85:
                raise OutOfMemoryError('MEM OVERFLOW')

    def monitor_time(self):
        if time.time() - self.heart_time > 0.1:
            self.heart_time = time.time()
            if time.time() - self.start_time > 60:
                raise OutOfTimeError('TIMEOUT')
    
    def groundify(self):
        self.grounded_init  = self._get_partial_state(self.problem.initial_state)
        self.grounded_goals = self._get_partial_state(self.problem.goal)
        try:
            self._run_TDGGround(self.lifted_itn)
        except OutOfMemoryError as e:
            self.status = e
            return None
        except OutOfTimeError as e:
            self.status = e
            return None
        except RecursionError as e:
            self.status =  'STACK OVERFLOW' 
            return None
        
        
        self.grounded_tasks   = [ t for t in self.grounded_tasks.values()]
        self.grounded_methods = [ m for m in self.grounded_methods.values()]
        self.grounded_actions = [ a for a in self.grounded_actions.values()]
        
        self.status = 'SUCCESS'
        return super().groundify()
    
    def _run_TDGGround(self, lifted_itn):
        """
            The grounding process initiates with the initial task network, 
            progressively working through the hierarchy 
            to ground all accessible methods, tasks, and operators. 
            
            This procedure utilizes constants derived from previously grounded tasks 
            to ensure consistency and completeness. 
            Additionally, it constructs the Task Decomposition Graph (TDG), 
            for planning search by representing the relationships 
            and dependencies among tasks, methods, and operators in a grounded context.
        """
        for lifted_task in lifted_itn:
            parameters     = [str(ptype[0]) for ptype in lifted_task.signature]
            grounded_task  = self._ground_task(lifted_task, parameters)
            self.grounded_itn.append(grounded_task)

    def _find_decompositions(self, compound_task, assignment):
        '''
        Identifies which methods can be decomposed by the given compound task, ensuring
        that each method is grounded in accordance with parameters already established by
        the compound task.

        The method iterates through all lifted methods to find those applicable for
        decomposition based on the compound task. For each compatible method,
        it maps the compound task's parameters to the method's parameters and attempts to
        ground the method using these mapped values. 

        @param compound_task: The grounded task that is being decomposed.
        @param assignment: A dictionary mapping each parameter to its assigned value within
                        the context of the compound task.
        '''
        self.monitor_memory()
        self.monitor_time()
        
        for l_m in self.lifted_methods:
            
            if not l_m.compound_task.name in compound_task.name:
                continue
            
            lifted_to_ground_map = {}
            # the parameters used in the compound task will be assigned to the method
            for idx, dt_s in enumerate(l_m.compound_task.signature):
                lifted_to_ground_map[dt_s[0]] = assignment[idx]
            
            assignments =self._assign_objects(l_m, self.type_map, already_facts = lifted_to_ground_map)
            for assign in assignments:
                grounded_method = self._ground_method(l_m, compound_task, dict(assign)) 
                if not grounded_method is None:
                    compound_task.decompositions.append(grounded_method)
            
        
        
        
    def _reach_task_network(self, decomposition, lifted_method, assignment):
        '''
        Expands the task network for a given decomposition by grounding each subtask defined in the lifted method.
        This involves identifying whether each subtask is a primitive action or abstract and grounding it accordingly.

        Args:
            decomposition: The current decomposition object being expanded.
            lifted_method: The lifted method from which the task network is being constructed.
            assignment: The current assignment of parameters to values for grounding.

        '''
        self.monitor_memory() 
        self.monitor_time()
        
        
        # reach task network
        for subt in lifted_method.ordered_subtasks:
            subtask_name = subt.name
            
            # empty subtask
            if subtask_name is None:
                break
            
            subtask_sig  = subt.signature
            task_type    = subt.task_type
            subt_params = []
            for param_sig in subtask_sig:
                subt_assign = assignment.get(param_sig[0])
                if subt_assign is None: # its a constant, already assignment
                    subt_assign = self.objects.get(param_sig[0]).name
                
                subt_params.append(subt_assign)
                    
            
            if task_type == 'primitive':
                l_a = self.lifted_actions[subtask_name]
                new_operator = self._ground_operator(l_a, subt_params)
                decomposition.task_network.append(new_operator)
            else:
                l_t = self.lifted_tasks[subtask_name]
                new_task = self._ground_task(l_t, subt_params)
                decomposition.task_network.append(new_task)

    def _ground_method(self, lifted_method, compound_task, assignment):
        '''
        Grounds a method based on the current assignment of parameters. 

        Args:
            lifted_method: The method to ground.
            compound_task: The compound task that this method decomposes.
            assignment: Mapping of parameter names to their assigned values.

        Returns:
            A Decomposition object if the method can be successfully grounded; otherwise, None.
        '''
        self.monitor_memory() 
        self.monitor_time()
        
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
        self.grounded_methods[decomposition.name] = decomposition #NOTE: not necessary to check if it is already there because the task would be there first and it will return before reching the method
        
        self._reach_task_network(decomposition, lifted_method, assignment)
        return decomposition           
                
    def _ground_task(self, lifted_task, parameters):
        '''
        Grounds a lifted task into a specific instance by assigning the given parameters.
        If the task has not been grounded before, it is added to the set of grounded tasks.

        Args:
            lifted_task: The task to ground.
            parameters: The parameters to assign to the task.

        Returns:
            The grounded task instance.
        '''
        self.monitor_memory() 
        self.monitor_time()
        
        grounded_name = self._get_grounded_string(lifted_task.name, parameters)
        task = self.grounded_tasks.get(grounded_name)
        if task is None:
            task = AbstractTask(grounded_name) 
            self.grounded_tasks[grounded_name] = task
            self._find_decompositions(task, parameters)
        return task

    def _ground_operator(self, lifted_action, parameters):
        '''
        Grounds a lifted action into an operator by assigning the given parameters.
        This includes grounding the action's preconditions and effects.

        Args:
            lifted_action: The action to ground.
            parameters: The parameters to assign to the action.

        Returns:
            The grounded operator instance.
        '''
        self.monitor_memory() 
        self.monitor_time()
        
        #print(f'grounded_name {lifted_action} \n {parameters}')
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
        self.monitor_memory() 
        self.monitor_time()
        
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
