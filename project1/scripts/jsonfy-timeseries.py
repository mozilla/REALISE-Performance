import os
import pandas as pd
import json


projects_folders = ["autoland1", "autoland2", "autoland3", "autoland4", "firefox-android", "mozilla-central", "mozilla-beta", "mozilla-release"]

with open('tp6_signatures.txt', 'r') as file:
    tp6_signatures = file.read().split(',')
with open('speedometer3_signatures.txt', 'r') as file:
    speedometer3_signatures = file.read().split(',')

filtered_signatures = speedometer3_signatures + tp6_signatures
filtered_signatures = [str(i) for i in filtered_signatures]

annotations = dict()
for project in projects_folders:
    for signature_file in os.listdir('../datasets/' + project):
        signature_id = signature_file.split("_")[0]
        if (isinstance(filtered_signatures, list) and signature_id in filtered_signatures):
            df = pd.read_csv('../datasets/' + project + '/' + signature_file)
            df['alert_status'] = df['alert_status'].apply(lambda x: 1 if x == 'FP' else 0)
            indices = df.index[df['alert_status'] == 1].tolist()
            indices.sort()
            new_entry = {
                "1": indices
            }
            annotations[signature_id] = new_entry
            with open('../datasets-json/annotations.json', 'w') as file:
                json.dump(annotations, file, indent=4)
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
            with open('../datasets-json/' + project + '/' + signature_json_file, 'w') as file:
                json.dump(json_df, file, indent=4)