import pandas as pd
import matplotlib.pyplot as plt

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
        expanded_node_count =-1
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
                experiment_names.append(current_experiment)
                domains.append(current_domain)
                problems.append(current_problem)
                facts.append(fact_count)
                abstract_tasks.append(abstract_task_count)
                operators.append(operator_count)
                decompositions.append(decomposition_count)
                to_reachability_times.append(reachability_time)
                expanded_nodes.append(expanded_node_count)
                # Reset for the next block
                current_experiment = None
                current_domain = None
                current_problem = None
                expanded_node_count =-1
                

    # Create DataFrames
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
    """Filter the expanded nodes data to include only cases where both experiments have expanded nodes > -1."""
    # Pivot table to create a wide format dataframe with each experiment as a column
    expanded_nodes_df = model_info_df.pivot_table(index=['Domain', 'Problem'], columns='Experiment name', values='Expanded Nodes')

    # Filter out rows where any experiment has expanded nodes <= -1
    filtered_expanded_nodes_df = expanded_nodes_df[(expanded_nodes_df > -1).all(axis=1)]

    # Sum the expanded nodes by domain after filtering
    grouped_expanded_nodes_df = filtered_expanded_nodes_df.groupby('Domain').sum()

    return grouped_expanded_nodes_df

def generate_and_save_tables(model_info_df):
    """Generate comparison tables and save them to CSV files."""
    # Pivot tables for each category, grouped by Domain
    abstract_tasks_df = model_info_df.pivot_table(index='Domain', columns='Experiment name', values='Abstract Tasks', aggfunc='sum')
    decompositions_df = model_info_df.pivot_table(index='Domain', columns='Experiment name', values='Decompositions', aggfunc='sum')
    facts_df = model_info_df.pivot_table(index='Domain', columns='Experiment name', values='Facts', aggfunc='sum')
    operators_df = model_info_df.pivot_table(index='Domain', columns='Experiment name', values='Operators', aggfunc='sum')
    expanded_nodes_df = model_info_df.pivot_table(index='Domain', columns='Experiment name', values='Expanded Nodes', aggfunc='sum')
    expanded_nodes_df = filter_expanded_nodes(model_info_df)
    # Create a table comparing the number of problems each experiment terminated
    problems_terminated_df = model_info_df.groupby(['Domain', 'Experiment name']).size().unstack(fill_value=0)

    # Save the tables to CSV files
    abstract_tasks_df.to_csv('abstract_tasks_comparison.csv', index=True)
    decompositions_df.to_csv('decompositions_comparison.csv', index=True)
    facts_df.to_csv('facts_comparison.csv', index=True)
    operators_df.to_csv('operators_comparison.csv', index=True)
    problems_terminated_df.to_csv('problems_terminated_comparison.csv', index=True)
    expanded_nodes_df.to_csv('expanded_nodes_comparison.csv', index=True)

    # Print the tables for verification
    print("Abstract Tasks Comparison:")
    print(abstract_tasks_df)
    print("\nDecompositions Comparison:")
    print(decompositions_df)
    print("\nFacts Comparison:")
    print(facts_df)
    print("\nOperators Comparison:")
    print(operators_df)
    print("\nProblems Terminated Comparison:")
    print(problems_terminated_df)
    print("\nExpanded Nodes Comparison:")
    print(expanded_nodes_df)

def save_reachability_data(reachability_df):
    """Save reachability data to a CSV file."""
    reachability_df.to_csv('to_reachability_times.csv', index=False)

def plot_reachability_times(reachability_df):
    """Create and display a boxplot for TO reachability times by domain."""
    # Create a single plot with increased width
    fig, ax = plt.subplots(figsize=(16, 10))  # Using subplots to manage figure and axis explicitly

    # Create a boxplot to visualize the distribution of TO reachability times per domain
    reachability_df.boxplot(column='TO Reachability Time (s)', by='Domain', grid=False, vert=False, ax=ax)

    # Adjusting the plot
    ax.set_title('TO Reachability Elapsed Time per Domain for TO-TDG')
    plt.suptitle('')  # Make sure the extra title is not displayed
    ax.set_xlabel('TO Reachability Time (s)')
    ax.set_ylabel('Domain')

    # Display the plot
    plt.show()

def main(log_file_path):
    """Main function to parse the log, generate tables, and plot data."""
    # Parse the log file
    model_info_df, reachability_df = parse_log_file(log_file_path)
    
    # Generate and save comparison tables
    generate_and_save_tables(model_info_df)
    
    # Save reachability data
    save_reachability_data(reachability_df)
    
    # Plot reachability times
    plot_reachability_times(reachability_df)

# Run the main function with the specified log file
main('log-results/tor.out')
