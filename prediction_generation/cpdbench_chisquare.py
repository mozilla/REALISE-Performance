#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import time
import copy
import numpy as np
from alibi_detect.cd import ChiSquareDrift
from cpdbench_utils import load_dataset, exit_success, exit_with_error

def parse_args():
    parser = argparse.ArgumentParser(description="Run Chi-Square Drift Detection.")
    parser.add_argument("-i", "--input", help="Path to input JSON dataset.")
    parser.add_argument("-o", "--output", help="Path to output JSON file.")
    parser.add_argument("--p-val", type=float, default=0.05, help="Significance level.")
    parser.add_argument("--correction", choices=["bonferroni", "fdr"], default="bonferroni", help="Correction type.")
    parser.add_argument("--update-x-ref", default=None, help="Update size for x_ref. If None, no update.")
    parser.add_argument("--init-size", type=int, default=10, help="Number of initial reference instances (default: 100).")
    return parser.parse_args()

def main():
    args = parse_args()
    data, _ = load_dataset(args.input)
    raw_args = copy.deepcopy(args)
    try:
        series = data['series'][0]['raw']
        n_points = len(series)
        init_size = max(1, int((args.init_size / 100.0) * n_points))
        x_ref = np.array(series[:init_size], dtype=int).reshape(-1, 1)
        x_test = np.array(series[init_size:], dtype=int).reshape(-1, 1)

        # Parse update_x_ref safely
        update = None
        if args.update_x_ref is not None:
            try:
                update_size = int(args.update_x_ref)
                update = {"last": update_size}
            except ValueError:
                update = None

        # Extract unique categories from reference
        unique_categories = np.unique(x_ref[:, 0])
        categories_per_feature = {0: unique_categories.tolist()}

        min_cat = min(categories_per_feature[0])
        max_cat = max(categories_per_feature[0])

        detector = ChiSquareDrift(
            x_ref=x_ref,
            p_val=args.p_val,
            correction=args.correction,
            categories_per_feature=categories_per_feature,
            update_x_ref=update
        )

        drift_points = []
        start_time = time.time()

        for i, x in enumerate(x_test):
            val = x[0]
            if val not in categories_per_feature[0]:
                continue

            try:
                pred = detector.predict(np.array([[val]]))
                if pred["data"]["is_drift"]:
                    drift_points.append(i + init_size)
            except ValueError as ve:
                continue


        runtime = time.time() - start_time
        exit_success(data, raw_args, vars(args), drift_points, runtime, __file__)
    except Exception as e:
        exit_with_error(data, raw_args, vars(args), str(e), __file__)

if __name__ == "__main__":
    main()