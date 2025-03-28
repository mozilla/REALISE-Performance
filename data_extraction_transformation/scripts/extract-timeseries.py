import os
import requests
from datetime import datetime, timedelta
import pandas as pd
import json
import random
from helper import append_strings, get_json, txt_to_list
import argparse
 
'''
The following function extracts a list of strings associated with a given attribute and it appends them in a pipe-separated string
'''
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

'''
this function extracts signature attributes and returns them given a signature JSON
'''
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

 

'''
this function extracts signature summary attributes and returns them given a summary JSON
'''
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


def extract_timeseries(output_folder, project):
    global filtered_sig_ids
    global columns
    signature_url = "https://treeherder.mozilla.org/api/project/" + project + "/performance/signatures/"
    signatures_json = get_json(signature_url)
    cond = lambda x: x[1]["id"] in filtered_sig_ids
    signatures_json = dict(filter(cond, signatures_json.items()))
    # The purpose of this code is to avoid re-extracting time series that have already been extracted.
    # This is necessary because running the script in one go is not feasible due to the long time
    # required to extract all the time series at once.

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
    
    with open('../datasets/' + project + '/buffer.txt', 'a+') as file:
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
    for signature_id in available_elems_dict:
        signature_attributes = extract_sig_attr(available_elems_dict[signature_id])
        framework_id = available_elems_dict[signature_id]["framework_id"]
        '''
    for signature_id in signatures_json:
        signature_attributes = extract_sig_attr(signatures_json[signature_id])
        framework_id = signatures_json[signature_id]["framework_id"]
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
            df.to_csv(output_folder + '/' + project + '/' + signature_id + '_timeseries_data.csv', header=True, mode='w', index=False)






def parse_args():
    parser = argparse.ArgumentParser(description="Fetch timeseires details from an API and save to a folder of CSV files organized into separate folders per project.")
    parser.add_argument('-o', '--output-folder', help="Path to the output folder of time series CSV files.")
    parser.add_argument('-a', '--alerts-file', help="Path to the alerts CSV file.")

    return parser.parse_args()



def main():
    global filtered_sig_ids
    global columns
    args = parse_args()
    output_folder = args.output_folder
    alerts_file = args.alerts_file
    alerts_df = pd.read_csv(alerts_file)
    mentionned_projects = alerts_df['alert_summary_repository'].unique().tolist()
    filtered_sig_ids = alerts_df['signature_id'].unique().tolist()

    # For reference, these are all of the projects
    '''
    all_porjects = [
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
    '''

    '''
    The following list contains the columns names of the CSV to be generated through this script
    '''
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


    for project in mentionned_projects:
        if not os.path.exists(output_folder + '/' + project):
            os.makedirs(output_folder + '/' + project, exist_ok=True)
        extract_timeseries(output_folder, project)

if __name__ == "__main__":
    main()