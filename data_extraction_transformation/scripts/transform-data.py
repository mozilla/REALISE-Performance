import os
import pandas as pd
import shutil

input_folder = '../datasets-original'
output_folder = '../datasets-original-annotated-test'
alerts_df_path = '../datasets/2_rectified_alerts_data.csv'

alert_status_mapping = {
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

test_status_mapping = {
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

def process_folder(folder):
    for signature_file in os.listdir(input_folder + '/' + folder):
        try:
            df = pd.read_csv(input_folder + '/' + folder + '/' + signature_file, index_col=False)
            # df = pd.read_csv('../datasets/' + folder + '/' + signature_file, index_col=False)[["job_id", "entry_id", "push_timestamp", "value", "revision", "push_id", "repository_name", "test", "lower_is_better", "name", "parent_signature", "repository_id", "measurement_unit", "application", "has_subtests", "tags", "extra_options", "signature_id", "framework_id" , "signature_hash", "option_collection_hash", "machine_platform", "suite", "should_alert"]]
            # df["push_timestamp"] = pd.to_datetime(df["push_timestamp"], format='%Y-%m-%dT%H:%M:%S', errors='coerce')
            df["push_timestamp"] = pd.to_datetime(df['push_timestamp'], format='mixed')
            df = df[df['push_timestamp'] < cutoff_date_time]
            df_merged = pd.merge(df, df_alerts, left_on=['revision', 'signature_id'], right_on=['alert_revision', 'signature_id'], how='left')
            df_merged['test_status_general'] = df_merged['test_status'].map(test_status_mapping)
            df_merged['test_status_general'].fillna('TN', inplace=True)
            df_merged['alert_status_general'].fillna('TN', inplace=True)
            df_final = df_merged.drop_duplicates()
            df_final["test_status_general"] = df_final["test_status_general"].replace(category_mapping)
            df_final.loc[df_final['test_manually_created'] == True, 'test_status_general'] = "FN"
            df_final.loc[df_final['test_manually_created'] == True, 'alert_status_general'] = "FN"
            df_final.sort_values(by="push_timestamp", ascending=True)
            if not df_final['alert_id'].isna().all():
                df_final.to_csv(output_folder + '/' + folder + '/' + signature_file, index=False)
        except:
            problematic_signatures.append(folder + '/' + signature_file)

projects_folders_mapping = {"autoland": ["autoland1", "autoland2", "autoland3", "autoland4"], "firefox-android": ["firefox-android"], "mozilla-beta": ["mozilla-beta"]}
df_alerts = pd.read_csv(alerts_df_path, index_col=False)
# df_alerts['alert_push_timestamp'] = pd.to_datetime(df_alerts['alert_push_timestamp'], unit='s')
cutoff_date_time = df_alerts['alert_push_timestamp'].max()
df_alerts = df_alerts.drop(columns=['alert_push_timestamp'])
df_alerts['alert_status_general'] = df_alerts['alert_status'].map(alert_status_mapping)
df_alerts["alert_status_general"] = df_alerts["alert_status_general"].replace(category_mapping)
df_alerts.rename(columns={'test_series_signature_id': 'signature_id'}, inplace=True)

os.makedirs(output_folder, exist_ok=True)
for project in projects_folders_mapping:
    for folder in projects_folders_mapping[project]:
        os.makedirs(output_folder + '/' + folder, exist_ok=True)
        process_folder(folder)
        #shutil.rmtree('../datasets/' + folder)
        #os.rename('../datasets/' + folder + "-processed", '../datasets/' + folder)

print('####### Problematic signatures #######')
for sig in problematic_signatures:
    print('Signature path:')
    print(sig)