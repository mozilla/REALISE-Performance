# python3.9 ./analysis/scripts/summarize_metrics.py -s ./analysis/output/summaries -i abed_results -o only_best_plus_default
import os
import json
import argparse
import shutil

class MethodMeasurement:
    def __init__(self, f1_default=None, precision_default=None, recall_default=None, 
                 f1_oracle=None, precision_oracle=None, recall_oracle=None, 
                 f1_best=None, precision_best=None, recall_best=None, precision_f1_best=None, recall_f1_best=None):
        self.f1_default = f1_default
        self.precision_default = precision_default
        self.recall_default = recall_default
        self.f1_oracle = f1_oracle
        self.precision_oracle = precision_oracle
        self.recall_oracle = recall_oracle
        self.f1_best = f1_best
        self.precision_f1_best = precision_f1_best
        self.recall_f1_best = recall_f1_best
        self.precision_best = precision_best
        self.recall_best = recall_best

    def __setattr__(self, name, value):
        super().__setattr__(name, value)

    def __getattr__(self, name):
        return None


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--summary-dir",
        help="Directory with summary files of all datasets/methods",
        required=True,
    )
    parser.add_argument(
        "-f",
        "--failure-threshold",
        help="The threshold of failed dataset runs per hyper parameter configuration (in decimal)",
        type=float,
        default=0.05,
        required=False,
    )
    parser.add_argument(
        "-i",
        "--input-directory",
        help="Directory with all raw results files of all datasets/methods",
        required=False,
    )
    parser.add_argument(
        "-o",
        "--output-directory",
        help="Directory in which to include the handpicked results files",
        required=False,
    )
    return parser.parse_args()

 
args = parse_args()
summaries_folder_path = args.summary_dir
failure_threshold_decimal = args.failure_threshold
input_directory = args.input_directory
output_directory = args.output_directory

# It will contain all the summaries from the summary directory. A summary is specific to one dataset. It has the results of running that dataset on all hyper parameters in all methods.
datasets_metrics = []
best_paths = []
default_paths = []

for filename in os.listdir(summaries_folder_path):
    if filename.endswith('.json'):
        file_path = os.path.join(summaries_folder_path, filename)
        with open(file_path, 'r') as file:
            data = json.load(file)
            datasets_metrics.append(data)

nb_datasets_threshold = len(datasets_metrics) * (1.0 - failure_threshold_decimal)
methods = set()

for dataset_metrics in datasets_metrics:
    if "results" in dataset_metrics:
        methods.update(dataset_metrics["results"].keys())
default_methods = {method for method in methods if method.startswith("default_")}
best_methods = {method for method in methods if method.startswith("best_")}
stripped_methods = {method.replace("best_", "").replace("default_", "") for method in methods if method.startswith("best_") or method.startswith("default_")}
# This dictionary will contain the conclusive results for each method (Default, Best, Oracle)
MethodsMeasurements = {method: MethodMeasurement() for method in stripped_methods}


def process_default(method):
    default_f1, default_precision, default_recall = -1, -1, -1
    stripped_method = method.replace("default_", "")
    nb_success = 0
    for dataset_metrics in datasets_metrics:
        if dataset_metrics["results"][method][0]["status"] == "SUCCESS":
            nb_success += 1
            metrics = dataset_metrics["results"][method][0]["scores"]
            default_f1 = max(0, default_f1) + metrics["f1"]
            default_precision = max(0, default_precision) + metrics["precision"]
            default_recall = max(0, default_recall) + metrics["recall"]
    if nb_success > nb_datasets_threshold:
        if default_f1 > -1:
            MethodsMeasurements[stripped_method].f1_default = default_f1 / nb_success
        else:
            MethodsMeasurements[stripped_method].f1_default = None
        if default_precision > -1:
            MethodsMeasurements[stripped_method].precision_default = default_precision / nb_success
        else:
            MethodsMeasurements[stripped_method].precision_default = None
        if default_recall > -1:
            MethodsMeasurements[stripped_method].recall_default = default_recall / nb_success
        else:
            MethodsMeasurements[stripped_method].recall_default = None
    for dataset_metrics in datasets_metrics:
        signature_id = dataset_metrics["dataset"]
        default_conf_file_name = dataset_metrics["results"][method][0]["task_file"]
        default_paths.append(signature_id + "/" + method + "/" + default_conf_file_name)

