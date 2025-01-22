import os 
import pandas as pd
import shutil
import argparse
 
def parse_args():
    parser = argparse.ArgumentParser(description="Run KCPA algorithm on a time series dataset.")
    parser.add_argument('-i', '--input-folder', help="Path to the input CSV timeseries folder")
    parser.add_argument('-a', '--alerts-file', help="Path to the alerts CSV file")
    return parser.parse_args()

def select_favorable_status(status_series):
    return sorted(status_series, key=lambda x: status_priority.get(x, float('inf')))[0]

def process_folder(input_folder, folder):
    global measurement_count
    global rev
    global avg_rev
    global uniq_sig
    global rev_in_alert
    for signature_file in os.listdir(input_folder + '/' + folder):
        print(folder + '/' + signature_file)
        df = pd.read_csv(input_folder + '/' + folder + '/' + signature_file, index_col=False)
        uniq_sig += 1
        measurement_count += len(df)
        avg_rev += df['revision'].nunique()
        rev = rev + df["revision"].unique().tolist()
        rev_in_alert = rev_in_alert + df["alert_summary_revision"].unique().tolist()

def main():
    global measurement_count
    global rev
    global rev_in_alert
    global avg_rev
    global uniq_sig
    uniq_sig = 0
    measurement_count = 0
    rev = []
    rev_in_alert = []
    args = parse_args()
    avg_rev = 0
    input_folder = args.input_folder
    alerts_file = args.alerts_file
    alerts_df = pd.read_csv(alerts_file)
    revisions_in_alerts = set(alerts_df['alert_summary_revision'].unique().tolist())
    projects_folders_mapping = {
        "autoland": ["autoland1", "autoland2", "autoland3", "autoland4"],
        "firefox-android": ["firefox-android"],
        "mozilla-beta": ["mozilla-beta"],
        "mozilla-central": ["mozilla-central"],
        "mozilla-release": ["mozilla-release"],
    }


    # projects_folders_mapping = {
    #     "autoland": ["autoland1"]
    # }
    # Process each project and folder
    for project in projects_folders_mapping:
        for folder in projects_folders_mapping[project]:
            process_folder(input_folder, folder)    
    print("Uncommon revisions")
    mutually_exclusive = set(rev_in_alert) ^ revisions_in_alerts
    comma_separated_string = ",".join(map(str, rev_in_alert))
    with open("rev_in_timeseries.txt", "w") as file:
        file.write(comma_separated_string)
    print(mutually_exclusive)
    print(len(set(rev_in_alert)))
    print(len(revisions_in_alerts))
    print("Revision count")
    print(len(set(rev)))
    print("Revision average")
    print(avg_rev / uniq_sig)
    print("Measurement count")
    print(measurement_count)
    print("Unique signatures")
    print(uniq_sig)
    print("Average measurement count per time series")
    print(measurement_count / uniq_sig)
if __name__ == "__main__":
    main()