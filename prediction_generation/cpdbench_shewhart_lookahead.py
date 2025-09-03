#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import time
import copy
import numpy as np
from cpdbench_utils import load_dataset, exit_success, exit_with_error

def parse_args():
    parser = argparse.ArgumentParser(description="Run Online Shewhart Control Chart with lookahead average.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output JSON file.")
    parser.add_argument('--threshold', type=float, default=3.0,
                        help="Threshold multiplier for control limits (default: 3.0)")
    parser.add_argument('--init-size', type=float, default=10.0,
                        help="Initial window size as percentage of dataset (default: 10.0)")
    parser.add_argument('--min-distance', type=int, default=30,
                        help="Minimum distance between detected change points (default: 30)")
    parser.add_argument('--lookahead', type=int, default=12,
                        help="Number of future points to average for artificial current (default: 12)")
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

        # Estimate initial mean and std
        mu0 = np.mean(series[:init_count])
        std0 = np.std(series[:init_count])
        threshold = args.threshold * std0

        drift_points = []
        last_cp = -args.min_distance

        start_time = time.time()

        for i in range(init_count, n_points):
            # compute artificial current point as future average
            if i + args.lookahead < n_points:
                x = np.mean(series[i+1:i+1+args.lookahead])
            else:
                x = series[i]

            if abs(x - mu0) > threshold and (i - last_cp > args.min_distance):
                drift_points.append(i)
                last_cp = i

        runtime = time.time() - start_time
        exit_success(data, raw_args, vars(args), drift_points, runtime, __file__)

    except Exception as e:
        exit_with_error(data, raw_args, vars(args), str(e), __file__)

if __name__ == "__main__":
    main()
