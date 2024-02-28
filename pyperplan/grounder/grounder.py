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

class Grounder:
    def __init__(self,
        problem
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
        self.problem  = problem
        self.domain   = problem.domain
        self.objects  = self.problem.objects
        self.objects.update(self.domain.constants)
        self.lifted_actions = {action.name: action for action in self.domain.actions.values()}        
        self.lifted_tasks   = {task.name: task for task in self.domain.tasks.values()}        
        self.lifted_methods =  self.domain.methods.values()
        self.lifted_itn     = self.problem.htn                      
        self.type_map       = self._create_type_map(self.objects)

        self.grounded_init  = set()
        self.grounded_goals = set()
        self.grounded_itn     = []
        self.grounded_actions = {}
        self.grounded_methods = {}
        self.grounded_tasks   = {}


    def groundify(self):
        self.grounded_actions = [a for a in self.grounded_actions]
        self.grounded_methods = [a for a in self.grounded_methods]
        self.grounded_tasks   = [a for a in self.grounded_tasks]
        
        for t in self.grounded_tasks:
            t.decompositions.sort(key=lambda x: x.name, reverse=True)
        
        self.grounded_methods.sort(key=lambda x: x.name, reverse=True) 
        self.grounded_actions.sort(key=lambda x: x.name, reverse=True) 
        self.grounded_tasks.sort(key=lambda x: x.name, reverse=True) 
        
        model = Model(self.problem.name, [], self.grounded_init, self.grounded_itn, self.grounded_goals, self.grounded_actions, self.grounded_methods, self.grounded_tasks)
        
        # remove operators and tasks not achievable from initial task network
        clean_tdg(model)
        # remove negative preconditions converting it into negated facts 'not_<literal>'
        remove_negative_precons(model)
        # convert facts representation to bitwise
        convert_bitwise_repr(model)
        # remove non delete relaxed tdg operators, tasks and methods
        del_relax_rechability(model) #NOTE: works only using bitwise representation
        
        return model

    def _create_type_map(self, objects):
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

    def _get_grounded_string(self, name, args):
        """We use the lisp notation (e.g. "(unstack c e)")."""
        args_string = " " + " ".join(args) if args else ""
        return f"({name}{args_string})"


    def _ground_atom(self, atom, assignment):
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
        return self._get_grounded_string(atom.name, names)


    def _ground_atoms(self, atoms, assignment):
        """Return a set of the grounded representation of the atoms."""
        return {self._ground_atom(atom, assignment) for atom in atoms}

    def _get_fact(self, atom):
        """Return the string representation of the grounded atom."""
        args = [name for name, types in atom.signature]
        return self._get_grounded_string(atom.name, args)

    def _get_partial_state(self, atoms):
        """Return a set of the string representation of the grounded atoms."""
        return frozenset(self._get_fact(atom) for atom in atoms)

    def export_elements_to_txt(self, filename="grounded_elements.txt"):
        """
        Exports all grounded actions, methods, and tasks to a text file.

        :param filename: The name of the file where to save the grounded elements.
        """
        # # For grounded methods
        # for m in self.grounded_methods:
        #     # Temporarily convert frozensets to lists, sort them, and convert back to frozensets
        #     m.pos_precons = frozenset(sorted(list(m.pos_precons)))
        #     m.neg_precons = frozenset(sorted(list(m.neg_precons)))

        # # For grounded actions
        # for a in self.grounded_actions:
        #     # Repeat the process for each attribute of the actions
        #     a.pos_precons = set(sorted(list(a.pos_precons)))
        #     a.neg_precons = set(sorted(list(a.neg_precons)))
        #     a.add_effects = set(sorted(list(a.add_effects)))
        #     a.del_effects = set(sorted(list(a.del_effects)))

        with open(filename, 'w') as file:
            file.write("Actions:\n")
            for action in self.grounded_actions:
                file.write(f"{action.name}\n")
                #file.write(f"\t {sorted([a for a in action.pos_precons])}\n")
                #file.write(f"\t {sorted([a for a in action.add_effects])}\n")
                #file.write(f"\t {sorted([a for a in action.del_effects])}\n")
            
            file.write("\nMethods:\n")
            for method in self.grounded_methods:
                file.write(f"{method.name}\n")
                #file.write(f"\t {sorted([m for m in method.pos_precons])}\n")
                #for subtask in method.task_network:
                #   file.write(f"\t\t- {subtask.name}\n")
            
            file.write("\nTasks:\n")
            for task in self.grounded_tasks:
                file.write(f"{task.name}\n")
            #    if hasattr(task, 'decompositions') and task.decompositions:
            #        for decomposition in task.decompositions:
            #            file.write(f"\t\t- {decomposition.name}\n")
