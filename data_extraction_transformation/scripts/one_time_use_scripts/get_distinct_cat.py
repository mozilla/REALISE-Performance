import os
import pandas as pd
import shutil

def get_unique_categories_across_directories(parent_folder, column_name):
    unique_categories = set()
    
    # Walk through all files and directories within the parent folder
    for root, dirs, files in os.walk(parent_folder):
        for dir in dirs:
            for filename in os.listdir(os.path.join(root, dir)):
                # Process only CSV files
                if filename.endswith('.csv'):
                    file_path = os.path.join(root, dir, filename)
                    
                    # Read the CSV file
                    try:
                        df = pd.read_csv(file_path)
                        '''
                        # Check if the column exists in the file
                        if column_name in df.columns:
                            # Update the set with unique values from this file's column
                            unique_categories.update(df[column_name].dropna().unique())
                        else:
                            print(f"Column '{column_name}' not found in {filename}")
                        '''
                        if len(df['alert_status_general'].unique()) > 4:
                            sig_id = filename.split['_'][0]
                            shutil.copy(file_path, 'temp/' + filename)
                            '''
                            json_name = 'summary_' + sig_id + '.json'
                            if ('summaries/' + json_name).is_file():
                                print('##########')
                                print(sig_id)
                                shutil.copy(file_path, 'temp/' + filename)
                                shutil.copy('summaries/' + json_name, 'temp/' + json_name)
                            '''
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")
                    
    
    return unique_categories

# Set the path of the parent folder and the column name
parent_folder = 'project1/datasets-original-annotated-2-aggregated'
column_name = 'alert_status_general'

# Get unique categories across all directories
unique_categories = get_unique_categories_across_directories(parent_folder, column_name)

# Print the unique categories
print("Unique categories across all CSV files in all directories:")
print(unique_categories)
