import os
import pandas as pd
import matplotlib.pyplot as plt
import directories

def parse_log_file(log_file_path):
    """Parse the log file to extract relevant data."""
    experiment_names = []
    domains = []
    problems = []
    facts = []
    abstract_tasks = []
    operators = []
    decompositions = []
    to_reachability_times = []
    expanded_nodes = []
    
    with open(log_file_path, 'r') as file:
        current_experiment = None
        current_domain = None
        current_problem = None
        expanded_node_count = -1
        for line in file:
            if "Experiment name:" in line:
                current_experiment = line.split(": ")[1].strip()
            elif "Domain:" in line:
                current_domain = line.split(": ")[1].strip()
            elif "Problem:" in line:
                current_problem = line.split(": ")[1].strip()
            elif "Facts:" in line:
                fact_count = int(line.split(": ")[1].strip())
            elif "Abstract Tasks:" in line:
                abstract_task_count = int(line.split(": ")[1].strip())
            elif "Operators:" in line:
                operator_count = int(line.split(": ")[1].strip())
            elif "Decompositions:" in line:
                decomposition_count = int(line.split(": ")[1].strip())
            elif "TO reachability elapsed time:" in line:
                reachability_time = float(line.split(": ")[1].strip().split(" ")[0])
            elif "Expanded Nodes:" in line:
                expanded_node_count = int(line.split(": ")[1].strip())
            elif "@" in line and current_experiment:
                # Append the data
                experiment_names.append(current_experiment)
                domains.append(current_domain)
                problems.append(current_problem)
                facts.append(fact_count)
                abstract_tasks.append(abstract_task_count)
                operators.append(operator_count)
                decompositions.append(decomposition_count)
                to_reachability_times.append(reachability_time)
                expanded_nodes.append(expanded_node_count)

                # Reset the values for the next block
                current_experiment = None
                current_domain = None
                current_problem = None
                expanded_node_count = -1

    # Create DataFrames for further analysis
    model_info_df = pd.DataFrame({
        'Experiment name': experiment_names,
        'Domain': domains,
        'Problem': problems,
        'Facts': facts,
        'Abstract Tasks': abstract_tasks,
        'Operators': operators,
        'Decompositions': decompositions,
        'Expanded Nodes': expanded_nodes
    })

    reachability_df = pd.DataFrame({
        'Domain': domains,
        'Problem': problems,
        'TO Reachability Time (s)': to_reachability_times
    })

    return model_info_df, reachability_df

def filter_expanded_nodes(model_info_df):
    """Filter the expanded nodes data to include only cases where all experiments have valid expanded node counts."""
    expanded_nodes_df = model_info_df.pivot_table(index=['Domain', 'Problem'], columns='Experiment name', values='Expanded Nodes')
    # Filter rows where all experiments have expanded nodes > -1
    filtered_expanded_nodes_df = expanded_nodes_df[(expanded_nodes_df > -1).all(axis=1)]
    # Group by domain to sum expanded nodes
    grouped_expanded_nodes_df = filtered_expanded_nodes_df.groupby('Domain').sum()
    return grouped_expanded_nodes_df

def generate_and_save_tables(model_info_df):
    """Generate comparison tables and save them to CSV files."""
    # Pivot tables for each category
    abstract_tasks_df = model_info_df.pivot_table(index='Domain', columns='Experiment name', values='Abstract Tasks', aggfunc='sum')
    decompositions_df = model_info_df.pivot_table(index='Domain', columns='Experiment name', values='Decompositions', aggfunc='sum')
    facts_df = model_info_df.pivot_table(index='Domain', columns='Experiment name', values='Facts', aggfunc='sum')
    operators_df = model_info_df.pivot_table(index='Domain', columns='Experiment name', values='Operators', aggfunc='sum')
    expanded_nodes_df = filter_expanded_nodes(model_info_df)

    # Number of problems terminated per experiment
    problems_terminated_df = model_info_df.groupby(['Domain', 'Experiment name']).size().unstack(fill_value=0)

    # Save to CSV files
    abstract_tasks_df.to_csv(directories.CSV_DIR + C_CSV_FILE, index=True)
    decompositions_df.to_csv(directories.CSV_DIR + D_CSV_FILE, index=True)
    facts_df.to_csv(directories.CSV_DIR + F_CSV_FILE, index=True)
    operators_df.to_csv(directories.CSV_DIR + A_CSV_FILE, index=True)
    problems_terminated_df.to_csv(directories.CSV_DIR + PT_CSV_FILE, index=True)
    expanded_nodes_df.to_csv(directories.CSV_DIR + EN_CSV_FILE, index=True)

    # Print for verification
    print("\nComparison tables generated and saved:")
    print("Abstract Tasks Comparison:\n", abstract_tasks_df)
    print("Decompositions Comparison:\n", decompositions_df)
    print("Facts Comparison:\n", facts_df)
    print("Operators Comparison:\n", operators_df)
    print("Problems Terminated Comparison:\n", problems_terminated_df)
    print("Expanded Nodes Comparison:\n", expanded_nodes_df)

def save_reachability_data(reachability_df):
    """Save reachability data to CSV."""
    reachability_df.to_csv(directories.CSV_DIR + TOR_CSV_FILE, index=False)

def plot_reachability_times(reachability_df):
    """Create and display a boxplot for TO reachability times."""
    fig, ax = plt.subplots(figsize=(16, 10))
    reachability_df.boxplot(column='TO Reachability Time (s)', by='Domain', grid=False, vert=False, ax=ax)
    ax.set_title('TO Reachability Elapsed Time per Domain')
    plt.suptitle('')
    ax.set_xlabel('TO Reachability Time (s)')
    ax.set_ylabel('Domain')
    plt.show()

def check_csv_exists():
    """Check if CSV files already exist and prompt the user for confirmation."""
    csv_files = [C_CSV_FILE, D_CSV_FILE, F_CSV_FILE, A_CSV_FILE, PT_CSV_FILE, EN_CSV_FILE]
    for csv_file in csv_files:
        if os.path.exists(directories.CSV_DIR + csv_file):
            response = input(f"{csv_file} already exists. Do you want to overwrite it? (y/n): ").lower()
            if response != 'y':
                print(f"Skipping file: {csv_file}")
                return False
    return True

def main(log_file_path):
    """Main function to parse the log, generate tables, and plot data."""
    # Check if any CSV files already exist before proceeding
    if check_csv_exists():
        # Parse the log file
        model_info_df, reachability_df = parse_log_file(log_file_path)
        # Generate and save comparison tables
        generate_and_save_tables(model_info_df)
        # Save reachability data
        save_reachability_data(reachability_df)
        # Plot reachability times
        plot_reachability_times(reachability_df)

# Constants for file names
LOG_FILE_NAME = 'tor.log'
C_CSV_FILE = 'compound_tasks_comparison.csv'
D_CSV_FILE = 'decompositions_comparison.csv'
F_CSV_FILE = 'facts_comparison.csv'
A_CSV_FILE = 'actions_comparison.csv'
PT_CSV_FILE = 'problems_terminated_comparison.csv'
EN_CSV_FILE = 'expanded_nodes_comparison.csv'
TOR_CSV_FILE = 'to_reachability_times.csv'
# Run the main function
main(directories.LOG_DIR + LOG_FILE_NAME)
