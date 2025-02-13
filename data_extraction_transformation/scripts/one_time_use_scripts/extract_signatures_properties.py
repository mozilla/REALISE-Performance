import os
import shutil
import pandas as pd
import json
import argparse
import numpy as np

def process_sig_df(dataf):
    sig_characteristics = dict()
    signature_id = dataf["signature_id"].unique().tolist()[0]
    sig_characteristics["repository"] = dataf["repository_name"].unique().tolist()[0]
    sig_characteristics["framework"] = dataf["framework_id"].unique().tolist()[0] # we don’t know if in the code we have the framework name or ID because it is SlugField in the Treeherder code
    sig_characteristics["platform"] = dataf["machine_platform"].unique().tolist()[0]
    sig_characteristics["option_collection"] = dataf["option_collection_hash"].unique().tolist()[0]
    sig_characteristics["test"] = dataf["test"].unique().tolist()[0]
    sig_characteristics["suite"] = dataf["suite"].unique().tolist()[0]
    sig_characteristics["application"] = dataf["application"].unique().tolist()[0]
    sig_characteristics["lower_is_better"] = dataf["lower_is_better"].unique().tolist()[0]
    sig_characteristics["parent_signature"] = dataf["parent_signature"].unique().tolist()[0]
    sig_characteristics["has_subtests"] = dataf["has_subtests"].unique().tolist()[0]
    sig_characteristics["suite_public_name"] = dataf["single_alert_series_signature_suite_public_name"].unique().tolist()[0]
    sig_characteristics["test_public_name"] = dataf["single_alert_series_signature_test_public_name"].unique().tolist()[0]
    sig_characteristics["tags"] = dataf["tags"].unique().tolist()[0]
    sig_characteristics["extra_options"] = dataf["extra_options"].unique().tolist()[0]
    sig_characteristics["measurement_unit"] = dataf["measurement_unit"].unique().tolist()[0]
    sig_characteristics["should_alert"] = dataf["should_alert"].unique().tolist()[0] # I think I could just set it to ’True’ because there might be alerts created from signatures that were alertable but not anymore
    sig_characteristics["last_updated"] = None
    sig_characteristics["min_back_window"] = None
    sig_characteristics["max_back_window"] = None
    sig_characteristics["fore_window"] = None
    sig_characteristics["alert_threshold"] = None
    sig_characteristics["alert_change_type"] = None
    sig_characteristics["timeseries_length"] = len(dataf)
    sig_characteristics["nb_unique_revisions"] = len(dataf["revision"].unique().tolist())
    sig_characteristics["fn_count"] = len(dataf[dataf["alert_summary_status_general"] == "FN"])
    sig_characteristics["fp_count"] = len(dataf[dataf["alert_summary_status_general"] == "FP"])
    sig_characteristics["sp_count"] = len(dataf[dataf["alert_summary_status_general"] == "SP"])
    sig_characteristics["tp_count"] = len(dataf[dataf["alert_summary_status_general"] == "TP"])
    return signature_id, sig_characteristics

def parse_args():
    parser = argparse.ArgumentParser(description="Handpick specific timeseries JSON files along with their annotations.json to run them on TCPCBench.")
    parser.add_argument('-i', '--input-folder', help="Path to the input folder of time series CSV files.")
    parser.add_argument('-o', '--output-file', help="Path to the output file of signatures properties JSON file.")
    return parser.parse_args()

def replace_nan(obj):
    if isinstance(obj, dict):
        return {k: replace_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_nan(item) for item in obj]
    elif isinstance(obj, float) and np.isnan(obj):
        return None  # Replace NaN with None
    return obj

def main():
    args = parse_args()
    input_folder = args.input_folder
    output_file = args.output_file
    subfolders = [os.path.join(input_folder, folder) for folder in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, folder))]
    if not subfolders:
        subfolders = [input_folder]  # Add input_folder if no subfolders exist
    attributes = dict()
    for subfolder in subfolders:
        for root, _, files in os.walk(subfolder):
            for file in files:
                if file.endswith(".csv"):
                    csv_file_path = os.path.join(root, file)
                    df = pd.read_csv(csv_file_path)
                    signature_id, sig_characteristics = process_sig_df(df)
                    attributes[signature_id] = sig_characteristics
    attributes_polished = replace_nan(attributes)
    with open(output_file, "w") as file:
        json.dump(attributes_polished, file, indent=4)
if __name__ == "__main__":
    main() 