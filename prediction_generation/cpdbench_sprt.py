#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import time
import copy
import numpy as np
from cpdbench_utils import load_dataset, exit_success, exit_with_error

from msprt import MSPRT

def parse_args():
    parser = argparse.ArgumentParser(description="Run Online MSPRT on a time series dataset.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output JSON file.")
    parser.add_argument('--mu0', type=float, default=0.0, help="Mean under H0 (default: 0.0)")
    parser.add_argument('--mu1', type=float, default=1.0, help="Mean under H1 (default: 1.0)")
    parser.add_argument('--sigma', type=float, default=1.0, help="Known standard deviation (default: 1.0)")
    parser.add_argument('--alpha', type=float, default=0.05, help="Type I error threshold (default: 0.05)")
    parser.add_argument('--beta', type=float, default=0.05, help="Type II error threshold (default: 0.05)")
    parser.add_argument('--init-size', type=float, default=10.0,
                        help="Initial window size as percentage of dataset to skip detection (default: 10.0)")
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

        init_count = max(1, int((args.init_size / 100.0) * n_points))
        if init_count >= n_points:
            raise ValueError("init_size too large for the dataset")

        detector = MSPRT(mu0=args.mu0, mu1=args.mu1, sigma=args.sigma,
                         alpha=args.alpha, beta=args.beta)

        drift_points = []
        last_cp = -args.min_distance
        start_time = time.time()

        for i, x in enumerate(series):
            decision = detector.update(x)
            if i >= init_count and decision == "accept H1" and (i - last_cp > args.min_distance):
                drift_points.append(i)
                last_cp = i
                detector.reset()  # Restart the test after detecting a change

        runtime = time.time() - start_time

        exit_success(data, raw_args, vars(args), drift_points, runtime, __file__)

    except Exception as e:
        exit_with_error(data, raw_args, vars(args), str(e), __file__)

if __name__ == "__main__":
    main()
