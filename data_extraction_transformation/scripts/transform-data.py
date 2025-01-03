import os
import pandas as pd
import shutil
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Script to cross-reference the data of the time series with the alerts data")
    parser.add_argument('-i', '--input-folder', required=True, help="Path to the input dataset folder")
    parser.add_argument('-a', '--alerts-file', required=True, help="Path to the alerts CSV file")
    parser.add_argument('-o', '--output-folder', required=True, help="Path of the folder ouputting CSV timeseries files")
    return parser.parse_args()

def process_folder(input_folder, output_folder, folder):
    global problematic_signatures
    global cutoff_date_time
    global df_alerts
    for signature_file in os.listdir(input_folder + '/' + folder):
        try:
            df = pd.read_csv(input_folder + '/' + folder + '/' + signature_file, index_col=False)
            # df = pd.read_csv('../datasets/' + folder + '/' + signature_file, index_col=False)[["job_id", "entry_id", "push_timestamp", "value", "revision", "push_id", "repository_name", "test", "lower_is_better", "name", "parent_signature", "repository_id", "measurement_unit", "application", "has_subtests", "tags", "extra_options", "signature_id", "framework_id" , "signature_hash", "option_collection_hash", "machine_platform", "suite", "should_alert"]]
            df["push_timestamp"] = pd.to_datetime(df["push_timestamp"], format='%Y-%m-%dT%H:%M:%S', errors='coerce')
            # df["push_timestamp"] = pd.to_datetime(df['push_timestamp'], format='mixed')
            df = df[df['push_timestamp'] <= cutoff_date_time]
            df_merged = pd.merge(df, df_alerts, left_on=['revision', 'signature_id'], right_on=['alert_summary_revision', 'signature_id'], how='left')
            df_merged['alert_summary_status_general'].fillna('TN', inplace=True)
            df_final = df_merged.drop_duplicates()
            df_final.loc[df_final['single_alert_manually_created'] == True, 'alert_summary_status_general'] = "FN"
            df_final.sort_values(by="push_timestamp", ascending=True)
            if not df_final['alert_summary_id'].isna().all():
                df_final.to_csv(output_folder + '/' + folder + '/' + signature_file, index=False)
        except:
            problematic_signatures.append(folder + '/' + signature_file)

# input_folder = '../datasets-original'
# output_folder = '../datasets-original-annotated-test'
# alerts_df_path = '../datasets/2_rectified_alerts_data.csv'

def main():
    global problematic_signatures
    global cutoff_date_time
    global df_alerts
    global category_mapping
    global alert_summary_status_mapping
    global alert_status_mapping
    args = parse_args()
    input_folder = args.input_folder
    output_folder = args.output_folder
    alerts_file = args.alerts_file
    alert_summary_status_mapping = {
        0: "untriaged",
        1: "downstream",
        2: "reassigned",
        3: "invalid",
        4: "improvement",
        5: "investigating",
        6: "wontfix",
        7: "fixed",
        8: "backedout"
    }

    alert_status_mapping = {
        0: "untriaged",
        1: "downstream",
        2: "reassigned",
        3: "invalid",
        4: "acknowledged"
    }

    category_mapping = {
        'investigating': 'SP',
        'reassigned': 'TP',
        'invalid': 'FP',
        'improvement': 'TP',
        'fixed': 'TP',
        'wontfix': 'TP',
        'untriaged': 'SP',
        'backedout': 'TP',
        'downstream': 'TP',
        'acknowledged': 'TP',
    }
    problematic_signatures = []

    projects_folders_mapping = {"autoland": ["autoland1", "autoland2", "autoland3", "autoland4"], "firefox-android": ["firefox-android"], "mozilla-beta": ["mozilla-beta"], "mozilla-release": ["mozilla-release"], "mozilla-central": ["mozilla-central"]}
    df_alerts = pd.read_csv(alerts_file, index_col=False)
    cutoff_date_time = df_alerts['push_timestamp'].max()
    df_alerts = df_alerts.drop(columns=['push_timestamp'])
    df_alerts['alert_summary_status_general'] = df_alerts['alert_summary_status'].map(alert_summary_status_mappingg)
    df_alerts["alert_summary_status_general"] = df_alerts["alert_summary_status_general"].replace(category_mapping)

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