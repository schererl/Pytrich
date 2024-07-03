import logging
import os
import sys
import time

from matplotlib import pyplot as plt
from itertools import combinations
import pandas as pd
import seaborn as sns
from pyperplan.planner import (
    SEARCHES,
    HEURISTICS,
    GROUNDERS
)


def format_data(dname, pfile, grounder_status, grounder_elapsed_time, results):
    h_name = f"{results['h_name']}"
    states = f"{results['status']}"
    plan_length = f"{results['plan_lenght']}"
    dtg_length = f"{results['dtg_lenght']}"
    exp_nodes = f"{results['nodes_expanded']}"
    elapsed_time = f"{results['elapsed_time']:.2f}s"
    init_h = f"{results['h_init']}hi"
    avg_h = f"{results['h_avg']:.2f}ha"
    common_columns = f'{dname}\t{os.path.basename(pfile)}\t{h_name}\t{grounder_status}\t{grounder_elapsed_time:.2f}s'
    return f"{common_columns}\t{states}\t{plan_length}\t{dtg_length}\t{exp_nodes}\t{elapsed_time}\t{init_h}\t{avg_h}\n"


def format_data_grounder_error(dname, pfile, grounder_status, grounder_elapsed_time):
    common_columns = f'{dname}\t{os.path.basename(pfile)}\t{grounder_status}\t{grounder_elapsed_time:.2f}s'
    noop = '\t'
    return f"{common_columns}\t{noop}\t{noop}\t{noop}\t{noop}\t{noop}\t{noop}\t{noop}\t{noop}\n"

def run_experiment(dfile, pfile, dname, results_file):
    logging.info('Starting grounder')
    ground_start_time = time.time()
    grounder = GROUNDERS['panda'](dfile, pfile)
    model = grounder.groundify()
    grounder_elapsed_time = time.time() - ground_start_time
    
    if grounder.grounder_status != 'SUCCESS' or grounder_elapsed_time > 100:
        logging.info('Grounder failed')
        with open(results_file, 'a', encoding='utf-8') as file:
            file.write(dname, pfile, grounder.grounder_status, grounder_elapsed_time)
            return
    logging.info('Grounder ended')

    results = {}
    for heuristic in HEURISTICS_INFO:
        heuristic_str = heuristic[0]
        data = SEARCHES["Astar"](model, h_params=heuristic[1], heuristic_type=HEURISTICS[heuristic_str])
        results[heuristic_str] = data
    
        with open(results_file, 'a', encoding='utf-8') as file:
            file.write(format_data(dname, pfile, grounder.grounder_status, grounder_elapsed_time, results[heuristic_str]))
    
            

def resume_data(results_file):
    df = pd.read_csv(results_file, sep='\t')
    
    goal_data = df[df['STATUS'] == 'GOAL']
    heuristics = goal_data['HEURISTIC'].unique()
    heuristic_pairs = list(combinations(heuristics, 2))
    for h1, h2 in heuristic_pairs:
        # Filter data for the specific pair of heuristics
        df_h1 = goal_data[goal_data['HEURISTIC'] == h1][['DOMAIN', 'PROBLEM', 'EXP. NODES']]
        df_h2 = goal_data[goal_data['HEURISTIC'] == h2][['DOMAIN', 'PROBLEM', 'EXP. NODES']]
        
        # Merge data on DOMAIN and PROBLEM
        df_merge = pd.merge(df_h1, df_h2, on=['DOMAIN', 'PROBLEM'], suffixes=(f'_{h1}', f'_{h2}'))
        
        # Plot comparison
        plt.figure(figsize=(10, 6))
        sns.scatterplot(x=f'EXP. NODES_{h1}', y=f'EXP. NODES_{h2}', hue='DOMAIN', data=df_merge)
        plt.title(f'Comparison of Expanded Nodes: {h1} vs {h2}')
        plt.xlabel(f'Expanded Nodes ({h1})')
        plt.ylabel(f'Expanded Nodes ({h2})')
        plt.grid(True)
        plt.legend(title='Domain')
        plt.savefig(f'{EXPERIMENT_FOLDER}{h1}_vs_{h2}_comparison.png')
        plt.show()

    # Create a coverage table for each heuristic
    coverage = goal_data.groupby(['DOMAIN', 'HEURISTIC']).size().unstack(fill_value=0)
    print("Coverage Table:")
    print(coverage)
    coverage.to_csv(f'{EXPERIMENT_FOLDER}coverage_table.csv')
    

EXPERIMENT_FOLDER=os.path.abspath('Experiments/Outputs/Search') + '/'
RESULTS_FILE='search_results.csv'
HEURISTICS_INFO = [
    ['LMCOUNT',"use_bid=True,name=\"LMCOUNT-BID\""],
    ['LMCOUNT',"use_bid=False,name=\"LMCOUNT-CLASS\""],
    ['TDG',"name=\"TDG\""]
]
HEADER = (
    'DOMAIN\tPROBLEM\tHEURISTIC\tGROUNDER STATUS\t'
    'GROUNDER TIME\tSTATUS\tPLAN LENGTH\tDTG LENGTH\t'
    'EXP. NODES\tTIME\tINIT-H\tAVG-H\n'
)
if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python3 search_experiment.py <domain_file> <problem_file> <domain_name> <command_type>")
        sys.exit(1)

    domain_file  = sys.argv[1]
    problem_file = sys.argv[2]
    domain_name  = sys.argv[3]
    command_type = sys.argv[4]
    resume_data(EXPERIMENT_FOLDER + RESULTS_FILE)
    if command_type == 'initialize':
        os.makedirs(EXPERIMENT_FOLDER, exist_ok=True)
        FILE_EXIST = os.path.exists(EXPERIMENT_FOLDER + RESULTS_FILE)
        print(f"Initializing results file at {EXPERIMENT_FOLDER + RESULTS_FILE}")
        with open(EXPERIMENT_FOLDER + RESULTS_FILE, 'a', encoding='utf-8') as result_file:
            if not FILE_EXIST:
                result_file.write(HEADER)
            else:
                print('already initialized')
    elif command_type == 'plot':
        resume_data(EXPERIMENT_FOLDER + RESULTS_FILE)
    else:
        run_experiment(domain_file, problem_file, domain_name, EXPERIMENT_FOLDER + RESULTS_FILE)
