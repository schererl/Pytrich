import os
import pandas as pd
import matplotlib.pyplot as plt
import parse_log

def create_data_frames(log_files_path):
    parser = parse_log.ParseLog(log_files_path)
    parser()

    # Create the DataFrame for model info
    model_info_df = pd.DataFrame({
        'Experiment Name': parser.experiment_names,
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
    
    # Create the DataFrame for reachability info
    reachability_df = pd.DataFrame({
        'Domain': parser.domains,
        'Problem': parser.problems,
        'TO Reachability Time (s)': parser.tor_elapsed_time
    })

    # Remove rows with NaN values
    reachability_df = reachability_df.dropna()
    return model_info_df, reachability_df


def filter_expanded_nodes(model_info_df):
    """Filter the expanded nodes data to include only cases where all experiments have valid expanded node counts."""
    expanded_nodes_df = model_info_df.pivot_table(index=['Domain', 'Problem'], columns='Experiment Name', values='Expanded Nodes')
    # Filter rows where all experiments have expanded nodes > -1
    filtered_expanded_nodes_df = expanded_nodes_df[(expanded_nodes_df > -1).all(axis=1)]
    # Group by domain to sum expanded nodes
    grouped_expanded_nodes_df = filtered_expanded_nodes_df.groupby('Domain').sum()
    return grouped_expanded_nodes_df

def generate_and_save_tables(model_info_df, csv_dir):
    """Generate comparison tables and save them to CSV files."""
    # Pivot tables for each category
    print("\nInitial model_info_df:")
    print(model_info_df)
    
    # Filter out rows where 'Domain', 'Experiment Name', or 'Abstract Tasks' are NaN
    abstract_tasks_df = model_info_df.dropna(subset=['Domain', 'Experiment Name', 'Abstract Tasks'])
    
    print("\nAfter filtering NaN values in 'Domain', 'Experiment Name', and 'Abstract Tasks':")
    print(abstract_tasks_df)
    decompositions_df = model_info_df.pivot_table(index='Domain', columns='Experiment Name', values='Decompositions', aggfunc='sum')
    facts_df = model_info_df.pivot_table(index='Domain', columns='Experiment Name', values='Facts', aggfunc='sum')
    operators_df = model_info_df.pivot_table(index='Domain', columns='Experiment Name', values='Operators', aggfunc='sum')
    expanded_nodes_df = filter_expanded_nodes(model_info_df)

    # Number of problems terminated per experiment
    problems_terminated_df = model_info_df.groupby(['Domain', 'Experiment Name']).size().unstack(fill_value=0)

    # Ensure the CSV directory exists
    if not os.path.exists(csv_dir):
        print(f"Creating CSV directory at {csv_dir}")
        os.makedirs(csv_dir, exist_ok=True)

    # Save to CSV files
    abstract_tasks_df.to_csv(os.path.join(csv_dir, C_CSV_FILE), index=True)
    decompositions_df.to_csv(os.path.join(csv_dir, D_CSV_FILE), index=True)
    facts_df.to_csv(os.path.join(csv_dir, F_CSV_FILE), index=True)
    operators_df.to_csv(os.path.join(csv_dir, A_CSV_FILE), index=True)
    problems_terminated_df.to_csv(os.path.join(csv_dir, PT_CSV_FILE), index=True)
    expanded_nodes_df.to_csv(os.path.join(csv_dir, EN_CSV_FILE), index=True)

    # Print for verification
    print("\nComparison tables generated and saved:")
    print("Abstract Tasks Comparison:\n", abstract_tasks_df)
    print("Decompositions Comparison:\n", decompositions_df)
    print("Facts Comparison:\n", facts_df)
    print("Operators Comparison:\n", operators_df)
    print("Problems Terminated Comparison:\n", problems_terminated_df)
    print("Expanded Nodes Comparison:\n", expanded_nodes_df)

def save_reachability_data(reachability_df, csv_dir):
    """Save reachability data to CSV."""
    # Ensure the CSV directory exists
    if not os.path.exists(csv_dir):
        print(f"Creating CSV directory at {csv_dir}")
        os.makedirs(csv_dir, exist_ok=True)
    reachability_df.to_csv(os.path.join(csv_dir, TOR_CSV_FILE), index=False)

def plot_reachability_times(reachability_df, plot_dir):
    """Create and save a boxplot for TO reachability times."""
    fig, ax = plt.subplots(figsize=(16, 10))
    reachability_df.boxplot(column='TO Reachability Time (s)', by='Domain', grid=False, vert=False, ax=ax)
    ax.set_title('TO Reachability Elapsed Time per Domain')
    plt.suptitle('')
    ax.set_xlabel('TO Reachability Time (s)')
    ax.set_ylabel('Domain')
    plt.tight_layout()

    # Ensure the Plot directory exists
    if not os.path.exists(plot_dir):
        print(f"Creating plot directory at {plot_dir}")
        os.makedirs(plot_dir, exist_ok=True)

    # Save the plot
    plot_file_path = os.path.join(plot_dir, 'reachability_times.png')
    plt.savefig(plot_file_path)
    print(f"Reachability times plot saved to {plot_file_path}")
    plt.close(fig)

def check_csv_exists(csv_dir):
    """Check if CSV files already exist and prompt the user for confirmation."""
    csv_files = [C_CSV_FILE, D_CSV_FILE, F_CSV_FILE, A_CSV_FILE, PT_CSV_FILE, EN_CSV_FILE, TOR_CSV_FILE]
    for csv_file in csv_files:
        full_path = os.path.join(csv_dir, csv_file)
        if os.path.exists(full_path):
            response = input(f"{csv_file} already exists. Do you want to overwrite it? (y/n): ").lower()
            if response != 'y':
                print(f"Skipping file: {csv_file}")
                return False
    return True

def main(log_files_path):
    """Main function to parse the log, generate tables, and plot data."""
    # Define local variables for directories
    log_dir = os.path.join('TOR', 'log-files')
    csv_dir = os.path.join('TOR', 'csv-files')
    plot_dir = os.path.join('TOR', 'plot-files')

    # Ensure the log directory exists
    if not os.path.exists(log_dir):
        print(f"Creating log directory at {log_dir}")
        os.makedirs(log_dir, exist_ok=True)
    else:
        print(f"Log directory exists at {log_dir}")

    # Ensure the CSV directory exists
    if not os.path.exists(csv_dir):
        print(f"Creating CSV directory at {csv_dir}")
        os.makedirs(csv_dir, exist_ok=True)
    else:
        print(f"CSV directory exists at {csv_dir}")

    # Ensure the Plot directory exists
    if not os.path.exists(plot_dir):
        print(f"Creating plot directory at {plot_dir}")
        os.makedirs(plot_dir, exist_ok=True)
    else:
        print(f"Plot directory exists at {plot_dir}")

    if check_csv_exists(csv_dir):
        model_info_df, reachability_df = create_data_frames(log_files_path)
        generate_and_save_tables(model_info_df, csv_dir)
        save_reachability_data(reachability_df, csv_dir)
        plot_reachability_times(reachability_df, plot_dir)

# Constants
LOG_FILES = ['test-tor-log.log']
C_CSV_FILE = 'compound_tasks_comparison.csv'
D_CSV_FILE = 'decompositions_comparison.csv'
F_CSV_FILE = 'facts_comparison.csv'
A_CSV_FILE = 'actions_comparison.csv'
PT_CSV_FILE = 'problems_terminated_comparison.csv'
EN_CSV_FILE = 'expanded_nodes_comparison.csv'
TOR_CSV_FILE = 'to_reachability_times.csv'

if __name__ == "__main__":
    # Define local variables for directories
    log_dir = os.path.join('TOR', 'log-files')
    csv_dir = os.path.join('TOR', 'csv-files')
    plot_dir = os.path.join('TOR', 'plot-files')

    # Prepare log files paths
    log_files_paths = [os.path.join(log_dir, fl) for fl in LOG_FILES]

    main(log_files_paths)
