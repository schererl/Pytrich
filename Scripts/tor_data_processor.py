import os
import pandas as pd
import matplotlib.pyplot as plt
import parse_log
import directories

def create_data_frames(log_files_path):
    parser = parse_log.ParseLog(log_files_path)
    parser()

    # Create the DataFrame for model info
    model_info_df = pd.DataFrame({
        'Experiment name': parser.experiment_names,
        'Domain': parser.domains,
        'Problem': parser.problems,
        'Facts': parser.facts,
        'Abstract Tasks': parser.abstract_tasks,
        'Operators': parser.operators,
        'Decompositions': parser.decompositions,
        'Expanded Nodes': parser.expanded_nodes
    })

    # Remove rows with NaN values
    model_info_df = model_info_df.dropna(subset=['Abstract Tasks'])
    print(model_info_df)

    # Create the DataFrame for reachability info
    reachability_df = pd.DataFrame({
        'Domain': parser.domains,
        'Problem': parser.problems,
        'TO Reachability Time (s)': parser.tor_elapsed_time
    })

    # Remove rows with NaN values
    reachability_df = reachability_df.dropna()
    print(reachability_df)

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
    print("\nInitial model_info_df:")
    print(model_info_df)
    
    # Filter out rows where 'Domain', 'Heuristic name', or 'Abstract Tasks' are NaN
    abstract_tasks_df = model_info_df.dropna(subset=['Domain', 'Experiment name', 'Abstract Tasks'])
    
    print("\nAfter filtering NaN values in 'Domain', 'Experiment name', and 'Abstract Tasks':")
    print(abstract_tasks_df)
    exit(0)
    
    decompositions_df = model_info_df.pivot_table(index='Domain', columns='Heuristic name', values='Decompositions', aggfunc='sum')
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

def main(log_files_path):
    """Main function to parse the log, generate tables, and plot data."""
    if check_csv_exists():
        model_info_df, reachability_df = create_data_frames(log_files_path)
        generate_and_save_tables(model_info_df)
        save_reachability_data(reachability_df)
        plot_reachability_times(reachability_df)


LOG_FILES = ['test-tor-log.log']
C_CSV_FILE = 'compound_tasks_comparison.csv'
D_CSV_FILE = 'decompositions_comparison.csv'
F_CSV_FILE = 'facts_comparison.csv'
A_CSV_FILE = 'actions_comparison.csv'
PT_CSV_FILE = 'problems_terminated_comparison.csv'
EN_CSV_FILE = 'expanded_nodes_comparison.csv'
TOR_CSV_FILE = 'to_reachability_times.csv'
main([directories.LOG_DIR + fl for fl in LOG_FILES])
