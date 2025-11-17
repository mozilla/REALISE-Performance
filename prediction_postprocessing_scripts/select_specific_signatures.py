import argparse
import os
import shutil
import json

def main():
    # Argument parser
    parser = argparse.ArgumentParser(description="Copy selected subfolders and print sig_IDs.")
    parser.add_argument('--input-folder', required=True, help="Path to input folder containing subfolders.")
    parser.add_argument('--annotations', required=True, help="Path to annotations.json file.")
    parser.add_argument('--output-folder', required=True, help="Path to output folder.")
    args = parser.parse_args()

    input_folder = args.input_folder
    annotations_path = args.annotations
    output_folder = args.output_folder

    # Load JSON
    with open(annotations_path, 'r') as f:
        annotations = json.load(f)

    # Extract sig_IDs (top-level keys)
    sig_ids = list(annotations.keys())

    # Print formatted sig_IDs
    quoted_sig_ids = [f'"{sig_id}"' for sig_id in sig_ids]
    print(", ".join(quoted_sig_ids))

    # Make sure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Copy subfolders
    for sig_id in sig_ids:
        src = os.path.join(input_folder, sig_id)
        dst = os.path.join(output_folder, sig_id)

        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
            print(f"Copied: {sig_id}")
        else:
            print(f"Skipped: {sig_id} (not found in input_folder)")

if __name__ == "__main__":
    main()
