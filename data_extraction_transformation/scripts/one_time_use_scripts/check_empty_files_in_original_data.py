import pandas as pd
import os

projects_folders = ["autoland1", "autoland2", "autoland3", "autoland4", "firefox-android", "mozilla-central", "mozilla-beta", "mozilla-release"]

datasets_folder = '../initialdataexploration'
empty_files_count = 0
for project in projects_folders:
    for signature_file in os.listdir(datasets_folder + '/' + project):
        signature_id = signature_file.split("_")[0]
        df = pd.read_csv(datasets_folder + '/' + project + '/' + signature_file)
        if (df.shape[0] == 0):
            empty_files_count += 1
            print(signature_id)
print("Number of empty files:")
print(empty_files_count)