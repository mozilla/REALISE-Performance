import os
import pandas as pd

input_files = 'project1/datasets-refined-status'

def process_file(file):
    df = pd.read_csv(input_files + '/' + folder + '/' + signature_file, index_col=False)

    
    filtered_df = df[(df['alert_status'] != 'TN') & (df['test_status_general'] == 'TN')]
    # duplicates = filtered_df[filtered_df.duplicated(subset='revision', keep=False)] 
    # different_status_in_duplicates = duplicates.groupby('revision').filter(lambda x: x['test_manually_created'].nunique() > 1)
    if(filtered_df.shape[0] > 0):
        print("###############")
        print(folder + '/' + signature_file)
        print(filtered_df)
    '''
    filtered_df = df[df['test_status_general'] == 'FN']
    if(filtered_df.shape[0] > 0):
        print("###############")
        print(folder + '/' + signature_file)
    '''

projects_folders_mapping = {"autoland": ["autoland1", "autoland2", "autoland3", "autoland4"], "firefox-android": ["firefox-android"], "mozilla-central": ["mozilla-central"], "mozilla-beta": ["mozilla-beta"], "mozilla-release": ["mozilla-release"]}
for project in projects_folders_mapping:
    for folder in projects_folders_mapping[project]:
        for signature_file in os.listdir(input_files + '/' + folder):
            process_file(signature_file)
