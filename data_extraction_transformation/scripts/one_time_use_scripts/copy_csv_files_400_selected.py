#!/usr/bin/env python3

import argparse
import os
import shutil

def parse_args():
    parser = argparse.ArgumentParser(description="Copy CSVs from input2 to output1 if corresponding JSON exists in input1.")
    parser.add_argument("--input1", help="Path to folder with JSON files")
    parser.add_argument("--input2", help="Path to folder with subfolders containing CSV files")
    parser.add_argument("--output1", help="Destination folder to copy valid CSV files")
    return parser.parse_args()

def get_valid_ids_from_json(input1_folder):
    return {
        os.path.splitext(file)[0]
        for file in os.listdir(input1_folder)
        if file.endswith(".json")
    }

def copy_csvs_if_json_exists(input2_folder, output1_folder, valid_ids):
    os.makedirs(output1_folder, exist_ok=True)
    for root, _, files in os.walk(input2_folder):
        for file in files:
            if file.endswith("_timeseries_data.csv"):
                id_of_sig = file.replace("_timeseries_data.csv", "")
                if id_of_sig in valid_ids:
                    src = os.path.join(root, file)
                    dst = os.path.join(output1_folder, file)
                    shutil.copyfile(src, dst)

def main():
    args = parse_args()
    valid_ids = get_valid_ids_from_json(args.input1)
    copy_csvs_if_json_exists(args.input2, args.output1, valid_ids)

if __name__ == "__main__":
    main()
