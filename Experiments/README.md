# Scripts Folder
### Experiments

- **LandmarkGenerationExperiment.sh**: Compares the efficiency of landmark generation methods.
- **LandmarkSearchExperiment.sh**: Compares landmarks during search.
- **TOReachabilityExperiment.sh**: Runs experiments related to the total-order reachability grounder (TOR).

### Data Processing Scripts

- **parse_log.py**: Parse Pytrich logs.
- **landmarks_data_processor.py**: Parses log files from the landmark generation experiment, generates CSV files with the results, ensures necessary directories exist, and outputs informative messages.
- **tor_data_processor.py**: Parses log files from the total-order reachability grounder (TOR) experiment, generates CSV files and plots with the results, ensures necessary directories exist, and outputs informative messages.
- **expnodes_plot.py**: Reads a CSV file processed from the landmark search experiment and plots a comparison of the number of expanded nodes between different methods, saving the plot into the appropriate directory.