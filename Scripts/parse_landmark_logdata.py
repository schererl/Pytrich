import pandas as pd
import glob

import directories

# Define the list of log files to process
log_files = ['lse.out']  # You can add more log files to this list

# Initialize lists to store the parsed data across all log files
heuristic_names = []
domains = []
problems = []
total_landmarks = []
task_landmarks = []
method_landmarks = []
fact_landmarks = []
min_cov_disjunctions = []
total_elapsed_times = []
elapsed_time_disjunctions = []
solution_sizes = []
expanded_nodes = []
elapsed_time_searches = []

# Parse each log file
for log_file_path in log_files:
    with open(log_file_path, 'r') as file:
        heuristic_name = None
        total_elapsed_time = None
        elapsed_time_disjunction = None
        total_landmarks_count = None
        task_landmarks_count = None
        method_landmarks_count = None
        fact_landmarks_count = None
        min_cov_disjunction_count = None
        solution_size = None
        expanded_node_count = None
        elapsed_time_search = None
        
        for line in file:
            if "heuristic name:" in line:
                heuristic_name = line.split(": ")[1].strip()
            elif "heuristic params:" and heuristic_name == "lmcount":
                params = line.split(": ")[1].strip()
                if "B" in params:
                    heuristic_name = "Bidirectional Landmarks"
                elif "C" in params:
                    heuristic_name = "Classical Landmarks"
            elif "Domain:" in line:
                domain = line.split(": ")[1].strip()
            elif "Problem:" in line:
                problem = line.split(": ")[1].strip()
            elif "number of total AND/OR landmarks:" in line:
                total_landmarks_count = int(line.split(": ")[1].strip())
            elif "number of task AND/OR landmarks:" in line:
                task_landmarks_count = int(line.split(": ")[1].strip())
            elif "number of methods AND/OR landmarks:" in line:
                method_landmarks_count = int(line.split(": ")[1].strip())
            elif "number of fact AND/OR landmarks:" in line:
                fact_landmarks_count = int(line.split(": ")[1].strip())
            elif "number of min-cov disjunctions:" in line:
                min_cov_disjunction_count = int(line.split(": ")[1].strip())
            elif "Elapsed time for AND/OR landmarks:" in line:
                total_elapsed_time_str = line.split(": ")[1].strip()
                total_elapsed_time = float(total_elapsed_time_str.split(" ")[0])  # Extract the numerical value only
            elif "Elapsed time for minimal disjunctions:" in line:
                elapsed_time_disjunction_str = line.split(": ")[1].strip()
                elapsed_time_disjunction = float(elapsed_time_disjunction_str.split(" ")[0])  # Extract the numerical value only
            elif "Elapsed Time:" in line:
                elapsed_time_search_str = line.split(": ")[1].strip()
                elapsed_time_search = float(elapsed_time_search_str.split(" ")[0])  # Extract the numerical value only
            elif "Solution size:" in line:
                solution_size = int(line.split(": ")[1].strip())
            elif "Expanded Nodes:" in line:
                expanded_node_count = int(line.split(": ")[1].strip())
            elif "@" in line and heuristic_name and total_elapsed_time is not None and total_landmarks_count is not None:
                # Append the parsed data to the lists
                heuristic_names.append(heuristic_name)
                domains.append(domain)
                problems.append(problem)
                total_landmarks.append(total_landmarks_count)
                task_landmarks.append(task_landmarks_count)
                method_landmarks.append(method_landmarks_count)
                fact_landmarks.append(fact_landmarks_count)
                min_cov_disjunctions.append(min_cov_disjunction_count)
                total_elapsed_times.append(total_elapsed_time)
                elapsed_time_disjunctions.append(elapsed_time_disjunction)
                solution_sizes.append(solution_size)
                expanded_nodes.append(expanded_node_count)
                elapsed_time_searches.append(elapsed_time_search)
                
                # Reset variables for the next block
                heuristic_name = None
                total_elapsed_time = None
                elapsed_time_disjunction = None
                total_landmarks_count = None
                task_landmarks_count = None
                method_landmarks_count = None
                fact_landmarks_count = None
                min_cov_disjunction_count = None
                solution_size = None
                expanded_node_count = None
                elapsed_time_search = None

# Create a DataFrame with the parsed data
log_data_df = pd.DataFrame({
    'heuristic name': heuristic_names,
    'domain': domains,
    'problem': problems,
    'total landmarks': total_landmarks,
    'task landmarks': task_landmarks,
    'method landmarks': method_landmarks,
    'fact landmarks': fact_landmarks,
    'min-cov disjunctions': min_cov_disjunctions,
    'total elapsed time': total_elapsed_times,
    'elapsed time for disjunctions': elapsed_time_disjunctions,
    'solution size': solution_sizes,
    'expanded nodes': expanded_nodes,
    'elapsed time from search': elapsed_time_searches
})

