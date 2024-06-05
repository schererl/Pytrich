"""
This module contains data structures needed to represent a HDDL domain.
"""
class Type:
    def __init__(self, name, parent):
        self.name = name.lower()
        self.parent = parent

    def __repr__(self):
        if self.parent:
            return f'Type(name: {self.name}, parent: {self.parent})'
        else:
            return self.name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if not isinstance(other, Type):
            return False
        return self.name == other.name and self.parent == other.parent
    
    def __hash__(self):
        return hash((self.name, self.parent))

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
        return f'{self.name}({self.signature})'

    def __str__(self):
        return f'{self.name}({self.signature})'
    
    def __eq__(self, other):
        if self.name != other.name:
            # check for different names
            return False
        elif len(self.signature) != len(other.signature):
            # check for different number of parameters
            return False
        size_variables = len(self.signature)
        # check for type mismatch
        for i in range(size_variables):
            if not self.signature[i][1] == other.signature[i][1]:
                return False
        return True

    def __hash__(self):
        return hash((self.name, tuple((param, tuple(types) if isinstance(types, list) else (types,)) for param, types in self.signature)))

class Effect:
    def __init__(self, addlist, dellist):
        """
        addlist: Set of predicates that have to be true after the action
        dellist: Set of predicates that have to be false after the action
        """
        self.addlist = addlist
        self.dellist = dellist
    
    def __str__(self):
        add_str = ''
        del_str = ''
        for p in self.addlist:
            add_str += '+' + str(p) + ' '
        for p in self.dellist:
            del_str += '-' + str(p) + ' '
        return add_str + del_str

    def __hash__(self):
        return hash((tuple(self.addlist), tuple(self.dellist)))

    def __eq__(self, other):
        if not isinstance(other, Effect):
            return False
        return self.addlist == other.addlist and self.dellist == other.dellist


class Precondition:
    def __init__(self, poslist, neglist):
        """
        poslist: Set of predicates that have to be true for the precondition
        neglist: Set of predicates that have to be false for the precondition
        """
        self.poslist = poslist
        self.neglist = neglist
    
    def __str__(self):
        pos_str = ''
        neg_str = ''
        for p in self.poslist:
            pos_str += '+' + str(p) + ' '
        for p in self.neglist:
            neg_str += '-' + str(p) + ' '
        return pos_str + neg_str

    def __hash__(self):
        return hash((tuple(self.poslist), tuple(self.neglist)))
    
    def __eq__(self, other):
        if not isinstance(other, Precondition):
            return False
        return self.poslist == other.poslist and self.neglist == other.neglist


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
        return f'Action({self.name} {str([f"{tp[0]}-{tp[1].name}" for tp in self.signature])})'

    def __hash__(self):
        return hash((self.name, tuple(self.signature), self.precondition, self.effect))

    def __eq__(self, other):
        if not isinstance(other, Action):
            return False
        return (self.name == other.name and
                self.signature == other.signature and
                self.precondition == other.precondition and
                self.effect == other.effect)

class Method:
    def __init__(self, name, signature, precondition, task_head, ordered_subtasks):
        """
        name: The name identifying the action
        signature: A list of tuples (name, [types]) to represent a list of
                   parameters an their type(s).
        precondition: A list of predicates that have to be true before the
                      action can be applied
        decomposed_task: Task which the method is decomposed into
        ordered_subtasks: contains a list of tasks (abstract or operators)
        """
        self.signature    = signature
        self.name         = name
        self.precondition = precondition
        self.task_head    = task_head 
        self.ordered_subtasks = ordered_subtasks
    
    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not isinstance(other, Method):
            return False
        
        if not len(self.ordered_subtasks) == len(other.ordered_subtasks):
            return False
        
        for i in range(len(self.ordered_subtasks)):
            if self.ordered_subtasks[i] != other.ordered_subtasks[i]:
                return False
        
        return (self.name == other.name and
                self.signature == other.signature and
                self.precondition == other.precondition and
                self.task_head == other.task_head
                )

    def __hash__(self):
        return hash((self.name, tuple(self.signature), self.precondition, self.task_head, tuple(self.ordered_subtasks)))

class AbstractTask:
    def __init__(self, name, signature):
        '''
        name:      The name identifying the task
        signature: A list of tuples (name, [types]) to represent a list of
                   parameters and their type(s).
        '''
        self.name = name
        self.signature = signature
        
    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not isinstance(other, AbstractTask):
            return False
        return self.name == other.name and self.signature == other.signature

    def __hash__(self):
        return hash((self.name, tuple(self.signature)))
    
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
