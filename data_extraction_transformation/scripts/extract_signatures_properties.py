import os
import shutil
import pandas as pd
import json
import argparse
import numpy as np
import re
from scipy import stats

def process_sig_df(dataf, signature_id):
    sig_characteristics = dict()
    try:
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

        unique_push_dataf = dataf.drop_duplicates(subset=["push_timestamp"])
        '''
        sig_characteristics["fn_count"] = len(unique_push_dataf[unique_push_dataf["alert_summary_status_general"] == "FN"])
        sig_characteristics["fp_count"] = len(unique_push_dataf[unique_push_dataf["alert_summary_status_general"] == "FP"])
        sig_characteristics["sp_count"] = len(unique_push_dataf[unique_push_dataf["alert_summary_status_general"] == "SP"])
        sig_characteristics["tp_count"] = len(unique_push_dataf[unique_push_dataf["alert_summary_status_general"] == "TP"])
        '''

        values = dataf["value"]

        sig_characteristics["min"] = values.min()
        sig_characteristics["max"] = values.max()
        sig_characteristics["mean"] = values.mean()
        sig_characteristics["median"] = values.median()
        sig_characteristics["std"] = values.std()
        sig_characteristics["variance"] = values.var()
        sig_characteristics["iqr"] = values.quantile(0.75) - values.quantile(0.25)
        sig_characteristics["skewness"] = values.skew()
        sig_characteristics["kurtosis"] = values.kurt()
        sig_characteristics["coefficient_of_variation"] = values.std() / values.mean() if values.mean() != 0 else None
        sig_characteristics["range"] = values.max() - values.min()
        sig_characteristics["mad"] = values.mad() if hasattr(values, "mad") else values.sub(values.mean()).abs().mean()
        sig_characteristics["harmonic_mean"] = values.apply(lambda x: np.reciprocal(x)).mean() if all(values > 0) else None
        sig_characteristics["geometric_mean"] = np.exp(np.mean(np.log(values[values > 0]))) if all(values > 0) else None
        sig_characteristics["autocorrelation_lag1"] = values.autocorr(lag=1)
        sig_characteristics["autocorrelation_lag2"] = values.autocorr(lag=2)
        sig_characteristics["percentile_10"] = values.quantile(0.10)
        sig_characteristics["percentile_90"] = values.quantile(0.90)
        sig_characteristics["entropy"] = -np.sum((values.value_counts() / len(values)) * np.log2(values.value_counts() / len(values)))

        # --- Trend features ---
        x = np.arange(len(values))
        v = values.to_numpy()

        # Linear regression: slope, intercept, R², p-value, std error
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, v)
        sig_characteristics["trend_slope"] = slope               # Change per step (+ rising, - falling)
        sig_characteristics["trend_intercept"] = intercept       # Fitted value at step 0
        sig_characteristics["trend_r2"] = r_value ** 2           # Goodness of fit (0–1, higher = stronger linear trend)
        sig_characteristics["trend_p_value"] = p_value           # Statistical significance (< 0.05 = significant trend)
        sig_characteristics["trend_std_err"] = std_err           # Uncertainty of the slope estimate

        # Normalized slope: slope relative to the mean (like CV but for trend)
        sig_characteristics["trend_slope_normalized"] = slope / values.mean() if values.mean() != 0 else None

        # Direction: "increasing", "decreasing", or "stable" (using p-value threshold)
        if p_value < 0.05:
            sig_characteristics["trend_direction"] = "increasing" if slope > 0 else "decreasing"
        else:
            sig_characteristics["trend_direction"] = "stable"

        # Total drift: difference between last and first value
        sig_characteristics["trend_total_drift"] = float(v[-1] - v[0])

        # Relative drift: total drift as a fraction of the first value
        sig_characteristics["trend_relative_drift"] = float((v[-1] - v[0]) / v[0]) if v[0] != 0 else None

        # Mann-Kendall trend test (non-parametric, robust to outliers and non-normality)
        n = len(v)
        s = 0
        for i in range(n - 1):
            for j in range(i + 1, n):
                diff = v[j] - v[i]
                if diff > 0:
                    s += 1
                elif diff < 0:
                    s -= 1
        # Variance of S under H0 (no ties adjustment for simplicity)
        var_s = n * (n - 1) * (2 * n + 5) / 18
        if s > 0:
            mk_z = (s - 1) / np.sqrt(var_s)
        elif s < 0:
            mk_z = (s + 1) / np.sqrt(var_s)
        else:
            mk_z = 0.0
        mk_p_value = 2 * (1 - stats.norm.cdf(abs(mk_z)))  # Two-tailed p-value
        sig_characteristics["trend_mk_s"] = int(s)           # Mann-Kendall S statistic
        sig_characteristics["trend_mk_z"] = mk_z             # Standardized Z score
        sig_characteristics["trend_mk_p_value"] = mk_p_value # p-value (< 0.05 = significant monotonic trend)

        return sig_characteristics
    except Exception as e:
        print(f"[ERROR] Signature {signature_id}: {type(e).__name__}: {e}")
        return dict()


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
        return None
    return obj

def main():
    args = parse_args()
    input_folder = args.input_folder
    output_file = args.output_file
    subfolders = [os.path.join(input_folder, folder) for folder in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, folder))]
    if not subfolders:
        subfolders = [input_folder]
    attributes = dict()
    for subfolder in subfolders:
        for root, _, files in os.walk(subfolder):
            for file in files:
                if file.endswith(".csv"):
                    csv_file_path = os.path.join(root, file)
                    df = pd.read_csv(csv_file_path)
                    filename = os.path.basename(csv_file_path)
                    match = re.match(r"(\d+)_", filename)
                    signature_id = match.group(1)
                    sig_characteristics = process_sig_df(df, signature_id)
                    attributes[signature_id] = sig_characteristics
    attributes_polished = replace_nan(attributes)
    with open(output_file, "w") as file:
        json.dump(attributes_polished, file, indent=4)

if __name__ == "__main__":
    main()