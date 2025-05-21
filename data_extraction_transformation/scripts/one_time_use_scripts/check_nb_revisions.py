import os
import json
import argparse

def find_low_n_obs_files(root_folder, threshold=200):
    low_n_obs_files = []

    for subdir, _, files in os.walk(root_folder):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(subdir, file)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    if 'n_obs' in data and data['n_obs'] < threshold:
                        low_n_obs_files.append((file_path, data['n_obs']))
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    return low_n_obs_files

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check for JSON files with n_obs < threshold.")
    parser.add_argument("-i", "--input-folder", help="Path to the root folder to search.")
    parser.add_argument("-t", "--threshold", type=int, default=200, help="Threshold value for n_obs (default: 200)")
    args = parser.parse_args()

    results = find_low_n_obs_files(args.input_folder, args.threshold)
    for result in results:
        print(result)
        print("\n")
