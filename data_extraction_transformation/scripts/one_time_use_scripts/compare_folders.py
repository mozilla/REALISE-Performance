import os
import pandas as pd
import shutil
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Script to cross-checkif the signatures are corrct or not")
    parser.add_argument('-f', '--first-folder', required=True, help="Path to the first input timeseries dataset folder")
    parser.add_argument('-s', '--second-folder', required=True, help="Path to the second input timeseries dataset folder")
    parser.add_argument('-o', '--problematic-signatures-output', required=True, help="Path of the problrematic signatures output")
    parser.add_argument('-e', '--exception-revision', required=True, help="Revision to exclude in the comparison")

    return parser.parse_args()





def process_folder(first_folder, second_folder, folder, exception_revision):
    global problematic_signatures
    global prob_col
    for signature_file in os.listdir(first_folder + '/' + folder):
        try:
            df1 = pd.read_csv(first_folder + '/' + folder + '/' + signature_file, index_col=False)
            df2 = pd.read_csv(second_folder + '/' + folder + '/' + signature_file, index_col=False)

            # Remove rows with the exception_revision in both dataframes
            df1 = df1[df1['revision'] != exception_revision]
            df2 = df2[df2['revision'] != exception_revision]

            # Sort the columns to ensure consistency in comparison
            df1 = df1[sorted(df1.columns)].astype(str)
            df2 = df2[sorted(df2.columns)].astype(str)

            # Ensure the rows are in the same order (you can sort by index if no specific column is needed)
            df1 = df1.sort_index(axis=0)  # Sort by row index
            df2 = df2.sort_index(axis=0)  # Sort by row index

            # Compare the DataFrames (this compares both the content and the row order)
            are_equal = df1.equals(df2)

            # If content is not equal, get detailed comparison results
            if not are_equal:
                comparison = df1 != df2  # Element-wise comparison between df1 and df2
                rows_with_differences = comparison.any(axis=1).sum()  # Count rows with any difference

                # To also print the number of rows that differ in order, we compare the indices as well
                row_order_differences = (df1.index != df2.index).sum()  # Count rows where indices differ
                
                # Print the number of rows where content and order differ
                if row_order_differences > 0:
                    print(signature_file)
                    print(f"Number of rows with differences in order: {row_order_differences}")

                columns_with_differences = comparison.columns[comparison.any()]  # Get columns with differences
                
                # Check for differences in the 'alert_notes' column
                if 'alert_notes' in df1.columns and 'alert_notes' in df2.columns:
                    # Compare the 'alert_notes' columns
                    alert_notes_diff = df1['alert_notes'] != df2['alert_notes']

                    # Extract the differing rows
                    differing_rows = df1[alert_notes_diff]
                    differing_rows_df2 = df2[alert_notes_diff]

                    if not differing_rows.empty:
                        print(f"Differences found in 'alert_notes' for file: {signature_file}")
                        for idx, row in differing_rows.iterrows():
                            # Display the differing rows from df1 and df2 for 'alert_notes'
                            print(f"Row {idx} differs:")
                            print(f"df1 alert_notes: {row['alert_notes']}")
                            print(f"df2 alert_notes: {differing_rows_df2.loc[idx, 'alert_notes']}")
                            print('---')

                # If the 'value' column has significant differences, append to problematic_signatures
                if 'value' in df1.columns and 'value' in df2.columns:
                    # Calculate percentage differences in the 'value' column
                    df1_value = pd.to_numeric(df1['value'], errors='coerce')
                    df2_value = pd.to_numeric(df2['value'], errors='coerce')
                    
                    # Compute the percentage difference
                    value_difference = abs(df1_value - df2_value) / df1_value * 100  # Percentage difference

                    # Find rows with a difference greater than 0.01%
                    significant_diff = value_difference > 0.01  # Threshold for significant difference
                    if significant_diff.any():
                        problematic_signatures.append(signature_file)
                        print(f"Problematic file (value column significant difference): {signature_file}")
                        print(f"Significant differences found in 'value' column.")
                
                # Check for other columns' differences
                if len(columns_with_differences) == 1 and columns_with_differences[0] == 'value':
                    pass  # Handle 'value' column separately if needed
                else:
                    problematic_signatures.append(signature_file)
                    print(f"Problematic file: {signature_file} - Rows with content differences: {rows_with_differences}, Order differences: {row_order_differences}")

        except Exception as e:
            print(f"Error processing {signature_file}: {e}")










# def process_folder(first_folder, second_folder, folder, exception_revision):
#     global problematic_signatures
#     global prob_col
#     for signature_file in os.listdir(first_folder + '/' + folder):
#         try:
#             df1 = pd.read_csv(first_folder + '/' + folder + '/' + signature_file, index_col=False)
#             df2 = pd.read_csv(second_folder + '/' + folder + '/' + signature_file, index_col=False)

#             # Remove rows with the exception_revision in both dataframes
#             df1 = df1[df1['revision'] != exception_revision]
#             df2 = df2[df2['revision'] != exception_revision]

#             # Sort the columns to ensure consistency in comparison
#             df1 = df1[sorted(df1.columns)].astype(str)
#             df2 = df2[sorted(df2.columns)].astype(str)

#             # Ensure the rows are in the same order (you can sort by index if no specific column is needed)
#             df1 = df1.sort_index(axis=0)  # Sort by row index
#             df2 = df2.sort_index(axis=0)  # Sort by row index

#             # Compare the DataFrames (this compares both the content and the row order)
#             are_equal = df1.equals(df2)

