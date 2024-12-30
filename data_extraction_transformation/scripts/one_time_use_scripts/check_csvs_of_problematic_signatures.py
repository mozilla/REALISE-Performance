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
    parser.add_argument('-a', '--alerts-file', required=True, help="Path of the alerts file")
    return parser.parse_args()

def process_folder(input_folder, folder, lost_signatures, df_alerts, output_location=""):
    global counter_empty
    global counter_non_empty_but_only_tn
    global other
    test_status_mapping = {
        0: "untriaged",
        1: "downstream",
        2: "reassigned",
        3: "invalid",
        4: "acknowledged"
    }
    for signature_file in os.listdir(input_folder + '/' + folder):
        df = pd.read_csv(input_folder + '/' + folder + '/' + signature_file, index_col=False)
        uniq_sig = df['signature_id'].unique().flatten()
        uniq_sig = {int(x) for x in uniq_sig}
        sig_in_file = int(signature_file.split('_')[0])
        if sig_in_file in lost_signatures:
            df_merged = pd.merge(df, df_alerts, left_on=['revision', 'signature_id'], right_on=['alert_revision', 'signature_id'], how='left')
            df_merged['test_status_general'] = df_merged['test_status'].map(test_status_mapping)
            df_merged['test_status_general'].fillna('TN', inplace=True)
            df_merged['alert_status_general'].fillna('TN', inplace=True)
            df_final = df_merged.drop_duplicates()
            uniq_alert_status = df_final['alert_status_general'].unique().flatten()
            if (len(uniq_alert_status) == 1) and ('TN' in uniq_alert_status):
                counter_non_empty_but_only_tn += 1
            elif df_final.shape[0] == 0:
                counter_empty += 1
            else:
                other += 1

def main():
    global counter_empty
    global counter_non_empty_but_only_tn
    global other
    counter_empty = 0
    counter_non_empty_but_only_tn = 0
    other = 0
    alert_status_mapping = {
        0: "untriaged",
        1: "downstream",
        2: "reassigned",
        3: "invalid",
        4: "improvement",
        5: "investigating",
        6: "wontfix",
        7: "fixed",
        8: "backedout"
    }
    test_status_mapping = {
        0: "untriaged",
        1: "downstream",
        2: "reassigned",
        3: "invalid",
        4: "acknowledged"
    }
    category_mapping = {
        'investigating': 'SP',
        'reassigned': 'TP',
        'invalid': 'FP',
        'improvement': 'TP',
        'fixed': 'TP',
        'wontfix': 'TP',
        'untriaged': 'SP',
        'backedout': 'TP',
        'downstream': 'TP',
        'acknowledged': 'TP',
    }
    args = parse_args()
    input_folder = args.input_folder
    alerts_file = args.alerts_file
    lost_signatures = args.lost_signatures
    df_alerts = pd.read_csv(alerts_file)
    df_alerts = df_alerts.drop(columns=['alert_push_timestamp'])
    df_alerts['alert_status_general'] = df_alerts['alert_status'].map(alert_status_mapping)
    df_alerts["alert_status_general"] = df_alerts["alert_status_general"].replace(category_mapping)
    df_alerts.rename(columns={'test_series_signature_id': 'signature_id'}, inplace=True)
    with open(lost_signatures, "r") as f:
        lost_signatures_set = f.read()
    lost_signatures_set = {int(x) for x in lost_signatures_set.split(",")}
    projects_folders_mapping = {"autoland": ["autoland1", "autoland2", "autoland3", "autoland4"], "firefox-android": ["firefox-android"], "mozilla-beta": ["mozilla-beta"], "mozilla-central": ["mozilla-central"], "mozilla-release": ["mozilla-release"]}
    if projects_folders_mapping:
        for project in projects_folders_mapping:
            for folder in projects_folders_mapping[project]:
                process_folder(input_folder, folder, lost_signatures_set, df_alerts)
    print("COUNTERRRRRRRRR")
    print("enpty_counter:")
    print(counter_empty)
    print("counter_non_empty_but_only_tn:")
    print(counter_non_empty_but_only_tn)
    print("other:")
    print(other)
if __name__ == "__main__":
    main()