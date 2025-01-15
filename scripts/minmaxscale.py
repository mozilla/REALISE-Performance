import os
import pandas as pd
import helper
import shutil
from sklearn.preprocessing import MinMaxScaler
import time
import argparse

def process_folder(input_files, output_files, folder):
    for signature_file in os.listdir(input_files + '/' + folder):
        print(folder + '/' + signature_file)
        df = pd.read_csv(input_files + '/' + folder + '/' + signature_file, index_col=False)
        column_to_scale = 'value'
        scaler = MinMaxScaler()
        df[column_to_scale] = scaler.fit_transform(df[[column_to_scale]]) 
        df.to_csv(output_files + '/' + folder +  '/' + signature_file)
        # time.sleep(0.5)

def parse_args():
    parser = argparse.ArgumentParser(description="Minmaxscale timeseries data (in CSV)")
    parser.add_argument('-i', '--input-folder', help="Path to the input CSV timeseries folder")
    parser.add_argument('-o', '--output-folder', help="Path to the output CSV timeseries folder")
    return parser.parse_args()


def main():
    args = parse_args()
    input_files = args.input_folder
    output_files = args.output_folder
    # input_files = 'datasets-refined-status'
    # output_files = 'datasets-scaled'
    projects_folders_mapping = {"autoland": ["autoland1", "autoland2", "autoland3", "autoland4"], "firefox-android": ["firefox-android"], "mozilla-central": ["mozilla-central"], "mozilla-beta": ["mozilla-beta"], "mozilla-release": ["mozilla-release"]}
    for project in projects_folders_mapping:
        for folder in projects_folders_mapping[project]:
            
            os.makedirs(output_files + '/' + folder, exist_ok=True)
            process_folder(input_files, output_files, folder)
            #shutil.rmtree('../datasets/' + folder)
            #os.rename('../datasets/' + folder + "-processed", '../datasets/' + folder)

if __name__ == "__main__":
    main()