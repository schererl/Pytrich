import os
from pyperplan.planner import search_plan
import argparse
import logging
import os
import sys

FOLDER_LOCATION = 'benchmarks/' 
DOMAINS = ['Robot', 'Rover-GTOHP', 'Towers', 'Transport','Blocksworld-GTOHP', 'Depots','Barman' ]
from pyperplan.planner import (
    SEARCHES,
    HEURISTICS
)

def format_data(domain, problem, heuristic, data):
    '''
    Formats the data into a string like:
    'Blocksworld; p15; Blind; TIMEOUT; HEAP; -1; 5034949n; 60.67s, 82995.84 n/s; 23.7%'
    '''
    status = data['status']
    queue_type = "HEAP"
    h_init =f"{data['h_init']} hi"
    h_avg = F"{data['h_avg']:.2f} ha"
    nodes_expanded = f"{data['nodes_expanded']}n"
    elapsed_time = f"{data['elapsed_time']:.2f}s"
    nodes_per_second = f"{data['nodes_per_second']:.2f} n/s"
    memory_usage = f"{data['memory_usage']:.1f}%"
    solution_size = f"{data['s_size']}"
    
    return f"{domain}; {problem}; {heuristic}; {status}; {solution_size}; {queue_type}; {h_init}; {h_avg}; {nodes_expanded}; {elapsed_time}; {nodes_per_second}; {memory_usage};"

def get_problems(domain_path):
    return [os.path.join(domain_path, f) for f in os.listdir(domain_path) if f.endswith('.hddl') and 'p' in f.lower()]

def get_callable_names(callables, omit_string):
        names = [c.__name__ for c in callables]
        names = [n.replace(omit_string, "").replace("_", " ") for n in names]
        return ", ".join(names)

def run_benchmarks():
    
    print("Current working directory:", os.getcwd())
    
    for domain_name in DOMAINS:
        domain_path = os.path.abspath(os.path.join(FOLDER_LOCATION, domain_name))
        domain_file = os.path.join(domain_path, 'domain.hddl')
        
        problems = get_problems(domain_path)
        #print(problems)
        for problem_file in problems[:5]:
            for heuristic in ['Blind', 'TaskDecomposition']:
                #print(heuristic)
                data = search_plan(domain_file, problem_file, SEARCHES['blind'], HEURISTICS[heuristic])
                result = format_data(domain_name, os.path.basename(problem_file), heuristic, data)
                with open('benchmark_results.txt', 'a') as file:
                    file.write(result+'\n')
                
                #if data['status'] != 'GOAL': #and heuristic == 'Blind':
                #   break
