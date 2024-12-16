import os
import pandas as pd
import shutil

input_folder = '../datasets-original-annotated-2'

def process_folder(folder):
    for signature_file in os.listdir(input_folder + '/' + folder):
        df = pd.read_csv(input_folder + '/' + folder + '/' + signature_file, index_col=False)
        # result = df.groupby("revision")["push_timestamp"].nunique()
        result = df.groupby("revision")["alert_status_general"].nunique()
        revisions_with_more_than_one_timestamp = result[result > 1].index.tolist()
        cond_num = len(revisions_with_more_than_one_timestamp)
        if cond_num > 1:
            print(revisions_with_more_than_one_timestamp)
            print("################## " + folder + '/' + signature_file + " ##################")
            print(cond_num)

projects_folders_mapping = {"autoland": ["autoland1", "autoland2", "autoland3", "autoland4"], "firefox-android": ["firefox-android"], "mozilla-beta": ["mozilla-beta"]}

for project in projects_folders_mapping:
    for folder in projects_folders_mapping[project]:
        process_folder(folder)
