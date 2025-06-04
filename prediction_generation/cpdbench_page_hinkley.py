#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import time
import copy
from river.drift import PageHinkley
from cpdbench_utils import load_dataset, exit_success, exit_with_error

def parse_args():
    parser = argparse.ArgumentParser(description="Run Page-Hinkley (river) on a time series dataset.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output JSON file.")
    parser.add_argument('--min_instances', type=int, default=30, help="Minimum instances before detection (default: 30)")
    parser.add_argument('--delta', type=float, default=0.005, help="Delta factor for Page-Hinkley (default: 0.005)")
    parser.add_argument('--threshold', type=float, default=50.0, help="Threshold (lambda) (default: 50.0)")
    parser.add_argument('--alpha', type=float, default=0.9999, help="Forgetting factor (default: 0.9999)")
    parser.add_argument('--mode', type=str, choices=["up", "down", "both"], default="both", help="Mode to detect (default: both)")
    return parser.parse_args()

def main():
    args = parse_args()
    data, mat = load_dataset(args.input)
    start_time = time.time()
    raw_args = copy.deepcopy(args)

    try:
        series = data['series'][0]['raw']
        detector = PageHinkley(
            min_instances=args.min_instances,
            delta=args.delta,
            threshold=args.threshold,
            alpha=args.alpha,
            mode=args.mode
        )
        drift_points = []

        for i, val in enumerate(series):
            detector.update(val)
            if detector.change_detected:
                drift_points.append(i)

        runtime = time.time() - start_time
        exit_success(data, raw_args, vars(args), drift_points, runtime, __file__)
    except Exception as e:
        exit_with_error(data, raw_args, vars(args), str(e), __file__)

if __name__ == "__main__":
    main()
