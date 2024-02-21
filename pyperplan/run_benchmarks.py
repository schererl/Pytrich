import os
from pyperplan.planner import search_plan
import argparse
import logging
import os
import sys

FOLDER_LOCATION = 'benchmarks/' 
DOMAINS = ['Blocksworld-GTOHP', 'Robot', 'Rover-GTOHP', 'Towers', 'Transport', 'Depots', 'Barman' ]

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
    operators_size = f"{data['o_size']}"
    SEPARATOR = '\t'
    
    #return f"{domain} {SEPARATOR} {problem} {SEPARATOR} {heuristic} {SEPARATOR} {status} {SEPARATOR} {solution_size} {SEPARATOR} {operators_size} {SEPARATOR} {queue_type} {SEPARATOR} {h_init} {SEPARATOR} {h_avg} {SEPARATOR} {nodes_expanded} {SEPARATOR} {elapsed_time} {SEPARATOR} {nodes_per_second} {SEPARATOR} {memory_usage} {SEPARATOR}"

def get_problems(domain_path):
    return [os.path.join(domain_path, f) for f in os.listdir(domain_path) if f.endswith('.hddl') and 'p' in f.lower()]

def get_callable_names(callables, omit_string):
        names = [c.__name__ for c in callables]
        names = [n.replace(omit_string, "").replace("_", " ") for n in names]
        return ", ".join(names)


def format_data(domain_name, problem_file, results):
    common_columns = f'{domain_name}\t{os.path.basename(problem_file)}'
    states = '\t'.join(d['status'] for d in results.values())
    plan_length = '\t'.join(str(d['s_size']) for d in results.values())
    exp_nodes = '\t'.join(f"{d['nodes_expanded']}n" for d in results.values())
    elapsed_time = '\t'.join(f"{d['elapsed_time']:.2f}s" for d in results.values())
    init_h = '\t'.join(f"{d['h_init']}hi" for d in results.values())
    avg_h = '\t'.join(f"{d['h_avg']:.2f}ha" for d in results.values())
    return f"{common_columns}\t{states}\t{plan_length}\t{exp_nodes}\t{elapsed_time}\t{init_h}\t{avg_h}\n"

def create_header(heuristics):
    """
    Creates a header that describes the layout of the benchmark results file.
    Correctly places tabs to align heuristic names under the categories.
    """
    
    # Defining the categories to be displayed in the header
    categories = ['STATUS', 'PLAN LENGTH', 'EXP. NODES', 'TIME', 'INIT-H', 'AVG-H']
    number_spaces = '\t'.join(['' for h in heuristics]) + '\t'
    # First line of the header: Each category listed once, separated by tabs
    first_line = '\t\t' + ' '.join([c+number_spaces for c in categories])

    # Second line of the header: Heuristic names listed in sequence, correctly spaced with tabs for alignment
    # Each heuristic name repeats for the number of categories, with a tab in between to align under each category
    #second_line_heuristics = '\t'.join([h for h in heuristics for _ in categories])
    second_line_heuristics = '\t'.join([h for _ in categories for h in heuristics])
    second_line = f"DOMAIN\tPROBLEM\t{second_line_heuristics}"

    return f"{first_line}\n{second_line}\n"





def run_benchmarks():
    import time
    heuristics = ['Blind', 'TaskDecomposition', 'FactCount', 'TaskCount']
    with open('run_bench_results.txt', 'a') as file:
        file.write(create_header(heuristics))
    print(create_header(heuristics))
    time.sleep(5)
    for domain_name in DOMAINS:
        domain_path = os.path.abspath(os.path.join(FOLDER_LOCATION, domain_name))
        domain_file = os.path.join(domain_path, 'domain.hddl')
        problems = get_problems(domain_path)
        for problem_file in problems[:]:
            done = True
            results = {}
            for heuristic in heuristics:
                #print(heuristic)
                data = search_plan(domain_file, problem_file, SEARCHES['blind'], HEURISTICS[heuristic])
                #result = format_data(domain_name, os.path.basename(problem_file), heuristic, data)
                results[heuristic] = data
                if data['status'] != 'GOAL' and heuristic == 'Blind':
                    done = False
                    break
            if done:
                with open('run_bench_results.txt', 'a') as file:
                    file.write(format_data(domain_name, problem_file, results))
                