print(log_data_df)

log_data_df.to_csv('parsed_log_data.csv', index=False)


# Create the first table summarizing total landmarks
total_landmarks_summary = log_data_df.pivot_table(
    index='domain', 
    columns='heuristic name', 
    values='total landmarks', 
    aggfunc='sum'
)

# Create the second table summarizing average elapsed time
avg_elapsed_time_summary = log_data_df.pivot_table(
    index='domain', 
    columns='heuristic name', 
    values='total elapsed time', 
    aggfunc='mean'
)

# Create the third table summarizing the count of problems each heuristic handled
problem_count_summary = log_data_df.pivot_table(
    index='domain', 
    columns='heuristic name', 
    values='problem', 
    aggfunc='count'
)

print(f'COVERAGE:')
print(problem_count_summary)
print(f'LANDMARK GENERATION:')
print(total_landmarks_summary)
print(f'AVERAGE ELAPSED TIME:')
print(avg_elapsed_time_summary)


# Filter out rows where both implementations did not solve the problem
coverage_df = log_data_df.pivot_table(
    index=['domain', 'problem'], 
    columns='heuristic name', 
    values='total landmarks', 
    aggfunc='count'
)

## INTERSECTION ##
# Keep only the problems where both heuristics have results
# Keep only the problems where both heuristics have results
intersection_problems = coverage_df.dropna().index
# Filter the original DataFrame to keep only the rows corresponding to the intersection problems
log_data_df_intersection = log_data_df[log_data_df.set_index(['domain', 'problem']).index.isin(intersection_problems)].reset_index(drop=True)
print(log_data_df_intersection)


# Create the first table summarizing total landmarks
total_landmarks_summary = log_data_df_intersection.pivot_table(
    index='domain', 
    columns='heuristic name', 
    values='total landmarks', 
    aggfunc='sum'
)

print(f'LANDMARK GENERATION (INTERSECTION COVERAGE):')
print(total_landmarks_summary)

# Create the table summarizing fact landmarks
fact_landmarks_summary = log_data_df_intersection.pivot_table(
    index='domain', 
    columns='heuristic name', 
    values='fact landmarks', 
    aggfunc='sum'
)
print(f'FACT LANDMARKS (INTERSECTION COVERAGE):')
print(fact_landmarks_summary)

# Create the table summarizing task landmarks
task_landmarks_summary = log_data_df_intersection.pivot_table(
    index='domain', 
    columns='heuristic name', 
    values='task landmarks', 
    aggfunc='sum'
)
print(f'TASK LANDMARKS (INTERSECTION COVERAGE):')
print(task_landmarks_summary)

# Create the table summarizing method landmarks
method_landmarks_summary = log_data_df_intersection.pivot_table(
    index='domain', 
    columns='heuristic name', 
    values='method landmarks', 
    aggfunc='sum'
)
print(f'METHOD LANDMARKS (INTERSECTION COVERAGE):')
print(method_landmarks_summary)

# Create the table summarizing the number of disjunctions for each domain
classical_landmarks_df = log_data_df[log_data_df['heuristic name'] == 'Classical Landmarks']
disjunctions_summary = classical_landmarks_df.pivot_table(
    index='domain', 
    columns='heuristic name', 
    values='min-cov disjunctions', 
    aggfunc='sum'
)
print(f'NUMBER OF DISJUNCTIONS (Classical Landmarks):')
print(disjunctions_summary)

# Step 4: Further filter where both heuristics had expanded nodes > 0
expanded_nodes_df = log_data_df_intersection.pivot_table(
    index=['domain', 'problem'], 
    columns='heuristic name', 
    values='expanded nodes', 
    aggfunc='min'
)

# Identify problems where both heuristics had expanded nodes > 0
intersection_expanded_nodes = expanded_nodes_df[expanded_nodes_df > 0].dropna().index
# Step 5: Filter log_data_df_intersection for this new intersection
log_data_df_final_intersection = log_data_df_intersection[log_data_df_intersection.set_index(['domain', 'problem']).index.isin(intersection_expanded_nodes)].reset_index(drop=True)
# Save the filtered DataFrame to a CSV file
log_data_df_final_intersection.to_csv('filtered_expnodes.csv', index=False)

#print(log_data_df_final_intersection)