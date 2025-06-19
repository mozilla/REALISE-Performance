#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import time
import copy
import numpy as np
from cpdbench_utils import load_dataset, exit_success, exit_with_error


def parse_args():
    parser = argparse.ArgumentParser(description="Run MOSUM on a time series dataset.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output JSON file.")
    parser.add_argument('--window-size', type=int, default=20,
                        help="Half-window size G (default: 20 means MOSUM compares G points before and after)")
    parser.add_argument('--threshold', type=float, default=3.0,
                        help="Z-score threshold to trigger change (default: 3.0)")
    parser.add_argument('--init-size', type=float, default=10.0,
                        help="Initial window size as percentage of dataset (default: 10.0)")
    parser.add_argument('--min-distance', type=int, default=30,
                        help="Minimum distance between detected change points (default: 30)")
    return parser.parse_args()

def main():
    args = parse_args()
    data, mat = load_dataset(args.input)
    raw_args = copy.deepcopy(args)

    try:
        series = data['series'][0]['raw']
        n_points = len(series)
        G = args.window_size

        init_count = max(1, int((args.init_size / 100.0) * n_points))
        if init_count + 2 * G >= n_points:
            raise ValueError("init_size and/or window_size too large for dataset")

        drift_points = []
        last_cp = -args.min_distance
        start_time = time.time()

        for t in range(init_count + G, n_points - G):
            left_window = series[t - G:t]
            right_window = series[t:t + G]

            mean_left = np.mean(left_window)
            mean_right = np.mean(right_window)
            pooled_std = np.std(series[t - G:t + G], ddof=1)

            if pooled_std == 0:
                continue  # avoid divide by zero

            mosum_stat = abs(mean_right - mean_left) / (pooled_std / np.sqrt(G))
            if mosum_stat > args.threshold and (t - last_cp > args.min_distance):
                drift_points.append(t)
                last_cp = t

        # Enforce min_distance between points
        filtered_points = []
        last_cp = -np.inf
        for cp in drift_points:
            if cp - last_cp >= args.min_distance:
                filtered_points.append(cp)
                last_cp = cp

        runtime = time.time() - start_time
        exit_success(data, raw_args, vars(args), filtered_points, runtime, __file__)

    except Exception as e:
        exit_with_error(data, raw_args, vars(args), str(e), __file__)

if __name__ == "__main__":
    main()
