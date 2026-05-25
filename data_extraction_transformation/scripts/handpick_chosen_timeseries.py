import os
import shutil
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Extract CSV files that have a corresponding JSON file.")
    parser.add_argument('-c', '--csv-folder', required=True, help="Path to the folder containing subfolders with CSV files.")
    parser.add_argument('-j', '--json-folder', required=True, help="Path to the folder containing JSON files.")
    parser.add_argument('-o', '--output-folder', required=True, help="Path to the output folder.")
    return parser.parse_args()

def main():
    args = parse_args()
    csv_folder = args.csv_folder
    json_folder = args.json_folder
    output_folder = args.output_folder

    # Collect all JSON IDs
    json_ids = {
        os.path.splitext(f)[0]  # filename without .json extension = ID
        for f in os.listdir(json_folder)
        if f.endswith(".json")
    }
    print(f"Found {len(json_ids)} JSON files.")

    os.makedirs(output_folder, exist_ok=True)

    matched = 0
    skipped = 0

    for root, _, files in os.walk(csv_folder):
        for file in files:
            if not file.endswith("_timeseries_data.csv"):
                continue
            # Extract ID from filename: <ID>_timeseries_data.csv
            csv_id = file.replace("_timeseries_data.csv", "")
            if csv_id in json_ids:
                src = os.path.join(root, file)
                dst = os.path.join(output_folder, file)
                shutil.copy2(src, dst)
                matched += 1
            else:
                skipped += 1

    print(f"Matched and copied: {matched} CSV files.")
    print(f"Skipped (no matching JSON): {skipped} CSV files.")

if __name__ == "__main__":
    main()