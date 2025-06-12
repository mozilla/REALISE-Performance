#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import time
import copy
import numpy as np
from cpdbench_utils import load_dataset, exit_success, exit_with_error

from river.drift import PeriodicTrigger

def parse_args():
    parser = argparse.ArgumentParser(description="Run Online PeriodicTrigger on a time series dataset.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output JSON file.")
    parser.add_argument('--period', type=int, default=50,
                        help="Number of samples between triggers (default: 50)")
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

        detector = PeriodicTrigger(period=args.period)
        drift_points = []
        last_cp = -args.min_distance

        start_time = time.time()

        for i, x in enumerate(series):
            detector.update(x)
            if i >= init_count:
                if detector.change_detected and (i - last_cp > args.min_distance):
                    drift_points.append(i)
                    last_cp = i

        runtime = time.time() - start_time

        exit_success(data, raw_args, vars(args), drift_points, runtime, __file__)

    except Exception as e:
        exit_with_error(data, raw_args, vars(args), str(e), __file__)

if __name__ == "__main__":
    main()
