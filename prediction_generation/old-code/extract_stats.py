import os
import json
import pandas as pd

folder_path = 'ccresults'
df_dict = dict()


for filename in os.listdir(folder_path):
    if filename.endswith('.json'):
        file_path = os.path.join(folder_path, filename)
        signature = filename.split('_')[1].split('.')[0]
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
            results = data['results']['best_rfpop']
            for element in results:
                sorted_cluster = str(dict(sorted(element['parameters'].items())))
                if sorted_cluster in df_dict.keys():
                    df_dict[sorted_cluster][signature + '_f1'] = element['scores']['f1']
                    df_dict[sorted_cluster][signature + '_precision'] = element['scores']['precision']
                    df_dict[sorted_cluster][signature + '_recall'] = element['scores']['recall']
                else:
                    appendable_elem = {
                        signature + '_f1': element['scores']['f1'],
                        signature + '_precision': element['scores']['precision'],
                        signature + '_recall': element['scores']['recall'],
                    }
                    df_dict[sorted_cluster] = appendable_elem
df = pd.DataFrame.from_dict(df_dict, orient='index')
df.to_csv('results_extracted.csv')