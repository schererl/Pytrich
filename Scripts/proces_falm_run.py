import pandas as pd

# Define the path to the log file
file_path = './log-execution.out'

# Read the content of the log file
with open(file_path, 'r') as file:
    log_lines = file.readlines()

# Initialize variables to store extracted information
data = []
problem = None
domain = None
landmark_info = {
    'and_or_operators': 0,
    'and_or_facts': 0,
    'and_or_total': 0,
    'gord_operators': 0,
    'gord_facts': 0,
    'gord_total': 0,
    'gord_disjunctions': 0
}

# Function to reset landmark_info
def reset_landmark_info():
    return {
        'and_or_operators': 0,
        'gord_operators': 0,
        'and_or_facts': 0,
        'gord_facts': 0,
        'and_or_total': 0,
        'gord_total': 0,
        'gord_disjunctions': 0
    }

# Loop through each line in the log file and extract relevant information
skip = False
for line in log_lines:
    if '@' in line:
        skip = True
        continue

    if "Running experiment" in line:
        # Save the current data if problem and domain are set
        if problem and domain:
            # Combine problem, domain, and landmark_info into a single list
            row = [problem, domain] + list(landmark_info.values())
            data.append(row)
        
        # Reset problem, domain, and landmark_info for the new experiment
        problem = None
        domain = None
        landmark_info = reset_landmark_info()
        skip = False

    if skip:
        continue

    if "domain name:" in line:
        domain = line.split(":")[1].strip()
    elif "problem name:" in line:
        problem = line.split(":")[1].strip()
    elif "and-or landmark operators:" in line:
        landmark_info['and_or_operators'] = int(line.split(":")[1].strip())
    elif "and-or landmark facts:" in line:
        landmark_info['and_or_facts'] = int(line.split(":")[1].strip())
    elif "and-or landmark total:" in line:
        landmark_info['and_or_total'] = int(line.split(":")[1].strip())
    elif "gord landmark operators:" in line:
        landmark_info['gord_operators'] = int(line.split(":")[1].strip())
    elif "gord landmark facts:" in line:
        landmark_info['gord_facts'] = int(line.split(":")[1].strip())
    elif "gord landmark total:" in line:
        landmark_info['gord_total'] = int(line.split(":")[1].strip())
    elif "disjunctions:" in line:
        landmark_info['gord_disjunctions'] = int(line.split(":")[1].strip())
            

# Append the last entry if it exists
if problem and domain:
    row = [problem, domain] + list(landmark_info.values())
    data.append(row)

# Create a DataFrame with the extracted data
columns = ["Problem", "Domain", "and_or_operators", "gord_operators", "and_or_facts",  "gord_facts", 
           "and_or_total", "gord_total", "gord_disjunctions"]

df = pd.DataFrame(data, columns=columns)
df = df[(df.iloc[:, 2:] != 0).any(axis=1)]

output_csv_path = './landmark_info.csv'
df.to_csv(output_csv_path, index=False)
