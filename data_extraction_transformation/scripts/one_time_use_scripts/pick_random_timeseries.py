import argparse
import os
import random
import json
import shutil

def main():
    parser = argparse.ArgumentParser(description="Randomly select JSON files from nested folders with n_obs >= 200.")
    parser.add_argument('-i', '--input-folder', help="Path to the input folder", required=True)
    parser.add_argument('-o', '--output-folder', help="Path to the output folder", required=True)
    parser.add_argument('-c', '--count', type=int, help="Number of JSON files to select", required=True)
    args = parser.parse_args()

    input_folder = args.input_folder
    output_folder = args.output_folder
    count = args.count

    os.makedirs(output_folder, exist_ok=True)

    # Load annotations
    input_annotations_path = os.path.join(input_folder, 'annotations.json')
    with open(input_annotations_path, 'r') as f:
        annotations = json.load(f)

    # Filter JSON files with n_obs >= 200
    valid_json_files = []
    for root, _, files in os.walk(input_folder):
        for file in files:
            if file.endswith('.json') and file != 'annotations.json':
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, 'r') as jf:
                        data = json.load(jf)
                    if 'n_obs' in data and data['n_obs'] >= 200:
                        valid_json_files.append(full_path)
                except Exception as e:
                    print(f"Skipping {full_path} due to error: {e}")

    if len(valid_json_files) < count:
        print(f"Error: Only {len(valid_json_files)} files with n_obs >= 200 found, but {count} requested.")
        return

    selected_files = random.sample(valid_json_files, count)
    output_annotations = {}

    for filepath in selected_files:
        rel_path = os.path.relpath(filepath, input_folder)
        output_path = os.path.join(output_folder, rel_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        shutil.copy(filepath, output_path)

        base_name = os.path.splitext(os.path.basename(filepath))[0]
        if base_name in annotations:
            output_annotations[base_name] = annotations[base_name]

    output_annotations_path = os.path.join(output_folder, 'annotations.json')
    with open(output_annotations_path, 'w') as f:
        json.dump(output_annotations, f, indent=2)

if __name__ == "__main__":
    main()
