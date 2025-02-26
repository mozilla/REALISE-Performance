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
    sig_characteristics["framework"] = dataf["framework_id"].unique().tolist()[0]
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
    sig_characteristics["should_alert"] = dataf["should_alert"].unique().tolist()[0]
    sig_characteristics["last_updated"] = None
    sig_characteristics["min_back_window"] = None
    sig_characteristics["max_back_window"] = None
    sig_characteristics["fore_window"] = None
    sig_characteristics["alert_threshold"] = None
    sig_characteristics["alert_change_type"] = None
    sig_characteristics["timeseries_length"] = len(dataf)
    sig_characteristics["nb_unique_revisions"] = len(dataf["revision"].unique().tolist())
    # Count occurrences for each status, considering only rows with unique push_timestamp values
    unique_push_dataf = dataf.drop_duplicates(subset=["push_timestamp"])
    sig_characteristics["fn_count"] = len(unique_push_dataf[unique_push_dataf["alert_summary_status_general"] == "FN"])
    sig_characteristics["fp_count"] = len(unique_push_dataf[unique_push_dataf["alert_summary_status_general"] == "FP"])
    sig_characteristics["sp_count"] = len(unique_push_dataf[unique_push_dataf["alert_summary_status_general"] == "SP"])
    sig_characteristics["tp_count"] = len(unique_push_dataf[unique_push_dataf["alert_summary_status_general"] == "TP"])
    
    # Time series statistics
    values = dataf["value"]
    # Minimum value in the series
    sig_characteristics["min"] = values.min()
    # Maximum value in the series
    sig_characteristics["max"] = values.max()
    # Mean (average) value
    sig_characteristics["mean"] = values.mean()
    # Median (middle value when sorted)
    sig_characteristics["median"] = values.median()
    # Standard deviation (measure of dispersion)
    sig_characteristics["std"] = values.std()
    # Variance (spread of the data)
    sig_characteristics["variance"] = values.var()
    # Interquartile range (spread between Q3 and Q1)
    sig_characteristics["iqr"] = values.quantile(0.75) - values.quantile(0.25)
    # Skewness (measure of asymmetry)
    sig_characteristics["skewness"] = values.skew()
    # Kurtosis (measure of outlier presence)
    sig_characteristics["kurtosis"] = values.kurt()
    # Coefficient of variation (relative measure of dispersion)
    sig_characteristics["coefficient_of_variation"] = values.std() / values.mean() if values.mean() != 0 else None
    # Range (max - min)
    sig_characteristics["range"] = values.max() - values.min()
    # Mean absolute deviation (average absolute deviation from mean)
    sig_characteristics["mad"] = values.mad() if hasattr(values, "mad") else values.sub(values.mean()).abs().mean()
    # Mode (most frequent value)
    # sig_characteristics["mode"] = values.mode().tolist()
    # Harmonic mean (useful for rates, requires positive values)
    sig_characteristics["harmonic_mean"] = values.apply(lambda x: np.reciprocal(x)).mean() if all(values > 0) else None
    # Geometric mean (useful for growth rates, requires positive values)
    sig_characteristics["geometric_mean"] = np.exp(np.mean(np.log(values[values > 0]))) if all(values > 0) else None
    # Autocorrelation with lag 1 (correlation with previous value)
    sig_characteristics["autocorrelation_lag1"] = values.autocorr(lag=1)
    # Autocorrelation with lag 2 (correlation with value two steps back)
    sig_characteristics["autocorrelation_lag2"] = values.autocorr(lag=2)
    # 10th percentile (value below which 10% of data falls)
    sig_characteristics["percentile_10"] = values.quantile(0.10)
    # 90th percentile (value below which 90% of data falls)
    sig_characteristics["percentile_90"] = values.quantile(0.90)
    # Entropy (measure of randomness in the distribution)
    sig_characteristics["entropy"] = -np.sum((values.value_counts() / len(values)) * np.log2(values.value_counts() / len(values)))
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