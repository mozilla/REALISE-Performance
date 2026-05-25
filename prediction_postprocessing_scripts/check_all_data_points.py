import json
import argparse
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="Summarize n_obs across all JSON files in a folder.")
    parser.add_argument('-f', '--folder', required=True, help="Path to the folder containing JSON files.")
    return parser.parse_args()

def main():
    args = parse_args()
    folder = Path(args.folder)
    
    values = []
    for json_file in folder.glob('*.json'):
        with open(json_file) as f:
            data = json.load(f)
        values.append(data['n_obs'])

    values.sort()
    total = sum(values)
    average = total / len(values)
    mid = len(values) // 2
    median = values[mid] if len(values) % 2 != 0 else (values[mid - 1] + values[mid]) / 2

    print(f"Number of time series : {len(values)}")
    print(f"Total n_obs           : {total}")
    print(f"Average n_obs         : {average:.2f}")
    print(f"Median n_obs          : {median:.2f}")

if __name__ == "__main__":
    main()