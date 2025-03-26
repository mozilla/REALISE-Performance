import os
import pandas as pd
import numpy as np
import shutil
import argparse
import requests

def parse_args():
    parser = argparse.ArgumentParser(description="Script to cross-reference the data of the time series with the alerts data")
    parser.add_argument('-i', '--input-folder', required=True, help="Path to the input dataset folder")
    parser.add_argument('-o', '--output-folder', required=True, help="Path of the folder ouputting CSV timeseries files")
    return parser.parse_args()

def process_folder(input_folder, output_folder, folder):
    global problematic_signatures
    project_name = folder
    for signature_file in os.listdir(input_folder + '/' + folder):
        df = pd.read_csv(input_folder + '/' + folder + '/' + signature_file, index_col=False)
        df = df[df["push_submission_delta"] >= 4]
        df.to_csv(output_folder + '/' + folder + '/' + signature_file, index=False)

def main():
    global problematic_signatures
    args = parse_args()
    input_folder = args.input_folder
    output_folder = args.output_folder
    problematic_signatures = []
    
    projects_folders_mapping = {name: [name] for name in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, name))}

    os.makedirs(output_folder, exist_ok=True)
    for project in projects_folders_mapping:
        for folder in projects_folders_mapping[project]:
            os.makedirs(output_folder + '/' + folder, exist_ok=True)
            process_folder(input_folder, output_folder, folder)
            # shutil.rmtree('../datasets/' + folder)
            # os.rename('../datasets/' + folder + "-processed", '../datasets/' + folder)

    print('####### Problematic signatures #######')
    for sig in problematic_signatures:
        print('Signature path:')
        print(sig)

if __name__ == "__main__":
    main()


