"""
This module contains data structures needed to represent a HDDL domain.
"""
class Type:
    def __init__(self, name, parent):
        self.name = name.lower()
        self.parent = parent

    def __repr__(self):
        pass

    def __str__(self):
        pass

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
        pass

    def __str__(self):
        pass

class Effect:
    def __init__(self):
        """
        addlist: Set of predicates that have to be true after the action
        dellist: Set of predicates that have to be false after the action
        """
        self.addlist = set()
        self.dellist = set()
    
    def __str__(self):
        pass

class Precondition:
    def __init__(self):
        """
        addlist: Set of predicates that have to be true for the precondition
        dellist: Set of predicates that have to be false for the precondition
        """
        self.poslist = set()
        self.neglist = set()
    def __str__(self):
        pass

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
        self.signature = signature
        self.name = name
        self.precondition = precondition
        self.effect = effect
    
    def __str__(self):
        pass


class Method:
    def __init__(self, name, signature, precondition, task_head, ordered_subtasks):
        """
        name: The name identifying the action
        signature: A list of tuples (name, [types]) to represent a list of
                   parameters an their type(s).
        precondition: A list of predicates that have to be true before the
                      action can be applied
        decomposed_task: Task which the method is decomposed into
        ordered_subtasks: contains the OrderedSubtasks instance
        """
        self.signature    = signature
        self.name         = name
        self.precondition = precondition
        self.task_head    = task_head 
        self.ordered_subtasks = ordered_subtasks
    def __str__(self):
        pass
    def __repr__(self) -> str:
        pass

class AbstractTask:
    def __init__(self, name, signature):
        '''
        name:      The name identifying the task
        signature: A list of tuples (name, [types]) to represent a list of
                   parameters and their type(s).
        '''
        self.name = name
        self.signature = signature
        
    def __str__(self):
        pass
    def __repr__(self) -> str:
        pass
    
class Domain:
    def __init__(self, name, types, predicates, tasks, actions, methods, constants={}):
        """
        name: The name of the domain
        types: A dict of typename->Type instances in the domain
        predicates: A list of predicates in the domain
        methods: A list of methods in the domain
        actions: A list of actions in the domain
        tasks: A list of tasks in the domain
        """
        self.name       = name
        self.types      = types
        self.predicates = predicates
        self.actions    = actions
        self.methods    = methods
        self.tasks      = tasks

    def __repr__(self):
        pass

    __str__ = __repr__


class Problem:
    def __init__(self, name, domain, objects, init, htn, goal):
        """
        name: The name of the problem
        domain: The domain in which the problem has to be solved
        objects: A dict KEY:object name, VALUE:type
        init: A list of predicates describing the initial state
        goal: A list of predicates describing the goal state
        """
        self.name       = name
        self.domain     = domain
        self.objects    = objects
        self.htn        = htn
        self.goal_state = goal
        self.initial_state = init
        
    def __repr__(self):
        pass

    __str__ = __repr__
