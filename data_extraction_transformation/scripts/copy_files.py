import os
import shutil
import pandas as pd
import json

df = pd.read_csv("../datasets/more_than_10_alert_summaries_speedometer3_tp6.csv")
signatures = df['test_series_signature_id'].unique().tolist()
signatures = list(map(str, signatures))

main_dir = "../datasets-original-annotated-2-aggregated-min-json"
subfolders = [os.path.join(main_dir, folder) for folder in os.listdir(main_dir) if os.path.isdir(os.path.join(main_dir, folder))]
annotations_file_path = os.path.join(main_dir, "annotations.json")
dest = "../filtered-datasets-original-annotated-2-aggregated-min-json"

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