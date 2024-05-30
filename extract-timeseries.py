import os
import requests
from datetime import datetime, timedelta
import pandas as pd
import json
import random

def get_json(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        json_data = response.json()
        return json_data
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None

def extract_from_list(lst, attr):
    the_list = ""
    try:
        if (len(lst[attr]) > 0):
            the_list = "|"
            for item in lst[attr]:
                the_list = the_list + str(item) + '|'
        return the_list
    except:
        return ""

def extract_sig_attr(signature_json):
    summary_entry = {
        "signature_id": signature_json["id"],
        "framework_id": signature_json["framework_id"],
        "signature_hash": signature_json["signature_hash"],
        "option_collection_hash": signature_json["option_collection_hash"],
        "machine_platform": signature_json["machine_platform"],
        "suite": signature_json["suite"],
        "should_alert": signature_json["should_alert"]
    }
    return summary_entry

def extract_summary(json_summary):
    summary_entry = {
        "repository_name": json_summary["repository_name"],
        "test": json_summary["test"],
        "lower_is_better": json_summary["lower_is_better"],
        "name": json_summary["name"],
        "parent_signature": json_summary["parent_signature"],
        "repository_id": json_summary["repository_id"],
        "measurement_unit": json_summary["measurement_unit"],
        "application": json_summary["application"],
        "has_subtests": json_summary["has_subtests"],
        "tags": extract_from_list(json_summary, "tags"),
        "extra_options": extract_from_list(json_summary, "extra_options")
    }
    return summary_entry

def extract_data(json_data):
    data_entry = {
        "job_id": json_data["job_id"],
        "entry_id": json_data["id"],
        "push_timestamp": json_data["push_timestamp"],
        "value": json_data["value"],
        "revision": json_data["revision"],
        "push_id": json_data["push_id"]
    }
    return data_entry

def csv_to_list(filename):
    with open(filename, 'r') as file:
        content = file.read().strip()
        ids = content.split(',')
        return ids

important_porjects = [
#    'firefox-android',
    "mozilla-central",
#    "mozilla-beta",
#    "mozilla-release",
#    "autoland"
]
unimportant_porjects = [
    "try",
    "android-components",
    "application-services",
    "ash",
    "birch",
    "cedar",
    "ci-admin",
    "ci-admin-try",
    "ci-configuration",
    "ci-configuration-try",
    "comm-beta",
    "comm-central",
    "comm-esr115",
    "comm-release",
    "elm",
    "fenix",
    "firefox-ios",
    "firefox-translations-training",
    "focus-android",
    "holly",
    "jamun",
    "kaios",
    "kaios-try",
    "larch",
    "maple",
    "mozilla-esr115",
    "mozilla-release",
    "mozilla-vpn-client",
    "mozilla-vpn-client-release",
    "nss",
    "nss-try",
    "oak",
    "pine",
    "reference-browser",
    "servo-auto",
    "servo-master",
    "servo-try",
    "staging-android-components",
    "staging-fenix",
    "staging-firefox-translations-training",
    "staging-focus-android",
    "taskgraph",
    "toolchains",
    "try-comm-central",
    "webrender"
]

columns = [
    "repository_name",
    "signature_id",
    "framework_id",
    "signature_hash",
    "machine_platform",
    "should_alert",
    "has_subtests",
    "extra_options",
    "tags",
    "option_collection_hash",
    "test",
    "suite",
    "lower_is_better",
    "name",
    "parent_signature",
    "repository_id",
    "measurement_unit",
    "application",
    "job_id",
    "entry_id",
    "push_timestamp",
    "value",
    "revision",
    "push_id"
]

# autoland total signatures number : 69173
# number of unique signatures in the alerts dataset : 6085
n = 1000

filtered_sig_ids = csv_to_list("signatures.txt")

def extract_timeseries(project):
    signature_url = "https://treeherder.mozilla.org/api/project/" + project + "/performance/signatures/"
    signatures_json = get_json(signature_url)
    cond = lambda x: str(x[1]["id"]) in filtered_sig_ids
    signatures_json = dict(filter(cond, signatures_json.items()))
    '''
    with open(project + '/buffer.txt', 'a+') as file:
        lines = file.readlines()
        ids = [line.strip("| \n") for line in lines]
        available_keys = [key for key in signatures_json.keys() if key not in ids]
        min_nb = min(n, len(available_keys))
        random_keys = random.sample(available_keys, min_nb)
        random_dict = {key: signatures_json[key] for key in random_keys}
        keys_string = "".join([f"|{key}|\n" for key in random_dict.keys()])
        file.write(keys_string + "\n")
    '''
    with open(project + '/buffer.txt', 'a+') as file:
        file.seek(0)
        lines = file.readlines()
        ids = [line.strip("| \n") for line in lines]
        ids = [id for id in ids if id]
        file.seek(0, 2)
        available_keys = [key for key in signatures_json.keys() if key not in ids]
        available_elems_dict = {key: signatures_json[key] for key in available_keys}
        keys_string = "".join([f"|{key}|\n" for key in available_elems_dict.keys()])
        file.write(keys_string + "\n")
        file.flush()
    #for signature_id in signatures_json:
    for signature_id in available_elems_dict:
        signature_attributes = extract_sig_attr(available_elems_dict[signature_id])
        framework_id = available_elems_dict[signature_id]["framework_id"]
        summary_url = "https://treeherder.mozilla.org/api/performance/summary/?repository=" + project + "&signature=" + str(signature_id) + "&framework=" + str(framework_id) + "&interval=126144000&all_data=true&replicates=false"
        summaries_json = get_json(summary_url)
        if (len(summaries_json) > 0):
            summary_json = summaries_json[0]
            summary_attributes = extract_summary(summary_json)
            df = pd.DataFrame(columns=columns)
            for timeseries_entry in summary_json["data"]:
                new_row = signature_attributes
                new_row.update(summary_attributes)
                data_attributes = extract_data(timeseries_entry)
                new_row.update(data_attributes)
                new_row_df = pd.DataFrame(new_row, index=[0])
                df = pd.concat([df, new_row_df], ignore_index=True)
            df.to_csv(project + '/' + signature_id + '_timeseries_data.csv', header=True, mode='w', index=False)

#for project in ["mozilla-central"]:
for project in important_porjects:
    if not os.path.exists(project):
        os.makedirs(project)
    extract_timeseries(project)
#for project in important_porjects:

            #df.to_csv('timeseries_data.csv', mode='a', index=False)
# repository_name,signature_id,framework_id,signature_hash,platform,test,suite,lower_is_better,name,parent_signature,repository_id,measurement_unit,application,job_id,id,push_timestamp,value,revision

