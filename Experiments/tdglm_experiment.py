import logging
import os
import sys
import time

from matplotlib import pyplot as plt
import pandas as pd
from pyperplan.grounder.panda_ground import pandaGrounder
from pyperplan.heuristics.tdglm_heuristic import TDGLmHeuristic
from pyperplan.search.htn_node import AstarNode

def compute_classical_tdglm(model, domain_name, problem_file):
    start_time = time.time()
    logging.info('Starting classical Landmark procedure')
    initial_node = AstarNode(None, None, None, model.initial_state, model.initial_tn, 0, 0)
    classical_tdglm = TDGLmHeuristic(model, initial_node, use_bid=False)
    heuristic_value = initial_node.h_value
    total_time = time.time() - start_time
    logging.info('Classical landmark procedure ended')
    return f'{domain_name},{problem_file},Classical TDGLM, heuristic value={heuristic_value}, landmarks={classical_tdglm.total_lms}, total={total_time:.2f}s'

def compute_bidirectional_tdglm(model, domain_name, problem_file):
    start_time = time.time()
    logging.info('Starting bidirectional TDG procedure')
    initial_node = AstarNode(None, None, None, model.initial_state, model.initial_tn, 0, 0)
    bidirectional_tdglm = TDGLmHeuristic(model, initial_node, use_bid=True)
    heuristic_value = initial_node.h_value
    total_time = time.time() - start_time
    logging.info('Bidirectional TDG procedure ended')
    
    return f'{domain_name},{problem_file},Bidirectional TDGLM, heuristic value={heuristic_value}, landmarks={bidirectional_tdglm.total_lms}, total={total_time:.2f}s'

def compute_tdg(model, domain_name, problem_file):
    start_time = time.time()
    logging.info('Starting TDG procedure')
    initial_node = AstarNode(None, None, None, model.initial_state, model.initial_tn, 0, 0)
    tdg_heuristic = TDGLmHeuristic(model, initial_node, use_landmarks=False)
    heuristic_value = initial_node.h_value
    total_time = time.time() - start_time
    logging.info('TDG procedure ended')
    
    return f'{domain_name},{problem_file},TDG, heuristic value={heuristic_value}, landmarks={tdg_heuristic.total_lms}, total={total_time:.2f}s'

def run_experiment(dfile, pfile, dname, rfile):
    grounder = pandaGrounder(dfile, pfile)
    model = grounder.groundify()
    results = []
    base_path = os.path.basename(pfile)
    results.append(compute_classical_tdglm(model, dname, base_path))
    results.append(compute_bidirectional_tdglm(model, dname, base_path))
    results.append(compute_tdg(model, dname, base_path))

    print(rfile)
    with open(rfile, 'a',encoding='utf-8') as rfile:
        for result in results:
            rfile.write(result + '\n')

def plot_results(output_file):
    with open(output_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    header = lines[0].strip().split(',')
    data_lines = lines[1:]
    data = []
    for line in data_lines:
        fields = line.strip().split(',')
        record = {header[i]: fields[i].strip() for i in range(len(header))}
        data.append(record)

    df = pd.DataFrame(data)
    df['Heuristic Value'] = df['Heuristic Value'].str.extract(r'heuristic value=(\d+)').astype(float)
    domains = df['Domain'].unique()

    for domain in domains:
        domain_data = df[df['Domain'] == domain]

        classical_data = domain_data[domain_data['Type'] == 'Classical TDGLM']
        bidirectional_data = domain_data[domain_data['Type'] == 'Bidirectional TDGLM']
        tdg_data = domain_data[domain_data['Type'] == 'TDG']

        if not classical_data.empty and not tdg_data.empty:
            plt.figure(figsize=(14, 6))
            plt.subplot(1, 2, 1)
            plt.scatter(classical_data['Heuristic Value'], tdg_data['Heuristic Value'], label=domain)
            plt.plot([0, max(classical_data['Heuristic Value'].max(), tdg_data['Heuristic Value'].max())], 
                    [0, max(classical_data['Heuristic Value'].max(), tdg_data['Heuristic Value'].max())], 'k--')
            plt.xlabel('Classical TDGLM Heuristic Value')
            plt.ylabel('TDG Heuristic Value')
            plt.title(f'TDG vs Classical TDGLM for {domain}')
            plt.legend()
            plt.grid(True)

        if not classical_data.empty and not bidirectional_data.empty:
            plt.subplot(1, 2, 2)
            plt.scatter(classical_data['Heuristic Value'], bidirectional_data['Heuristic Value'], label=domain)
            plt.plot([0, max(classical_data['Heuristic Value'].max(), bidirectional_data['Heuristic Value'].max())], 
                    [0, max(classical_data['Heuristic Value'].max(), bidirectional_data['Heuristic Value'].max())], 'k--')
            plt.xlabel('Classical TDGLM Heuristic Value')
            plt.ylabel('Bidirectional TDGLM Heuristic Value')
            plt.title(f'Bidirectional TDGLM vs Classical TDGLM for {domain}')
            plt.legend()
            plt.grid(True)

        plt.tight_layout()
        plt.savefig(f'{EXPERIMENT_FOLDER}{domain}_comparison.png')
        plt.show()


EXPERIMENT_HEADER='Domain,Problem,Type,Heuristic Value,Total Landmarks,Total Time\n'
EXPERIMENT_FOLDER=os.path.abspath('Experiments/Outputs/TDGLM') + '/'
RESULTS_FILE='tdglm_results.csv'

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python3 tdglm_experiment.py <domain_file> <problem_file> <domain_name> <command_type>")
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
                result_file.write(EXPERIMENT_HEADER)
            else:
                print('already initialized')              
    elif command_type == 'plot':
        plot_results(EXPERIMENT_FOLDER + RESULTS_FILE)
    else:
        run_experiment(domain_file, problem_file, domain_name, EXPERIMENT_FOLDER + RESULTS_FILE)