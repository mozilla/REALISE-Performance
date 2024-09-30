import os
import pandas as pd
import helper
import shutil

def process_folder(folder):
    for signature_file in os.listdir('../datasets/' + folder):
        df = pd.read_csv('../datasets/' + folder + '/' + signature_file, index_col=False)
        df["push_timestamp"] = pd.to_datetime(df["push_timestamp"], format='mixed')
        df['alert_status'] = df['alert_status'].replace('downstream', 'TP')
        df.to_csv('../datasets/' + folder + "-processed/" + signature_file, index=False)

projects_folders_mapping = {"autoland": ["autoland3", "autoland4"], "firefox-android": ["firefox-android"], "mozilla-central": ["mozilla-central"], "mozilla-beta": ["mozilla-beta"], "mozilla-release": ["mozilla-release"]}
for project in projects_folders_mapping:
    for folder in projects_folders_mapping[project]:
        if not os.path.exists('../datasets/' + folder + "-processed"):
            os.makedirs('../datasets/' + folder + "-processed", exist_ok=True)
        process_folder(folder)
        shutil.rmtree('../datasets/' + folder)
        os.rename('../datasets/' + folder + "-processed", '../datasets/' + folder)
