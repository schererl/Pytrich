import argparse
import json
import os
import re
import csv

class ParseLog:
    def __init__(self, log_files):
        self.log_files = log_files
        # Load descriptions from JSON file
        with open("../../descriptions.json", "r") as f:
            self.descriptions = json.load(f)
        
        # Initialize storage for parsed data
        self.domains = []
        self.problems = []
        self.experiment_names = []
        self.heuristic_names = []
        self.heuristics_elapsed_time = []
        self.solution_sizes = []
        self.expanded_nodes = []
        self.search_elapsed_time = []
        self.facts = []
        self.abstract_tasks = []
        self.operators = []
        self.decompositions = []
        self.total_landmarks = []
        self.task_landmarks = []
        self.method_landmarks = []
        self.fact_landmarks = []
        self.mincov_disj_landmarks = []
        self.mincov_disj_elapsed_time = []
        self.tor_elapsed_time = []

        # Compile regex patterns
        self.domain_pattern = self._compile_pattern('domain_name')
        self.problem_pattern = self._compile_pattern('problem_name')
        self.experiment_name_pattern = self._compile_pattern('experiment_name')
        self.nodes_expanded_pattern = self._compile_pattern('nodes_expanded', r'(\d+)')
        self.search_time_pattern = self._compile_pattern('search_elapsed_time', r'([0-9.]+)')
        self.solution_size_pattern = self._compile_pattern('solution_size', r'([0-9.]+)')
        self.heuristic_name_pattern = self._compile_pattern('heuristic_name')
        self.heuristic_elapsed_pattern = self._compile_pattern('heuristic_elapsed_time', r'([0-9.]+)')
        self.tor_elapsed_time_pattern = self._compile_pattern('tor_elapsed_time', r'([0-9.]+)')
        self.mincov_disj_landmarks_pattern = self._compile_pattern('mincov_disj_landmarks', r'(\d+)')
        self.mincov_disj_elapsed_time_pattern = self._compile_pattern('mincov_disj_elapsed_time', r'([0-9.]+)')
        self.total_landmarks_pattern = self._compile_pattern('total_landmarks', r'(\d+)')
        self.task_landmarks_pattern = self._compile_pattern('task_landmarks', r'(\d+)')
        self.fact_landmarks_pattern = self._compile_pattern('fact_landmarks', r'(\d+)')
        self.method_landmarks_pattern = self._compile_pattern('method_landmarks', r'(\d+)')
        self.model_fact_pattern = self._compile_pattern('fact_model', r'(\d+)')
        self.model_decomposition_pattern = self._compile_pattern('decomposition_model', r'(\d+)')
        self.model_operator_pattern = self._compile_pattern('operator_model', r'(\d+)')
        self.model_abstract_task_pattern = self._compile_pattern('abstract_task_model', r'(\d+)')

    def _compile_pattern(self, key, value_regex=r'(.+)'):
        if key not in self.descriptions:
            raise KeyError(f"The key '{key}' does not exist in the descriptions file.")
        description = self.descriptions[key].get('description', key)
        description = re.sub(r'\s+', r'\\s*', description)
        pattern = re.sub(r'\s*(\([^)]*\))?', '', description)
        return re.compile(rf'\s*{pattern}\s*:\s*{value_regex}\s*')

    def _reset_tmp_variables(self, tmp_variables):
        for key in tmp_variables:
            tmp_variables[key] = None

    def _append_parsed_data(self, tmp_variables):
        self.domains.append(tmp_variables['domain_name'])
        self.problems.append(tmp_variables['problem_name'])
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

    def __call__(self):
        tmp_variables = {
            'domain_name': None, 'problem_name': None, 'experiment_name': None,
            'solution_size': None, 'expanded_nodes': None, 'search_elapsed_time': None, 
            'heuristic_name': None, 'heuristic_elapsed_time': None,
            'total_landmarks': None, 'task_landmarks': None,
            'method_landmarks': None, 'fact_landmarks': None,
            'mincov_disj_landmarks': None, 'mincov_disj_elapsed_time': None,
            'fact_model': None, 'decomposition_model': None, 'abstract_task_model': None,
            'operator_model': None, 'tor_elapsed_time': None
        }
        for log_file_path in self.log_files:
            with open(log_file_path, 'r') as file:
                for line in file:
                    if line == '@': 
                        if len(tmp_variables["domain_name"])>0:
                            self._append_parsed_data(tmp_variables)
                            self._reset_tmp_variables(tmp_variables)
                        continue
                    self._parse_line(line, tmp_variables)
                
                    


    def _parse_line(self, line, tmp_variables):
        """Parse a single line using regex patterns and extract relevant data."""
        # Remove parentheses from lines:
        line = re.sub(r'\s*\([^)]*\)', '', line)
        if domain_match := self.domain_pattern.search(line):
            tmp_variables['domain_name'] = domain_match.group(1)
        elif problem_match := self.problem_pattern.search(line):
            tmp_variables['problem_name'] = problem_match.group(1)
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
            tmp_variables['mincov_disj_elapsed_time'] = float(disjunctions_elapsed_time_match.group(1))
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
        elif "@" in line:  # Delimiter for a new data block
            self._append_parsed_data(tmp_variables)
            self._reset_tmp_variables(tmp_variables)


    def save_as_csv(self, out_file):
        headers = [
            "domain_name", "problem_name", "experiment_name", 
            "search_elapsed_time", "solution_size", "expanded_nodes",
            "heuristic_name",
            "heuristic_elapsed_time", "total_landmarks", "task_landmarks",
            "method_landmarks", "fact_landmarks", "mincov_disj_landmarks",
            "mincov_disj_elapsed_time", 
            "facts", "decompositions", "operators",
            "abstract_tasks", "tor_elapsed_time"
        ]
        rows = zip(
            self.domains, self.problems, self.experiment_names,
            self.search_elapsed_time, self.solution_sizes, self.expanded_nodes, 
            self.heuristic_names, self.heuristics_elapsed_time,
            self.total_landmarks, self.task_landmarks, self.method_landmarks,
            self.fact_landmarks, self.mincov_disj_landmarks,
            self.mincov_disj_elapsed_time,
            self.facts,
            self.decompositions, self.operators, self.abstract_tasks,
            self.tor_elapsed_time
        )
        # Filter out rows where all elements are None or empty
        filtered_rows = [
            row for row in rows 
            if any(value is not None and value != "" for value in row)
        ]
        
        with open(out_file, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(filtered_rows)

def main():
    input_parser = argparse.ArgumentParser(description="Parse log files and optionally save the output to a CSV file.")
    input_parser.add_argument("--log_file", required=True, help="Path to the input log file.")
    input_parser.add_argument("--out_file", help="Optional: Path to the output CSV file.")
    args = input_parser.parse_args()

    if not os.path.isfile(args.log_file):
        print(f"Error: The specified log file does not exist: {args.log_file}")
        return

    parser = ParseLog([args.log_file])
    parser()
    print("Parsing completed.")

    if args.out_file:
        output_dir = os.path.dirname(args.out_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        parser.save_as_csv(args.out_file)
        print(f"Parsed data has been saved to: {args.out_file}")

if __name__ == "__main__":
    main()
