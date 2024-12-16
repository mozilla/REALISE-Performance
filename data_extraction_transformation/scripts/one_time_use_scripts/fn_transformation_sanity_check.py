import os
import pandas as pd

# Paths for original and refined datasets
original_folder = 'project1/datasets-refined-status'
refined_folder = 'project1/datasets-refined-status-2'

# Helper function to read CSV files and return their content as a string
def read_file(file_path):
    return pd.read_csv(file_path).to_string()

# Function to compare files
def compare_filesystem():
    unchanged_files = 0
    changed_files = []
    
    # Walk through the original filesystem and compare files
    for root, dirs, files in os.walk(original_folder):
        for filename in files:
            if filename.endswith('.csv'):
                # Construct full file paths
                original_file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(original_file_path, original_folder)
                refined_file_path = os.path.join(refined_folder, relative_path)

                # Check if the corresponding file exists in the refined filesystem
                if os.path.exists(refined_file_path):
                    # Compare the content of the files
                    original_content = read_file(original_file_path)
                    refined_content = read_file(refined_file_path)

                    # If contents differ, it's a changed file
                    if original_content != refined_content:
                        changed_files.append(refined_file_path)
                    else:
                        unchanged_files += 1
                else:
                    print(f"File {refined_file_path} is missing in the refined filesystem.")
    
    # Display the results
    print(f"Number of unchanged files: {unchanged_files}")
    if changed_files:
        print(f"Changed files:")
        for changed_file in changed_files:
            print(changed_file)

# Run the comparison
compare_filesystem()
