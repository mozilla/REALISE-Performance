import os
import pandas as pd

def process_folder(folder):
    global results
    folder_path = input_folder + '/' + folder
    for signature_file in os.listdir(folder_path):
        try:
            # Read the CSV file
            file_path = folder_path + '/' + signature_file
            df = pd.read_csv(file_path, index_col=False)
            
            if 'alert_status_general' in df.columns:
                counts = df['alert_status_general'].value_counts()
                # Add counts for all categories, defaulting to 0 for missing categories
                results.append({
                    'file_name': signature_file,
                    'TN': counts.get('TN', 0),
                    'TP': counts.get('TP', 0),
                    'FP': counts.get('FP', 0),
                    'FN': counts.get('FN', 0),
                    'SP': counts.get('SP', 0)
                })
            else:
                print(f"'alert_status_general' column not found in {signature_file}")
        
        except Exception as e:
            print(f"Error processing file {signature_file} in folder {folder}: {e}")

# Input folder path
input_folder = '../datasets-original-annotated-2-aggregated'

# Mapping of projects to their folders
projects_folders_mapping = {
    "autoland": ["autoland1", "autoland2", "autoland3", "autoland4"],
    "firefox-android": ["firefox-android"],
    "mozilla-beta": ["mozilla-beta"]
}

# "firefox-android": ["firefox-android"],

# Initialize the results list
results = []

# Loop through projects and their folders
for project in projects_folders_mapping:
    for folder in projects_folders_mapping[project]:
        process_folder(folder)

# Convert results to a DataFrame
results_df = pd.DataFrame(results)

# Add columns for metrics
# Save the DataFrame to a CSV file (optional)
# def calculate_metrics(row, treat_sp_as_tp):
#     """
#     Calculate Precision, Recall, and F1 Score.
#     """
#     tp = row['TP'] + (row['SP'] if treat_sp_as_tp else 0)
#     fp = row['FP']
#     fn = row['FN']
#     precision = tp / (tp + fp) if (tp + fp) > 0 else 0
#     recall = tp / (tp + fn) if (tp + fn) > 0 else 0
#     f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
#     return precision, recall, f1
# results_df[['Precision_SP_as_TP', 'Recall_SP_as_TP', 'F1_Score_SP_as_TP']] = results_df.apply(
#     lambda row: calculate_metrics(row, treat_sp_as_tp=True), axis=1, result_type='expand'
# )
# results_df[['Precision_SP_as_FP', 'Recall_SP_as_FP', 'F1_Score_SP_as_FP']] = results_df.apply(
#     lambda row: calculate_metrics(row, treat_sp_as_tp=False), axis=1, result_type='expand'
# )

# Save the DataFrame to a CSV file (optional)
results_df.to_csv('../summarized_CSVs/alert_status_summary_4.csv', index=False)