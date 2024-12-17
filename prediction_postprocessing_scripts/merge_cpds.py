import json
import os
import argparse
import sys
import random
import string
# bocpd, amoc, binseg, cpnp, kcpa, mongodb, pelt, rfpop, wbs, zero
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input-directory",
        help="Path of results input directory",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output-directory",
        help="Path of results output directory",
        required=True,
    )
    parser.add_argument(
        "-f",
        "--first-method",
        help="First method",
        required=True
    )
    parser.add_argument(
        "-s",
        "--second-method",
        help="Second method",
        required=True
    )
    parser.add_argument(
        "-c",
        "--combination-strategy",
        choices=['union', 'intersection_strict', 'intersection_first'],
        help="Strategy of combining the CPLocations from different methods",
        required=True
    )
    parser.add_argument(
        "-m",
        "--margin",
        help="Margin for True Positive verification",
        default=5,
        required=True
    )
    return parser.parse_args()

def load_json(json_file_path):
     with open(json_file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def prefix_param_arg(first_json_conf, second_json_conf, first_method, second_method):
    result_conf_params = dict()
    result_conf_args = dict()

    for key, value in first_json_conf["parameters"].items():
        result_conf_params[first_method + "_" + key] = value

    for key, value in first_json_conf["args"].items():
        result_conf_args[first_method + "_" + key] = value

    for key, value in second_json_conf["parameters"].items():
        result_conf_params[second_method + "_" + key] = value

    for key, value in second_json_conf["args"].items():
        result_conf_args[second_method + "_" + key] = value
    return result_conf_params, result_conf_args

def merge_cpocations(first_method_cplocations, second_method_cplocations, combination_strategy, margin):
    if combination_strategy == 'union':
        return sorted(set(first_method_cplocations + second_method_cplocations))
    elif combination_strategy == 'intersection_strict':
        return sorted(set(first_method_cplocations).intersection(set(second_method_cplocations)))
    elif combination_strategy == 'intersection_first':
        final_cplocations = list()
        for cplocation in first_method_cplocations:
            if any(abs(cplocation - compcploc) <= margin for compcploc in second_method_cplocations):
                final_cplocations.append(cplocation)
        return sorted(final_cplocations)
    else:
        sys.exit('Combination strategy unknown')

def create_fail_file(first_json, second_json, first_method, second_method):
    result_json = dict()
    result_json["error"] = "One of the configurations of the methods is failing"
    # if (first_json["dataset"] == second_json["dataset"]) and (first_json["dataset_md5"] == second_json["dataset_md5"]):
    if (first_json["dataset"] == second_json["dataset"]):
        result_json["dataset"] = first_json["dataset"]
        result_json["dataset_md5"] = second_json["dataset_md5"]
    else:
        sys.exit("Data inconsistency found. Check results folder")
    result_json["hostname"] = first_json["hostname"]
    result_json["status"] = "FAIL"
    result_json["parameters"], result_json["args"] = prefix_param_arg(first_json, second_json, first_method, second_method)
    result_json["result"] = dict()
    result_json["result"]["cplocations"] = None
    result_json["result"]["runtime"] = None
    return result_json

def merge_files(first_json, second_json, first_method, second_method, combination_strategy, margin):
    result_json = dict()
    result_json["error"] = None
    # if (first_json["dataset"] == second_json["dataset"]) and (first_json["dataset_md5"] == second_json["dataset_md5"])
    if (first_json["dataset"] == second_json["dataset"]):
        result_json["dataset"] = first_json["dataset"]
        result_json["dataset_md5"] = second_json["dataset_md5"]
    else:
        sys.exit("Data inconsistency found. Check results folder")
    result_json["hostname"] = first_json["hostname"]
    result_json["status"] = "SUCCESS"
    result_json["parameters"], result_json["args"] = prefix_param_arg(first_json, second_json, first_method, second_method)
    result_json["result"] = dict()
    result_json["result"]["cplocations"] = merge_cpocations(first_json["result"]["cplocations"], second_json["result"]["cplocations"], combination_strategy, margin)
    result_json["result"]["runtime"] = first_json["result"]["runtime"] + second_json["result"]["runtime"]
    return result_json

def store_json(output_directory, sig_path, result_json, first_second_conf):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    signature_path = os.path.join(output_directory, sig_path)
    if not os.path.exists(signature_path):
        os.makedirs(signature_path)
    signature_methods_path = os.path.join(signature_path, first_second_conf)
    if not os.path.exists(signature_methods_path):
        os.makedirs(signature_methods_path)
    file_path = ''.join(random.choices(string.ascii_lowercase + string.digits, k=15)) + ".json"
    file_path = os.path.join(signature_methods_path, file_path)
    with open(file_path, "w") as json_file:
        json.dump(result_json, json_file, indent=4)

def process_signature(root, sig_path, first_method, second_method, output_directory, combination_strategy, margin, conf):
    conf_folder_name = conf + '_' + first_method + '_' + second_method
    first_method_conf_dir = os.path.join(root, sig_path, conf + '_' + first_method)
    second_method_conf_dir = os.path.join(root, sig_path, conf + '_' + second_method)
    for first_method_file in os.listdir(first_method_conf_dir):
        first_method_file_path = os.path.join(first_method_conf_dir, first_method_file)
        if os.path.isfile(first_method_file_path) and first_method_file_path.endswith('.json'):
            first_method_json = load_json(first_method_file_path)
            for second_method_file in os.listdir(second_method_conf_dir):
                second_method_file_path = os.path.join(second_method_conf_dir, second_method_file)
                if os.path.isfile(second_method_file_path) and second_method_file_path.endswith('.json'):
                    second_method_json = load_json(second_method_file_path)
                    if first_method_json['status'] == 'SUCCESS' and second_method_json['status'] == 'SUCCESS':
                        result_json = merge_files(first_method_json, second_method_json, first_method, second_method, combination_strategy, margin)
                        store_json(output_directory, sig_path, result_json, conf_folder_name)
                    elif (conf == "default") and not (first_method_json['status'] == 'SUCCESS' and second_method_json['status'] == 'SUCCESS'):
                        result_json = create_fail_file(first_method_json, second_method_json, first_method, second_method)
                        store_json(output_directory, sig_path, result_json, conf_folder_name)
def main():
    args = parse_args()
    root = args.input_directory
    combination_strategy = args.combination_strategy
    margin = int(args.margin)
    for signature_path in os.listdir(root):
        process_signature(root, signature_path, args.first_method, args.second_method, args.output_directory, combination_strategy, margin, 'best')
        process_signature(root, signature_path, args.first_method, args.second_method, args.output_directory, combination_strategy, margin, 'default')

if __name__ == "__main__":
    main()