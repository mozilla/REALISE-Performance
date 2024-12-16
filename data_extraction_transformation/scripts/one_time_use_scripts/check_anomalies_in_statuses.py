import os
import pandas as pd
problematic_alert_summary_ids =  [47, 38368, 38585, 38609, 38763, 38778, 38813, 38828, 38976, 39052, 39165, 39406, 39482, 39977, 40189, 40336, 40347, 40367, 40386, 40435, 40458, 40491, 40538, 40705, 40762, 40800, 40861, 40927, 40992, 41013, 41014, 41033, 41112, 41123, 41174, 41586, 41689, 41815, 42233]


def check_inconsistent_alerts(parent_folder, alert_status_column, alert_id_column):
    inconsistent_alerts = []
    
    # Walk through all files and directories within the parent folder
    for root, dirs, files in os.walk(parent_folder):
        for filename in files:
            # Process only CSV files
            if filename.endswith('.csv'):
                file_path = os.path.join(root, filename)
                
                # Read the CSV file
                try:
                    df = pd.read_csv(file_path)
                    
                    # Filter out rows where 'alert_status' is 'TN' or NaN
                    # filtered_df = df[(df[alert_status_column] != 'TN') & (df[alert_status_column].notna())]
                    filtered_df = df
                    # Check for rows with the same alert_id but different alert_status
                    duplicates = filtered_df.groupby(alert_id_column)[alert_status_column].nunique()
                    inconsistent_alerts_in_file = duplicates[duplicates > 1].index.tolist()
                    
                    if inconsistent_alerts_in_file:
                        inconsistent_alerts.append({
                            'file': filename,
                            'alert_ids': inconsistent_alerts_in_file
                        })
                
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return inconsistent_alerts

# Set the path of the parent folder and the column names
parent_folder = 'project1/datasets-refined-status'
alert_status_column = 'alert_status'
alert_id_column = 'alert_id'

# Find inconsistent alerts across all CSV files
inconsistent_alerts = check_inconsistent_alerts(parent_folder, alert_status_column, alert_id_column)

# Print inconsistent alerts
if inconsistent_alerts:
    print("Files with inconsistent alert statuses for the same alert_id:")
    for item in inconsistent_alerts:
        print(f"File: {item['file']}, Alert IDs with inconsistencies: {item['alert_ids']}")
else:
    print("No inconsistencies found in alert statuses for the same alert_id across all files.")
