import os
import logging
import sys
import time
import pandas as pd
import matplotlib.pyplot as plt

from pyperplan.grounder.panda_ground import pandaGrounder
from pyperplan.heuristics.landmarks.landmark import Landmarks, ContentType

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
    df['Total Landmarks'] = df['Total Landmarks'].str.extract(r'total=(\d+)').astype(int)
    df['Total Time'] = df['Total Time'].str.extract(r'total=([\d.]+)').astype(float)
    domains = df['Domain'].unique()

    for domain in domains:
        domain_data = df[df['Domain'] == domain]
        classical_data = domain_data[domain_data['Type'] == 'Classical Landmarks']
        bidirectional_data = domain_data[domain_data['Type'] == 'Bidirectional Landmarks']

        if not classical_data.empty and not bidirectional_data.empty:
            plt.figure(figsize=(14, 6))
            plt.subplot(1, 2, 1)
            plt.scatter(classical_data['Total Landmarks'], 
                        bidirectional_data['Total Landmarks'], 
                        label=domain)
            plt.plot([0, max(classical_data['Total Landmarks'].max(), 
                             bidirectional_data['Total Landmarks'].max())], 
                    [0, max(classical_data['Total Landmarks'].max(), 
                            bidirectional_data['Total Landmarks'].max())], 'k--')
            plt.xlabel('Classical Landmarks')
            plt.ylabel('Bidirectional Landmarks')
            plt.title(f'Landmarks Comparison for {domain}')
            plt.legend()
            plt.grid(True)

            plt.subplot(1, 2, 2)
            
            plt.scatter(classical_data['Total Time'], bidirectional_data['Total Time'], label=domain)
            plt.plot([0, max(classical_data['Total Time'].max(), 
                             bidirectional_data['Total Time'].max())],
                    [0, max(classical_data['Total Time'].max(), 
                            bidirectional_data['Total Time'].max())], 'k--')
            plt.xlabel('Classical Total Time (s)')
            plt.ylabel('Bidirectional Total Time (s)')
            plt.title(f'Time Comparison for {domain}')
            plt.legend()
            plt.grid(True)

            plt.tight_layout()
            plt.savefig(f'{EXPERIMENT_FOLDER}/{domain}_comparison.png')
            plt.show()

def compute_classical_lm(model, dname, pfile):
    start_time = time.time()
    logging.info('Starting classical Landmark procedure')

    logging.info('\tBuilding and-or-graph')
    start_and_or_time = time.time()
    classical_lm = Landmarks(model, bidirectional=False)
    end_and_or_time = time.time() - start_and_or_time

    logging.info('\tStarting bottom landmark extraction')
    start_extract_time = time.time()
    classical_lm.bottom_up_lms()
    end_extract_time = time.time() - start_extract_time
    
    bu_lm_set = set()
    bu_lm_operator_set = set()
    bu_lm_methods_set = set()
    bu_lm_tasks_set = set()
    bu_lm_facts_set = set()
    
    for t in model.initial_tn:
        for lm_id in classical_lm.bu_landmarks[t.global_id]:
            bu_lm_set.add(lm_id)
    for g_fact in range(len(bin(model.goals)) - 2):
        if model.goals & (1 << g_fact):
            for lm_id in classical_lm.bu_landmarks[g_fact]:
                bu_lm_set.add(lm_id)
    
    for lm_id in bu_lm_set:
        node = classical_lm.bu_AND_OR.nodes[lm_id]
        if node.content_type == ContentType.OPERATOR:
            bu_lm_operator_set.add(lm_id)
        elif node.content_type == ContentType.METHOD:
            bu_lm_methods_set.add(lm_id)
        elif node.content_type == ContentType.ABSTRACT_TASK:
            bu_lm_tasks_set.add(lm_id)
        elif node.content_type == ContentType.FACT:
            bu_lm_facts_set.add(lm_id)
    
    total_time = time.time() - start_time
    logging.info('Ended bottom landmark extraction')
    logging.info('Classical landmark procedure ended')
    return (f'{dname},{pfile},Classical Landmarks,total={len(bu_lm_set)}, '
            f'operators={len(bu_lm_operator_set)}, methods={len(bu_lm_methods_set)}, '
            f'tasks={len(bu_lm_tasks_set)}, facts={len(bu_lm_facts_set)}, '
            f'and-or-graph={end_and_or_time:.2f}s, extraction={end_extract_time:.2f}s, total={total_time:.2f}s')

def compute_bidirectional_lm(model, dname, pfile):
    start_time = time.time()
    logging.info('Starting bidirectional Landmark procedure')

    logging.info('\tBuilding and-or-graph')
    start_and_or_time = time.time()
    bid_lm = Landmarks(model, bidirectional=True)
    end_and_or_time = time.time() - start_and_or_time

    logging.info('\tStarting landmark extraction')
    start_extract_time = time.time()
    bid_lm.bottom_up_lms()
    bid_lm.top_down_lms()
    bid_lm_set = bid_lm.bidirectional_lms(model, model.initial_state, model.initial_tn)
    end_extract_time = time.time() - start_extract_time
    
    bid_lm_operator_set = set()
    bid_lm_methods_set = set()
    bid_lm_tasks_set = set()
    bid_lm_facts_set = set()
    
    for lm_id in bid_lm_set:
        node = bid_lm.bu_AND_OR.nodes[lm_id]
        if node.content_type == ContentType.OPERATOR:
            bid_lm_operator_set.add(lm_id)
        elif node.content_type == ContentType.METHOD:
            bid_lm_methods_set.add(lm_id)
        elif node.content_type == ContentType.ABSTRACT_TASK:
            bid_lm_tasks_set.add(lm_id)
        elif node.content_type == ContentType.FACT:
            bid_lm_facts_set.add(lm_id)
    
    total_time = time.time() - start_time
    logging.info('Ended landmark extraction')
    logging.info('Bidirectional landmark procedure ended')
    
    return (f'{dname},{pfile},Bidirectional Landmarks,total={len(bid_lm_set)}, '
            f'operators={len(bid_lm_operator_set)}, methods={len(bid_lm_methods_set)}, '
            f'tasks={len(bid_lm_tasks_set)}, facts={len(bid_lm_facts_set)}, '
            f'and-or-graph={end_and_or_time:.2f}s, extraction={end_extract_time:.2f}s, total={total_time:.2f}s')

    
def run_experiment(dfile, pfile, dname, rfile):
    grounder = pandaGrounder(dfile, pfile)
    grounder_status = 'SUCCESS'
    model = grounder.groundify()
    if grounder_status != 'SUCCESS':
        logging.error('Grounder failed')
        

    logging.info('Grounder ended')
    classical_result = compute_classical_lm(model, dname, os.path.basename(pfile))
    bidirectional_result = compute_bidirectional_lm(model, dname, os.path.basename(pfile))
    
    with open(rfile, 'a', encoding='utf-8') as rfile:
        rfile.write(classical_result + '\n')
        rfile.write(bidirectional_result + '\n')
    
EXPERIMENT_HEADER = (
    'Domain,Problem,Type,Total Landmarks,'
    'Operators,Methods,Tasks,Facts,'
    'And-Or Graph Time,Extraction Time,Total Time\n'
)
EXPERIMENT_FOLDER=os.path.abspath('Experiments/Outputs/Landmarks') + '/'
RESULTS_FILE='landmark_results.csv'
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 5:
        print("Usage: python3 tdglm_experiment.py <domain_file> <problem_file> <domain_name> <command_type>")
        sys.exit(1)
    
    domain_file  = sys.argv[1]
    problem_file = sys.argv[2]
    domain_name  = sys.argv[3]
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

