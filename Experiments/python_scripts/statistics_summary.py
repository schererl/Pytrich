import argparse
import csv
import os
from collections import defaultdict

def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate a table of coverage from log files.")
    parser.add_argument("-i", "--input_file", required=True, help="Path to the input CSV file.")
    parser.add_argument("-o", "--output_file", required=True, help="Path to the output CSV file.")
    return parser.parse_args()

def calculate_coverage(input_file):
    # We store count of solved instances, sum of solution sizes, and sum of expanded nodes
    coverage_data = defaultdict(
        lambda: defaultdict(lambda: {"count": 0, "solution_size_sum": 0, "expanded_nodes_sum": 0})
    )

    # Read input CSV and calculate coverage
    with open(input_file, "r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        # Normalize header names by stripping whitespace
        headers = [header.strip() for header in reader.fieldnames]
        reader.fieldnames = headers

        for row in reader:
            domain = row["domain_name"].strip()
            experiment_name = row["experiment_name"].strip()
            solution_size_str = row["solution_size"].strip()
            expanded_nodes_str = row["expanded_nodes"].strip()

            # Only consider coverage if solution size is not empty
            if solution_size_str:
                coverage_data[domain][experiment_name]["count"] += 1
                coverage_data[domain][experiment_name]["solution_size_sum"] += int(solution_size_str)

                # If expanded_nodes is not empty, add it to the sum
                if expanded_nodes_str:
                    coverage_data[domain][experiment_name]["expanded_nodes_sum"] += int(expanded_nodes_str)

    return coverage_data

def save_coverage(output_file, coverage_data):
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        # Add a new column for avg_expanded_nodes
        writer.writerow(["domain", "experiment_name", "coverage", "avg_solution_size", "avg_expanded_nodes"])

        for domain, experiments in coverage_data.items():
            for experiment_name, data in experiments.items():
                coverage = data["count"]
                if coverage > 0:
                    avg_solution_size = data["solution_size_sum"] / coverage
                    avg_expanded_nodes = data["expanded_nodes_sum"] / coverage
                else:
                    avg_solution_size = 0
                    avg_expanded_nodes = 0

                writer.writerow([
                    domain, 
                    experiment_name, 
                    coverage, 
                    f"{avg_solution_size:.2f}", 
                    f"{avg_expanded_nodes:.2f}"
                ])

def main():
    args = parse_arguments()

    # Validate input file
    if not os.path.isfile(args.input_file):
        print(f"Error: The specified input file does not exist: {args.input_file}")
        return

    # Calculate coverage
    coverage_data = calculate_coverage(args.input_file)

    # Save coverage to output file
    save_coverage(args.output_file, coverage_data)
    print(f"Coverage data has been saved to: {args.output_file}")

if __name__ == "__main__":
    main()
