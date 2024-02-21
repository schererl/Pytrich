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
from ..utils import LogicalOperator
"""
This module contains all data structures needed to represent a HDDL domain and
possibly a model.
"""
class Type:
    """
    This class represents a PDDL type.
    """

    def __init__(self, name, parent):
        self.name = name.lower()
        self.parent = parent

    def __repr__(self):
        return self.name

    def __str__(self):
        if self.parent == None:
            return f'TYPE<{self.name}>'
        return f'TYPE<{self.name} {self.parent}>'
        #return f'TYPE<{self.parent},{self.name}>'

    
class Predicate:
    def __init__(self, name, signature):
        """
        name: The name of the predicate.
        signature: A list of tuples (name, [types]) to represent a list of
                   parameters and their type(s).
        """
        self.name = name
        self.signature = signature

    def __repr__(self):
        return self.name + str(self.signature)

    def __str__(self):
        return self.name + str(self.signature)


#Formula is unused right now!
# class Formula:
#     def __init__(self, operator, operands=[]):
#         # right now we only need AND
#         self._operator = operator # 'AND' | 'OR' | 'NOT'
#         self._operands = operands # Other formulas until literals
  
#     def __repr__(self):
#         return f"Formula(operator={self._operator}, operands={self._operands!r})"

#     def __str__(self):
#         if self._operator == LogicalOperator.NOOP:
#             return 'NOOP'
#         elif self._operator == LogicalOperator.LITERAL:
#             return str(self._operands) if self._operands else 'Empty Literal'
#         operand_strs = [str(operand) for operand in self._operands]
#         joined_operands = ', '.join(operand_strs)
#         return f"{self._operator.name}({joined_operands})"



class Effect:
    def __init__(self):
        """
        addlist: Set of predicates that have to be true after the action
        dellist: Set of predicates that have to be false after the action
        """
        self.addlist = set()
        self.dellist = set()
    
    def __str__(self):
        return (
            "Effect(Add: {}, Del: {})".format(
                ", ".join([str(pred) for pred in self.addlist]),
                ", ".join([str(pred) for pred in self.dellist])
            )
        )

class Precondition:
    def __init__(self):
        """
        addlist: Set of predicates that have to be true for the precondition
        dellist: Set of predicates that have to be false for the precondition
        """
        self.poslist = set()
        self.neglist = set()
        self.neqlist = set() #'=' signal solved during grounding

    def __str__(self):
        return (
            "Precondition(Pos: {}, Neg: {})".format(
                ", ".join([str(pred) for pred in self.poslist]),
                ", ".join([str(pred) for pred in self.neglist])
            )
        )


class Action:
    def __init__(self, name, signature, precondition, effect):
        """
        name: The name identifying the action
        signature: A list of tuples (name, [types]) to represent a list of
                   parameters an their type(s).
        precondition: A list of predicates that have to be true before the
                      action can be applied
        effect: An effect instance specifying the postcondition of the action
        """
        self.name = name
        self.signature = signature
        self.precondition = precondition
        self.effect = effect
    
    def __str__(self):
        return (
            "Action(Name: {}, Signature: {}, Precondition: {}, Effect: {})".format(
                self.name,
                ", ".join(["{} - {}".format(param[0], "/".join([str(ptype) for ptype in param[1]])) for param in self.signature]),
                str(self.precondition),
                str(self.effect)
            )
        )


class Method:
    def __init__(self, name, signature, precondition, compound_task, ordered_subtasks):
        """
        name: The name identifying the action
        signature: A list of tuples (name, [types]) to represent a list of
                   parameters an their type(s).
        precondition: A list of predicates that have to be true before the
                      action can be applied
        decomposed_task: Task which the method is decomposed into
        ordered_subtasks: contains the OrderedSubtasks instance
        """
        self.name = name
        self.signature = signature
        self.precondition = precondition
        self.compound_task = compound_task  #NOTE:here not sure if class called 'CompoundTask' is necessary *I think, maybe Task is sufficient
        self.ordered_subtasks = ordered_subtasks
    
    def __str__(self):
        return (
            "Methods(Name: {}\n\tSignature: {}\n\tPrecondition: {}\n\tDecomposed Task: {}\n\tOrdered Subtasks {})".format(
                self.name,
                ", ".join(["{} - {}".format(param[0], " ".join([str(ptype) for ptype in param[1]])) for param in self.signature]),
                str(self.precondition),
                str(self.compound_task),
                self.ordered_subtasks
            )
        )

class Task:
    def __init__(self, name, signature, task_type = 'abstract'):
        """
        name:      The name identifying the task
        signature: A list of tuples (name, [types]) to represent a list of
                   parameters and their type(s).
        task_type: Flag indicating if its primitive, abstract or none (for empty tasks only)
        """
        self.name = name
        self.signature = signature
        self.task_type = task_type
        
    def __str__(self):
        return (
            "Task(Name: {}, Signature: {})".format(
                self.name,
                ", ".join(["{} - {}".format(param[0], "/".join([str(ptype) for ptype in param[1]])) for param in self.signature])
            )
        )
    def __repr__(self) -> str:
        return f'TSK<{self.name}:{self.signature}>'
    
class Domain:
    def __init__(self, name, types, predicates, tasks, actions, methods, constants={}):
        """
        name: The name of the domain
        types: A dict of typename->Type instances in the domain
        predicates: A list of predicates in the domain
        methods: A list of methods in the domain
        actions: A list of actions in the domain
        constants: A dict of name->type pairs of the constants in the domain
        tasks: A list of tasks in the domain
        """
        self.name = name
        self.types = types
        self.predicates = predicates
        self.actions = actions
        self.methods = methods
        self.constants = constants
        self.tasks = tasks

    def __repr__(self):
        return (
            "< Domain definition: %s Predicates: %s Tasks: %s Actions: %s "
            "Constants: %s >"
            % (
                self.name,
                [str(p) for p in self.predicates],
                [str(t) for t in self.tasks],
                [str(a) for a in self.actions],
                [str(m) for m in self.methods],
                [str(c) for c in self.constants],
            )
        )

    __str__ = __repr__


class Problem:
    def __init__(self, name, domain, objects, init, htn, goal):
        """
        name: The name of the problem
        domain: The domain in which the problem has to be solved
        objects: A dict name->type of objects that are used in the problem
        init: A list of predicates describing the initial state
        goal: A list of predicates describing the goal state
        """
        self.name = name
        self.domain = domain
        self.objects = objects
        self.initial_state = init
        self.htn = htn
        self.goal = goal
        

    def __repr__(self):
        return (
            "< Problem definition: %s "
            "Domain: %s Objects: %s htn task: %s Initial State: %s Goal State : %s >"
            % (
                self.name,
                self.domain.name,
                sorted(self.objects),
                self.htn,
                [str(p) for p in self.initial_state],
                [str(p) for p in self.goal],
            )
        )

    __str__ = __repr__
