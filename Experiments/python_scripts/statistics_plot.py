import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Plot coverage and average expanded nodes by domain (x-axis) with experiments as bars."
    )
    parser.add_argument("-i", "--input_file", required=True, help="Path to the input CSV file.")
    parser.add_argument("-o", "--output_prefix", default="plot", 
                        help="Prefix for output plot files. (Default: 'plot')")
    return parser.parse_args()

def main():
    args = parse_arguments()

    # Read the CSV file into a pandas DataFrame.
    df = pd.read_csv(args.input_file)

    # Check for required columns.
    required_columns = ["domain", "experiment_name", "total_problems", "coverage", "avg_solution_size", "avg_expanded_nodes"]
    for col in required_columns:
        if col not in df.columns:
            print(f"Error: Required column '{col}' not found in the CSV file.")
            return

    # Filter out the aggregated "Total" row.
    df = df[df["domain"].str.lower() != "total"]

    # Set a seaborn style.
    sns.set(style="whitegrid")

    # ---------------------
    # Plot 1: Coverage per Domain with each Experiment as a Bar
    # ---------------------
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(data=df, x="domain", y="coverage", hue="experiment_name")
    plt.title("Coverage by Domain and Experiment")
    plt.xlabel("Domain")
    plt.ylabel("Coverage (Solved Problems)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    coverage_plot_file = f"{args.output_prefix}_coverage.png"
    plt.savefig(coverage_plot_file)
    plt.close()

    # ---------------------
    # Plot 2: Average Expanded Nodes per Domain with each Experiment as a Bar
    # ---------------------
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(data=df, x="domain", y="avg_expanded_nodes", hue="experiment_name")
    plt.title("Average Expanded Nodes by Domain and Experiment")
    plt.xlabel("Domain")
    plt.ylabel("Avg. Expanded Nodes")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    expanded_plot_file = f"{args.output_prefix}_expanded_nodes.png"
    plt.savefig(expanded_plot_file)
    plt.close()

    print("Plots saved as:")
    print(f"  {coverage_plot_file}")
    print(f"  {expanded_plot_file}")

if __name__ == "__main__":
    main()
