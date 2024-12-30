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


def parse_args():
    parser = argparse.ArgumentParser(description="Script to do sanity checks on the data for the artifact challenge submission")
    parser.add_argument('-i', '--input-folder', required=True, help="Path to the input dataset folder (labeled data)")
    parser.add_argument('-a', '--alerts-file', required=True, help="Path to the alerts CSV file")
    parser.add_argument('-l', '--old-alerts-file', required=True, help="Path to the old alerts CSV file")
    parser.add_argument('-b', '--bugs-file', required=True, help="Path to the alerts CSV file")
    parser.add_argument('-o', '--output-folder', required=True, help="Path of the folder ouputting the alerts/bugs files")
    return parser.parse_args()


def process_folder(folder, input_folder, sig_set):
    sig_folder_set = sig_set.copy()
    for signature_file in os.listdir(input_folder + '/' + folder):
        timeseries_df = pd.read_csv(input_folder + '/' + folder + '/' + signature_file, encoding='ISO-8859-1')
        sig = set(timeseries_df['signature_id'].unique())
        sig = {int(x) for x in sig}
        if len(sig) > 1:
            sys.exit('a signature timeseries in file ' + folder + '/' + signature_file + ' has multiple signature : ' + str(sig))
        sig_folder_set = sig_folder_set.union(sig)
    return sig_folder_set


def check_csv_sig_timesries_sig_compatibility(alerts_df, input_folder, output_folder):
    #checks the mutually exclusive signatures between the timeseries files and the alerts CSV
    sig_set_alert_csv = set(alerts_df['test_series_signature_id'].unique().flatten())
    sig_set_alert_csv = {int(x) for x in sig_set_alert_csv}
    projects_folders_mapping = {"autoland": ["autoland1", "autoland2", "autoland3", "autoland4"], "firefox-android": ["firefox-android"], "mozilla-beta": ["mozilla-beta"]}
    sig_set_timeseries = set()
    if projects_folders_mapping:
        for project in projects_folders_mapping:
            for folder in projects_folders_mapping[project]:
                sig_set_timeseries = process_folder(folder, input_folder, sig_set_timeseries)
    # These are the sigs that exist only in the alerts CSV but not in the timeseries (perhaps they were added in September by the new refresh or they belong to the mozilla-central/mozilla-release)
    sig_only_alert_csv = sig_set_alert_csv - sig_set_timeseries
    # These are the sigs that exist only in the timeseries but not the alerts CSV (perhaps they were removed in September by the new refresh)
    sig_only_timeseries =  sig_set_timeseries - sig_set_alert_csv
    print("Report of Singatures compability between timeseires and alerts CSV:")
    print('########## The signatures that exist in the alerts CSV but not the timeseries ##########')
    print(sig_only_alert_csv)
    output_string = ",".join(map(str, sig_only_alert_csv))
    with open(output_folder + "/sig_only_alert_csv_output.txt", "w") as f:
        f.write(output_string)
    print('########## The signatures that exist in the timeseries but not the alerts CSV ##########')
    print(sig_only_timeseries)
    output_string = ",".join(map(str, sig_only_timeseries))
    with open(output_folder + "/sig_only_timeseries_output.txt", "w") as f:
        f.write(output_string)

def check_alert_csv_bug_compatibility(alerts_df, bugs_df, output_folder, generate_ouput=True, prefix=""):
    #checks the mutually exclusive bug IDs between the bugs CSV and the alerts CSV
    bug_id_bug_csv = set(bugs_df['bug_id'].dropna().unique().flatten())
    bug_id_bug_csv = {int(x) for x in bug_id_bug_csv}
    bug_id_alert_csv = set(alerts_df['alert_bug_number'].dropna().unique().flatten())
    bug_id_alert_csv = {int(x) for x in bug_id_alert_csv}
    # These are the bugs that exist only in the alerts CSV but not in the bugs CSV (perhaps they were added in September by the new refresh or they belong to the mozilla-central/mozilla-release)
    bug_only_alert_csv = bug_id_alert_csv - bug_id_bug_csv
    # These are the bugs that exist only in the bugs CSV but not the alerts CSV (perhaps they were removed in September by the new refresh)
    bug_only_bug_csv =  bug_id_bug_csv - bug_id_alert_csv
    print("Report of bugs compability between bugs CSV and alerts CSV:")
    print('########## The bugs that exist in the alerts CSV but not the bugs CSV ##########')
    print(bug_only_alert_csv)
    if generate_ouput:
        output_string = ",".join(map(str, bug_only_alert_csv))
        with open(output_folder + "/" + prefix + "_bug_only_alert_csv_output.txt", "w") as f:
            f.write(output_string)
    print('########## The bugs that exist in the bugs but not the alerts CSV ##########')
    print(bug_only_bug_csv)
    output_string = ",".join(map(str, bug_only_bug_csv))
    if generate_ouput:
        with open(output_folder + "/" + prefix + "_bug_only_bug_csv_output.txt", "w") as f:
            f.write(output_string)

def main():
    args = parse_args()
    input_folder = args.input_folder
    alerts_file = args.alerts_file
    old_alerts_file = args.old_alerts_file
    bugs_file = args.bugs_file
    output_folder = args.output_folder
    alerts_df = pd.read_csv(alerts_file)
    old_alerts_df = pd.read_csv(old_alerts_file)
    bugs_df = pd.read_csv(bugs_file)
    #check_csv_sig_timesries_sig_compatibility(alerts_df, input_folder, output_folder)
    check_alert_csv_bug_compatibility(alerts_df, bugs_df, output_folder, False)
    check_alert_csv_bug_compatibility(old_alerts_df, bugs_df, output_folder, False, "old")
if __name__ == "__main__":
    main()