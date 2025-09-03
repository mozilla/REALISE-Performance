#!/usr/bin/env python3

import argparse
import pandas as pd
import json

def parse_args():
    parser = argparse.ArgumentParser(description="Convert annotation CSV to nested JSON format.")
    parser.add_argument("--input", required=True, help="Path to the input CSV file")
    parser.add_argument("--output", required=True, help="Path to the output JSON file")
    parser.add_argument("--top", type=int, default=None, help="Minimum number of unique users per dataset to include")
    return parser.parse_args()

def main():
    args = parse_args()
    
    df = pd.read_csv(args.input)

    # Exclude datasets that start with "demo_"
    df = df[~df["DatasetName"].astype(str).str.startswith("demo_")]

    temp = {}
    
    for _, row in df.iterrows():
        dataset = str(row["DatasetName"])
        user_id = str(row["UserID"])
        annotation_type = str(row["AnnotationType"]).strip()
        annotation_index = row["AnnotationIndex"]
        
        if dataset not in temp:
            temp[dataset] = {}
        
        if user_id not in temp[dataset]:
            temp[dataset][user_id] = []

        if annotation_type == "no_cp":
            temp[dataset][user_id] = []
        else:
            try:
                index = int(annotation_index)
                temp[dataset][user_id].append(index)
            except ValueError:
                continue
    
    # Apply --top filtering if requested
    result = {}
    for dataset, user_dict in temp.items():
        if args.top is None or len(user_dict) >= args.top:
            result[dataset] = {
                user: sorted(set(indices)) for user, indices in user_dict.items()
            }

    with open(args.output, "w") as f:
        json.dump(result, f, indent=4)
    print(len(result))

if __name__ == "__main__":
    main()