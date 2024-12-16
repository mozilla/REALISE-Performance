import os
import pandas as pd

def find_multiple_fn_alerts_in_file(parent_folder, alert_status_column, alert_id_column):
    alert_ids_with_multiple_fn = {}

    # Walk through all files and directories within the parent folder
    for root, dirs, files in os.walk(parent_folder):
        for filename in files:
            # Process only CSV files
            if filename.endswith('.csv'):
                file_path = os.path.join(root, filename)
                
                # Read the CSV file
                try:
                    df = pd.read_csv(file_path)
                    
                    # Group by alert_id
                    for alert_id, group in df.groupby(alert_id_column):
                        # Check if there's an 'FN' in alert_status and more than one entry for this alert_id
                        if 'FN' in group[alert_status_column].values and len(group) > 1:
                            if file_path not in alert_ids_with_multiple_fn:
                                alert_ids_with_multiple_fn[file_path] = []
                            alert_ids_with_multiple_fn[file_path].append(alert_id)
                
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return alert_ids_with_multiple_fn

# Set the path of the parent folder and column names
parent_folder = 'project1/datasets-refined-status'
alert_status_column = 'alert_status'
alert_id_column = 'alert_id'

# Find alert_ids with multiple 'FN' entries in each file
alerts_with_multiple_fn = find_multiple_fn_alerts_in_file(parent_folder, alert_status_column, alert_id_column)

# Print the results
for file, alert_ids in alerts_with_multiple_fn.items():
    print(f"In file '{file}', alert_ids with 'FN' and multiple entries: {alert_ids}")
