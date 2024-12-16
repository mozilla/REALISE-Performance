import os
import pandas as pd

folder1 = 'project1/datasets-normalized'
folder2 = 'project1/datasets-normalized-2'
ignore_columns = ['test_status_general', 'Unnamed: 0']
output_file = 'aadiffering_files.txt'

def compare_csv_files(file1, file2):
    # Load both files as dataframes
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)
    
    # Drop the columns to ignore, if they exist in both dataframes
    for col in ignore_columns:
        if col in df1.columns:
            df1 = df1.drop(columns=[col])
        if col in df2.columns:
            df2 = df2.drop(columns=[col])
    
    # Sort columns and rows for consistent comparison
    df1 = df1.reindex(sorted(df1.columns), axis=1).sort_values(by=df1.columns.tolist()).reset_index(drop=True)
    df2 = df2.reindex(sorted(df2.columns), axis=1).sort_values(by=df2.columns.tolist()).reset_index(drop=True)
    
    # Check if the dataframes are identical
    return df1.equals(df2)

# Open the output file in write mode
with open(output_file, 'w') as f:
    # Iterate over subfolders in folder1
    for subfolder in os.listdir(folder1):
        subfolder_path1 = os.path.join(folder1, subfolder)
        subfolder_path2 = os.path.join(folder2, subfolder)
        
        # Check if the subfolder exists in both directories and is a directory
        if os.path.isdir(subfolder_path1) and os.path.isdir(subfolder_path2):
            # Compare files with identical names in both subfolders
            for filename in os.listdir(subfolder_path1):
                file1 = os.path.join(subfolder_path1, filename)
                file2 = os.path.join(subfolder_path2, filename)
                
                # Only process if both files exist and are CSVs
                if os.path.isfile(file1) and os.path.isfile(file2) and filename.endswith('.csv'):
                    are_identical = compare_csv_files(file1, file2)
                    if are_identical:
                        print(f"{subfolder}/{filename}: Files are identical (ignoring '{', '.join(ignore_columns)}').")
                    else:
                        print(f"{subfolder}/{filename}: Files differ.")
                        # Write the path of the differing file from folder1 to the output file
                        f.write(f"{file1}\n")
