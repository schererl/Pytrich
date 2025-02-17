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
    # For each domain and experiment we now track:
    # - "total": total number of problems (solved and unsolved)
    # - "count": number of solved problems (solution_size is not empty)
    # - "solution_size_sum": sum of solution sizes for solved problems
    # - "expanded_nodes_sum": sum of expanded nodes for solved problems
    coverage_data = defaultdict(
        lambda: defaultdict(lambda: {"total": 0, "count": 0, "solution_size_sum": 0, "expanded_nodes_sum": 0})
    )

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

            # Increment the total number of problems regardless of whether it's solved.
            coverage_data[domain][experiment_name]["total"] += 1

            # Only count as a solved problem if solution_size is provided.
            if solution_size_str:
                coverage_data[domain][experiment_name]["count"] += 1
                coverage_data[domain][experiment_name]["solution_size_sum"] += int(solution_size_str)
                if expanded_nodes_str:
                    coverage_data[domain][experiment_name]["expanded_nodes_sum"] += int(expanded_nodes_str)

    return coverage_data

def save_coverage(output_file, coverage_data):
    # Aggregated totals across domains for each experiment.
    totals = defaultdict(lambda: {"total": 0, "count": 0, "solution_size_sum": 0, "expanded_nodes_sum": 0})
    
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        # Write header row including the "total_problems" column.
        writer.writerow(["domain", "experiment_name", "total_problems", "coverage", "avg_solution_size", "avg_expanded_nodes"])

        # Write rows for each domain and accumulate totals.
        for domain, experiments in coverage_data.items():
            # For this domain, compute the maximum total (i.e. total number of problems)
            domain_max_total = max(data["total"] for data in experiments.values())
            
            for experiment_name, data in experiments.items():
                coverage = data["count"]
                if coverage > 0:
                    avg_solution_size = data["solution_size_sum"] / coverage
                    avg_expanded_nodes = data["expanded_nodes_sum"] / coverage
                else:
                    avg_solution_size = 0
                    avg_expanded_nodes = 0

                # Use the maximum total problems for every row of the same domain.
                writer.writerow([
                    domain, 
                    experiment_name, 
                    domain_max_total,
                    coverage, 
                    f"{avg_solution_size:.2f}", 
                    f"{avg_expanded_nodes:.2f}"
                ])

                # Aggregate totals for each experiment name.
                totals[experiment_name]["total"] += data["total"]
                totals[experiment_name]["count"] += data["count"]
                totals[experiment_name]["solution_size_sum"] += data["solution_size_sum"]
                totals[experiment_name]["expanded_nodes_sum"] += data["expanded_nodes_sum"]

        # Write aggregated total rows for each experiment name.
        for experiment_name, data in totals.items():
            coverage = data["count"]
            if coverage > 0:
                avg_solution_size = data["solution_size_sum"] / coverage
                avg_expanded_nodes = data["expanded_nodes_sum"] / coverage
            else:
                avg_solution_size = 0
                avg_expanded_nodes = 0

            writer.writerow([
                "Total", 
                experiment_name, 
                data["total"],
                coverage, 
                f"{avg_solution_size:.2f}", 
                f"{avg_expanded_nodes:.2f}"
            ])

def main():
    args = parse_arguments()

    # Validate input file.
    if not os.path.isfile(args.input_file):
        print(f"Error: The specified input file does not exist: {args.input_file}")
        return

    # Calculate coverage.
    coverage_data = calculate_coverage(args.input_file)

    # Save coverage to output file.
    save_coverage(args.output_file, coverage_data)
    print(f"Coverage data has been saved to: {args.output_file}")

if __name__ == "__main__":
    main()
