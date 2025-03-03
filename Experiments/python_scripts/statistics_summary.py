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
    # - "nodes_per_second_sum": sum of nodes per second for solved problems
    coverage_data = defaultdict(
        lambda: defaultdict(lambda: {
            "total": 0, 
            "count": 0, 
            "solution_size_sum": 0, 
            "expanded_nodes_sum": 0,
            "nodes_per_second_sum": 0
        })
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
            nodes_per_second_str = row.get("nodes_per_second", "").strip()

            # Increment the total number of problems regardless of whether it's solved.
            coverage_data[domain][experiment_name]["total"] += 1

            # Only count as a solved problem if solution_size is provided.
            if solution_size_str:
                coverage_data[domain][experiment_name]["count"] += 1
                coverage_data[domain][experiment_name]["solution_size_sum"] += int(solution_size_str)
                if expanded_nodes_str:
                    coverage_data[domain][experiment_name]["expanded_nodes_sum"] += int(expanded_nodes_str)
                if nodes_per_second_str:
                    coverage_data[domain][experiment_name]["nodes_per_second_sum"] += float(nodes_per_second_str)

    return coverage_data

def save_coverage(output_file, coverage_data):
    # Aggregated totals across domains for each experiment.
    totals = defaultdict(lambda: {
        "total": 0, 
        "count": 0, 
        "solution_size_sum": 0, 
        "expanded_nodes_sum": 0,
        "nodes_per_second_sum": 0
    })
    
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        # Write header row including the "total_problems" and "avg_nodes_per_second" columns.
        writer.writerow([
            "domain", 
            "experiment_name", 
            "total_problems", 
            "coverage", 
            "avg_solution_size", 
            "avg_expanded_nodes",
            "avg_nodes_per_second"
        ])

        # Write rows for each domain and accumulate totals.
        for domain, experiments in coverage_data.items():
            # For this domain, use the maximum total number of problems across experiments.
            domain_max_total = max(data["total"] for data in experiments.values())
            
            for experiment_name, data in experiments.items():
                solved = data["count"]
                if solved > 0:
                    avg_solution_size = data["solution_size_sum"] / solved
                    avg_expanded_nodes = data["expanded_nodes_sum"] / solved
                    avg_nodes_per_second = data["nodes_per_second_sum"] / solved
                else:
                    avg_solution_size = 0
                    avg_expanded_nodes = 0
                    avg_nodes_per_second = 0

                writer.writerow([
                    domain, 
                    experiment_name, 
                    domain_max_total,
                    solved, 
                    f"{avg_solution_size:.2f}", 
                    f"{avg_expanded_nodes:.2f}",
                    f"{avg_nodes_per_second:.2f}"
                ])

                # Aggregate totals for each experiment name.
                totals[experiment_name]["total"] += data["total"]
                totals[experiment_name]["count"] += solved
                totals[experiment_name]["solution_size_sum"] += data["solution_size_sum"]
                totals[experiment_name]["expanded_nodes_sum"] += data["expanded_nodes_sum"]
                totals[experiment_name]["nodes_per_second_sum"] += data["nodes_per_second_sum"]

        # Write aggregated total rows for each experiment name.
        for experiment_name, data in totals.items():
            solved = data["count"]
            if solved > 0:
                avg_solution_size = data["solution_size_sum"] / solved
                avg_expanded_nodes = data["expanded_nodes_sum"] / solved
                avg_nodes_per_second = data["nodes_per_second_sum"] / solved
            else:
                avg_solution_size = 0
                avg_expanded_nodes = 0
                avg_nodes_per_second = 0

            writer.writerow([
                "Total", 
                experiment_name, 
                data["total"],
                solved, 
                f"{avg_solution_size:.2f}", 
                f"{avg_expanded_nodes:.2f}",
                f"{avg_nodes_per_second:.2f}"
            ])

def main():
    args = parse_arguments()

    if not os.path.isfile(args.input_file):
        print(f"Error: The specified input file does not exist: {args.input_file}")
        return

    coverage_data = calculate_coverage(args.input_file)
    save_coverage(args.output_file, coverage_data)
    print(f"Coverage data has been saved to: {args.output_file}")

if __name__ == "__main__":
    main()
