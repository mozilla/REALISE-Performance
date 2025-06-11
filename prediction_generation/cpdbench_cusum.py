#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import time
import copy
import numpy as np
from cpdbench_utils import load_dataset, exit_success, exit_with_error

def parse_args():
    parser = argparse.ArgumentParser(description="Run CUSUM on a time series dataset.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output JSON file.")
    parser.add_argument('--k', type=float, default=1.0, help="Reference value to filter small changes (default: 1.0)")
    parser.add_argument('--h', type=float, default=15.0, help="Threshold to trigger change detection (default: 15.0)")
    parser.add_argument('--init-size', type=float, default=10.0, help="Initial window size as percentage of dataset (default: 10.0)")
    parser.add_argument('--min-distance', type=int, default=30, help="Minimum distance between change points (default: 30)")
    return parser.parse_args()

def main():
    args = parse_args()
    data, mat = load_dataset(args.input)
    raw_args = copy.deepcopy(args)

    try:
        series = data['series'][0]['raw']
        n_points = len(series)
        init_count = max(1, int((args.init_size / 100.0) * n_points))

        if init_count >= n_points:
            raise ValueError("init_size too large for the dataset")

        mean_est = np.mean(series[:init_count])
        s_pos = 0.0
        s_neg = 0.0
        drift_points = []

        last_cp = -args.min_distance  # allow first detection
        start_time = time.time()

        for i in range(init_count, n_points):
            x = series[i]
            s_pos = max(0, s_pos + (x - mean_est - args.k))
            s_neg = max(0, s_neg - (x - mean_est + args.k))

            if (s_pos > args.h or s_neg > args.h) and (i - last_cp > args.min_distance):
                drift_points.append(i)
                last_cp = i
                s_pos, s_neg = 0.0, 0.0
                mean_est = np.mean(series[max(0, i - init_count):i])  # adaptive reset

        # Second-pass filtering to enforce min_distance strictly
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
