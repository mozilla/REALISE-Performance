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
    parser = argparse.ArgumentParser(description="Check if there are alerts addjacent to the SP datapoints")
    parser.add_argument('-i', '--input-folder', required=True, help="Path to the input dataset folder")
    return parser.parse_args()

def process_folder(input_folder, folder):
    global sp_only_sigs
    valid_values = ['TN', 'SP']
    for signature_file in os.listdir(input_folder + '/' + folder):
        df = pd.read_csv(input_folder + '/' + folder + '/' + signature_file, index_col=False)
        if df['alert_status_general'].isin(valid_values).all():
            sp_only_sigs.append(df['signature_id'].unique()[0])
        


def main():
    args = parse_args()
    global sp_only_sigs
    sp_only_sigs = []
    input_folder = args.input_folder
    projects_folders_mapping = {"autoland": ["autoland1", "autoland2", "autoland3", "autoland4"], "firefox-android": ["firefox-android"], "mozilla-beta": ["mozilla-beta"]}
    if projects_folders_mapping:
        for project in projects_folders_mapping:
            for folder in projects_folders_mapping[project]:
                process_folder(input_folder, folder)
    print("Number of signatures having nothing but SP alerts and non-alerting data points:")
    print(len(sp_only_sigs))
if __name__ == "__main__":
    main()