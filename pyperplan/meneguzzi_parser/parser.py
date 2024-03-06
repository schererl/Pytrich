import time
class pandaGroundedParser:
    def __init__(self, grounded_file):
        self.grounded_file = grounded_file
        self.predicates = []

    def parse_grounded_problem(self):
        tokens = self._scan_tokens(self.grounded_file)
        leads_set = set()
        actions_set = set()
        if type(tokens) is list and tokens.pop(0) == 'define':
            while tokens:
                group = tokens.pop(0)
                lead = group.pop(0)
                leads_set.add(lead)

                if lead == ":action":
                    self._parse_action(group)
                elif lead == ":method":
                    continue #method = self._parse_method(group)
                elif lead == ":task":
                    task = self._parse_task(group)
                elif lead == "domain":
                    self.domain_name = group[0]
                elif lead == ":predicates":
                    self.predicates = self._parse_predicates(group)
                else:
                    raise AttributeError("Unknown tag; {}".format(lead))
        #self._post_domain_parsing_grounding()
        print(f'head keywords: {leads_set}')
        print(f'predicate list: {self.predicates}')

    def _parse_action(self, params):
        i = 0
        l = len(params)
        action_name, parameters, precon, precon_conditions, effects = None, None, None, None, None
        while i < l:
            if i == 0:
                action_name = params[i]
            elif params[i] == ":parameters":
                i += 1
                pass
            elif params[i] == ":precondition":
                pos_precons = set()
                neg_precons = set()
                self._parse_formula(params[i + 1], pos_precons, neg_precons)
                i += 1
            elif params[i] == ":effect":
                add_eff = set()
                del_eff = set()
                self._parse_formula(params[i + 1], add_eff, del_eff)
                i += 1
            else:
                raise TypeError("Unknown identifier {}".format(params[i]))
            i += 1
        
    def _parse_formula(self, params, pos_param, neg_param, negated=False, t = ''):
        def __extract_effect_values(params, pos_param, neg_param, negated):
            if negated:
                neg_param.add(params)
            else:
                pos_param.add(params)
        
        while not params == []:
            param= params.pop(0) #NOTE: maybe we are going to have a problem in case there is inner 'ands'
            keyword = param
            if not type(keyword) == str:
                keyword = keyword[0]
            
            if keyword == 'and':
                self._parse_formula(params, pos_param, neg_param, negated, '\t'+t)
                params = []
            elif keyword == "not":
                content = param[1:]
                self._parse_formula(content, pos_param, neg_param, not negated, '\t'+t)
            elif type(keyword)==str:
                __extract_effect_values(keyword, pos_param, neg_param, negated)
            else:
                print('\t{t}undentified')
            
    def _parse_task(self, params):
        i = 0
        l = len(params)
        task_name, parameters = None, []
        while i < l:
            if i == 0:
                task_name = params[i]
            elif params[i] == ":parameters":
                assert i + 1 < l
                i += 1
                pass
            else:
                raise TypeError
            i += 1
        print(task_name)
      
    def _parse_predicates(self, params):
        predicate_lst = []
        for i in params:
            predicate_name = i[0]
            predicate_lst.append(predicate_name)
        return predicate_lst
    
    def _scan_tokens(self, file_path):
        import re
        """ Taken with permission from:
        https://github.com/pucrs-automated-planning/heuristic-planning/blob/master/pddl/pddl_parser.py"""
        with open(file_path, 'r') as f:
            # Remove single line comments
            str = re.sub(r';.*$', '', f.read(), flags=re.MULTILINE)
        # Tokenize
        stack = []
        sections = []
        for t in re.findall(r'[()]|[^\s()]+', str):
            if t == '(':
                stack.append(sections)
                sections = []
            elif t == ')':
                if stack:
                    l = sections
                    sections = stack.pop()
                    sections.append(l)
                else:
                    raise Exception('Missing open parentheses')
            else:
                sections.append(t)
        if stack:
            raise Exception('Missing close parentheses')
        if len(sections) != 1:
            raise Exception('Malformed expression')
        return sections[0]
    
if __name__ == "__main__":
    import os
    file_path = os.path.abspath("./domain-p01.psas.d.hddl")
    print(file_path)
    groundedParser = pandaGroundedParser(file_path)
    groundedParser.parse_grounded_problem()