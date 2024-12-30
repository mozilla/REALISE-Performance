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
    parser = argparse.ArgumentParser(description="Check if there are alerts adjacent to the SP datapoints")
    parser.add_argument('-i', '--input-folder', required=True, help="Path to the input timeseries folder")
    parser.add_argument('-l', '--lost-signatures', required=True, help="Path to the lost singatures txt file")
    parser.add_argument('-o', '--output-location', required=True, help="Path to the txt file having the captured sig")
    return parser.parse_args()

def process_folder(input_folder, folder, lost_signatures, output_location):
    global captured_sigs
    global counter
    for signature_file in os.listdir(input_folder + '/' + folder):
        df = pd.read_csv(input_folder + '/' + folder + '/' + signature_file, index_col=False)
        uniq_sig = df['signature_id'].unique().flatten()
        uniq_sig = {int(x) for x in uniq_sig}
        sig_in_file = int(signature_file.split('_')[0])
        if sig_in_file in lost_signatures:
            captured_sigs.add(sig_in_file)
            counter += 1
        # for sig in uniq_sig:
        #     if sig in lost_signatures:
        #         captured_sigs.add(sig)


def main():
    global captured_sigs
    global counter
    counter = 0
    captured_sigs = set()
    args = parse_args()
    input_folder = args.input_folder
    output_location = args.output_location
    lost_signatures = args.lost_signatures
    with open(lost_signatures, "r") as f:
        lost_signatures_set = f.read()
    lost_signatures_set = {int(x) for x in lost_signatures_set.split(",")}
    projects_folders_mapping = {"autoland": ["autoland1", "autoland2", "autoland3", "autoland4"], "firefox-android": ["firefox-android"], "mozilla-beta": ["mozilla-beta"], "mozilla-central": ["mozilla-central"], "mozilla-release": ["mozilla-release"]}
    if projects_folders_mapping:
        for project in projects_folders_mapping:
            for folder in projects_folders_mapping[project]:
                process_folder(input_folder, folder, lost_signatures_set, output_location)
    with open(output_location + '/captured_signatures.txt', mode='w') as file:
        file.write(','.join(map(str, captured_sigs)))
    print("counterrrrrrrrrrrrr")
    print(counter)
if __name__ == "__main__":
    main()