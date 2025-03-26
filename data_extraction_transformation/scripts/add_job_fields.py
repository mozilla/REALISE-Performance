import os
import pandas as pd
import numpy as np
import shutil
import argparse
import requests

def parse_args():
    parser = argparse.ArgumentParser(description="Script to cross-reference the data of the time series with the alerts data")
    parser.add_argument('-i', '--input-folder', required=True, help="Path to the input dataset folder")
    parser.add_argument('-o', '--output-folder', required=True, help="Path of the folder ouputting CSV timeseries files")
    return parser.parse_args()


def fetch_job_details(job_id, project_name):
    global fields
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    if pd.isna(job_id):
        return {"job_" + field: np.nan for field in fields}

    url = f"https://treeherder.mozilla.org/api/project/{project_name}/jobs/{int(job_id)}/"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {"job_" + field: data.get(field, np.nan) for field in fields}
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching job {job_id}: {e}")
        return {"job_" + field: np.nan for field in fields}


def process_folder(input_folder, output_folder, folder):
    global problematic_signatures
    global fields
    fields = [
        "build_architecture", "build_os", "build_platform", "build_platform_id", "build_system_type", "taskcluster", "end_timestamp", "failure_classification_id",
        "job_group_description", "job_group_id", "job_group_name", "job_group_symbol", "job_guid", "job_type_description", "job_type_id", "job_type_name",
        "job_type_symbol", "last_modified", "machine_name", "machine_platform_architecture", "machine_platform_os", "platform",
        "reason", "ref_data_name", "result", "result_set_id", "start_timestamp", "state", "submit_timestamp", "tier", "platform_option", "task_id", "retry_id"
    ]
    project_name = folder
    for signature_file in os.listdir(input_folder + '/' + folder):
        df = pd.read_csv(input_folder + '/' + folder + '/' + signature_file, index_col=False)
        # df = pd.read_csv('../datasets/' + folder + '/' + signature_file, index_col=False)[["job_id", "entry_id", "push_timestamp", "value", "revision", "push_id", "repository_name", "test", "lower_is_better", "name", "parent_signature", "repository_id", "measurement_unit", "application", "has_subtests", "tags", "extra_options", "signature_id", "framework_id" , "signature_hash", "option_collection_hash", "machine_platform", "suite", "should_alert"]]
        df["push_timestamp"] = pd.to_datetime(df["push_timestamp"], format='mixed')
        df = df.join(df["job_id"].apply(lambda job_id: fetch_job_details(job_id, project_name)).apply(pd.Series))
        df.sort_values(by="push_timestamp", ascending=True)
        df["job_submit_timestamp"] = pd.to_datetime(df["job_submit_timestamp"], unit="s").dt.strftime("%Y-%m-%dT%H:%M:%S")
        df["job_start_timestamp"] = pd.to_datetime(df["job_start_timestamp"], unit="s").dt.strftime("%Y-%m-%dT%H:%M:%S")
        df["job_end_timestamp"] = pd.to_datetime(df["job_end_timestamp"], unit="s").dt.strftime("%Y-%m-%dT%H:%M:%S")

        df["job_submit_timestamp"] = pd.to_datetime(df["job_submit_timestamp"], format="%Y-%m-%dT%H:%M:%S")
        df["job_start_timestamp"] = pd.to_datetime(df["job_start_timestamp"], format="%Y-%m-%dT%H:%M:%S")
        df["job_end_timestamp"] = pd.to_datetime(df["job_end_timestamp"], format="%Y-%m-%dT%H:%M:%S")
        # df["job_submit_timestamp"] = pd.to_datetime(df["job_submit_timestamp"], format='%Y-%m-%dT%H:%M:%S', errors='coerce')
        # df["job_start_timestamp"] = pd.to_datetime(df["job_start_timestamp"], format='%Y-%m-%dT%H:%M:%S', errors='coerce')
        # df["job_end_timestamp"] = pd.to_datetime(df["job_end_timestamp"], format='%Y-%m-%dT%H:%M:%S', errors='coerce')
        df["push_submission_delta"] = (df["job_submit_timestamp"] - df["push_timestamp"]).dt.total_seconds() / 3600
        df.to_csv(output_folder + '/' + folder + '/' + signature_file, index=False)


def main():
    global problematic_signatures
    global df_alerts
    global category_mapping
    global alert_summary_status_mapping
    global alert_status_mapping
    args = parse_args()
    input_folder = args.input_folder
    output_folder = args.output_folder
    problematic_signatures = []
    
    projects_folders_mapping = {name: [name] for name in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, name))}

    os.makedirs(output_folder, exist_ok=True)
    for project in projects_folders_mapping:
        for folder in projects_folders_mapping[project]:
            os.makedirs(output_folder + '/' + folder, exist_ok=True)
            process_folder(input_folder, output_folder, folder)
            # shutil.rmtree('../datasets/' + folder)
            # os.rename('../datasets/' + folder + "-processed", '../datasets/' + folder)

    print('####### Problematic signatures #######')
    for sig in problematic_signatures:
        print('Signature path:')
        print(sig)

if __name__ == "__main__":
    main()