#             # If content is not equal, get detailed comparison results
#             if not are_equal:
#                 comparison = df1 != df2  # Element-wise comparison between df1 and df2
#                 rows_with_differences = comparison.any(axis=1).sum()  # Count rows with any difference

#                 # To also print the number of rows that differ in order, we compare the indices as well
#                 row_order_differences = (df1.index != df2.index).sum()  # Count rows where indices differ
                
#                 # Print the number of rows where content and order differ
#                 if row_order_differences > 0:
#                     print(signature_file)
#                     print(f"Number of rows with differences in order: {row_order_differences}")

#                 columns_with_differences = comparison.columns[comparison.any()]  # Get columns with differences
                
#                 # Check if 'value' is the problematic column (and handle it differently)
#                 if len(columns_with_differences) == 1 and columns_with_differences[0] == 'value':
#                     pass  # Handle 'value' column separately if needed
#                 else:
#                     problematic_signatures.append(signature_file)
#                     print(f"Problematic file: {signature_file} - Rows with content differences: {rows_with_differences}, Order differences: {row_order_differences}")

#         except Exception as e:
#             print(f"Error processing {signature_file}: {e}")

                    # if len(columns_with_differences != 0):
        #     for col in columns_with_differences:
        #         prob_col.add(col)

        # same_row_count = len(df1) == len(df2)
        # same_columns = sorted(df1.columns)  == sorted(df2.columns)
        # alert_status_column = 'alert_status_general'
        # same_alert_status_distribution = df1[alert_status_column].value_counts(normalize=True).equals(df2[alert_status_column].value_counts(normalize=True))
        # revision_ids_df1 = df1['revision'].unique()
        # revision_ids_df2 = df2['revision'].unique()
        # set_df1 = set(revision_ids_df1)
        # set_df2 = set(revision_ids_df2)
        # unique_in_df1 = set_df1 - set_df2
        # unique_in_df2 = set_df2 - set_df1
        # identical_revisions = unique_in_df2.union(unique_in_df1) == set()
        # column_name = 'value'
        # differences_in_column = df1[column_name] != df2[column_name]
        # rows_with_differences = df1[differences_in_column]
        # rows_in_df2 = df2[differences_in_column]
        # comparison_df = pd.DataFrame({
        #     f'{column_name} in df1': rows_with_differences[column_name],
        #     f'{column_name} in df2': rows_in_df2[column_name]
        # })
        
        # print("Identical revisions:")
        # print(identical_revisions)
        # print("Row count:")
        # print(len(df1))
        # print(len(df2))
        # print(len(rows_with_differences))
        # print(comparison_df)
        # # print(same_row_count)
        # print("Same columns:")
        # # print(df1.columns)
        # # print(df2.columns)
        # print(same_columns)
        # print("Same status dist")
        # # print(df1[alert_status_column].value_counts(normalize=True))
        # # print(df2[alert_status_column].value_counts(normalize=True))
        # print(same_alert_status_distribution)

        # # print("Are equal:")
        # # print(are_equal)
        # # if are_equal:
        # #     pass
        # # else:
        # #     problematic_signatures.append([signature_file])
        '''same_row_count = len(df1) == len(df2)
        same_columns = sorted(df1.columns)  == sorted(df2.columns)
        alert_status_column = 'alert_status_general'
        same_alert_status_distribution = df1[alert_status_column].value_counts(normalize=True).equals(df2[alert_status_column].value_counts(normalize=True))
        revision_ids_df1 = df1['revision'].unique()
        revision_ids_df2 = df2['revision'].unique()
        set_df1 = set(revision_ids_df1)
        set_df2 = set(revision_ids_df2)
        unique_in_df1 = set_df1 - set_df2
        unique_in_df2 = set_df2 - set_df1
        identical_revisions = unique_in_df2.union(unique_in_df1) == set()
        print("Identical revisions:")
        print(identical_revisions)
        print("Row count:")
        print(len(df1))
        print(len(df2))
        print(same_row_count)
        print("Same columns:")
        # print(df1.columns)
        # print(df2.columns)
        print(same_columns)
        print("Same status dist")
        # print(df1[alert_status_column].value_counts(normalize=True))
        # print(df2[alert_status_column].value_counts(normalize=True))
        print(same_alert_status_distribution)
        if same_row_count and same_columns and same_alert_status_distribution:
            print(signature_file)
        else:
            problematic_signatures.append([signature_file])'''

def main():
    global problematic_signatures
    global prob_col
    prob_col = set()
    args = parse_args()
    first_folder = args.first_folder
    second_folder = args.second_folder
    problematic_signatures_output = args.problematic_signatures_output
    exception_revision = args.exception_revision
    problematic_signatures = []

    projects_folders_mapping = {"autoland": ["autoland1", "autoland2", "autoland3", "autoland4"], "firefox-android": ["firefox-android"], "mozilla-beta": ["mozilla-beta"], "mozilla-release": ["mozilla-release"], "mozilla-central": ["mozilla-central"]}
    # projects_folders_mapping = {"autoland": ["autoland1"]}
    for project in projects_folders_mapping:
        for folder in projects_folders_mapping[project]:
            print("################################################# ROUND BEGINS #################################################")
            process_folder(first_folder, second_folder, folder, exception_revision)
            print("################################################# ROUND PASSED #################################################")
    print('####### Problematic signatures #######')
    for sig in problematic_signatures:
        print('Signature path:')
        print(sig)
    for col in prob_col:
        print('problematic col:')
        print(col)
    with open(problematic_signatures_output + '/problematic_signatures.txt', mode='w') as file:
        file.write(','.join(map(str, problematic_signatures)))

if __name__ == "__main__":
    main()