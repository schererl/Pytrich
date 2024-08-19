import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the CSV file
file_path = 'filtered_expnodes.csv'
df = pd.read_csv(file_path)

# Filter out rows where either algorithm did not have expanded nodes
df_filtered = df.dropna(subset=['expanded nodes'])

# Separate data for classical and bidirectional landmarks
df_classical = df_filtered[df_filtered['heuristic name'] == 'Classical Landmarks']
df_bidirectional = df_filtered[df_filtered['heuristic name'] == 'Bidirectional Landmarks']

# Merge the data on domain and problem to ensure both algorithms have results for the same problem
df_merged = pd.merge(
    df_classical[['domain', 'problem', 'expanded nodes']],
    df_bidirectional[['domain', 'problem', 'expanded nodes']],
    on=['domain', 'problem'],
    suffixes=('_classical', '_bidirectional')
)

# Exclude specific domains
excluded_domains = ['hiking', 'minecraft', 'rover', 'snake', 'towers']
df_merged = df_merged[~df_merged['domain'].isin(excluded_domains)]

# Calculate min and max for a correct diagonal line in log scale
min_value = min(df_merged['expanded nodes_classical'].min(), df_merged['expanded nodes_bidirectional'].min())
max_value = max(df_merged['expanded nodes_classical'].max(), df_merged['expanded nodes_bidirectional'].max())

# Define a list of markers to use for each domain
markers = ['o', 's', 'D', '^', 'v', 'p', '*', 'H', 'X', 'P', 'd', '<', '>']

# Plot the data with the corrected main diagonal and log scale
plt.figure(figsize=(14, 8))

# Loop over each domain and use different markers and colors
for i, domain in enumerate(df_merged['domain'].unique()):
    df_domain = df_merged[df_merged['domain'] == domain]
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

# Show the plot
plt.tight_layout()  # Adjust layout to accommodate the legend outside the plot
plt.show()
