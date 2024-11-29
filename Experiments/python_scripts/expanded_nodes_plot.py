import argparse
import csv
import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate a PDF plot comparing expanded nodes between two experiments.")
    parser.add_argument("--input_file", required=True, help="Path to the input CSV file.")
    parser.add_argument("--e_x", required=True, help="Name of the experiment to use as the x-axis.")
    parser.add_argument("--e_y", required=True, help="Name of the experiment to use as the y-axis.")
    parser.add_argument("--output_file", required=True, help="Path to the output PDF file.")
    return parser.parse_args()

def load_data(input_file, experiment_x, experiment_y):
    data = []

    with open(input_file, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            print(row)
            domain = row["domain_name"].strip()
            problem = row["problem_name"].strip()
            experiment_name = row["experiment_name"].strip()
            expanded_nodes = row["expanded_nodes"].strip()

            if expanded_nodes.lower() == "inf" or expanded_nodes == "":
                expanded_nodes = float('inf')  # Treat "inf" and empty as infinity
            else:
                print(expanded_nodes)
                expanded_nodes = float(expanded_nodes)
                print(expanded_nodes)

            data.append({
                "domain": domain,
                "problem": problem,
                "experiment_name": experiment_name,
                "expanded_nodes": expanded_nodes
            })

    df = pd.DataFrame(data)
    pivot_df = df.pivot(index=["domain", "problem"], columns="experiment_name", values="expanded_nodes")

    
    max_x = pivot_df[experiment_x].replace([float('inf')], np.nan).max()
    max_y = pivot_df[experiment_y].replace([float('inf')], np.nan).max()

    placeholder_value = max(max_x, max_y) + 1

    pivot_df = pivot_df.fillna(placeholder_value)
    pivot_df = pivot_df.replace([float('inf')], placeholder_value)

    filtered_df = pivot_df[[experiment_x, experiment_y]].reset_index()

    return filtered_df, placeholder_value

def plot_expanded_nodes(data, experiment_x, experiment_y, output_file, placeholder_value):
    plt.figure(figsize=(10, 8))

    sns.scatterplot(
        data=data,
        x=experiment_x,
        y=experiment_y,
        hue="domain",
        palette="tab10",
        s=100,
        edgecolor="w",
        alpha=0.7
    )

    
    plt.xscale('log')
    plt.yscale('log')

    
    max_value = data[[experiment_x, experiment_y]].max().max()
    plt.xlim(1, max_value + 1)
    plt.ylim(1, max_value + 1)

    
    plt.plot([1, max_value + 1], [1, max_value + 1], ls='--', color='red', label="x = y")
    plt.xlabel(f"{experiment_x}")
    plt.ylabel(f"{experiment_y}")
    plt.title(f"Expanded Nodes Between {experiment_x} vs {experiment_y}")
    plt.legend(title="Domain", bbox_to_anchor=(1.05, 1), loc='upper left')
    #plt.grid(False, which="both", linestyle="--", linewidth=0.5)
    plt.tight_layout()

    plt.savefig(output_file, format="pdf")
    plt.close()



def main():
    args = parse_arguments()

    if not os.path.isfile(args.input_file):
        print(f"Error: The specified input file does not exist: {args.input_file}")
        return

    # Unpack the returned values
    data, placeholder_value = load_data(args.input_file, args.e_x, args.e_y)

    # Pass the placeholder_value to plot_expanded_nodes
    plot_expanded_nodes(data, args.e_x, args.e_y, args.output_file, placeholder_value)

    print(f"Plot has been saved to: {args.output_file}")

if __name__ == "__main__":
    main()

# Example Usage:
# python3 expanded_nodes_plot.py --input_file input.csv --e_x LMCOUNT --e_y NOVELTY --output_file output.pdf
#
# Explanation:
# This command will take 'input.csv' as the input file and create a scatter plot comparing the number of expanded nodes for two experiments: 'LMCOUNT' and 'NOVELTY'.
# The x-axis will represent the 'LMCOUNT' experiment, and the y-axis will represent the 'NOVELTY' experiment.
# Each point on the scatter plot represents a problem, and the points are colored by the domain they belong to.
# The output is saved as a PDF file named 'output.pdf'.
