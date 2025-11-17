#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import time
import copy
import numpy as np
from river.drift import ADWIN
from cpdbench_utils import load_dataset, exit_success, exit_with_error

def parse_args():
    parser = argparse.ArgumentParser(description="Run ADWIN (river) on a time series dataset.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output JSON file.")
    parser.add_argument('--delta', type=float, default=0.002, help="Delta value for ADWIN")
    parser.add_argument('--max-buckets', type=int, default=5, help="The maximum number of buckets of each size that ADWIN should keep before merging buckets")
    parser.add_argument('--min-window-length', type=int, default=5, help="The minimum length allowed for a subwindow when checking for concept drift")
    parser.add_argument('--grace-period', type=float, default=10, help="ADWIN does not perform any change detection until at least this many data points have arrived.")
    return parser.parse_args()

def main():
    args = parse_args()
    data, mat = load_dataset(args.input)
    start_time = time.time()
    raw_args = copy.deepcopy(args)

    try:
        series = data['series'][0]['raw']
        detector = ADWIN(delta=args.delta, clock=1, min_window_length=args.min_window_length, grace_period=args.grace_period, max_buckets=args.max_buckets)
        drift_points = []

        for i, val in enumerate(series):
            detector.update(val)
            if detector.drift_detected:
                drift_points.append(i)

        runtime = time.time() - start_time
        exit_success(data, raw_args, vars(args), drift_points, runtime, __file__)
    except Exception as e:
        exit_with_error(data, raw_args, vars(args), str(e), __file__)

if __name__ == "__main__":
    main()
