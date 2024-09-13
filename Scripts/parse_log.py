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
        self.heuristic_elapsed_times = []
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
        self.min_cov_disjunctions = []
        self.disjunctions_elapsed_time = []
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
        self.min_cov_disjunctions_pattern = self._compile_pattern('min_cov_disjunctions', r'(\d+)')
        self.disjunctions_elapsed_time_pattern = self._compile_pattern('elapsed_time_disjunctions', r'([0-9.]+)')
        self.total_landmarks_pattern = self._compile_pattern('total_landmarks', r'(\d+)')
        self.task_landmarks_pattern = self._compile_pattern('task_landmarks', r'(\d+)')
        self.fact_landmarks_pattern = self._compile_pattern('fact_landmarks', r'(\d+)')
        self.method_landmarks_pattern = self._compile_pattern('method_landmarks', r'(\d+)')
        # Model patterns
        self.model_facts_pattern = self._compile_pattern('model_facts', r'(\d+)')
        self.model_decompositions_pattern = self._compile_pattern('model_decompositions', r'(\d+)')
        self.model_operators_pattern = self._compile_pattern('model_operators', r'(\d+)')
        self.model_abstract_tasks_pattern = self._compile_pattern('model_abstract_tasks', r'(\d+)')

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
        self.heuristic_names.append(tmp_variables['heuristic_name'])
        self.domains.append(tmp_variables['domain'])
        self.problems.append(tmp_variables['problem'])
        self.total_landmarks.append(tmp_variables['total_landmarks'])
        self.task_landmarks.append(tmp_variables['task_landmarks'])
        self.method_landmarks.append(tmp_variables['method_landmarks'])
        self.fact_landmarks.append(tmp_variables['fact_landmarks'])
        self.min_cov_disjunctions.append(tmp_variables['min_cov_disjunction'])
        self.heuristic_elapsed_times.append(tmp_variables['total_elapsed_time'])
        self.disjunctions_elapsed_time.append(tmp_variables['disjunctions_elapsed_time'])
        self.solution_sizes.append(tmp_variables['solution_size'])
        self.expanded_nodes.append(tmp_variables['expanded_nodes'])
        self.search_elapsed_time.append(tmp_variables['search_elapsed_time'])

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
        elif min_cov_disjunctions_match := self.min_cov_disjunctions_pattern.search(line):
            tmp_variables['min_cov_disjunctions'] = int(min_cov_disjunctions_match.group(1))
        elif disjunctions_elapsed_time_match := self.disjunctions_elapsed_time_pattern.search(line):
            tmp_variables['disjunctions_elapsed_time'] = float(disjunctions_elapsed_time_match.group(1))
        elif solution_size_match := self.solution_size_pattern.search(line):
            tmp_variables['solution_size'] = int(solution_size_match.group(1))
        elif "@" in line and tmp_variables['current_experiment']:
            self._append_parsed_data(tmp_variables)
            print(tmp_variables)
            self._reset_tmp_variables(tmp_variables)


    def __call__(self):
        """Parse all log files provided during initialization."""
        tmp_variables = {
            'heuristic_name': None,
            'domain': None,
            'problem': None,
            'experiment_name': None,
            'total_landmarks': None,
            'task_landmarks': None,
            'method_landmarks': None,
            'fact_landmarks': None,
            'min_cov_disjunction': None,
            'disjunctions_elapsed_time': None,
            'solution_size': None,
            'expanded_nodes': None,
            'search_elapsed_time': None
        }
        for log_file_path in self.log_files:
            self._reset_tmp_variables(tmp_variables)
            with open(log_file_path, 'r') as file:
                for line in file:
                    self._parse_line(line, tmp_variables)
                print(tmp_variables)


if __name__ == "__main__":
    pl =ParseLog(['log-files/last-log.log', 'log-files/last-log.log'])
    pl()
    print(pl.domains)