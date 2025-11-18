#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import time
import copy
import numpy as np
from cpdbench_utils import load_dataset, exit_success, exit_with_error

def parse_args():
    parser = argparse.ArgumentParser(description="Run Online CUSUM with lookahead average on a time series dataset.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output JSON file.")
    parser.add_argument('--k', type=float, default=1.0, help="Reference value to filter small changes (default: 1.0)")
    parser.add_argument('--h', type=float, default=15.0, help="Threshold to trigger change detection (default: 15.0)")
    parser.add_argument('--init-size', type=float, default=10.0, help="Initial window size as percentage of dataset (default: 10.0)")
    parser.add_argument('--min-distance', type=int, default=30, help="Minimum distance between change points (default: 30)")
    parser.add_argument('--lookahead', type=int, default=12, help="Number of future points to average for detection (default: 12)")
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

        last_cp = -args.min_distance
        start_time = time.time()

        for i in range(init_count, n_points):
            if i + args.lookahead < n_points:
                future_avg = np.mean(series[i+1:i+1+args.lookahead])
                x = 0.5 * (series[i] + future_avg)
            else:
                x = series[i]

            s_pos = max(0, s_pos + (x - mean_est - args.k))
            s_neg = max(0, s_neg - (x - mean_est + args.k))

            if (s_pos > args.h or s_neg > args.h) and (i - last_cp >= args.min_distance):
                drift_points.append(i)
                last_cp = i
                s_pos, s_neg = 0.0, 0.0
                mean_est = np.mean(series[max(0, i - init_count):i+1])  # re-estimate mean with past window

        runtime = time.time() - start_time
        exit_success(data, raw_args, vars(args), drift_points, runtime, __file__)

    except Exception as e:
        exit_with_error(data, raw_args, vars(args), str(e), __file__)

if __name__ == "__main__":
    main()
