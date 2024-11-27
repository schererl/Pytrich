import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def create_plot(df, plot_dir):
    """Create and save a scatter plot comparing expanded nodes between Classical and Bidirectional Landmarks."""
    # Exclude specific domains
    excluded_domains = ['Transport', 'Hiking', 'Minecraft-Regular', 'Rover-GTOHP', 'Snake', 'Towers']
    df = df[~df['domain'].isin(excluded_domains)]
    
    # Check if the dataframe is empty after exclusion
    if df.empty:
        print("No data to plot after excluding domains.")
        return
    
    # Calculate min and max for a correct diagonal line in log scale
    min_value = min(df['expanded nodes_classical'].min(), df['expanded nodes_bidirectional'].min())
    max_value = max(df['expanded nodes_classical'].max(), df['expanded nodes_bidirectional'].max())
    
    # Define a list of markers to use for each domain
    markers = ['o', 's', 'D', '^', 'v', 'p', '*', 'H', 'X', 'P', 'd', '<', '>']
    
    # Plot the data with the corrected main diagonal and log scale
    plt.figure(figsize=(14, 8))
    
    # Loop over each domain and use different markers and colors
    for i, domain in enumerate(df['domain'].unique()):
        df_domain = df[df['domain'] == domain]
        plt.scatter(
            df_domain['expanded nodes_classical'], 
            df_domain['expanded nodes_bidirectional'], 
            label=domain, 
            marker=markers[i % len(markers)]
        )
    
    # Plot the main diagonal
    plt.plot([min_value, max_value], [min_value, max_value], 'r--', label='Main Diagonal')
    
    # Set log scale for both axes
    plt.xscale('log')
    plt.yscale('log')
    
    # Set labels and title with increased font size
    plt.xlabel('Bottom-up Landmarks', fontsize=14)
    plt.ylabel('Bidirectional Landmarks', fontsize=14)
    plt.title('GBFS Expanded Nodes: Bottom-up vs Bidirectional (Log Scale)', fontsize=16)
    
    # Adjust legend font size, reduce its size, and move it outside the plot
    plt.legend(title='Domain', fontsize=10, title_fontsize=12, bbox_to_anchor=(1.05, 1), loc='upper left', ncol=2)
    
    # Adjust layout to accommodate the legend outside the plot
    plt.tight_layout()
    
    # Define plot file path
    plot_file_path = os.path.join(plot_dir, 'gbfs_expanded_nodes.png')
    
    # Check if plot file already exists
    if os.path.exists(plot_file_path):
        response = input(f"{plot_file_path} already exists. Do you want to overwrite it? (y/n): ").lower()
        if response != 'y':
            print(f"Skipping plot generation.")
            plt.close()
            return
    
    # Save the plot
    plt.savefig(plot_file_path)
    print(f"Plot saved to {plot_file_path}")
    
    # Close the plot to free up memory
    plt.close()

def main():
    """Main function to load data, process it, and generate the plot."""
    # Define local variables for directories
    csv_dir = os.path.join('HTN', 'csv-files')
    plot_dir = os.path.join('HTN', 'plot-files')
    
    # Ensure the CSV directory exists
    if not os.path.exists(csv_dir):
        print(f"Creating CSV directory at {csv_dir}")
        os.makedirs(csv_dir, exist_ok=True)
    else:
        print(f"CSV directory exists at {csv_dir}")
    
    # Ensure the Plot directory exists
    if not os.path.exists(plot_dir):
        print(f"Creating plot directory at {plot_dir}")
        os.makedirs(plot_dir, exist_ok=True)
    else:
        print(f"Plot directory exists at {plot_dir}")
    
    # Define the CSV file path
    csv_file = os.path.join(csv_dir, 'filtered_expnodes.csv')
    
    # Check if the CSV file exists
    if not os.path.exists(csv_file):
        print(f"CSV file {csv_file} does not exist.")
        return
    
    # Load the CSV file
    df = pd.read_csv(csv_file)
    
    # Filter out rows where 'expanded nodes' is NaN
    df_filtered = df.dropna(subset=['expanded nodes'])
    
    # Separate data for Classical and Bidirectional Landmarks
    df_classical = df_filtered[df_filtered['heuristic name'] == 'Classical Landmarks']
    df_bidirectional = df_filtered[df_filtered['heuristic name'] == 'Bidirectional Landmarks']
    
    # Merge the data on 'domain' and 'problem' to ensure both heuristics have results for the same problem
    df_merged = pd.merge(
        df_classical[['domain', 'problem', 'expanded nodes']],
        df_bidirectional[['domain', 'problem', 'expanded nodes']],
        on=['domain', 'problem'],
        suffixes=('_classical', '_bidirectional')
    )
    
    # Check if the merged dataframe is empty
    if df_merged.empty:
        print("No matching data found between Classical and Bidirectional Landmarks.")
        return
    
    # Create the plot
    create_plot(df_merged, plot_dir)
    
if __name__ == "__main__":
    main()
