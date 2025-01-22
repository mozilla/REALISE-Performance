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
    parser.add_argument('-o', '--output-folder', required=True, help="Path to the output timeseries folder")
    return parser.parse_args()

def process_folder(input_folder, output_folder, folder):
    drop_cols = [
        "single_alert_series_signature_test",
        "alert_summary_performance_tags",
        "alert_summary_push_id",
        "alert_summary_revision",
        "alert_summary_repository",
        "single_alert_series_signature_measurement_unit",
        "single_alert_series_signature_lower_is_better",
        "single_alert_series_signature_option_collection_hash",
        "single_alert_series_signature_machine_platform",
        "single_alert_series_signature_has_subtests",
        "single_alert_series_signature_extra_options",
        "single_alert_series_signature_signature_hash"
    ]
    for signature_file in os.listdir(input_folder + '/' + folder):
        df = pd.read_csv(input_folder + '/' + folder + '/' + signature_file, index_col=False)
        df = df.drop(columns=drop_cols)
        print(folder + '/' + signature_file)
        df.to_csv(output_folder + '/' + folder + '/' + signature_file, index=False)

def main():
    args = parse_args()
    input_folder = args.input_folder
    output_folder = args.output_folder
    projects_folders_mapping = {"autoland": ["autoland1", "autoland2", "autoland3", "autoland4"],
    "firefox-android": ["firefox-android"],
    "mozilla-beta": ["mozilla-beta"],
    "mozilla-release": ["mozilla-release"],
    "mozilla-central": ["mozilla-central"]
    }
    os.makedirs(output_folder, exist_ok=True)
    if projects_folders_mapping:
        for project in projects_folders_mapping:
            for folder in projects_folders_mapping[project]:
                os.makedirs(output_folder + '/' + folder, exist_ok=True)
                process_folder(input_folder, output_folder, folder)
if __name__ == "__main__":
    main()