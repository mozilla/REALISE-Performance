import pandas as pd
import json
import os
import shutil


'''
{
	"command": "/TCPDBench/execs/python/cpdbench_zero.py -i /TCPDBench/datasets/4405556.json",
	"dataset": "4405556",
	"dataset_md5": "311477a9dccc391e2ca6e04e4bf74187",
	"error": null,
	"hostname": "0ecb21cdbe86",
	"parameters": {},
	"result": {
		"cplocations": [],
		"runtime": 4.76837158203125e-07
	},
	"script": "/TCPDBench/execs/python/cpdbench_zero.py",
	"script_md5": "95b65ddd5669b41385966a4aad387118",
	"status": "SUCCESS"
}
'''



def write_json(dict_sig, sig_path, conf):
    path = sig_path + '/' + conf
    os.makedirs(path, exist_ok=True)
    with open(path + '/' + conf + '.json', 'w') as file:
        json.dump(dict_sig, file, indent=4)


df = pd.read_csv("../datasets/more_than_10_alert_summaries_speedometer3_tp6.csv")
signatures = df['signature_id'].unique().tolist()
signatures = list(map(str, signatures))

input_folder = '../datasets-original-annotated-2-aggregated'
output_folder = '../filtered-datasets-original-annotated-2-aggregated-tcpdbench-2'

problematic_signatures = []

def process_folder(folder):
    for signature_file in os.listdir(input_folder + '/' + folder):
        df = pd.read_csv(input_folder + '/' + folder + '/' + signature_file, index_col=False)
        sig = signature_file.split('_')[0]
        try:
            dict_sig = dict()
            dict_sig['error'] = None
            dict_sig['command'] = 'no_command'
            dict_sig['script'] = 'no_script'
            dict_sig['script_md5'] = 'no_script'
            dict_sig['hostname'] = "no_host"
            dict_sig['dataset'] = sig
            dict_sig['dataset_md5'] = sig + '_md5'
            dict_sig['status'] = 'SUCCESS'
            dict_sig['parameters'] = {'method': 'Mozilla'}
            cplocations = sorted(df[df['alert_status_general'].isin(['TP', 'SP', 'FP'])].index.tolist())
            dict_sig['result'] = {'cplocations': cplocations, 'runtime': 0}
            dict_sig['args'] = {'method': 'Mozilla'}
            output_path = output_folder + '/' + sig
            if sig in signatures:
                os.makedirs(output_path, exist_ok=True)
                write_json(dict_sig, output_path, 'best_mozilla')
                write_json(dict_sig, output_path, 'default_mozilla')
        except:
            problematic_signatures.append(sig)

projects_folders_mapping = {"autoland": ["autoland1", "autoland2", "autoland3", "autoland4"], "firefox-android": ["firefox-android"], "mozilla-beta": ["mozilla-beta"], "mozilla-release": ["mozilla-release"], "mozilla-central": ["mozilla-central"]}
os.makedirs(output_folder, exist_ok=True)
if projects_folders_mapping:
    for project in projects_folders_mapping:
        for folder in projects_folders_mapping[project]:
            # os.makedirs(output_folder + '/' + folder, exist_ok=True)
            process_folder(folder)
            #shutil.rmtree('../datasets/' + folder)
            #os.rename('../datasets/' + folder + "-processed", '../datasets/' + folder)
else:
    process_folder(input_folder)
print('####### Problematic signatures #######')
for sig in problematic_signatures:
    print('Signature path:')
    print(sig)