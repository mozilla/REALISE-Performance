import json
import os
import pandas as pd

# Define the folder containing the JSON files
folder_path = 'showcase-diagram-results/JSON2'

# A dictionary to hold results with unique args as keys
results = {}

# Iterate through each JSON file in the folder
for file_name in os.listdir(folder_path):
    if file_name.endswith('.json'):
        file_path = os.path.join(folder_path, file_name)
        with open(file_path) as json_file:
            data = json.load(json_file)
            for entry in data['results']['best_binseg']:
                args = tuple(entry['args'].items())  # Flatten args to use as a unique key
                
                if args not in results:
                    results[args] = {}
                
                # Handle the case where 'scores' might be None
                scores = entry.get('scores', {})
                if scores is None:
                    scores = {}  # If scores is None, treat it as an empty dictionary
                
                # Collect scores if available
                results[args][file_name] = {
                    'f1': scores.get('f1', None),
                    'precision': scores.get('precision', None),
                    'recall': scores.get('recall', None)
                }

# Create a DataFrame from the results
rows = []
for args, file_scores in results.items():
    flattened_args = ' '.join(f"{key}={value}" for key, value in args)  # Flatten args into a string
    row = {'args': flattened_args}
    for file_name, scores in file_scores.items():
        file_name_stripped = file_name.split("_")[1].split(".")[0]
        row[f"{file_name_stripped}_f1"] = scores.get('f1')
        row[f"{file_name_stripped}_precision"] = scores.get('precision')
        row[f"{file_name_stripped}_recall"] = scores.get('recall')
    rows.append(row)

# Convert rows to DataFrame and save to CSV
df = pd.DataFrame(rows)
df.to_csv('output2.csv', index=False)