def process_best(method):
    hyperparams = dict()
    stripped_method = method.replace("best_", "")
    for dataset_metrics in datasets_metrics:
        for unit_method in dataset_metrics["results"][method]:
            conf = unit_method["args"]
            conf_str = json.dumps(conf, sort_keys=True)
            if unit_method["status"] == "SUCCESS":
                metrics = unit_method["scores"]
                f1 = metrics["f1"]
                precision = metrics["precision"]
                recall = metrics["recall"]
                if conf_str in hyperparams:
                    hyperparams[conf_str]["f1"].append(f1)
                    hyperparams[conf_str]["precision"].append(precision)
                    hyperparams[conf_str]["recall"].append(recall)
                else:
                    metrics_dict = {
                        "f1": [f1],
                        "precision": [precision],
                        "recall": [recall]
                    }
                    hyperparams[conf_str] = metrics_dict

    dict_f1 = {key: sum(value['f1']) / len(value['f1']) for key, value in hyperparams.items() if len(value['f1']) > nb_datasets_threshold}
    dict_precision = {key: sum(value['precision']) / len(value['precision']) for key, value in hyperparams.items() if len(value['precision']) > nb_datasets_threshold}
    dict_recall = {key: sum(value['recall']) / len(value['recall']) for key, value in hyperparams.items() if len(value['recall']) > nb_datasets_threshold}

    try:
        max_f1 = dict_f1[max(dict_f1, key=dict_f1.get)]
    except Exception as e:
        max_f1 = None
    try:
        precision_max_f1 = dict_precision[max(dict_f1, key=dict_f1.get)]
    except Exception as e:
        precision_max_f1 = None
    try:
        recall_max_f1 = dict_recall[max(dict_f1, key=dict_f1.get)]
    except Exception as e:
        recall_max_f1 = None
    try:
        max_precision = dict_precision[max(dict_precision, key=dict_precision.get)]
    except Exception as e:
        max_precision = None
    try:
        max_recall = dict_recall[max(dict_recall, key=dict_recall.get)]
    except Exception as e:
        max_recall = None
    MethodsMeasurements[stripped_method].f1_best = max_f1
    MethodsMeasurements[stripped_method].precision_best = max_precision
    MethodsMeasurements[stripped_method].recall_best = max_recall
    MethodsMeasurements[stripped_method].precision_f1_best = precision_max_f1
    MethodsMeasurements[stripped_method].recall_f1_best = recall_max_f1
    if max_f1:
        best_f1_conf = max(dict_f1, key=dict_f1.get)
        for dataset_metrics in datasets_metrics:
            signature_id = dataset_metrics["dataset"]
            best_conf_file_names = [conf["task_file"] for conf in dataset_metrics["results"][method] if json.dumps(conf["args"], sort_keys=True)  == best_f1_conf]
            for file_name in best_conf_file_names:
                best_paths.append(signature_id + "/" + method + "/" + file_name)
    '''
    if max_precision:
            best_precision_conf = max(dict_precision, key=dict_precision.get)
            for dataset_metrics in datasets_metrics:
                signature_id = dataset_metrics["dataset"]
                best_conf_file_names = [conf["task_file"] for conf in dataset_metrics["results"][method] if json.dumps(conf["args"], sort_keys=True)  == best_precision_conf]
                for file_name in best_conf_file_names:
                    best_paths.append(signature_id + "/" + method + "/" + file_name)
    if max_recall:
            best_recall_conf = max(dict_recall, key=dict_recall.get)
            for dataset_metrics in datasets_metrics:
                signature_id = dataset_metrics["dataset"]
                best_conf_file_names = [conf["task_file"] for conf in dataset_metrics["results"][method] if json.dumps(conf["args"], sort_keys=True)  == best_recall_conf]
                for file_name in best_conf_file_names:
                    best_paths.append(signature_id + "/" + method + "/" + file_name)        
    '''

