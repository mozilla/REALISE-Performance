import os
import json
import pandas as pd
import argparse

def process_csv_files(folder_path, output_json):
    result = {}

    # Get all CSV files in the folder
    csv_files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]

    for csv_file in csv_files:
        file_path = os.path.join(folder_path, csv_file)

        # Read CSV
        df = pd.read_csv(file_path)

        # Ensure there is only one unique signature_id
        unique_ids = df["signature_id"].unique()
        if len(unique_ids) != 1:
            print(f"Skipping {csv_file}: Expected 1 unique signature_id, found {len(unique_ids)}")
            continue

        signature_id = str(unique_ids[0])  # Convert to string for JSON keys

        # Get the row indices where alert_summary_status_general is TP, FP, or SP
        valid_rows = df[df["alert_summary_status_general"].isin(["TP", "FP", "SP"])].index.tolist()

        # Store results in expected format
        result[signature_id] = {"1": valid_rows}

    # Save JSON file
    with open(output_json, "w") as json_file:
        json.dump(result, json_file, indent=4)

    print(f"JSON saved to {output_json}")

def main():
    parser = argparse.ArgumentParser(description="Convert CSV files in a folder to JSON format.")
    parser.add_argument("-f", "--folder", required=True, help="Path to the folder containing CSV files")
    parser.add_argument("-o", "--output", required=True, help="Path to save the output JSON file")

    args = parser.parse_args()

    process_csv_files(args.folder, args.output)

if __name__ == "__main__":
    main()
