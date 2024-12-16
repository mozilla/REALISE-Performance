import os
import argparse
import pandas as pd
import json
import sys
import matplotlib.pyplot as plt


summaries_folder_path = "showcase-diagram-results/JSON3"
csvs_folder_path = "showcase-diagram-results/CSV3"

datasets_metrics = []

for filename in os.listdir(summaries_folder_path):
    if filename.endswith('.json'):
        file_path = os.path.join(summaries_folder_path, filename)
        with open(file_path, 'r') as file:
            data = json.load(file)
            datasets_metrics.append(data)

def process_best(method, metric):
    hyperparams = dict()
    for dataset_metrics in datasets_metrics:
        for unit_method in dataset_metrics["results"]["best_" + method]:
            if unit_method["status"] == "SUCCESS":
                conf = unit_method["args"]
                metrics = unit_method["scores"]
                metric_value = metrics[metric]
                conf_str = json.dumps(conf, sort_keys=True)
                if conf_str in hyperparams:
                    hyperparams[conf_str].append(metric_value)
                else:
                    hyperparams[conf_str] = [metric_value]
    dict_metric = {key: sum(value) / len(value) for key, value in hyperparams.items()}
    best_conf  = max(dict_metric, key=dict_metric.get)
    best_conf_score  = dict_metric[best_conf]
    return best_conf, best_conf_score 

def process_oracle(data, method, metric):
    elements = data["results"]["best_" + method]
    elements_dict = {json.dumps(element["args"], sort_keys=True): element["scores"][metric] for element in elements if "args" in element and element.get("scores") is not None}
    oracle_conf  = max(elements_dict, key=elements_dict.get)
    oracle_conf_score  = elements_dict[oracle_conf]
    return oracle_conf, oracle_conf_score

def process_default(data, method, metric):
    default_conf = data["results"]["default_" + method][0]["args"]
    default_conf_score = data["results"]["default_" + method][0]["scores"][metric]
    return default_conf, default_conf_score

def parse_args():
    parser = argparse.ArgumentParser(description="Generator of timeseries graphs")
    parser.add_argument("-m", "--method", help="CPD method", required=True)
    parser.add_argument("-t", "--timeseriessignature", help="timeseries signature", required=True)
    parser.add_argument("-e", "--evaluationmode", help="Results related to evaluation mode", choices=['default', 'best', 'oracle'], required=True)
    parser.add_argument("-s", "--scoremetric", help="Metric on which to base evaluation in case of Best or Oracle modes", choices=['precision', 'recall', 'f1'], required= False)
    return parser.parse_args()

def fetch_data(signature_id, method, mode, metric):
    df = pd.read_csv(csvs_folder_path + "/" + signature_id + "_timeseries_data.csv")
    with open(summaries_folder_path + "/summary_" + signature_id + ".json", "r") as fp:
        try:
            s = fp.read()
            s = s[s.find('{'): s.rfind('}') + 1]
            data = json.loads(s)
        except json.decoder.JSONDecodeError:
            sys.exit("Error parsing json file: %s" % signature_id, file=sys.stderr)
    if (mode == "best"):
        conf, conf_score = process_best(method, metric)
        for elem in data["results"]["best_" + method]:
            if json.dumps(elem["args"], sort_keys=True) == conf:
                conf_cplocations = elem["cplocations"]
    elif(mode == "oracle"):
        conf, conf_score = process_oracle(data, method, metric)
        for elem in data["results"]["best_" + method]:
            print()
            if json.dumps(elem["args"], sort_keys=True) == conf:
                conf_cplocations = elem["cplocations"]
    elif(mode == "default"):
        conf, conf_score = process_default(data, method, metric)
        conf_cplocations = data["results"]["default_" + method][0]["cplocations"]
    else:
        sys.exit("Evaluation method does not exist")
    
    return df, conf, conf_score, conf_cplocations


def display_timeseries(sample_df, sig_id, cplocations=None): 
    # Ensure 'push_timestamp' is treated as datetime
    sample_df['push_timestamp'] = pd.to_datetime(sample_df['push_timestamp'])
    sample_df.set_index('push_timestamp', inplace=True)
    
    plt.figure(figsize=(20, 10))

    color_mapping = {
        'TP': 'green',
        'FP': 'red',
        'SP': 'grey',
        'acknowledged': 'green'
    }

    # Plot the timeseries data
    for idx, row in sample_df.iterrows():
        plt.plot(idx, row['value'], marker='o', markersize=8, color=color_mapping.get(row['test_status_general'], 'blue'), alpha=0.6)
        if row['test_status_general'] in ['TP', 'FP', 'SP', 'acknowledged']:
            plt.axvline(x=idx, color=color_mapping.get(row['test_status_general']), linestyle='--', alpha=0.6)

    # Add yellow lines for changepoints if they exist
    if cplocations is not None:
        for cp in cplocations:
            # Convert integer indices in cplocations to corresponding timestamps
            if isinstance(cp, int):
                cp_timestamp = sample_df.index[cp]  # Get the timestamp from the index
            else:
                cp_timestamp = pd.to_datetime(cp)  # In case cp is already a timestamp

            plt.axvline(x=cp_timestamp, color='yellow', linestyle='--', alpha=0.9)  # Removed label

    plt.title('Time Series Plot')
    plt.xlabel('Date')
    plt.ylabel(f'Measurement values associated with signature ID {sig_id}')
    plt.grid(axis='y')

    # Define y-axis limits
    plt.xlim(sample_df.index.min(), sample_df.index.max())
    y_min = 0
    y_max = sample_df['value'].max() * 2
    plt.ylim(bottom=y_min, top=y_max)

    # Set weekly ticks for x-axis
    start_date = sample_df.index.min()
    end_date = sample_df.index.max()
    weekly_ticks = pd.date_range(start=start_date, end=end_date, freq='W-MON')
    plt.xticks(weekly_ticks, rotation=45)

    plt.legend(loc='upper right')  # The legend will no longer include 'Change Point'
    plt.show()


def main():
    args = parse_args()
    method = args.method
    signature = args.timeseriessignature
    metric = args.scoremetric
    mode = args.evaluationmode
    df, conf, conf_score, conf_cplocations = fetch_data(str(signature), method, mode, metric)
    print(conf)
    print(conf_score)
    display_timeseries(df, signature, conf_cplocations)


if __name__ == "__main__":
    main()
