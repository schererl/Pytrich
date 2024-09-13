import pandas as pd
import os
import directories
import parse_log

def create_data_frames(log_files_path):
    """Creates DataFrames from the parsed log data using the ParseLog class."""
    parser = parse_log.ParseLog(log_files_path)
    parser()  # Parse the logs

    # Create a DataFrame with the parsed data
    log_data_df = pd.DataFrame({
        'heuristic name': parser.heuristic_names,
        'domain': parser.domains,
        'problem': parser.problems,
        'heuristic elapsed time': parser.heuristics_elapsed_time,
        'total landmarks': parser.total_landmarks,
        'task landmarks': parser.task_landmarks,
        'method landmarks': parser.method_landmarks,
        'fact landmarks': parser.fact_landmarks,
        'min-cov disjunctions': parser.mincov_disj_landmarks,
        'elapsed time for disjunctions': parser.mincov_disj_elapsed_time,
        'solution size': parser.solution_sizes,
        'expanded nodes': parser.expanded_nodes,
        'elapsed time from search': parser.search_elapsed_time
    })
    print(log_data_df)
    return log_data_df

def generate_and_save_tables(log_data_df):
    """Generates and saves comparison tables to CSV files."""
    # Total landmarks summary
    total_landmarks_summary = log_data_df.pivot_table(
        index='domain',
        columns='heuristic name',
        values='total landmarks',
        aggfunc='sum'
    )

    # Average elapsed time summary
    avg_elapsed_time_summary = log_data_df.pivot_table(
        index='domain',
        columns='heuristic name',
        values='heuristic elapsed time',
        aggfunc='mean'
    )

    # Problem count summary
    problem_count_summary = log_data_df.pivot_table(
        index='domain',
        columns='heuristic name',
        values='problem',
        aggfunc='count'
    )

    total_landmarks_summary.to_csv(directories.CSV_DIR + OUTPUT_TOTAL_LMS_SUMMARY)
    avg_elapsed_time_summary.to_csv(directories.CSV_DIR + OUTPUT_ELAPSEDTIME_LMS_SUMMARY)
    problem_count_summary.to_csv(directories.CSV_DIR + OUTPUT_LMSGEN_COVERAGE)

    print(f'COVERAGE:\n{problem_count_summary}')
    print(f'LANDMARK GENERATION:\n{total_landmarks_summary}')
    print(f'AVERAGE ELAPSED TIME:\n{avg_elapsed_time_summary}')

def save_filtered_intersection_data(log_data_df):
    """Filters the log data to only include problems where both heuristics solved them."""
    coverage_df = log_data_df.pivot_table(
        index=['domain', 'problem'],
        columns='heuristic name',
        values='total landmarks',
        aggfunc='count'
    )

    intersection_problems = coverage_df.dropna().index
    log_data_df_intersection = log_data_df[log_data_df.set_index(['domain', 'problem']).index.isin(intersection_problems)].reset_index(drop=True)
    log_data_df_intersection.to_csv(directories.CSV_DIR + OUTPUT_LMS, index=False)

    return log_data_df_intersection

def check_csv_exists():
    """Check if CSV files already exist and prompt the user for confirmation."""
    csv_files = ['total_landmarks_summary.csv', 'avg_elapsed_time_summary.csv', 'problem_count_summary.csv', 'filtered_landmarks_intersection.csv']
    for csv_file in csv_files:
        if os.path.exists(directories.CSV_DIR + csv_file):
            response = input(f"{csv_file} already exists. Do you want to overwrite it? (y/n): ").lower()
            if response != 'y':
                print(f"Skipping file: {csv_file}")
                return False
    return True

def main(log_files_path):
    if check_csv_exists():
        log_data_df = create_data_frames(log_files_path)
        generate_and_save_tables(log_data_df)
        log_data_df_intersection = save_filtered_intersection_data(log_data_df)
        print("Filtered data saved successfully.")

# Define log files and directories
LOG_FILES = ['blocksworld-logfile.log']
OUTPUT_LMS = 'landmarks_file.csv'
OUTPUT_TOTAL_LMS_SUMMARY = 'total_landmarks_summary.csv'
OUTPUT_ELAPSEDTIME_LMS_SUMMARY = 'avg_elapsed_time_summary.CSV'
OUTPUT_LMSGEN_COVERAGE = 'lms_coverage_summary.csv'
main([directories.LOG_DIR + fl for fl in LOG_FILES])
