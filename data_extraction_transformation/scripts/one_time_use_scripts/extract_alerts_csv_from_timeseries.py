import os
import pandas as pd
import shutil
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Script to cross-reference the data of the time series with the alerts data")
    parser.add_argument('-i', '--input-folder', required=True, help="Path to the input dataset folder")
    parser.add_argument('-o', '--output-folder', required=True, help="Path of the folder outputting the alert CSV file")
    return parser.parse_args()

def process_folder(input_folder, folder, columns_to_be_kept):
    # Create an empty list to store the data from all CSV files
    all_data = []
    eligible_summary_status = ["TP", "FP", "SP", "FN"]
    # Iterate over each file in the folder
    for signature_file in os.listdir(input_folder + '/' + folder):
        # Construct the full path of the current file
        file_path = os.path.join(input_folder, folder, signature_file)
        
        if file_path.endswith('.csv'):
            # Read the CSV file into a DataFrame
            df = pd.read_csv(file_path, index_col=False)
            df = df[df['alert_summary_status_general'].isin(eligible_summary_status)]
            df['push_timestamp'] = pd.to_datetime(df['push_timestamp'])

            # Filter the dataframe to keep only the required columns
            df_filtered = df[columns_to_be_kept]
            df = df.drop_duplicates()

            # Append the filtered data to the list
            all_data.append(df_filtered)
    
    # Return all the dataframes concatenated into one
    return pd.concat(all_data, ignore_index=True)

def main():
    args = parse_args()
    input_folder = args.input_folder
    output_folder = args.output_folder

    # Define the columns that you want to keep in the final dataframe
    columns_to_be_kept = [
        'single_alert_new_value', 'single_alert_classifier', 'alert_summary_prev_push_revision', 'alert_summary_id', 'single_alert_amount_pct', 
        'alert_summary_performance_tags', 'single_alert_prev_value', 'alert_summary_first_triaged', 'single_alert_series_signature_has_subtests', 
        'alert_summary_framework', 'single_alert_series_signature_framework_id', 'single_alert_series_signature_suite_public_name', 
        'alert_summary_related_alerts', 'single_alert_taskcluster_metadata_retry_id', 'alert_summary_prev_push_id', 'alert_summary_status', 
        'alert_summary_push_id', 'single_alert_status', 'alert_summary_assignee_username', 'single_alert_series_signature_signature_hash', 
        'single_alert_prev_taskcluster_metadata_task_id', 'single_alert_series_signature_machine_platform', 'alert_summary_bug_number', 
        'alert_summary_repository', 'alert_summary_bug_due_date', 'single_alert_series_signature_test_public_name', 'alert_summary_issue_tracker', 
        'single_alert_amount_abs', 'single_alert_id', 'single_alert_series_signature_measurement_unit', 'single_alert_taskcluster_metadata_task_id', 
        'single_alert_backfill_record_total_backfills_successful', 'alert_summary_id', 'single_alert_series_signature_option_collection_hash', 
        'single_alert_prev_taskcluster_metadata_retry_id', 'single_alert_is_regression', 'single_alert_manually_created', 'single_alert_classifier_email', 
        'single_alert_backfill_record_total_backfills_failed', 'single_alert_backfill_record_total_actions_triggered', 'alert_summary_assignee_email', 
        'alert_summary_creation_timestamp', 'single_alert_prev_profile_url', 'alert_summary_notes', 'single_alert_series_signature_test', 
        'single_alert_noise_profile', 'single_alert_series_signature_lower_is_better', 'alert_summary_revision', 'single_alert_related_summary_id', 
        'alert_summary_bug_updated', 'single_alert_profile_url', 'single_alert_backfill_record_context', 'single_alert_starred', 
        'single_alert_backfill_record_total_backfills_in_progress', 'single_alert_t_value', 'single_alert_series_signature_suite', 
        'single_alert_series_signature_extra_options', 'single_alert_backfill_record_status', 'single_alert_series_signature_tags', 
        'alert_summary_triage_due_date', 'push_timestamp', 'signature_id'
    ]

    # Mapping of projects to folders
    projects_folders_mapping = {
        "autoland": ["autoland1", "autoland2", "autoland3", "autoland4"], 
        "firefox-android": ["firefox-android"], 
        "mozilla-beta": ["mozilla-beta"],
        "mozilla-central": ["mozilla-central"],
        "mozilla-release": ["mozilla-release"]
    }

    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Create an empty list to store all the dataframes
    all_data = []

    # Process each folder for each project
    for project in projects_folders_mapping:
        for folder in projects_folders_mapping[project]:
            # Process files in the current project folder and get the combined dataframe
            folder_data = process_folder(input_folder, folder, columns_to_be_kept)
            
            # Append the result to the list of all data
            all_data.append(folder_data)

    # Concatenate all dataframes into one final dataframe
    final_df = pd.concat(all_data, ignore_index=True)
    # final_df = final_df.rename(columns={
    #     'push_timestamp': 'alert_summary_push_timestamp',
    #     'signature_id': 'single_alert_series_signature_id'
    # })
    final_df = final_df.drop_duplicates()

    output_file = os.path.join(output_folder, "curated_alerts_data.csv")

    final_df.to_csv(output_file, index=False)
    print(f"All data saved to {output_file}")

if __name__ == "__main__":
    main()
