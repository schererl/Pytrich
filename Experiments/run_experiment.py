import json
import os
import logging
import resource
import signal
import subprocess
import sys
import psutil

def load_config(experiment_location):
    config_path = os.path.join(experiment_location, 'config.json')
    with open(config_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def limit_resources(memory_limit, time_limit):
    def set_limits():
        # Set memory limit
        resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))

        # Set time limit
        def timeout_handler(signum, frame):
            raise TimeoutError("Process exceeded time limit")

        signal.signal(signal.SIGXCPU, timeout_handler)
        resource.setrlimit(resource.RLIMIT_CPU, (time_limit, time_limit))
    
    return set_limits

def run_with_limits(command, memory_limit, time_limit):
    process = psutil.Popen(command, preexec_fn=limit_resources(memory_limit, time_limit), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = process.communicate(timeout=time_limit)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        logging.error("Process exceeded time limit")
        return 1, stdout, stderr
    except Exception as e:
        process.kill()
        logging.error('Process failed with exception: %s', e)
        return 1, stdout, stderr
    
    return process.returncode, stdout.decode(), stderr.decode()

def get_domain_problem_pairs(domain_path):
    files = [f for f in os.listdir(domain_path) if f.endswith('.hddl') and '-grounded' not in f.lower()]
    domain_files = [f for f in files if 'domain' in f]
    problem_files = sorted([f for f in files if 'domain' not in f])
    
    if len(domain_files) == 1:
        domain_file = domain_files[0]
        return [
            (
            os.path.join(domain_path, domain_file),
            os.path.join(domain_path, problem_file)
            ) for problem_file in problem_files
        ]

    domain_problem_pairs = []
    for domain_file in domain_files:
        corresponding_problem = [
            problem_file for problem_file in problem_files 
            if domain_file.replace('-domain', '') in problem_file
        ]
        for problem_file in corresponding_problem:
            domain_problem_pairs.append(
                (os.path.join(domain_path, domain_file), os.path.join(domain_path, problem_file))
            )
    
    return domain_problem_pairs

def run_experiment(etype):
    experiment_location = os.path.dirname(os.path.realpath(__file__))
    config = load_config(experiment_location)
    benchmarks_location = os.path.abspath(os.path.join(experiment_location, '..', config['BENCHMARK_FOLDER_NAME']))
    # Header initialization
    initialize_command = [
        'python3', f'{experiment_location}/{etype}_experiment.py', 
        'dummy_domain_file', 'dummy_problem_file', 
        'dummy_domain_name', 'initialize'
    ]
    print(initialize_command)
    returncode, stdout, stderr = run_with_limits(
        initialize_command, config['MEMORY_LIMIT'], config['TIME_LIMIT']
    )
    
    for domain_name in config['DOMAINS']:
        domain_path = os.path.abspath(os.path.join(benchmarks_location, domain_name))
        domain_problem_pairs = get_domain_problem_pairs(domain_path)
        for domain_file, problem_file in domain_problem_pairs:
            logging.info('Starting Experiment %s:%s', domain_name, os.path.basename(problem_file))
            command = [
                'python3', f'{experiment_location}/{etype}_experiment.py', domain_file, problem_file, domain_name, 'run_experiment'
            ]
            returncode, stdout, stderr = run_with_limits(command, config['MEMORY_LIMIT'], config['TIME_LIMIT'])
            print(stdout)
            print(stderr, file=sys.stderr)
            
            if returncode != 0:
                logging.error('Experiment failed for %s: %s, getting next domain', domain_name, problem_file)
                logging.error(stderr)
                break # next domain
            else:
                logging.info('Experiment ended')
                
    plot_command = [
        'python3', f'{experiment_location}/{etype}_experiment.py', 
        'dummy_domain_file', 'dummy_problem_file', 
        'dummy_domain_name', 'plot'
    ]
    
    returncode, stdout, stderr = run_with_limits(plot_command, config['MEMORY_LIMIT'], config['TIME_LIMIT'])
    print(stdout)
    print(stderr, file=sys.stderr)

if __name__ == "__main__":
    experiment_type = sys.argv[1]
    run_experiment(experiment_type)
