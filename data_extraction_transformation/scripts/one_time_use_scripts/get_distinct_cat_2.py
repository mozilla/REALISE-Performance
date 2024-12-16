import os
import pandas as pd
from collections import defaultdict
import re

def find_category_counts(parent_folder, column_name):
    # Dictionary to store the count of files for each category
    category_counts = defaultdict(int)
    
    # Regular expression to match files with the pattern "<ID>_timeseries_data.csv"
    file_pattern = re.compile(r'.+_timeseries_data\.csv$')
    
    # Walk through all directories and files within the parent folder
    for root, dirs, files in os.walk(parent_folder):
        for filename in files:
            # Only process files matching the pattern
            if file_pattern.match(filename):
                file_path = os.path.join(root, filename)
                
                # Read the CSV file
                try:
                    df = pd.read_csv(file_path)
                    
                    # Check if the column exists in the file
                    if column_name in df.columns:
                        # Find unique categories in the column for this file
                        unique_categories_in_file = df[column_name].dropna().unique()
                        
                        # Update the count for each category
                        for category in unique_categories_in_file:
                            category_counts[category] += 1
                    else:
                        print(f"Column '{column_name}' not found in {filename}")
                
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return category_counts

# Set the path of the parent folder and the column name
parent_folder = 'project1/datasets-normalized'
column_name = 'test_status_general'

# Get the count of files containing each category at least once
category_counts = find_category_counts(parent_folder, column_name)

# Print the result
print("Category occurrence breakdown by file count:")
for category, count in category_counts.items():
    print(f"Category '{category}' found in {count} files")
