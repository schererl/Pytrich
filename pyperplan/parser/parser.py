import hddl
from typing import List
import re


class Parser:
    """Simplafy-based parser class for HDDL. Incomplete
    Wenbo to finalize this.
    """

    def parse_domain(self, domain_filename) -> hddl.Domain:
        tokens = self.scan_tokens(domain_filename)
        if type(tokens) is list and tokens.pop(0) == 'define':
            domain_name = None
            types = {}
            objects = {}
            actions = []
            tasks = []
            methods = []
            predicates = {}
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
            return hddl.Domain(domain_name, types, predicates, tasks, actions, methods, constants=objects)
        else:
            raise Exception('File ' + domain_filename + ' does not match domain pattern')

    def parse_problem(self, problem_filename, lifted_domain) -> hddl.Problem:
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
            return hddl.Problem(problem_name, lifted_domain, objects, initial_state, htn, goals)
        else:
            raise Exception('File ' + problem_filename + ' does not match problem pattern')

    def parse_types(self) -> List[hddl.Type]:
        pass

    def parse_action(self) -> List[hddl.Action]:
        pass

    def parse_methods(self) -> List[hddl.Method]:
        pass

    def parse_tasks(self) -> List[hddl.AbstractTask]:
        pass

    def parse_precondition(self) -> hddl.Precondition:
        pass

    def parse_effect(self) -> hddl.Effect:
        pass

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