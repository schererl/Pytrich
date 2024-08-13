import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV file
file_path = 'filtered_parsed_log_data.csv'
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

# Calculate min and max for a correct diagonal line in log scale
min_value = min(df_merged['expanded nodes_classical'].min(), df_merged['expanded nodes_bidirectional'].min())
max_value = max(df_merged['expanded nodes_classical'].max(), df_merged['expanded nodes_bidirectional'].max())

# Plot the data with the corrected main diagonal and log scale
plt.figure(figsize=(10, 8))
for domain in df_merged['domain'].unique():
    df_domain = df_merged[df_merged['domain'] == domain]
    plt.scatter(df_domain['expanded nodes_classical'], df_domain['expanded nodes_bidirectional'], label=domain)

# Plot the main diagonal
plt.plot([min_value, max_value], [min_value, max_value], 'r--', label='Main Diagonal')

# Set log scale for both axes
plt.xscale('log')
plt.yscale('log')

# Set labels and title
plt.xlabel('Expanded Nodes - Classical Landmarks (Log Scale)')
plt.ylabel('Expanded Nodes - Bidirectional Landmarks (Log Scale)')
plt.title('Comparison of Expanded Nodes: Classical vs Bidirectional Landmarks (Log Scale)')
plt.legend(title='Domain')
plt.show()
