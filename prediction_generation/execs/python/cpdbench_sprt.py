#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import time
import copy
import numpy as np
from cpdbench_utils import load_dataset, exit_success, exit_with_error

def parse_args():
    parser = argparse.ArgumentParser(description="Run SPRT on a time series dataset.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output JSON file.")
    parser.add_argument('--mu0', type=float, default=0.0, help="Mean under null hypothesis H0 (default: 0.0)")
    parser.add_argument('--mu1', type=float, default=1.0, help="Mean under alternative hypothesis H1 (default: 1.0)")
    parser.add_argument('--sigma', type=float, default=1.0, help="Known standard deviation (default: 1.0)")
    parser.add_argument('--threshold', type=float, default=15.0, help="Threshold to trigger change detection (default: 15.0)")
    parser.add_argument('--min-distance', type=int, default=30, help="Minimum distance between change points (default: 30)")
    return parser.parse_args()

def main():
    args = parse_args()
    data, mat = load_dataset(args.input)
    raw_args = copy.deepcopy(args)

    try:
        series = np.array(data['series'][0]['raw'])
        mu0, mu1 = args.mu0, args.mu1
        sigma2 = args.sigma ** 2
        threshold = args.threshold
        min_distance = args.min_distance

        llr_sum = 0.0
        drift_points = []
        cooldown = 0
        n = len(series)

        start_time = time.time()

        for t in range(n):
            if cooldown > 0:
                cooldown -= 1
                continue

            x = series[t]
            llr = ((mu1 - mu0) / sigma2) * (x - (mu0 + mu1) / 2)
            llr_sum += llr

            if abs(llr_sum) > threshold:
                if t > 0:  # avoid detecting at t=0
                    drift_points.append(t)
                    llr_sum = 0.0
                    cooldown = min_distance  # block next min_distance samples

        runtime = time.time() - start_time
        exit_success(data, raw_args, vars(args), drift_points, runtime, __file__)

    except Exception as e:
        exit_with_error(data, raw_args, vars(args), str(e), __file__)

if __name__ == "__main__":
    main()
