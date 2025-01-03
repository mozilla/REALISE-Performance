import os
import pandas as pd

input_files = '../../../data/all-datasets-annotated-aggregated'
col = 'alert_summary_status_general'

total_data_points = 0
total_sig = 0
# Function to process each CSV file
def process_file(file_path):
    global total_data_points
    # Read the CSV into a DataFrame
    df = pd.read_csv(file_path, index_col=False)
    #filtered_df = df[~df[col].isin(['TN']) & df[col].notna()]
    df[col] = df[col].fillna('TN')
    total_data_points += df.shape[0]
    return df[col]

# Define the mapping of projects to folders
projects_folders_mapping = {
    "autoland": ["autoland1", "autoland2", "autoland3", "autoland4"],
    "firefox-android": ["firefox-android"],
    "mozilla-beta": ["mozilla-beta"],
    "mozilla-central": ["mozilla-central"],
    "mozilla-release": ["mozilla-release"]
}

# Initialize an empty list to store the 'status' values
all_statuses = []

# Loop through the folders and files
for project in projects_folders_mapping:
    for folder in projects_folders_mapping[project]:
        folder_path = os.path.join(input_files, folder)  # Get the full folder path
        for signature_file in os.listdir(folder_path):
            # Construct the full file path
            file_path = os.path.join(folder_path, signature_file)
            # Process the file and get the 'status' column
            statuses = process_file(file_path)
            all_statuses.extend(statuses)  # Add the statuses from this file to the list
            total_sig += 1

# Convert the list of statuses into a pandas Series
status_series = pd.Series(all_statuses)

# Get the overall distribution of the 'status' column in percentages
status_percentage = status_series.value_counts(normalize=True) * 100


print(len(all_statuses))

# Print the distribution in percentage
print("Overall 'status' distribution across all files (in percentage):")
print(status_percentage)
print("Overall number of signatures")
print(total_sig)
print("Overall number of data points")
print(total_data_points)