import os
import pandas as pd
import helper
import shutil

def process_folder(folder):
    for signature_file in os.listdir('../datasets/' + folder):
        df = pd.read_csv('../datasets/' + folder + '/' + signature_file, index_col=False)
        #df_grouped = df.drop(['job_id'], axis=1).groupby('revision').agg({'value': 'mean', **{col: 'first' for col in df.columns if col not in ['revision', 'value']}}).reset_index()
        df_grouped = df.groupby('revision').agg({'value': 'mean', **{col: 'first' for col in df.columns if col not in ['revision', 'value']}}).reset_index()
        df_grouped.to_csv('../datasets-normalized/' + folder +  '/' + signature_file, index_col=False)

projects_folders_mapping = {"autoland": ["autoland1", "autoland2", "autoland3", "autoland4"], "firefox-android": ["firefox-android"], "mozilla-central": ["mozilla-central"], "mozilla-beta": ["mozilla-beta"], "mozilla-release": ["mozilla-release"]}
for project in projects_folders_mapping:
    for folder in projects_folders_mapping[project]:
        
        os.makedirs('../datasets-normalized/' + folder, exist_ok=True)
        process_folder(folder)
        #shutil.rmtree('../datasets/' + folder)
        #os.rename('../datasets/' + folder + "-processed", '../datasets/' + folder)
