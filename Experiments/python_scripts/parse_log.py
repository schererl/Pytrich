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
        self.operator_landmarks = []
        self.abtask_landmarks = []
        self.method_landmarks = []
        self.fact_landmarks = []
        self.disj_landmarks = []
        self.nodes_per_second = []

        # Compile regex patterns
        self.domain_pattern = self._compile_pattern('domain_name')
        self.problem_pattern = self._compile_pattern('problem_name')
        self.experiment_name_pattern = self._compile_pattern('experiment_name')
        self.nodes_expanded_pattern = self._compile_pattern('nodes_expanded', r'(\d+)')
        self.search_time_pattern = self._compile_pattern('search_elapsed_time', r'([0-9.]+)')
        self.solution_size_pattern = self._compile_pattern('solution_size', r'([0-9.]+)')
        self.heuristic_name_pattern = self._compile_pattern('heuristic_name')
        self.heuristic_elapsed_pattern = self._compile_pattern('heuristic_elapsed_time', r'([0-9.]+)')
        self.total_landmarks_pattern = self._compile_pattern('total_landmarks', r'(\d+)')
        self.operator_landmarks_pattern = self._compile_pattern('operator_landmarks', r'(\d+)')
        self.abtask_landmarks_pattern = self._compile_pattern('abtask_landmarks', r'(\d+)')
        self.fact_landmarks_pattern = self._compile_pattern('fact_landmarks', r'(\d+)')
        self.disj_landmarks_pattern = self._compile_pattern('disj_landmarks', r'(\d+)')
        self.method_landmarks_pattern = self._compile_pattern('method_landmarks', r'(\d+)')
        self.nodes_per_second_pattern = self._compile_pattern('nodes_per_second', r'([0-9.]+)')
        

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
        self.disj_landmarks.append(tmp_variables['disj_landmarks'])
        self.method_landmarks.append(tmp_variables['method_landmarks'])
        self.fact_landmarks.append(tmp_variables['fact_landmarks'])
        self.operator_landmarks.append(tmp_variables['operator_landmarks'])
        self.abtask_landmarks.append(tmp_variables['abtask_landmarks'])
        self.solution_sizes.append(tmp_variables['solution_size'])
        self.expanded_nodes.append(tmp_variables['expanded_nodes'])
        self.search_elapsed_time.append(tmp_variables['search_elapsed_time'])
        self.nodes_per_second.append(tmp_variables['nodes_per_second'])

    def __call__(self):
        tmp_variables = {
            'domain_name': None, 'problem_name': None, 'experiment_name': None,
            'solution_size': None, 'expanded_nodes': None, 'search_elapsed_time': None, 
            'nodes_per_second':None,
            'heuristic_name': None, 'heuristic_elapsed_time': None,
            'total_landmarks': None, 'operator_landmarks': None, 'abtask_landmarks': None,
            'method_landmarks': None, 'fact_landmarks': None,
            'disj_landmarks': None,
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
        elif nodes_per_second_match := self.nodes_per_second_pattern.search(line):
            tmp_variables['nodes_per_second'] = float(nodes_per_second_match.group(1))
        elif total_landmarks_match := self.total_landmarks_pattern.search(line):
            tmp_variables['total_landmarks'] = int(total_landmarks_match.group(1))
        elif disj_landmarks_match := self.disj_landmarks_pattern.search(line):
            tmp_variables['disj_landmarks'] = int(disj_landmarks_match.group(1))
        elif abtask_landmarks_match := self.abtask_landmarks_pattern.search(line):
            tmp_variables['abtask_landmarks'] = int(abtask_landmarks_match.group(1))
        elif operator_landmarks_match := self.operator_landmarks_pattern.search(line):
            tmp_variables['operator_landmarks'] = int(operator_landmarks_match.group(1))
        elif fact_landmarks_match := self.fact_landmarks_pattern.search(line):
            tmp_variables['fact_landmarks'] = int(fact_landmarks_match.group(1))
        elif method_landmarks_match := self.method_landmarks_pattern.search(line):
            tmp_variables['method_landmarks'] = int(method_landmarks_match.group(1))
        elif nodes_expanded_match := self.nodes_expanded_pattern.search(line):
            tmp_variables['expanded_nodes'] = int(nodes_expanded_match.group(1))
        elif search_time_match := self.search_time_pattern.search(line):
            tmp_variables['search_elapsed_time'] = float(search_time_match.group(1))
        elif solution_size_match := self.solution_size_pattern.search(line):
            tmp_variables['solution_size'] = int(solution_size_match.group(1))
        elif "@" in line:  # Delimiter for a new data block
            self._append_parsed_data(tmp_variables)
            self._reset_tmp_variables(tmp_variables)


    def save_as_csv(self, out_file):
        headers = [
            "domain_name", "problem_name", "experiment_name", 
            "search_elapsed_time", "solution_size", 
            "expanded_nodes", "nodes_per_second",
            "heuristic_name", 
            "heuristic_elapsed_time", "total_landmarks", "disj_landmarks",
            "abtask_landmarks", "operator_landmarks", "method_landmarks", "fact_landmarks", 
        ]
        rows = zip(
            self.domains, self.problems, self.experiment_names,
            self.search_elapsed_time, self.solution_sizes, 
            self.expanded_nodes, self.nodes_per_second,
            self.heuristic_names, self.heuristics_elapsed_time,
            self.total_landmarks, self.disj_landmarks,
            self.abtask_landmarks, self.method_landmarks, self.fact_landmarks,
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
    input_parser.add_argument("-i","--input_file", required=True, help="Path to the input log file.")
    input_parser.add_argument("-o", "--output_file", help="Optional: Path to the output CSV file.")
    args = input_parser.parse_args()

    if not os.path.isfile(args.input_file):
        print(f"Error: The specified log file does not exist: {args.input_file}")
        return

    parser = ParseLog([args.input_file])
    parser()
    print("Parsing completed.")

    if args.output_file:
        output_dir = os.path.dirname(args.output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        parser.save_as_csv(args.output_file)
        print(f"Parsed data has been saved to: {args.output_file}")

if __name__ == "__main__":
    main()
