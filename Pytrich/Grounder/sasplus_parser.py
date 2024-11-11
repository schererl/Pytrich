import re
import sys
from typing import List, Set, Dict, Union

from Pytrich.model import Fact

class SASPlusParser:
    def __init__(self, sas_content: str):
        self.sas_content = sas_content.replace('\r\n', '\n').replace('\r', '\n')
        self.facts: List[str] = []
        self.operators = []
        self.abstract_tasks = []
        self.tasks_by_id: Dict[int, Union[str, List]] = {}  # Mapping of task IDs to names or operator data
        self.decompositions = []
        self.initial_state: Set[str] = set()
        self.goals: Set[str] = set()
        self.initial_task_network = []

        self.count_facts   = 0
        self.count_actions = 0
        self.count_abstract_tasks = 0
        self.count_methods = 0
        

    def parse(self):
        self.parse_facts()
        self.parse_actions()
        self.parse_task_names()
        self.parse_initial_abstract_task()
        self.parse_methods()
        self.parse_initial_state()
        self.parse_goals()
        
    def parse_facts(self):
        state_features_section = re.search(r';; #state features\n(\d+)(.*?)\n\n', self.sas_content, re.DOTALL)
        if state_features_section:
            tmp_count_facts, features = state_features_section.groups()
            self.count_facts = int(tmp_count_facts)
            # Create a dictionary with fact details instead of Fact instances
            self.facts = [
                {'name': fact, 'local_id': f_id, 'global_id': f_id}
                for f_id, fact in enumerate(feature.strip() for feature in features.strip().split('\n') if feature.strip())
            ]
        else:
            print("State features section not found.")

    def _to_binary_representation(self, fact_ids: Set[int]) -> int:
        """Convert a set of fact IDs to a binary representation."""
        binary_representation = 0
        for fact_id in fact_ids:
            binary_representation |= (1 << fact_id)  # Set the bit at the position of each fact ID
        return binary_representation

    def _parse_effects_line(self, line: str) -> Set[int]:
        """
        Parses a line of effects, skipping the fact operation type.
        Example: '0 28 0 15 0 7 -1' -> {28, 15, 7}
        """
        tokens = line.split()
        fact_ids = set()
        
        num_pairs = len(tokens) // 2
        for i in range(num_pairs):
            fact_id = tokens[i * 2 + 1]
            if fact_id != '-1':
                fact_ids.add(int(fact_id))
        return fact_ids

    def parse_actions(self):
        
        # Parse actions (operators)
        actions_section = re.search(r';; Actions\n(\d+)(.*?)\n\n', self.sas_content, re.DOTALL)
        if actions_section:
            tmp_count_actions, actions = actions_section.groups()
            self.count_actions = int(tmp_count_actions)
            action_lines = [line.strip() for line in actions.strip().split('\n') if line.strip()]
            i = 0
            while i < len(action_lines):
                action_data = {
                    'global_id': self.count_facts+int(i/4), 
                    'local_id': int(i/4),  
                    'name': '', 
                    'cost': int(action_lines[i]),
                    'pos_precons': self._to_binary_representation({int(x) for x in action_lines[i + 1].split() if x != '-1'}),
                    'neg_precons': 0,
                    'add_effects': self._to_binary_representation(self._parse_effects_line(action_lines[i+2])),
                    'del_effects': self._to_binary_representation(self._parse_effects_line(action_lines[i+3])),
                }

                self.operators.append(action_data)
                i += 4
            if len(self.operators) != int(self.count_actions):
                raise ValueError(f"Parsing failed, expected {self.count_actions} actions but got {len(self.operators)}")
            
        else:
            print("Actions section not found.")

    def parse_task_names(self):
        # Parse tasks (primitive and abstract)
        tasks_section = re.search(r';; tasks \(primitive and abstract\)\n(\d+)(.*?)\n\n', self.sas_content, re.DOTALL)
        if tasks_section:
            tmp_count_tasks, tasks = tasks_section.groups()
            self.count_abstract_tasks = int(tmp_count_tasks)-self.count_actions
            task_lines = [line.strip() for line in tasks.strip().split('\n') if line.strip()]
            for task_id, line in enumerate(task_lines):
                match = re.match(r'(\d+)\s+(.*)', line)
                if match:
                    task_type_str, name = match.groups()
                    task_type = int(task_type_str)
                    if task_type == 0:
                        # Primitive tasks are considered as operators
                        name = name.strip()
                        if task_id < len(self.operators):
                            self.operators[task_id]["name"] = name
                            self.tasks_by_id[task_id] = self.operators[task_id]
                        else:
                            print(f"Warning: Task ID {task_id} exceeds the number of operators.")
                    elif task_type == 1:
                        # Abstract tasks are added separately
                        name = name.strip()
                        abstract_task_data = {
                            'global_id': self.count_facts +  task_id, 
                            'local_id': task_id-self.count_actions,  
                            'name': name, 
                            'decompositions': []
                        }
                        self.abstract_tasks.append(abstract_task_data)
                        self.tasks_by_id[task_id] = name
                else:
                    print(f"Invalid task line: {line}")
        else:
            print("Tasks section not found.")

    def parse_methods(self):
        # Parse methods (decompositions)
        methods_section = re.search(r';; methods\s*\n(\d+)\s*\n(.*)', self.sas_content, re.DOTALL)
        if methods_section:
            count_methods_str, methods_content = methods_section.groups()
            self.count_methods = int(count_methods_str)
            method_lines = [line.strip() for line in methods_content.strip().split('\n') if line.strip()]
            methods = []
            current_method = []
            for line in method_lines:
                if not re.match(r'^(-1|\d)', line):
                    # method name
                    if current_method:
                        methods.append(current_method)
                    current_method = [line]
                else:
                    current_method.append(line)
            if current_method:
                methods.append(current_method)
            if len(methods) != self.count_methods:
                raise ValueError(f"Parsing failed, expected {self.count_methods} methods but got {len(methods)}")

            # Parse each method
            for m_local_id, method in enumerate(methods):
                # Parse method name
                method_name = method[0]
                # Parse abstract task
                abstract_task_id = int(method[1])-self.count_actions
                abstract_task = self.abstract_tasks[abstract_task_id]
                # Parse subtasks
                subtasks_line = method[2]
                subtasks_ids = [int(x) for x in subtasks_line.split() if x != '-1']
                subtasks = []
                for subtask_id in subtasks_ids:
                    if subtask_id >= self.count_actions:
                        subtasks.append(('AT',subtask_id-self.count_actions))
                    else:
                        subtasks.append(('O',subtask_id))
                # Parse orderings
                orderings = []
                ordering_line = method[3]
                if re.match(r'^-?\d+(\s+-?\d+)*\s*-1$', ordering_line):
                    ordering_elements = [int(x) for x in ordering_line.split() if x != '-1']
                    for j in range(0, len(ordering_elements), 2):
                        orderings.append((ordering_elements[j], ordering_elements[j + 1]))
                
                decomposition = {
                    'name': method_name,
                    'compound_task': abstract_task,
                    'pos_precons': 0,
                    'neg_precons': 0,
                    'task_network': subtasks,
                    'global_id': self.count_facts+self.count_actions+self.count_abstract_tasks+m_local_id, #,
                    'local_id': m_local_id #,
                    #'orderings': orderings #NOTE: task orderings not available yet
                }

                #self.abstract_tasks[abstract_task['local_id']]['decompositions'].append(decomposition)
                self.decompositions.append(decomposition)
        else:
            print("Methods section not found.")

    def parse_initial_abstract_task(self):
        initial_task_network_section = re.search(r';; initial abstract task\s*\n(\d+)\s*(?=\n|$)', self.sas_content)
        if initial_task_network_section:
            compound_task_id = int(initial_task_network_section.group(1)) - self.count_actions
            task_name = self.abstract_tasks[compound_task_id]
            self.initial_task_network.append(task_name)
        else:
            print("Initial abstract task section not found.")

    def parse_initial_state(self):
        initial_state_section = re.search(r';; initial state\n(.*?)\n\n', self.sas_content, re.DOTALL)
        if initial_state_section:
            state_indices = [int(x) for x in initial_state_section.group(1).split() if x.strip() and x != '-1']
            self.initial_state = self._to_binary_representation(set(state_indices))
        else:
            print("Initial state section not found.")

    def parse_goals(self):
        goal_section = re.search(r';; goal\n(.*?)\n\n', self.sas_content, re.DOTALL)
        if goal_section:
            goal_indices = [int(x) for x in goal_section.group(1).split() if x.strip() and x != '-1']
            self.goals = self._to_binary_representation(set(goal_indices))
        else:
            print("Goal section not found.")

    def get_parsed_data(self):
        return {
            'facts': self.facts,
            'operators': self.operators,
            'tasks_by_id': self.tasks_by_id,
            'initial_task_network': self.initial_task_network,
            'decompositions': self.decompositions,
            'initial_state': self.initial_state,
            'goals': self.goals
        }

    def print_parsed_data(self):
        print(f"Facts ({len(self.facts)}):")
        print(self.facts)
        print(f"\nOperators ({len(self.operators)}):")
        for idx, op in enumerate(self.operators):
            print(f"Operator {idx}: {op}")
        print(f"\nTasks ({len(self.tasks_by_id)}):")
        for task_id, name in self.tasks_by_id.items():
            print(f"Task {task_id}: {name}")
        print(f"\nInitial Task Network:")
        print(self.initial_task_network)
        print(f"\nDecompositions ({len(self.decompositions)}):")
        for decomposition in self.decompositions:
            print(decomposition)
        print(f"\nInitial State:")
        print(self.initial_state)
        print(f"\nGoals:")
        print(self.goals)

if __name__ == "__main__":
    # Get the file path from command line arguments
    if len(sys.argv) != 2:
        print("Usage: python script.py <sas_problem_file_path>")
        sys.exit(1)

    sas_file_path = sys.argv[1]
    with open(sas_file_path, "r") as problem_file:
        sas_content = problem_file.read()

    # Create a parser instance and parse the content
    parser = SASPlusParser(sas_content)
    parser.parse()

    # Optionally, print the parsed data
    parser.print_parsed_data()
