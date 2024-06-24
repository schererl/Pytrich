import logging
import os
import sys
import time

from pyperplan.planner import (
    SEARCHES,
    HEURISTICS,
    GROUNDERS
)

def format_data(dname, pfile, grounder_status, grounder_elapsed_time, results):
    common_columns = f'{dname}\t{os.path.basename(pfile)}\t{grounder_status}\t{grounder_elapsed_time:.2f}s'
    states = '\t'.join(d['status'] for d in results.values())
    plan_length = '\t'.join(str(d['s_size']) for d in results.values())
    exp_nodes = '\t'.join(f"{d['nodes_expanded']}" for d in results.values())
    elapsed_time = '\t'.join(f"{d['elapsed_time']:.2f}s" for d in results.values())
    init_h = '\t'.join(f"{d['h_init']}hi" for d in results.values())
    avg_h = '\t'.join(f"{d['h_avg']:.2f}ha" for d in results.values())
    return f"{common_columns}\t{states}\t{plan_length}\t{exp_nodes}\t{elapsed_time}\t{init_h}\t{avg_h}\n"

def format_data_grounder_error(dname, pfile, grounder_status, grounder_elapsed_time, number_heuristics):
    common_columns = f'{dname}\t{os.path.basename(pfile)}\t{grounder_status}\t{grounder_elapsed_time:.2f}s'
    noop = '\t'.join('-' for _ in range(number_heuristics))
    return f"{common_columns}\t{noop}\t{noop}\t{noop}\t{noop}\t{noop}\t{noop}\n"

def create_header(heuristics):
    """
    Creates a header that describes the layout of the benchmark results file.
    """
    categories = ['STATUS', 'PLAN LENGTH', 'EXP. NODES', 'TIME', 'INIT-H', 'AVG-H']
    number_spaces = '\t'.join(['' for h in heuristics]) + '\t'
    first_line = '\t\t\t\t' + ' '.join([c+number_spaces for c in categories])
    second_line_heuristics = '\t'.join([h for _ in categories for h in heuristics])
    second_line = f"DOMAIN\tPROBLEM\tGROUNDER STATUS\tGROUNDER TIME\t{second_line_heuristics}"

    return f"{first_line}\n{second_line}\n"

HEURISTICS_STR = ['TDGLM']
def run_experiment(dfile, pfile, dname, results_file):
    logging.info('Starting grounder')
    ground_start_time = time.time()
    grounder = GROUNDERS['panda'](dfile, pfile)
    model = grounder.groundify()
    grounder_elapsed_time = time.time() - ground_start_time
    
    if grounder.grounder_status != 'SUCCESS' or grounder_elapsed_time > 100:
        logging.info('Grounder failed')
        with open(results_file, 'a', encoding='utf-8') as file:
            file.write(format_data_grounder_error(dname, pfile, grounder.grounder_status, grounder_elapsed_time, len(HEURISTICS)))
            return
    logging.info('Grounder ended')

    results = {}
    for heuristic_str in HEURISTICS_STR:
        logging.info('Starting search with %s', heuristic_str)
        search_start_time = time.time()
        data = SEARCHES["Astar"](model, HEURISTICS[heuristic_str])
        elapsed_time = time.time() - search_start_time
        if elapsed_time > 300:
            logging.info('Experiment failed: search with %s aborted due to timeout', heuristic_str)
            return
        results[heuristic_str] = data
        logging.info('Search ended')
        
    with open(results_file, 'a', encoding='utf-8') as file:
        file.write(format_data(dname, pfile, grounder.grounder_status, grounder_elapsed_time, results))

EXPERIMENT_FOLDER=os.path.abspath('Experiments/Outputs/Search') + '/'
RESULTS_FILE='search_results.csv'
if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python3 search_experiment.py <domain_file> <problem_file> <domain_name> <command_type>")
        sys.exit(1)

    domain_file = sys.argv[1]
    problem_file = sys.argv[2]
    domain_name = sys.argv[3]
    command_type = sys.argv[4]
    
    if command_type == 'initialize':
        os.makedirs(EXPERIMENT_FOLDER, exist_ok=True)
        FILE_EXIST = os.path.exists(EXPERIMENT_FOLDER + RESULTS_FILE)
        print(f"Initializing results file at {EXPERIMENT_FOLDER + RESULTS_FILE}")
        with open(EXPERIMENT_FOLDER + RESULTS_FILE, 'a', encoding='utf-8') as result_file:
            if not FILE_EXIST:
                result_file.write(create_header(HEURISTICS_STR))
            else:
                print('already initialized')
    else:
        run_experiment(domain_file, problem_file, domain_name, EXPERIMENT_FOLDER + RESULTS_FILE)
