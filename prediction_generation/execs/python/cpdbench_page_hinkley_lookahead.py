#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import time
import copy
import numpy as np
from river.drift import PageHinkley
from cpdbench_utils import load_dataset, exit_success, exit_with_error

def parse_args():
    parser = argparse.ArgumentParser(description="Run Page-Hinkley (river) with future-lookahead averaging.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output JSON file.")
    parser.add_argument('--min_instances', type=int, default=10, help="Minimum instances before detection (default: 30)")
    parser.add_argument('--delta', type=float, default=0.005, help="Delta factor for Page-Hinkley (default: 0.005)")
    parser.add_argument('--threshold', type=float, default=50.0, help="Threshold (lambda) (default: 50.0)")
    parser.add_argument('--alpha', type=float, default=0.9999, help="Forgetting factor (default: 0.9999)")
    parser.add_argument('--mode', type=str, choices=["up", "down", "both"], default="both", help="Mode to detect (default: both)")
    parser.add_argument('--lookahead', type=int, default=12, help="Number of future points to average (default: 12)")
    return parser.parse_args()

def main():
    args = parse_args()
    data, mat = load_dataset(args.input)
    start_time = time.time()
    raw_args = copy.deepcopy(args)

    try:
        series = data['series'][0]['raw']
        n_points = len(series)

        min_instances_count = max(1, int((args.min_instances / 100.0) * n_points))

        detector = PageHinkley(
            min_instances=min_instances_count,
            delta=args.delta,
            threshold=args.threshold,
            alpha=args.alpha,
            mode=args.mode
        )

        drift_points = []

        for i in range(n_points):
            # Update main detector with the true current point
            detector.update(series[i])

            # Build artificial future-based point
            if i + args.lookahead < n_points:
                artificial_x = np.mean(series[i+1:i+1+args.lookahead])
            else:
                artificial_x = series[i]

            # Clone detector to evaluate artificial point
            temp_detector = copy.deepcopy(detector)
            temp_detector.update(artificial_x)

            if temp_detector.drift_detected:
                drift_points.append(i)

        runtime = time.time() - start_time
        exit_success(data, raw_args, vars(args), drift_points, runtime, __file__)

    except Exception as e:
        exit_with_error(data, raw_args, vars(args), str(e), __file__)

if __name__ == "__main__":
    main()
