#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: Mohamed Bilel Besbes
Date: 2024-12-23
"""
import argparse
import pandas as pd
import os
import sys
import datetime

def parse_args():
    parser = argparse.ArgumentParser(description="Script to do sanity checks on the data for the artifact challenge submission")
    parser.add_argument('-i', '--input-folder', required=True, help="Path to the input dataset folder (labeled data)")
    return parser.parse_args()


def process_folder(folder, input_folder, minimum_timestamp):
    min_timestamp = minimum_timestamp
    for signature_file in os.listdir(input_folder + '/' + folder):
        timeseries_df = pd.read_csv(input_folder + '/' + folder + '/' + signature_file, encoding='ISO-8859-1')
        timeseries_df['push_timestamp'] = pd.to_datetime(timeseries_df['push_timestamp'])
        earliest_time = timeseries_df['push_timestamp'].min()
        if min_timestamp > earliest_time:
            print(earliest_time)
            min_timestamp = earliest_time
    return min_timestamp


def check_min_date(input_folder):
    minimum_timestamp = datetime.datetime.now()
    projects_folders_mapping = {"autoland": ["autoland1", "autoland2", "autoland3", "autoland4"], "firefox-android": ["firefox-android"], "mozilla-beta": ["mozilla-beta"]}
    if projects_folders_mapping:
        for project in projects_folders_mapping:
            for folder in projects_folders_mapping[project]:
                minimum_timestamp = process_folder(folder, input_folder, minimum_timestamp)
    return minimum_timestamp

def main():
    args = parse_args()
    input_folder = args.input_folder
    min_date = check_min_date(input_folder)
    print("Minimum timestamp in all timseries dataframes")
    print(min_date)
if __name__ == "__main__":
    main()