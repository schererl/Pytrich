import json
import re
class ParseLog:
    def __init__(self, log_files):
        self.log_files = log_files
        # Load descriptions from JSON file
        with open("../descriptions.json", "r") as f:
            self.descriptions = json.load(f)
        
        # Problem info
        self.domains = []
        self.problems = []
        self.experiment_names = []
        # Heuristic info
        self.heuristic_names = []
        self.heuristics_elapsed_time = []
        # Search info
        self.solution_sizes = []
        self.expanded_nodes = []
        self.search_elapsed_time = []
        # Model info
        self.facts = []
        self.abstract_tasks = []
        self.operators = []
        self.decompositions = []
        # Specific Landmark info
        self.total_landmarks = []
        self.task_landmarks = []
        self.method_landmarks = []
        self.fact_landmarks = []
        self.mincov_disj_landmarks = []
        self.mincov_disj_elapsed_time = []
        # Specific Total-Order Grounder info
        self.tor_elapsed_time = []

        ## REGEX PATTERNS ##

        # Problem patterns
        self.domain_pattern = self._compile_pattern('domain')
        self.problem_pattern = self._compile_pattern('problem')
        self.experiment_name_pattern = self._compile_pattern('experiment_name')
        # Search patterns
        self.nodes_expanded_pattern = self._compile_pattern('nodes_expanded', r'(\d+)')
        self.search_time_pattern = self._compile_pattern('search_elapsed_time', r'([0-9.]+)') 
        self.solution_size_pattern = self._compile_pattern('solution_size', r'([0-9.]+)')
        # Heuristic patterns
        self.heuristic_name_pattern = self._compile_pattern('heuristic_name')
        self.heuristic_elapsed_pattern = self._compile_pattern('heuristic_elapsed_time', r'([0-9.]+)')
        # Total-Order reachability patterns
        self.tor_elapsed_time_pattern = self._compile_pattern('tor_elapsed_time', r'([0-9.]+)') 
        # Landmark patterns
        self.mincov_disj_landmarks_pattern = self._compile_pattern('mincov_disj_landmarks', r'(\d+)')
        self.mincov_disj_elapsed_time_pattern = self._compile_pattern('mincov_disj_elapsed_time', r'([0-9.]+)')
        self.total_landmarks_pattern = self._compile_pattern('total_landmarks', r'(\d+)')
        self.task_landmarks_pattern = self._compile_pattern('task_landmarks', r'(\d+)')
        self.fact_landmarks_pattern = self._compile_pattern('fact_landmarks', r'(\d+)')
        self.method_landmarks_pattern = self._compile_pattern('method_landmarks', r'(\d+)')
        # Model patterns
        self.model_fact_pattern = self._compile_pattern('fact_model', r'(\d+)')
        self.model_decomposition_pattern = self._compile_pattern('decomposition_model', r'(\d+)')
        self.model_operator_pattern = self._compile_pattern('operator_model', r'(\d+)')
        self.model_abstract_task_pattern = self._compile_pattern('abstract_task_model', r'(\d+)')

    def _compile_pattern(self, key, value_regex=r'(.+)'):
        """Compile regex pattern based on the key from descriptions.json and a value regex."""
        description = self.descriptions.get(key, {}).get('description', key)
        description = re.sub(r'\s+', r'\\s*', description) # modify description patter to include \s* when some space is found
        pattern = re.sub(r'\s*(\([^)]*\))?', '', description)  # remove 0 or more parentheses parts
        return re.compile(rf'\s*{pattern}\s*:\s*{value_regex}\s*')

    def _reset_tmp_variables(self, tmp_variables):
        """Reset temporary variables for parsing a new block of data."""
        for key in tmp_variables:
            tmp_variables[key] = None

    def _append_parsed_data(self, tmp_variables):
        """Append parsed data from temporary variables to their corresponding lists."""
        self.domains.append(tmp_variables['domain'])
        self.problems.append(tmp_variables['problem'])
        self.experiment_names.append(tmp_variables['experiment_name'])
        self.heuristic_names.append(tmp_variables['heuristic_name'])
        self.heuristics_elapsed_time.append(tmp_variables['heuristic_elapsed_time'])
        self.total_landmarks.append(tmp_variables['total_landmarks'])
        self.task_landmarks.append(tmp_variables['task_landmarks'])
        self.method_landmarks.append(tmp_variables['method_landmarks'])
        self.fact_landmarks.append(tmp_variables['fact_landmarks'])
        self.mincov_disj_landmarks.append(tmp_variables['mincov_disj_landmarks'])
        self.mincov_disj_elapsed_time.append(tmp_variables['mincov_disj_elapsed_time'])
        self.solution_sizes.append(tmp_variables['solution_size'])
        self.expanded_nodes.append(tmp_variables['expanded_nodes'])
        self.search_elapsed_time.append(tmp_variables['search_elapsed_time'])
        self.facts.append(tmp_variables["fact_model"])
        self.decompositions.append(tmp_variables["decomposition_model"])
        self.operators.append(tmp_variables["operator_model"])
        self.abstract_tasks.append(tmp_variables["abstract_task_model"])
        self.tor_elapsed_time.append(tmp_variables["tor_elapsed_time"])

    def _parse_line(self, line, tmp_variables):
        """Parse a single line using regex patterns and extract relevant data."""
        # remove parentheses from lines:
        line = re.sub(r'\s*\([^)]*\)', '', line)
        
        if domain_match := self.domain_pattern.search(line):
            tmp_variables['domain'] = domain_match.group(1)
        elif problem_match := self.problem_pattern.search(line):
            tmp_variables['problem'] = problem_match.group(1)
        elif experiment_name_match := self.experiment_name_pattern.search(line):
            tmp_variables['experiment_name'] = experiment_name_match.group(1)
        elif heuristic_name_match := self.heuristic_name_pattern.search(line):
            tmp_variables['heuristic_name'] = heuristic_name_match.group(1)
        elif heuristic_elapsed_match := self.heuristic_elapsed_pattern.search(line):
            tmp_variables['heuristic_elapsed_time'] = float(heuristic_elapsed_match.group(1))  # Use float here
        elif total_landmarks_match := self.total_landmarks_pattern.search(line):
            tmp_variables['total_landmarks'] = int(total_landmarks_match.group(1))
        elif task_landmarks_match := self.task_landmarks_pattern.search(line):
            tmp_variables['task_landmarks'] = int(task_landmarks_match.group(1))
        elif fact_landmarks_match := self.fact_landmarks_pattern.search(line):
            tmp_variables['fact_landmarks'] = int(fact_landmarks_match.group(1))
        elif method_landmarks_match := self.method_landmarks_pattern.search(line):
            tmp_variables['method_landmarks'] = int(method_landmarks_match.group(1))
        elif nodes_expanded_match := self.nodes_expanded_pattern.search(line):
            tmp_variables['expanded_nodes'] = int(nodes_expanded_match.group(1))
        elif search_time_match := self.search_time_pattern.search(line):
            tmp_variables['search_elapsed_time'] = float(search_time_match.group(1))
        elif tor_elapsed_time_match := self.tor_elapsed_time_pattern.search(line):
            tmp_variables['tor_elapsed_time'] = float(tor_elapsed_time_match.group(1))
        elif mincov_disjs_landmarks_match := self.mincov_disj_landmarks_pattern.search(line):
            tmp_variables['mincov_disj_landmarks'] = int(mincov_disjs_landmarks_match.group(1))
        elif disjunctions_elapsed_time_match := self.mincov_disj_elapsed_time_pattern.search(line):
            tmp_variables['disjunctions_elapsed_time'] = float(disjunctions_elapsed_time_match.group(1))
        elif solution_size_match := self.solution_size_pattern.search(line):
            tmp_variables['solution_size'] = int(solution_size_match.group(1))
        elif model_abstract_task_match := self.model_abstract_task_pattern.search(line):
            tmp_variables['abstract_task_model'] = int(model_abstract_task_match.group(1))
        elif model_fact_match := self.model_fact_pattern.search(line):
            tmp_variables['fact_model'] = int(model_fact_match.group(1))
        elif model_decomposition_match := self.model_decomposition_pattern.search(line):
            tmp_variables['decomposition_model'] = int(model_decomposition_match.group(1))
        elif model_operator_match := self.model_operator_pattern.search(line):
            tmp_variables['operator_model'] = int(model_operator_match.group(1))
        elif "@" in line:
            self._append_parsed_data(tmp_variables)
            self._reset_tmp_variables(tmp_variables)

    def __call__(self):
        """Parse all log files provided during initialization."""
        tmp_variables = {
            'domain': None,
            'problem': None,
            'experiment_name': None,
            'heuristic_name': None,
            'heuristic_elapsed_time': None,
            'total_landmarks': None,
            'task_landmarks': None,
            'method_landmarks': None,
            'fact_landmarks': None,
            'mincov_disj_landmarks': None,
            'mincov_disj_elapsed_time': None,
            'solution_size': None,
            'expanded_nodes': None,
            'search_elapsed_time': None,
            'fact_model': None,
            'decomposition_model': None,
            'abstract_task_model': None,
            'operator_model': None,
            'tor_elapsed_time': None
        }
        for log_file_path in self.log_files:
            print(f'open file: {log_file_path}')
            self._reset_tmp_variables(tmp_variables)
            with open(log_file_path, 'r') as file:
                for line in file:
                    self._parse_line(line, tmp_variables)
                
            if tmp_variables["domain"] != None:
                self._append_parsed_data(tmp_variables)
                self._reset_tmp_variables(tmp_variables)


if __name__ == "__main__":
    pl =ParseLog(['log-files/test.log', 'log-files/test.log'])
    pl()
    print(pl.domains)
    print(pl.problems)
    print(pl.search_elapsed_time)
    print(pl.expanded_nodes)