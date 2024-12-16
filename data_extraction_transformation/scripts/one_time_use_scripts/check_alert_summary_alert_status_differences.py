import os
import pandas as pd

def find_files_with_fn_mismatch(parent_folder, alert_status_column, test_status_column):
    files_with_fn_mismatch = []

    # Walk through all files and directories within the parent folder
    for root, dirs, files in os.walk(parent_folder):
        for filename in files:
            # Process only CSV files
            if filename.endswith('.csv'):
                file_path = os.path.join(root, filename)
                
                # Read the CSV file
                try:
                    df = pd.read_csv(file_path)
                    
                    # Check if there are rows with 'FN' in alert_status and a different value in test_status
                    condition = (df[alert_status_column] == 'FN') & (df[test_status_column] != 'FN')
                    if df[condition].shape[0] > 0:
                        files_with_fn_mismatch.append(root + '/' + filename)
                
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return files_with_fn_mismatch

# Set the path of the parent folder and column names
parent_folder = 'project1/datasets-refined-status'
alert_status_column = 'alert_status'
test_status_column = 'test_status_general'

# Find files with FN in alert_status and different value in test_status
files_with_mismatch = find_files_with_fn_mismatch(parent_folder, alert_status_column, test_status_column)

# Print the results
print("Files with rows where alert_status is 'FN' and test_status is different from 'FN':")
for file in files_with_mismatch:
    print(file)
