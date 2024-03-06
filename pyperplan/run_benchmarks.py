import os
import argparse
import logging
import os
import sys
import time

from pyperplan.parser.parser import Parser
from pyperplan.planner import search_plan
from pyperplan.grounder.full_grounding import FullGround
from pyperplan.grounder.TDG_grounding import TDGGround

FOLDER_LOCATION = 'benchmarks/' 
DOMAINS = [ 'Transport', 'Barman-BDI', 'Towers', 'Blocksworld-GTOHP', 'Depots', 'Barman', 'Satellite-GTOHP', 'Rover-GTOHP', 'Rover', 'Factories-simple','Robot',  'Lamps','Minecraft-Regular',  'ModifiedTransport', ]

from pyperplan.planner import (
    SEARCHES,
    HEURISTICS
)

def get_problems(domain_path):
    return [os.path.join(domain_path, f) for f in os.listdir(domain_path) if f.endswith('.hddl') and 'p' in f.lower()]

def get_callable_names(callables, omit_string):
        names = [c.__name__ for c in callables]
        names = [n.replace(omit_string, "").replace("_", " ") for n in names]
        return ", ".join(names)


def format_data(domain_name, problem_file, grounder_status, grounder_elapsed_time, results):
    common_columns = f'{domain_name}\t{os.path.basename(problem_file)}\t{grounder_status}\t{grounder_elapsed_time:.2f}s'
    states = '\t'.join(d['status'] for d in results.values())
    plan_length = '\t'.join(str(d['s_size']) for d in results.values())
    exp_nodes = '\t'.join(f"{d['nodes_expanded']}n" for d in results.values())
    elapsed_time = '\t'.join(f"{d['elapsed_time']:.2f}s" for d in results.values())
    init_h = '\t'.join(f"{d['h_init']}hi" for d in results.values())
    avg_h = '\t'.join(f"{d['h_avg']:.2f}ha" for d in results.values())
    return f"{common_columns}\t{states}\t{plan_length}\t{exp_nodes}\t{elapsed_time}\t{init_h}\t{avg_h}\n"

#TODO: fix here, need to create an empty dictionary
def format_data_blind_failed(domain_name, problem_file, grounder_status, grounder_elapsed_time, result, number_heuristics):
    common_columns = f'{domain_name}\t{os.path.basename(problem_file)}\t{grounder_status}\t{grounder_elapsed_time:.2f}s'
    states = '\t'.join(d['status'] for d in [result] + ['-']*number_heuristics)
    plan_length = '\t'.join(str(d['s_size']) for d in [result] + ['-']*number_heuristics)
    exp_nodes = '\t'.join(f"{d['nodes_expanded']}n" for d in [result] + ['-']*number_heuristics)
    elapsed_time = '\t'.join(f"{d['elapsed_time']:.2f}s" for d in [result] + ['-']*number_heuristics)
    init_h = '\t'.join(f"{d['h_init']}hi" for d in [result] + ['-']*number_heuristics)
    avg_h = '\t'.join(f"{d['h_avg']:.2f}ha" for d in [result] + ['-']*number_heuristics)
    return f"{common_columns}\t{states}\t{plan_length}\t{exp_nodes}\t{elapsed_time}\t{init_h}\t{avg_h}\n"



def format_data_grounder_error(domain_name, problem_file, grounder_status, grounder_elapsed_time, number_heuristics):
    common_columns = f'{domain_name}\t{os.path.basename(problem_file)}\t{grounder_status}\t{grounder_elapsed_time:.2f}s'
    noop = '\t'.join('-' for _ in range(number_heuristics))
    return f"{common_columns}\t{noop}\t{noop}\t{noop}\t{noop}\t{noop}\t{noop}\n" 

def create_header(heuristics):
    """
    Creates a header that describes the layout of the benchmark results file.
    """
    # Defining the categories to be displayed in the header
    categories = ['STATUS', 'PLAN LENGTH', 'EXP. NODES', 'TIME', 'INIT-H', 'AVG-H']
    number_spaces = '\t'.join(['' for h in heuristics]) + '\t'
    # First line of the header: Each category listed once, separated by tabs
    first_line = '\t\t\t\t' + ' '.join([c+number_spaces for c in categories])
    # Second line of the header: Heuristic names listed in sequence, correctly spaced with tabs for alignment
    second_line_heuristics = '\t'.join([h for _ in categories for h in heuristics])
    second_line = f"DOMAIN\tPROBLEM\tGROUNDER STATUS\tGROUNDER TIME\t{second_line_heuristics}"

    return f"{first_line}\n{second_line}\n"

def run_benchmarks():
    heuristics = ['Blind', 'TaskDecomposition', 'TaskCount']
    with open('run_bench_results.txt', 'a') as file:
        file.write(create_header(heuristics))
    print(create_header(heuristics))
    time.sleep(1)
    for domain_name in DOMAINS:
        domain_path = os.path.abspath(os.path.join(FOLDER_LOCATION, domain_name))
        domain_file = os.path.join(domain_path, 'domain.hddl')
        problems = get_problems(domain_path)
        for problem_file in problems[:]:
            done = True
            results = {}
            logging.info(f'Starting {domain_name}: {problem_file}')
            # run parser
            logging.info('Starting parser')
            parser = Parser(domain_file, problem_file)
            domain = parser.parse_domain()
            problem = parser.parse_problem(domain)
            logging.info('Parser finished')

            # run grounder
            logging.info('Starting grounder')
            ground_start_time = time.time()
            grounder_type = TDGGround
            grounder = grounder_type(
                problem
            )
            model = grounder.groundify()
            grounder_elapsed_time = time.time() - ground_start_time
            grounder_status = grounder.status
            if not grounder_status == 'SUCCESS':
                logging.info('Grounder failed')
                with open('run_bench_results.txt', 'a') as file:
                   file.write(format_data_grounder_error(domain_name, problem_file, grounder_status, grounder_elapsed_time, len(heuristics)))
                continue
            logging.info('Grounder ended')
            for heuristic in heuristics:
                logging.info(f'Starting search with {heuristic}')
                # search    
                data = SEARCHES['blind'](model, HEURISTICS[heuristic])
                results[heuristic] = data
                
                # if data['status'] != 'GOAL' and heuristic == 'Blind':
                #     done = False
                #     logging.info(f'Search with {heuristic} failed')
                #     #file.write(format_data_blind_failed(domain_name, problem_file, grounder_status, grounder_elapsed_time, data, len(heuristics)))
                #     break
                # logging.info(f'Goal reached with {heuristic}')
            if True: #done
                with open('run_bench_results.txt', 'a') as file:
                    file.write(format_data(domain_name, problem_file, grounder_status, grounder_elapsed_time, results))
                