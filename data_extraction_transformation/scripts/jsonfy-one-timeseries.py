import os
import pandas as pd
import json

true_alerting_mapping = ['TP', 'FN']
y_column = 'alert_status_general'
input_dir = 'datasets-original-annotated-2-aggregated/autoland3/'
input_file = '4361184_timeseries_data.csv'
input_signature_path = input_dir + input_file
dest_folder = 'demo_signature_test'

os.makedirs('../../' + dest_folder, exist_ok=True)


annotations = dict()
signature_id = "4361184"
df = pd.read_csv('../' + input_signature_path)
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

with open('../../' + dest_folder + '/' + signature_json_file, 'w') as file:
    json.dump(json_df, file, indent=4)

with open('../../' + dest_folder + '/annotations.json', 'a') as file:
    json.dump(annotations, file, indent=4)