def process_oracle(method):
    metrics_dict = {'f1': [], 'recall': [], 'precision': []}
    stripped_method = method.replace("best_", "")
    for dataset_metrics in datasets_metrics:
        oracle_f1, oracle_precision, oracle_recall = -1, -1, -1
        for unit_method in dataset_metrics["results"][method]: 
            if unit_method["status"] == "SUCCESS":
                metrics = unit_method["scores"]
                f1 = metrics["f1"]
                precision = metrics["precision"]
                recall = metrics["recall"]
                if f1 > oracle_f1:
                    oracle_f1 = f1
                if precision > oracle_precision:
                    oracle_precision = precision
                if recall > oracle_recall:
                    oracle_recall = recall
        if oracle_f1 > -1:
            metrics_dict["f1"].append(oracle_f1)
        if oracle_precision > -1:
            metrics_dict["precision"].append(oracle_precision)
        if oracle_recall > -1:
            metrics_dict["recall"].append(oracle_recall)
    if len(metrics_dict["f1"]) > 0:
        MethodsMeasurements[stripped_method].f1_oracle = sum(metrics_dict["f1"]) / len(metrics_dict["f1"])
    if len(metrics_dict["precision"]) > 0:
        MethodsMeasurements[stripped_method].precision_oracle = sum(metrics_dict["precision"]) / len(metrics_dict["precision"])
    if len(metrics_dict["recall"]) > 0:
        MethodsMeasurements[stripped_method].recall_oracle = sum(metrics_dict["recall"]) / len(metrics_dict["recall"])


def copy_file(input_path: str, output_path: str):
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)  # Ensure directories exist
        shutil.copy2(input_path, output_path)
    except FileNotFoundError:
        print(f"Error: Input file '{input_path}' not found.")
    except PermissionError:
        print("Error: Permission denied.")
    except Exception as e:
        print(f"Error copying file: {e}")

for method in default_methods:
    process_default(method)
for method in best_methods:
    process_oracle(method)
    process_best(method)

data = {key: vars(value) for key, value in MethodsMeasurements.items()}

# Sort methods alphabetically by their names
sorted_methods = sorted(data.items())

latex_table = """
\\begin{table*}[t!]
\\centering
\\resizebox{\\textwidth}{!}{%
\\begin{tabular}{|l|c|c|c||c|c|c|c|c||c|c|c|}
\\hline
Method & \\multicolumn{3}{c||}{Default} & \\multicolumn{5}{c||}{Best} & \\multicolumn{3}{c|}{Oracle} \\\\
\\cline{2-13}
 & F1 & Precision & Recall & F1 & Precision & Recall & Precision (F1 max) & Recall (F1 max) & F1 & Precision & Recall \\\\
\\hline
"""

def format_none(value):
    if value is None:
        return ""
    return f"{value:.3f}"

for method, metrics in sorted_methods:
    latex_table += f"{method} & "
    latex_table += " & ".join([
        format_none(metrics.get('f1_default')),
        format_none(metrics.get('precision_default')),
        format_none(metrics.get('recall_default')),
        format_none(metrics.get('f1_best')),
        format_none(metrics.get('precision_best')),
        format_none(metrics.get('recall_best')),
        format_none(metrics.get('precision_f1_best')),
        format_none(metrics.get('recall_f1_best')),
        format_none(metrics.get('f1_oracle')),
        format_none(metrics.get('precision_oracle')),
        format_none(metrics.get('recall_oracle'))
    ])
    latex_table += " \\\\\n"

latex_table += "\\hline\n\\end{tabular}%%\n}\n\\caption{Performance Metrics for Methods}\n\\end{table*}"

for path in best_paths:
    input_path = input_directory + "/" + path
    output_path = output_directory + "/" + path
    copy_file(input_path, output_path)

for path in default_paths:
    input_path = input_directory + "/" + path
    output_path = output_directory + "/" + path
    copy_file(input_path, output_path)


print(latex_table)