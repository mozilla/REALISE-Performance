import argparse
import os
import random
import json
import shutil

def main():
    parser = argparse.ArgumentParser(description="Randomly select JSON files from nested folders.")
    parser.add_argument('-i', '--input-folder', help="Path to the input folder", required=True)
    parser.add_argument('-o', '--output-folder', help="Path to the output folder", required=True)
    parser.add_argument('-c', '--count', type=int, help="Number of JSON files to select", required=True)
    args = parser.parse_args()

    input_folder = args.input_folder
    output_folder = args.output_folder
    count = args.count

    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Load annotations
    input_annotations_path = os.path.join(input_folder, 'annotations.json')
    with open(input_annotations_path, 'r') as f:
        annotations = json.load(f)

    # Find all JSON files in subfolders (excluding annotations.json)
    json_files = []
    for root, _, files in os.walk(input_folder):
        for file in files:
            if file.endswith('.json') and file != 'annotations.json':
                json_files.append(os.path.join(root, file))

    # Randomly select JSON files
    selected_files = random.sample(json_files, min(count, len(json_files)))

    # Prepare output annotations dictionary
    output_annotations = {}

    # Copy selected files and collect their annotations
    for filepath in selected_files:
        rel_path = os.path.relpath(filepath, input_folder)
        output_path = os.path.join(output_folder, rel_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        shutil.copy(filepath, output_path)

        # Get the base filename without extension
        base_name = os.path.splitext(os.path.basename(filepath))[0]
        if base_name in annotations:
            output_annotations[base_name] = annotations[base_name]

    # Save output annotations.json
    output_annotations_path = os.path.join(output_folder, 'annotations.json')
    with open(output_annotations_path, 'w') as f:
        json.dump(output_annotations, f, indent=2)

if __name__ == "__main__":
    main()
