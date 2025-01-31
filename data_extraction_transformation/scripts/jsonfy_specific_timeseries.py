import os
import pandas as pd
import json
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="JSONfy ONLY specific timeseries CSVs")
    parser.add_argument('-i', '--input-folder', help="Path to the input CSV timeseries folder")
    parser.add_argument('-o', '--output-folder', help="Path to the output CSV timeseries folder")
    return parser.parse_args()

def main():
    args = parse_args()
    input_folder = args.input_folder
    output_folder = args.output_folder
    true_alerting_mapping = ['TP', 'FN']
    y_column = 'alert_summary_status_general'
    os.makedirs(output_folder, exist_ok=True)
    annotations = dict()
    for signature_file in os.listdir(input_folder):
        signature_id = signature_file.split("_")[0]
        df = pd.read_csv(input_folder + '/' + signature_file)
        df[y_column] = df[y_column].apply(lambda x: 1 if x in true_alerting_mapping else 0)
        df = df.sort_values(by='push_timestamp', ascending=True)
        indices = df.index[df[y_column] == 1].tolist()
        indices.sort()
        new_entry = {
            "1": indices
        }
        annotations[signature_id] = new_entry
        n_obs = len(df)
        json_df = {
            "name": signature_id,
            "longname": f"{signature_id} timeseries",
            "n_obs": n_obs,
            "n_dim": 1,
            "time": {
                "type": "string",
                "format": "%Y-%m-%d %H:%M:%S",
                "index": list(range(n_obs)),
                "raw": df['push_timestamp'].tolist()
            },
            "series": [
                {
                    "label": "Timeseries",
                    "type": "float",
                    "raw": df['value'].tolist()
                }
            ]
        }
        signature_json_file = signature_id + ".json"
        with open(output_folder + '/' + signature_json_file, 'w') as file:
            json.dump(json_df, file, indent=4)
                
                
    with open(output_folder + '/annotations.json', 'a') as file:
        json.dump(annotations, file, indent=4)

if __name__ == "__main__":
    main()