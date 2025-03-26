#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: Mohamed Bilel Besbes
Date: 2024-12-18
"""
import argparse
import pandas as pd
import os


def parse_args():
    parser = argparse.ArgumentParser(description="Check if there are non-null job IDs")
    parser.add_argument('-i', '--input-folder', required=True, help="Path to the folder with the input timeseries sub-folders")
    return parser.parse_args()

def process_folder(input_folder, folder):
    global total_nan_count
    global partial_non_trust_nan_count
    global partial_trust_nan_count
    global total_non_nan_count
    global total_nb_of_sig
    for signature_file in os.listdir(input_folder + '/' + folder):
        total_nb_of_sig += 1
        df = pd.read_csv(input_folder + '/' + folder + '/' + signature_file, index_col=False)
        if df['job_id'].isna().all():
            total_nan_count += 1
        
        elif df['job_id'].notna().all():
            total_non_nan_count += 1

        elif df['job_id'].isna().any():
            if df['job_id'].isna().mean() >= 0.5:
                partial_non_trust_nan_count += 1
            else:
                partial_trust_nan_count += 1

def main():
    global total_nan_count
    global partial_non_trust_nan_count
    global partial_trust_nan_count
    global total_non_nan_count
    global total_nb_of_sig
    total_nan_count = 0
    partial_non_trust_nan_count = 0
    partial_trust_nan_count = 0
    total_non_nan_count = 0
    total_nb_of_sig = 0
    args = parse_args()
    input_folder = args.input_folder
    projects_folders_mapping = {"autoland": ["autoland1", "autoland2", "autoland3", "autoland4"], "firefox-android": ["firefox-android"], "mozilla-beta": ["mozilla-beta"], "mozilla-central": ["mozilla-central"], "mozilla-release": ["mozilla-release"]}
    if projects_folders_mapping:
        for project in projects_folders_mapping:
            for folder in projects_folders_mapping[project]:
                process_folder(input_folder, folder)
    print("Total nb of sig:")
    print(total_nb_of_sig)
    print("Sum of count:")
    print(
        total_nan_count + partial_non_trust_nan_count + partial_trust_nan_count + total_non_nan_count
    )
    print("Nb of signatures with only NaN Job IDs:")
    print(str((total_nan_count / total_nb_of_sig) * 100) + "%")
    print("Nb of signatures with some NaN Job IDs (no trust):")
    print(str((partial_non_trust_nan_count / total_nb_of_sig) * 100) + "%")
    print("Nb of signatures with some NaN Job IDs (trustable):")
    print(str((partial_trust_nan_count / total_nb_of_sig) * 100) + "%")
    print("Nb of signatures with no NaN Job IDs:")
    print(str((total_non_nan_count / total_nb_of_sig) * 100) + "%")
if __name__ == "__main__":
    main()