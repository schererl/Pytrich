# Adjusting the parsing to correctly handle the "seconds" in the elapsed time string.
import pandas as pd

# Load the log file
log_file_path = './landmarkgenerationlog.out'

# Initialize lists to store the parsed data
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

# Parse the log file
with open(log_file_path, 'r') as file:
    heuristic_name = None
    total_elapsed_time = None
    elapsed_time_disjunction = None
    total_landmarks_count = None
    task_landmarks_count = None
    method_landmarks_count = None
    fact_landmarks_count = None
    min_cov_disjunction_count = None
    
    for line in file:
        if "heuristic name:" in line:
            heuristic_name = line.split(": ")[1].strip()
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
            
            # Reset variables for the next block
            heuristic_name = None
            total_elapsed_time = None
            elapsed_time_disjunction = None
            total_landmarks_count = None
            task_landmarks_count = None
            method_landmarks_count = None
            fact_landmarks_count = None
            min_cov_disjunction_count = None

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
    'elapsed time for disjunctions': elapsed_time_disjunctions
})


print(log_data_df)
# Or save to a CSV file
log_data_df.to_csv('parsed_log_data.csv', index=False)
