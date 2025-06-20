#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import time
import copy
import numpy as np
from cpdbench_utils import load_dataset, exit_success, exit_with_error

def parse_args():
    parser = argparse.ArgumentParser(description="Run Online MOSUM on a time series dataset.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output JSON file.")
    parser.add_argument('--window-size', type=int, default=30, help="Size of the moving window (default: 30)")
    parser.add_argument('--threshold', type=float, default=3.0, help="Threshold on the mean change to flag a change point (default: 3.0)")
    parser.add_argument('--min-distance', type=int, default=30, help="Minimum distance between change points (default: 30)")
    return parser.parse_args()

def main():
    args = parse_args()
    data, mat = load_dataset(args.input)
    raw_args = copy.deepcopy(args)

    try:
        series = data['series'][0]['raw']
        n = len(series)
        W = args.window_size
        threshold = args.threshold

        if W >= n:
            raise ValueError("window-size too large for the dataset")

        drift_points = []
        last_cp = -args.min_distance  # allow first detection
        start_time = time.time()

        buffer = []

        for i in range(n):
            buffer.append(series[i])
            if len(buffer) > W:
                buffer.pop(0)

            if len(buffer) < W:
                continue  # wait for full window

            first_half = buffer[:W//2]
            second_half = buffer[W//2:]

            mean_diff = abs(np.mean(first_half) - np.mean(second_half))

            if mean_diff > threshold and (i - last_cp > args.min_distance):
                drift_points.append(i)
                last_cp = i
                # Optionally clear buffer to reset
                buffer = []

        runtime = time.time() - start_time
        exit_success(data, raw_args, vars(args), drift_points, runtime, __file__)

    except Exception as e:
        exit_with_error(data, raw_args, vars(args), str(e), __file__)

if __name__ == "__main__":
    main()
