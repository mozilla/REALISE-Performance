#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import time
import copy
import numpy as np
from cpdbench_utils import load_dataset, exit_success, exit_with_error
from river.drift import DummyDriftDetector

def parse_args():
    parser = argparse.ArgumentParser(description="Run DummyDriftDetector with lookahead average.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output JSON file.")
    parser.add_argument('--trigger-method', type=str, choices=['fixed', 'random'], default='fixed',
                        help="Trigger method: 'fixed' or 'random' (default: 'fixed')")
    parser.add_argument('--t_0', type=int, default=300,
                        help="Reference period for drift signals (default: 300)")
    parser.add_argument('--w', type=int, default=0,
                        help="Warmup length (for 'fixed') or spread (for 'random'). Required for 'random'.")
    parser.add_argument('--seed', type=int, default=None,
                        help="Random seed (default: None)")
    parser.add_argument('--init-size', type=float, default=10.0,
                        help="Initial window size as percentage of dataset to skip detection (default: 10.0)")
    parser.add_argument('--min-distance', type=int, default=30,
                        help="Minimum distance between detected change points (default: 30)")
    parser.add_argument('--lookahead', type=int, default=12,
                        help="Number of future points to average for evaluation (default: 12)")
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

        detector = DummyDriftDetector(
            trigger_method=args.trigger_method,
            t_0=args.t_0,
            w=args.w,
            seed=args.seed,
            dynamic_cloning=False
        )

        drift_points = []
        last_cp = -args.min_distance

        start_time = time.time()

        for i in range(n_points):
            # update detector with true past point
            detector.update(series[i])

            # build artificial "current" point from future average
            if i + args.lookahead < n_points:
                artificial_x = np.mean(series[i+1:i+1+args.lookahead])
            else:
                artificial_x = series[i]

            # clone detector to evaluate artificial point
            temp_detector = copy.deepcopy(detector)
            temp_detector.update(artificial_x)

            if i >= init_count and temp_detector.drift_detected and (i - last_cp > args.min_distance):
                drift_points.append(i)
                last_cp = i

        runtime = time.time() - start_time
        exit_success(data, raw_args, vars(args), drift_points, runtime, __file__)

    except Exception as e:
        exit_with_error(data, raw_args, vars(args), str(e), __file__)

if __name__ == "__main__":
    main()