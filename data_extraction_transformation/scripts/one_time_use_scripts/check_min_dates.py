import os
import pandas as pd

def process_folder(folder):
    global min_push_timestamp, min_alert_creation_timestamp, max_alert_creation_timestamp, max_push_timestamp
    folder_path = input_folder + '/' + folder
    for signature_file in os.listdir(folder_path):
        try:
            # Read the CSV file
            df = pd.read_csv(folder_path + '/' + signature_file, index_col=False)
            
            # Convert columns to datetime and find the minimum for the file
            if 'push_timestamp' in df.columns:
                file_min_push = pd.to_datetime(df['push_timestamp']).min()
                if min_push_timestamp is None or file_min_push < min_push_timestamp:
                    min_push_timestamp = file_min_push
                    
                file_max_push = pd.to_datetime(df['push_timestamp']).max()
                if max_push_timestamp is None or file_max_push > max_push_timestamp:
                    max_push_timestamp = file_max_push
            '''
            if 'alert_creation_timestamp' in df.columns:
                file_min_create = pd.to_datetime(df['alert_creation_timestamp']).min()
                if min_alert_creation_timestamp is None or file_min_create < min_alert_creation_timestamp:
                    min_alert_creation_timestamp = file_min_create

                file_max_create = pd.to_datetime(df['alert_creation_timestamp']).max()
                if max_alert_creation_timestamp is None or file_max_create > max_alert_creation_timestamp:
                    max_alert_creation_timestamp = file_max_create
            '''

        except Exception as e:
            print(f"Error processing file {signature_file} in folder {folder}: {e}")

# Input folder path
input_folder = 'project1/datasets-original'

# Mapping of projects to their folders
projects_folders_mapping = {
    "autoland": ["autoland1", "autoland2", "autoland3", "autoland4"],
    "firefox-android": ["firefox-android"],
    "mozilla-beta": ["mozilla-beta"]
}

# Initialize the global variables
min_push_timestamp = None
max_push_timestamp = None
'''
min_alert_creation_timestamp = None
max_alert_creation_timestamp = None
'''

# Loop through projects and their folders
for project in projects_folders_mapping:
    for folder in projects_folders_mapping[project]:
        process_folder(folder)

# Print the results
print(f"The minimum push_timestamp among all files is: {min_push_timestamp}")
# print(f"The minimum alert_creation_timestamp among all files is: {min_alert_creation_timestamp}")

print(f"The maximum push_timestamp among all files is: {max_push_timestamp}")
# print(f"The maximum alert_creation_timestamp among all files is: {max_alert_creation_timestamp}")