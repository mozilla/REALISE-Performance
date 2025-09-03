import os
import argparse
import pandas as pd

def main(json_folder, csv_file, output_dir):
    # Load signature IDs from JSON files
    json_ids = {os.path.splitext(f)[0] for f in os.listdir(json_folder) if f.endswith('.json')}

    # Load signature IDs from the CSV file
    df = pd.read_csv(csv_file)
    csv_ids = set(df['DatasetName'].astype(str).str.strip())

    # Determine picked and non-picked
    picked = json_ids & csv_ids
    non_picked = json_ids - csv_ids
    in_csv_not_in_folder = csv_ids - json_ids

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Write picked and non-picked to files
    picked_path = os.path.join(output_dir, 'picked.txt')
    non_picked_path = os.path.join(output_dir, 'non_picked.txt')

    with open(picked_path, 'w') as f:
        f.write('\n'.join(sorted(picked)))

    with open(non_picked_path, 'w') as f:
        f.write('\n'.join(sorted(non_picked)))

    # Print IDs in CSV but not in folder
    print("Signature IDs in CSV but not in folder:")
    for sid in sorted(in_csv_not_in_folder):
        print(sid)

    # Print counts
    print(f"\nCount in picked.txt: {len(picked)}")
    print(f"Count in non_picked.txt: {len(non_picked)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare signature IDs between folder and CSV.")
    parser.add_argument("--json-folder", required=True, help="Path to folder containing JSON files")
    parser.add_argument("--csv-file", required=True, help="Path to CSV file")
    parser.add_argument("--output-dir", required=True, help="Directory where output text files will be saved")

    args = parser.parse_args()
    main(args.json_folder, args.csv_file, args.output_dir)
