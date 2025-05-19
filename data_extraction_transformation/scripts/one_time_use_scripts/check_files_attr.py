import argparse
import os
import json

def main():
    parser = argparse.ArgumentParser(description="Check if JSON files have corresponding entries in data_timeseries_attributes.json.")
    parser.add_argument('-i', '--input-folder', help="Path to the input folder containing JSON files", required=True)
    parser.add_argument('-a', '--attributes-json', help="Path to data_timeseries_attributes.json", required=True)
    args = parser.parse_args()

    # Load the attributes JSON
    with open(args.attributes_json, 'r') as f:
        attributes = json.load(f)

    # Collect all JSON filenames (excluding the attributes JSON itself)
    missing_entries = []
    for root, _, files in os.walk(args.input_folder):
        for file in files:
            if file.endswith('.json') and file != os.path.basename(args.attributes_json):
                file_key = os.path.splitext(file)[0]
                if file_key not in attributes:
                    relative_path = os.path.relpath(os.path.join(root, file), args.input_folder)
                    missing_entries.append((file_key, relative_path))

    # Output results
    if missing_entries:
        print("❌ Missing entries in data_timeseries_attributes.json for the following files:")
        for file_key, rel_path in missing_entries:
            print(f"  - {rel_path} (missing key: '{file_key}')")
    else:
        print("✅ All JSON files have corresponding entries in the attributes JSON.")

if __name__ == "__main__":
    main()
