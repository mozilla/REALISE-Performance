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
    parser.add_argument('-m', '--margin', help="Tolerance margin to check before and after it")
    return parser.parse_args()

def process_folder(input_folder, folder, margin):
    global sp_only_tn_count
    global sp_other_values_count
    global sp_with_tp
    global sp_with_fp
    global sp_with_fn
    global sp_with_sp
    global total_sig
    global total_sp_sig
    for signature_file in os.listdir(input_folder + '/' + folder):
        total_sig += 1
        df = pd.read_csv(input_folder + '/' + folder + '/' + signature_file, index_col=False)
        df['push_timestamp'] = pd.to_datetime(df['push_timestamp'])
        df = df.sort_values(by='push_timestamp')
        df = df[['revision', 'signature_id', 'value', 'alert_status_general', 'push_timestamp']]
        sp_only_tn_count_temp = 0
        sp_other_values_count_temp = 0
        sp_with_tp_temp = 0
        sp_with_fp_temp = 0
        sp_with_fn_temp = 0
        sp_with_sp_temp = 0
        contains_sp = False
        for idx, row in df.iterrows():
            if row['alert_status_general'] == 'SP':
                contains_sp = True
                start_idx = max(0, idx - margin)
                end_idx = min(len(df), idx + margin + 1)
                buffer_values = df.loc[start_idx:end_idx, 'alert_status_general']
                buffer_values = buffer_values[buffer_values.index != idx]
                if all(value == 'TN' for value in buffer_values):
                    sp_only_tn_count_temp += 1
                else:
                    sp_other_values_count_temp += 1
                    if 'TP' in buffer_values.values:
                        sp_with_tp_temp += 1
                    if 'FP' in buffer_values.values:
                        sp_with_fp_temp += 1
                    if 'FN' in buffer_values.values:
                        sp_with_fn_temp += 1
                    if 'SP' in buffer_values.values:
                        sp_with_sp_temp += 1
        sp_only_tn_count += sp_only_tn_count_temp
        sp_other_values_count += sp_other_values_count_temp
        sp_with_tp += sp_with_tp_temp
        sp_with_fp += sp_with_fp_temp
        sp_with_fn += sp_with_fn_temp
        sp_with_sp += sp_with_sp_temp
        if contains_sp:
            total_sp_sig += 1


def main():
    args = parse_args()
    global sp_only_tn_count
    global sp_other_values_count
    global sp_with_tp
    global sp_with_fp
    global sp_with_fn
    global sp_with_sp
    global total_sig
    global total_sp_sig
    total_sig = 0
    total_sp_sig = 0
    sp_only_tn_count = 0
    sp_other_values_count = 0
    sp_with_tp = 0
    sp_with_fp = 0
    sp_with_fn = 0
    sp_with_sp = 0
    input_folder = args.input_folder
    margin = int(args.margin)
    projects_folders_mapping = {"autoland": ["autoland1", "autoland2", "autoland3", "autoland4"], "firefox-android": ["firefox-android"], "mozilla-beta": ["mozilla-beta"]}
    if projects_folders_mapping:
        for project in projects_folders_mapping:
            for folder in projects_folders_mapping[project]:
                process_folder(input_folder, folder, margin)
    total_sp_occ = sp_only_tn_count + sp_other_values_count
    print("Total number of signatures")
    print(total_sig)
    print("Total number of signatures having at least one SP alert")
    print(total_sp_sig)
    print("Total number of occurrences of SP alerts")
    print(total_sp_occ)
    print("Percentage of occurrence of only TN points in the margin buffer of SP alerts")
    print(str("{:.2f}".format((sp_only_tn_count / total_sp_occ) * 100)) + " %")
    print("Percentage of occurrence of at least one alert (FP/TP/SP/FN) in the margin buffer of SP alerts")
    print(str("{:.2f}".format((sp_other_values_count / total_sp_occ) * 100)) + " %")
    print("Percentage of occurrence of at least one alert TP in the margin buffer of SP alerts")
    print(str("{:.2f}".format((sp_with_tp / sp_other_values_count) * 100)) + " %")
    print("Percentage of occurrence of at least one alert FP in the margin buffer of SP alerts")
    print(str("{:.2f}".format((sp_with_fp / sp_other_values_count) * 100)) + " %")
    print("Percentage of occurrence of at least one alert FN in the margin buffer of SP alerts")
    print(str("{:.2f}".format((sp_with_fn / sp_other_values_count) * 100)) + " %")
    print("Percentage of occurrence of at least one alert SP in the margin buffer of SP alerts")
    print(str("{:.2f}".format((sp_with_sp / sp_other_values_count) * 100)) + " %")
if __name__ == "__main__":
    main()