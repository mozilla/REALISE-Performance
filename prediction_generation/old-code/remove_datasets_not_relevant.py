#!/usr/bin/env python3

import argparse
import json
import os

def parse_args():
    parser = argparse.ArgumentParser(description="Remove JSON files not referenced in annotations.json.")
    parser.add_argument("--annotations", required=True, help="Path to annotations.json file")
    parser.add_argument("--input-folder", required=True, help="Path to folder containing JSON files")
    return parser.parse_args()

def main():
    args = parse_args()

    # Load valid IDs from annotations.json
    with open(args.annotations, "r") as f:
        valid_ids = set(json.load(f).keys())

    # List all .json files in input_folder
    for filename in os.listdir(args.input_folder):
        if filename.endswith(".json"):
            file_id = os.path.splitext(filename)[0]
            if file_id not in valid_ids:
                file_path = os.path.join(args.input_folder, filename)
                os.remove(file_path)
                print(f"Removed: {file_path}")

if __name__ == "__main__":
    main()
