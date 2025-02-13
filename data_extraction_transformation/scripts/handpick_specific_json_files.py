import os
import shutil
import pandas as pd
import json
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="Handpick specific timeseries JSON files along with their annotations.json to run them on TCPCBench.")
    parser.add_argument('-o', '--output-folder', help="Path to the output folder of time series JSON files.")
    parser.add_argument('-i', '--input-folder', help="Path to the input folder of time series JSON files.")
    parser.add_argument('-f', '--filtered-singatures-file', help="Path to the CSV file with the signatures to handpick (it has to have a column signature_id).")

    return parser.parse_args()

'''main_dir = "../datasets-original-annotated-2-aggregated-min-json"
dest = "../filtered-datasets-original-annotated-2-aggregated-min-json"
filtered_signatures_file = "../datasets/more_than_10_alert_summaries_speedometer3_tp6.csv"'''


def main():
    args = parse_args()
    main_dir = args.input_folder
    filtered_signatures_file = args.filtered_signatures_file
    dest = args.output_folder
    df = pd.read_csv(filtered_signatures_file)
    signatures = df['signature_id'].unique().tolist()
    signatures = list(map(str, signatures))


    subfolders = [os.path.join(main_dir, folder) for folder in os.listdir(main_dir) if os.path.isdir(os.path.join(main_dir, folder))]
    if not subfolders:
        subfolders = [main_dir]  # Add main_dir if no subfolders exist

    annotations_file_path = os.path.join(main_dir, "annotations.json")


    if not os.path.exists(dest):
        os.makedirs(dest)
    counter = 0
    for subfolder in subfolders:
        for root, _, files in os.walk(subfolder):
            for file in files:
                if file.endswith(".json"):
                    json_file_path = os.path.join(root, file)
                    #print(json_file_path)
                    file_name = os.path.splitext(file)[0]
                    #print(file_name)
                    if file_name in signatures:
                        #print(file_name.split('.')[0])
                        shutil.copy(json_file_path, dest)
                        counter += 1

    with open(annotations_file_path, 'r') as f:
        annotations_data = json.load(f)

    filtered_annotations = {sig: annotations_data[sig] for sig in signatures if sig in annotations_data}

    filtered_annotations_file_path = os.path.join(dest, "annotations.json")
    with open(filtered_annotations_file_path, 'w') as f:
        json.dump(filtered_annotations, f, indent=4)
    print("Numer of copied JSON files:")
    print(counter)


if __name__ == "__main__":
    main() 