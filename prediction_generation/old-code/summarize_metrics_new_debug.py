import os
import json
import argparse
import pandas as pd


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
        default=0.05,
        required=False,
    )
    return parser.parse_args()

 
summaries_folder_path = parse_args().summary_dir

# It will contain all the summaries from the summary directory. A summary is specific to one dataset. It has the results of running that dataset on all hyper parameters in all methods.
datasets_metrics = []

for filename in os.listdir(summaries_folder_path):
    if filename.endswith('.json'):
        file_path = os.path.join(summaries_folder_path, filename)
        with open(file_path, 'r') as file:
            data = json.load(file)
            datasets_metrics.append(data)

failure_threshold_decimal = parse_args().failure_threshold
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


def process_best(method):
    hyperparams = dict()
    stripped_method = method.replace("best_", "")
    uniq_count = set()
    uniq_successful_conf = set()
    uniq_fail_conf = dict()
    uniq_conf = dict()
    for dataset_metrics in datasets_metrics:
        for unit_method in dataset_metrics["results"][method]:
            conf = unit_method["args"]
            conf_str = json.dumps(conf, sort_keys=True)
            if conf_str in uniq_conf:
                uniq_conf[conf_str] = uniq_conf[conf_str] + 1
            else:
                uniq_conf[conf_str] = 1
            if unit_method["status"] == "SUCCESS":
                uniq_successful_conf.add(conf_str)
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
                # elif unit_method["status"] == "FAIL" and method != 'best_pelt' and method != 'best_amoc' and method != 'best_binseg' and method != 'best_bocpd' and method != 'best_cpnp':
            elif unit_method["status"] == "FAIL":
                if conf_str in uniq_fail_conf:
                    uniq_fail_conf[conf_str].append(dataset_metrics['dataset'])
                else:
                    uniq_fail_conf[conf_str] = [dataset_metrics['dataset']]
                #print('AAAAAAAAAAAAAAAA')
                #print(method)
            # else:
            #     print('METHOD:')
            #     print(method)
            #     print(dataset_metrics["dataset"])
    # dict_f1 = {key: sum(value['f1']) / len(value['f1']) for key, value in hyperparams.items() if len(value['f1']) > nb_datasets_threshold}
    # dict_precision = {key: sum(value['precision']) / len(value['precision']) for key, value in hyperparams.items() if len(value['precision']) > nb_datasets_threshold}
    # dict_recall = {key: sum(value['recall']) / len(value['recall']) for key, value in hyperparams.items() if len(value['recall']) > nb_datasets_threshold}

    dict_f1 = {key: sum(value['f1']) / len(value['f1']) for key, value in hyperparams.items() if len(value['f1']) > nb_datasets_threshold}
    dict_precision = {key: sum(value['precision']) / len(value['precision']) for key, value in hyperparams.items() if len(value['precision']) > nb_datasets_threshold}
    dict_recall = {key: sum(value['recall']) / len(value['recall']) for key, value in hyperparams.items() if len(value['recall']) > nb_datasets_threshold}
    print('Method Kar lChebba thabbat fl wesfan')
    print(method)
    print('number of failed confs with no datasets overlap')
    print(len(uniq_fail_conf))
    print('number of failed confs with datasets overlap')
    for key, value in uniq_fail_conf.items():
        if key in uniq_successful_conf:
            print(key)
            print(value)
    # print(uniq_successful_conf.intersection(set(uniq_fail_conf.keys())))
    # for key, value in hyperparams.items():
    #     print(len(value['f1']))
    # print(method)
    # print('################')
    # print('dict_f1')
    # print(len(dict_f1))
    # print('dict_precision')
    # print(len(dict_precision))
    # print('dict_recall')
    # print(len(dict_recall))
    # print('Hyperparamssssssss')
    # print(len(hyperparams))
    for key, value in hyperparams.items():
        uniq_count.add(len(value['precision']))
        uniq_count.add(len(value['f1']))
        uniq_count.add(len(value['recall']))
        # print(len(value['f1']))
    # print(uniq_count)
    # for key, value in hyperparams.items():
    #     if (len(value['precision']) < 63):
    #         print('3omri mensit')
    #         print(method)
    #     if (len(value['recall']) < 63):
    #         print('3omri mensit')
    #         print(method)
    #     if (len(value['f1']) < 63):
    #         print('3omri mensit')
    #         print(method)
        # if (len(value['f1']) != len(value['precision'])) or (len(value['f1']) != len(value['recall'])):
        #     print('Kar lChebba thabbat fl wesfan')
    all_keys = set(dict_precision.keys()).union(set(dict_recall.keys())).union(set(dict_f1.keys()))

    # Save all configurations to CSV for debugging purposes
    data = {
        'Key': list(all_keys),
        'Precision': [dict_precision.get(key, float('nan')) for key in all_keys],
        'Recall': [dict_recall.get(key, float('nan')) for key in all_keys],
        'F1 Score': [dict_f1.get(key, float('nan')) for key in all_keys]
    }
    df = pd.DataFrame(data)
    df.to_csv('/TCPDBench/analysis/metrics_of_'+ method + '.csv', index=False)

    try:
        max_f1 = dict_f1[max(dict_f1, key=dict_f1.get)]
    except Exception as e:
        print('###f1####')
        print(e)
        max_f1 = None
    try:
        precision_max_f1 = dict_precision[max(dict_f1, key=dict_f1.get)]
    except Exception as e:
        print('###precision f1 max####')
        print(e)
        precision_max_f1 = None
    try:
        recall_max_f1 = dict_recall[max(dict_f1, key=dict_f1.get)]
    except Exception as e:
        print('###recall f1####')
        print(e)
        recall_max_f1 = None
    try:
        max_precision = dict_precision[max(dict_precision, key=dict_precision.get)]
    except Exception as e:
        print('###precision####')
        print(e)
        max_precision = None
    try:
        max_recall = dict_recall[max(dict_recall, key=dict_recall.get)]
    except Exception as e:
        print('###recall####')
        print(e)
        max_recall = None
    MethodsMeasurements[stripped_method].f1_best = max_f1
    MethodsMeasurements[stripped_method].precision_best = max_precision
    MethodsMeasurements[stripped_method].recall_best = max_recall
    MethodsMeasurements[stripped_method].precision_f1_best = precision_max_f1
    MethodsMeasurements[stripped_method].recall_f1_best = recall_max_f1


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

print(latex_table)
