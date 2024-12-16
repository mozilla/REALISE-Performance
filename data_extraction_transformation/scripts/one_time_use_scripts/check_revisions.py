import os
import pandas as pd
import shutil
import time

input_files = 'project1/datasets-refined-status'

def process_folder(folder):
    for signature_file in os.listdir(input_files + '/' + folder):
        df = pd.read_csv(input_files + '/' + folder + '/' + signature_file, index_col=False)
        push_timestamp_multiple_revisions = df.groupby('push_timestamp')['revision'].nunique()
        push_timestamp_multiple_revisions = push_timestamp_multiple_revisions[push_timestamp_multiple_revisions > 1]

        if not push_timestamp_multiple_revisions.empty:
            print("######################")
            print("Push timestamps with multiple revisions in " + signature_file + ":")
            print(push_timestamp_multiple_revisions)

        # 2. Check if there are `revision` values with multiple `push_timestamp` values
        revision_multiple_push_timestamps = df.groupby('revision')['push_timestamp'].nunique()
        revision_multiple_push_timestamps = revision_multiple_push_timestamps[revision_multiple_push_timestamps > 1]

        if not revision_multiple_push_timestamps.empty:
            print("######################")
            print("Revisions with multiple push timestamps in " + signature_file + ":")
            print(revision_multiple_push_timestamps)

projects_folders_mapping = {"autoland": ["autoland1", "autoland2", "autoland3", "autoland4"], "firefox-android": ["firefox-android"], "mozilla-central": ["mozilla-central"], "mozilla-beta": ["mozilla-beta"], "mozilla-release": ["mozilla-release"]}
for project in projects_folders_mapping:
    for folder in projects_folders_mapping[project]:
        process_folder(folder)
