import os
import pandas as pd
import helper
import shutil
from sklearn.preprocessing import MinMaxScaler
import time

input_files = 'datasets-refined-status'
output_files = 'datasets-scaled'

def process_folder(folder):
    for signature_file in os.listdir('../' + input_files + '/' + folder):
        print(folder + '/' + signature_file)
        df = pd.read_csv('../' + input_files + '/' + folder + '/' + signature_file, index_col=False)
        column_to_scale = 'value'
        scaler = MinMaxScaler()
        df[column_to_scale] = scaler.fit_transform(df[[column_to_scale]]) 
        df.to_csv('../' + output_files + '/' + folder +  '/' + signature_file)
        time.sleep(0.5)

projects_folders_mapping = {"autoland": ["autoland1", "autoland2", "autoland3", "autoland4"], "firefox-android": ["firefox-android"], "mozilla-central": ["mozilla-central"], "mozilla-beta": ["mozilla-beta"], "mozilla-release": ["mozilla-release"]}
for project in projects_folders_mapping:
    for folder in projects_folders_mapping[project]:
        
        os.makedirs('../' + output_files + '/' + folder, exist_ok=True)
        process_folder(folder)
        #shutil.rmtree('../datasets/' + folder)
        #os.rename('../datasets/' + folder + "-processed", '../datasets/' + folder)
