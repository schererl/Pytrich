import time
from ..model import Model, Operator, Decomposition, AbstractTask
from .grounder import Grounder
import subprocess
import os


class pandaGrounder(Grounder):
    def __init__(self, grounded_domain_file, grounded_problem_file):
        super().__init__(None, have_lifted=False)

        self.grounded_domain_file = ""
        self.grounded_problem_file = ""
        self.operator      = {} #helper
        self.abstract_task = {} #helper
        self.decomposition = {} #helper

        self.run_panda_grounding(grounded_domain_file, grounded_problem_file)
        self.parse_grounded_domain()
        self.parse_grounded_problem()

    def run_panda_grounding(self, domain_file_path, problem_file_path):
        script_dir = os.path.dirname(__file__) 
        pandaPIparser_path = os.path.join(script_dir, "../../pandaOpt/pandaPIparser")
        pandaPIgrounder_path = os.path.join(script_dir, "../../pandaOpt/pandaPIgrounder")
        pandaPIengine_path = os.path.join(script_dir, "../../pandaOpt/pandaPIengine")

        domain_base = os.path.splitext(os.path.basename(domain_file_path))[0]
        problem_base = os.path.splitext(os.path.basename(problem_file_path))[0]

        print(f'reading\n\tdomain: {domain_file_path}\n\tproblem: {problem_file_path}')
        parsed_output = "temp.parsed"
        subprocess.run([pandaPIparser_path, domain_file_path, problem_file_path, parsed_output], check=True)
        if not os.path.exists(parsed_output):
            print("Parsing failed.")
            exit()
        else:
            print("Parsing ended")

        psas_output = f"{domain_base}-{problem_base}.psas"
        subprocess.run([pandaPIgrounder_path, "-q", parsed_output, psas_output], check=True)
        os.remove(parsed_output)
        if not os.path.exists(psas_output):
            print("Grounding failed.")
            exit()
        else:
            print("Grounder ended")


        # Run the planner engine and write its output to a log file
        panda_log = "panda.log"
        subprocess.run([pandaPIengine_path, "--writeInputToHDDL", psas_output], stdout=open(panda_log, "w"), check=True)
        os.remove(psas_output)

        grounded_domain_output = domain_file_path[:-5]+'-grounded.hddl'
        grounded_problem_output = problem_file_path[:-5]+'-grounded.hddl'
        # Rename the output files to the desired names
        os.rename(f"{psas_output}.d.hddl", grounded_domain_output)
        os.rename(f"{psas_output}.p.hddl", grounded_problem_output)
        print(f"Grounding completed: \n\tdomain:{grounded_domain_output}\n\tproblem:{grounded_problem_output}")
        self.grounded_domain_file = grounded_domain_output
        self.grounded_problem_file = grounded_problem_output

    def groundify(self):
        self.grounded_actions = [o for o in self.operator.values()]
        self.grounded_tasks   = [t for t in self.abstract_task.values()]
        self.grounded_methods = [d for d in self.decomposition.values()]
        return super().groundify()

    def parse_grounded_problem(self):
        tokens = self._scan_tokens(self.grounded_problem_file)
        initial_state_lst, goal_lst = [], []
        if type(tokens) is list and tokens.pop(0) == 'define':
            while tokens:
                group = tokens.pop(0)
                lead = group.pop(0)

                if lead == "problem":
                    self.problem_name = group
                elif lead == ":domain":
                    pass
                elif lead == ":objects":
                    pass
                elif lead == ":init":
                    self._parse_facts(group, initial_state_lst)
                elif lead == ":goal":
                    self._parse_facts(group, goal_lst)
                elif lead == ":htn":
                    self._parse_htn_tag(group)

        self.grounded_init  = set(initial_state_lst)
        self.grounded_goals = set(goal_lst)

    def _parse_htn_tag(self, params):
        initial_tn_helper = []
        while params:
            lead = params.pop(0)
            if lead == ":ordered-subtasks" or lead == ":ordered-tasks" or lead == ":tasks" or lead == ":subtasks":
                self._parse_subtasks(params.pop(0), initial_tn_helper)
            elif lead == ":parameters":
                params.pop(0)
            elif lead == ":ordering":
                raise NotImplementedError("Partial ordered not accepted, YET {}")
            elif lead == ":constraints":
                group = params.pop(0)
                if len(group) > 0:
                    raise NotImplementedError("Constraints on Problem Initiation is not supported")
            else:
                raise TypeError("Unknown keyword {}".format(lead))

        for t_str in initial_tn_helper:
            self.grounded_itn.append(self.abstract_task[t_str])

    def _parse_facts(self, params, facts_lst):
        while not params == []:
            param= params.pop(0)
            keyword = param
            if not type(keyword) == str:
                keyword = keyword[0]
            if keyword == 'and': 
                self._parse_facts(param[1:], facts_lst)
            elif type(keyword)==str:
                facts_lst.append('('+keyword+')')
            else:
                raise SyntaxError('command undentified {}'.format(keyword))

    def parse_grounded_domain(self):
        tokens = self._scan_tokens(self.grounded_domain_file)

        decomposition_dict = {}
        operator_dict = {}
        tasks_dict = {}
        fact_lst = []      

        c_task_helper, subt_helper = {}, {} #both are used fetching coumpound tasks and subtasks
        if type(tokens) is list and tokens.pop(0) == 'define':
            while tokens:
                group = tokens.pop(0)
                lead = group.pop(0)
                if lead == ":action":
                    operator = self._parse_action(group)
                    operator_dict[operator.name] = operator
                elif lead == ":method":
                    decomposition = self._parse_method(group, c_task_helper, subt_helper)
                    decomposition_dict[decomposition.name] = decomposition
                elif lead == ":task":
                    task = self._parse_task(group)
                    tasks_dict[task.name] = task
                elif lead == "domain":
                    self.domain_name = group[0]
                elif lead == ":predicates":
                    fact_lst = self._parse_predicates(group)
                else:
                    raise AttributeError("Unknown tag; {}".format(lead))

        # fetch compound tasks and subtasks
        for d in decomposition_dict.values():
            d.compound_task = tasks_dict[c_task_helper[d.name]]
            d.compound_task.decompositions.append(d)

            for t_str in subt_helper[d.name]:
                if t_str in tasks_dict:
                    d.task_network.append(tasks_dict[t_str])
                elif t_str in operator_dict:
                    d.task_network.append(operator_dict[t_str])
                else:
                    raise SyntaxError("Task (abstract or primitive) not instantiated {}".format(t_str))

        self.grounded_facts  = set(fact_lst)
        self.operator        = operator_dict
        self.decomposition   = decomposition_dict
        self.abstract_task   = tasks_dict

    def _parse_action(self, params):
        i = 0
        l = len(params)
        action_name= None
        pos_precons, neg_precons, add_eff, del_eff = set(), set(), set(), set()

        while i < l:
            if i == 0:
                action_name = params[i]
            elif params[i] == ":parameters":
                i += 1
                pass
            elif params[i] == ":precondition":
                self._parse_formula(params[i + 1], pos_precons, neg_precons)
                i += 1
            elif params[i] == ":effect":
                self._parse_formula(params[i + 1], add_eff, del_eff)
                i += 1
            else:
                raise TypeError("Unknown identifier {}".format(params[i]))
            i += 1
        return Operator(action_name, pos_precons, neg_precons, add_eff, del_eff)

    def _parse_method(self, params, c_tasks, subt):
        i = 0
        l = len(params)
        method_name = {}
        pos_precons, neg_precons = set(), set()
        while i < l:
            if i == 0:
                if type(params[i]) != str or params[i][0] == ":":
                    raise SyntaxError("Error with Method name. Must be a string not beginning with ':'."
                                      "\nPlease check your domain file.")
                method_name = params[i]
            elif params[i] == ":parameters":
                i += 1
                pass
            elif params[i] == ":precondition":
                pos_precons = set()
                neg_precons = set()
                self._parse_formula(params[i + 1], pos_precons, neg_precons)
                i += 1
            elif params[i] == ":constraints":
                i += 1
            elif params[i] == ":task":
                c_tasks[method_name] = params[i + 1][0] 
                i += 1
            elif params[i] == ":ordered-subtasks" or params[i] == ":ordered-tasks" or ":subtasks" or ":tasks":
                subt[method_name] = []
                self._parse_subtasks(params[i+1], subt[method_name])
                i += 1
            elif params[i] == ":ordering":
                raise NotImplementedError("Partial ordered not accepted, YET {}".format(params[i]))        
            else:
                raise SyntaxError("Unknown token {}".format(params[i]))
            i += 1
        return Decomposition(method_name, pos_precons, neg_precons, None, [])    

    def _parse_subtasks(self, params, subtasks):
        while not params == []:
            param= params.pop(0)
            keyword = param
            if not type(keyword) == str:
                keyword = keyword[0]

            if keyword == 'and':
                self._parse_subtasks(params, subtasks)
                params = []
            elif type(keyword)==str:
                subtasks.append(keyword)
            else:
                raise SyntaxError('command undentified {}'.format(keyword))
        return subtasks

    def _parse_formula(self, params, pos_param, neg_param, negated=False, t = ''):
        def __extract_effect_values(p, pos_param, neg_param, negated):
            if negated:
                neg_param.add('('+p+')')
            else:
                pos_param.add('('+p+')')

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
                raise SyntaxError('command undentified {}'.format(keyword))

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
        return AbstractTask(task_name)

    def _parse_predicates(self, params):
        predicate_lst = []
        for i in params:
            predicate_name = '('+i[0]+')'
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

# if __name__ == "__main__":
#     import os
#     #file_path = os.path.abspath("./domain-p01.psas.d.hddl")
#     domain_file_path = os.path.abspath("./domain-p20.psas.d.hddl")
#     problem_file_path = os.path.abspath("./domain-p20.psas.p.hddl")
#     print(problem_file_path)
#     print(domain_file_path)
#     groundedParser = pandaGroundedParser(domain_file_path, problem_file_path)
#     groundedParser.parse_grounded_domain()
#     groundedParser.parse_grounded_problem()
#     groundedParser.groundify()