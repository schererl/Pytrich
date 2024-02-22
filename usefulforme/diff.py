# Python script to read two files and write differences to a third file

def compare_and_write_differences(file1_path, file2_path, output_file_path):
    with open(file1_path, 'r') as file1, open(file2_path, 'r') as file2:
        # Read lines from both files
        file1_lines = file1.readlines()
        file2_lines = file2.readlines()
        
        # Convert lists to sets for efficient comparison
        set1 = set(file1_lines)
        set2 = set(file2_lines)
        
        # Find lines that are different
        differences = set1.symmetric_difference(set2)
        
        # Write differences to the output file
        with open(output_file_path, 'w') as output_file:
            for line in differences:
                output_file.write(line)
                
        print(f"Differences written to {output_file_path}")

# Replace 'file1.txt', 'file2.txt', and 'differences.txt' with your actual file paths
file1_path = 'TDGGrounding.txt'
file2_path = 'FULLGrounding.txt'
output_file_path = 'differences.txt'

# Call the function with the paths
compare_and_write_differences(file1_path, file2_path, output_file_path)


# Define the paths to your files
plan_output_path = 'FULLPlan.txt'
differences_path = 'differences.txt'

# Read the differences file and store its lines in a set for efficient lookup
with open(differences_path, 'r') as diff_file:
    differences = set(line.strip() for line in diff_file.readlines())

# Now, open the plan output file and check each line against the differences
with open(plan_output_path, 'r') as plan_file:
    for line in plan_file:
        # Strip the newline character for a proper comparison
        action = line.strip()
        # Check if the action is in the differences set
        if action in differences:
            print(action)
