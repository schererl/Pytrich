from .hddl import Domain, Problem, Precondition, Predicate, AbstractTask, Action, Method, Effect, Type
from typing import List
import re

class IllegalParameterTypeException(Exception):
    pass

class Parser:
    def parse_domain(self, domain_filename) -> Domain:
        tokens = self.scan_tokens(domain_filename)
        if type(tokens) is list and tokens.pop(0) == 'define':
            domain_name = None
            self.types = {}
            self.predicates = {}
            self.objects = {}
            self.actions = {}
            self.abstract_tasks = {}
            self.methods = {}
            
            while tokens:
                group = tokens.pop(0)
                t = group.pop(0)
                if t == 'domain':
                    pass
                elif t == ':requirements':
                    pass    
                elif t == ':constants':
                    pass
                elif t == ':predicates':
                    pass
                elif t == ':types':
                    pass
                elif t == ':action':
                    pass
                elif t == ':methods':
                    pass
                elif t == ':tasks':
                    pass
                else: 
                    pass
            return Domain(domain_name, self.types, self.predicates, self.abstract_tasks, self.actions, self.methods, constants=self.objects)
        else:
            raise Exception('File ' + domain_filename + ' does not match domain pattern')
    
    def parse_problem(self, problem_filename, lifted_domain) -> Problem:
        tokens = self.scan_tokens(problem_filename)
        if type(tokens) is list and tokens.pop(0) == 'define':
            problem_name = None
            objects = {}
            htn = []
            goals = set()
            initial_state = set()
            while tokens:
                group = tokens.pop(0)
                t = group.pop(0)
                if t == 'problem':
                    pass
                elif t == ':domain':
                    pass
                elif t == ':requirements':
                    pass 
                elif t == ':objects':
                    pass
                elif t == ':htn':
                    pass
                elif t == ':goal':
                    pass
                else: 
                    pass
            return Problem(problem_name, lifted_domain, objects, initial_state, htn, goals)
        else:
            raise Exception('File ' + problem_filename + ' does not match problem pattern')


    def parse_predicates(self, predicates_group)->dict[str, Predicate]:
        return {}
    
    def parse_types(self, types_group)-> dict[str, Type]:
        return {}
    
    def parse_action(self, action_group)->Action:
        # TODO: Need to use validate_signature comparing domain predicates with action predicates
        # TODO: Need to use parse precondition  and parse effects
        pass
    
    def parse_method(self, method_group)->Method:
        # TODO: Need to use validate_signature comparing domain actions with method primitive subtasks
        # TODO: Need to use validate_signature comparing domain abstract tasks with method abstract subtasks
        # TODO: Need to use parse precondition
        pass
    
    def parse_abstract_task(self, abstract_task_group)->AbstractTask:
        # TODO: Need to use validate_signature comparing domain predicates with abstract task predicates
        return None

    def parse_precondition(self, precondition_group)->Precondition:
        return None
    
    def parse_effect(self, effect_group)->Effect:
        return None

    '''
        Here we need to check if the action or method parameters respects domain signatures
        Example:
            domain_signature: :predicates
            modifier_signature: action

        Example
            domain_signature: :tasks
            modifier_signature: method :task
    
        Example
            domain_signature: :tasks/operators
            modifier_signature: method :ordered-subtasks
    '''
    def validate_signature(self, domain_signature, modifier_signature):
        # TODO: Implement validation logic and raise IllegalParameterTypeException
        if False:
            raise IllegalParameterTypeException("Domain signature differs from modifier signature")
        return True
        

    # * from https://github.com/pucrs-automated-planning/pddl-parser/blob/master/pddl_parser/PDDL.py
    def scan_tokens(self, filename):
        with open(filename) as f:
            # Remove single line comments
            str = re.sub(r';.*', '', f.read(), flags=re.MULTILINE).lower()
        # Tokenize
        stack = []
        list = []
        for t in re.findall(r'[()]|[^\s()]+', str):
            if t == '(':
                stack.append(list)
                list = []
            elif t == ')':
                if stack:
                    li = list
                    list = stack.pop()
                    list.append(li)
                else:
                    raise Exception('Missing open parentheses')
            else:
                list.append(t)
        if stack:
            raise Exception('Missing close parentheses')
        if len(list) != 1:
            raise Exception('Malformed expression')
        return list[0]