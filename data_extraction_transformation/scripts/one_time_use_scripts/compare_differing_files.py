import pandas as pd

# Path to the modified text file containing file paths without the prefix
input_file = 'differing_files.txt'
folder1_prefix = 'project1/datasets-normalized/'  # Original files path
folder2_prefix = 'project1/datasets-normalized-2/'  # Second files path

# List of columns to ignore during comparison
ignore_columns = ['test_status_general', 'Unnamed: 0']  # Add any other columns to ignore here

def print_file_differences(file1, file2):
    # Load both files as dataframes
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    # Drop the columns to ignore from both dataframes
    df1 = df1.drop(columns=[col for col in ignore_columns if col in df1.columns], errors='ignore')
    df2 = df2.drop(columns=[col for col in ignore_columns if col in df2.columns], errors='ignore')
    
    # Display differences for each column
    for col in df1.columns:
        if col in df2.columns:
            if not df1[col].equals(df2[col]):
                # Find indices where the values differ
                differing_indices = df1[df1[col] != df2[col]].index.tolist()
                print(f"Differences in column '{col}':")
                for idx in differing_indices:
                    print(f"Index {idx}: {file1} = {df1[col][idx]}, {file2} = {df2[col][idx]}")
                print()  # Print a new line for better readability
        else:
            print(f"Column '{col}' is not present in {file2}.")
    
    for col in df2.columns:
        if col not in df1.columns:
            print(f"Column '{col}' is not present in {file1}.")

# Read the modified text file and compare the files listed
with open(input_file, 'r') as f:
    file_paths = f.readlines()

# Iterate over the list of file paths and print the differences
for path in file_paths:
    path = path.strip()  # Remove any leading/trailing whitespace
    file1 = folder1_prefix + path  # Construct the full path for the first file
    file2 = folder2_prefix + path  # Construct the full path for the second file
    
    print(f"Comparing {file1} and {file2}:")
    print_file_differences(file1, file2)
    print("-" * 80)  # Separator for each file comparison
