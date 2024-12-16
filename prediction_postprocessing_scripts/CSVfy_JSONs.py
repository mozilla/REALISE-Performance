import pandas as pd
import json
import os
import argparse

rows = []

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
        "--output-file",
        help="Path of results output file",
        required=True,
    )
    return parser.parse_args()


def process_signature(root, sig_path):
    sig = sig_path.split('_')[1].split('.')[0]
    sig_summary_path = os.path.join(root, sig_path)
    with open(sig_summary_path, 'r') as file:
        data = json.load(file)
    dataset = data['dataset']
    annotations = data['annotations']['1']
    results = data['results']
    for cpd in results:
        for conf in results[cpd]:
            if conf['status'] == 'SUCCESS':
                row = dict()
                row['dataset'] = dataset
                row['cpd_method'] = cpd
                row['args'] = conf['args']
                row['precision'] = conf['scores']['precision']
                row['recall'] = conf['scores']['recall']
                row['f1'] = conf['scores']['f1']
                row['predicted_cplocations'] = conf['cplocations']
                row['actual_cplocations'] = annotations
                rows.append(row)

def main():
    args = parse_args()
    root = args.input_directory
    dest = args.output_file
    for signature_path in os.listdir(root):
        process_signature(root, signature_path)
    df = pd.DataFrame(rows)
    df.to_csv(dest)

if __name__ == "__main__":
    main()