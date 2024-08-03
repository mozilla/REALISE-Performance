import os
import pandas as pd
import helper
import shutil

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

category_mapping = {
    'investigating': 'SP', # 'SP' stands for 'Still Processing'
    'reassigned': 'TP',
    'invalid': 'FP',
    'improvement': 'TP',
    'fixed': 'TP',
    'wontfix': 'TP',
    'untriaged': 'SP',
    'backedout': 'TP'
}

def process_folder(folder):
    for signature_file in os.listdir('../datasets/' + folder):
        df = pd.read_csv('../datasets/' + folder + '/' + signature_file, index_col=False)[["job_id", "entry_id", "push_timestamp", "value", "revision", "push_id", "repository_name", "test", "lower_is_better", "name", "parent_signature", "repository_id", "measurement_unit", "application", "has_subtests", "tags", "extra_options", "signature_id", "framework_id" , "signature_hash", "option_collection_hash", "machine_platform", "suite", "should_alert"]]
        #df["push_timestamp"] = pd.to_datetime(df["push_timestamp"], format='%Y-%m-%dT%H:%M:%S', errors='coerce')
        df["push_timestamp"] = pd.to_datetime(df["push_timestamp"], format='mixed')
        df = df[df['push_timestamp'] < cutoff_date_time]
        df_merged = pd.merge(df, df_alerts, left_on=['revision', 'signature_id'], right_on=['alert_revision', 'signature_id'], how='left')
        df_merged['alert_status'].fillna('TN', inplace=True)
        df_final = df_merged.drop_duplicates()
        df_final.drop(columns=['alert_revision'], inplace=True)
        df_final["alert_status"] = df_final["alert_status"].replace(category_mapping)
        df_final.to_csv('../datasets/' + folder + "-processed/" + signature_file, index=False)

projects_folders_mapping = {"autoland": ["autoland1", "autoland2", "autoland3", "autoland4"], "firefox-android": ["firefox-android"], "mozilla-central": ["mozilla-central"], "mozilla-beta": ["mozilla-beta"], "mozilla-release": ["mozilla-release"]}
df_alerts = pd.read_csv('../datasets/alerts_data.csv', index_col=False)
df_alerts['alert_status'] = df_alerts['alert_status'].map(alert_status_mapping)
df_alerts.rename(columns={'test_series_signature_id': 'signature_id'}, inplace=True)
cutoff_date_time = pd.to_datetime('2024-04-02 08:58:00')
for project in projects_folders_mapping:
    for folder in projects_folders_mapping[project]:
        if not os.path.exists('../datasets/' + folder + "-processed"):
            os.makedirs('../datasets/' + folder + "-processed", exist_ok=True)
        process_folder(folder)
        shutil.rmtree('../datasets/' + folder)
        os.rename('../datasets/' + folder + "-processed", '../datasets/' + folder)
