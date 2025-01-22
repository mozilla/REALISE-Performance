#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: Mohamed Bilel Besbes
Date: 2025-01-21
"""
import argparse
import pandas as pd
import os


def parse_args():
    parser = argparse.ArgumentParser(description="Investigate the prevalence of the Puh Timestamp in the time series to better understand it")
    parser.add_argument('-i',
                        '--input-folder',
                        required=True,
                        help="Path to the input dataset folder")
    return parser.parse_args()

def has_multiple_push_timestamps(dataf: pd.DataFrame) -> bool:
    grouped = dataf.groupby('revision')['push_timestamp'].nunique()
    return (grouped > 1).any()


def process_folder(input_folder, folder):
    global true_count
    global total_count
    folder_path = os.path.join(input_folder, folder)
    for signature_file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, signature_file)
        df = pd.read_csv(file_path, index_col=False, encoding='ISO-8859-1')
        total_count += 1
        df['push_timestamp'] = pd.to_datetime(df['push_timestamp'])
        df = df.sort_values(by='push_timestamp')
        multi_push_timestamp_per_revision = has_multiple_push_timestamps(df)
        # print(multi_push_timestamp_per_revision)
        if multi_push_timestamp_per_revision:
            print(f"Multiple push timestamps found in {file_path}")
            true_count += 1

def main():
    global true_count
    global total_count
    args = parse_args()
    input_folder = args.input_folder
    true_count = 0
    total_count = 0
    projects_folders_mapping = {
        "autoland": ["autoland1", "autoland2", "autoland3", "autoland4"],
        "firefox-android": ["firefox-android"],
        "mozilla-beta": ["mozilla-beta"],
        "mozilla-central": ["mozilla-central"],
        "mozilla-release": ["mozilla-release"]
    }
    
    for project in projects_folders_mapping:
        for folder in projects_folders_mapping[project]:
            process_folder(input_folder, folder)
    print(f"Total number of files: {total_count}")
    print(f"Number of files with multiple push timestamps per revision: {true_count}")
if __name__ == "__main__":
    main()
