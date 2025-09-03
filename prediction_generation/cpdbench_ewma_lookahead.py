#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import time
import copy
import numpy as np
from cpdbench_utils import load_dataset, exit_success, exit_with_error

def parse_args():
    parser = argparse.ArgumentParser(description="Run Online EWMA Change Detector with lookahead average on a time series dataset.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output JSON file.")
    parser.add_argument('--alpha', type=float, default=0.3,
                        help="EWMA smoothing factor alpha (default: 0.3)")
    parser.add_argument('--threshold', type=float, default=3.0,
                        help="Threshold multiplier for change detection (default: 3.0)")
    parser.add_argument('--init-size', type=float, default=10.0,
                        help="Initial window size as percentage of dataset (default: 10.0)")
    parser.add_argument('--min-distance', type=int, default=30,
                        help="Minimum distance between detected change points (default: 30)")
    parser.add_argument('--lookahead', type=int, default=12,
                        help="Number of future points to average for detection (default: 12)")
    return parser.parse_args()

class OnlineEWMAChangeDetector:
    def __init__(self, alpha=0.3, threshold=3.0):
        self.alpha = alpha
        self.threshold = threshold
        self.ewma = None
        self.prev_ewma = None
        self.variance = 0.0
        self.n = 0
        self.drift = False

    def update(self, x):
        """Update EWMA state with the *true* past value."""
        if self.ewma is None:
            self.ewma = x
            self.prev_ewma = x
            self.n = 1
            self.variance = 0.0
            return

        self.prev_ewma = self.ewma
        self.ewma = self.alpha * x + (1 - self.alpha) * self.ewma

        residual = x - self.prev_ewma
        self.n += 1
        self.variance = (1 - self.alpha) * (self.variance + self.alpha * residual ** 2)

    def check_drift(self, artificial_x):
        """Check drift using the artificial 'future average' as the present point."""
        self.drift = False
        std_dev = np.sqrt(self.variance)
        if std_dev > 0 and abs(artificial_x - self.ewma) > self.threshold * std_dev:
            self.drift = True
        return self.drift

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

        detector = OnlineEWMAChangeDetector(alpha=args.alpha, threshold=args.threshold)
        drift_points = []
        last_cp = -args.min_distance

        start_time = time.time()

        for i in range(n_points):
            # always update detector with the true point (considered past)
            detector.update(series[i])

            # build artificial current point for evaluation
            if i + args.lookahead < n_points:
                artificial_x = np.mean(series[i+1:i+1+args.lookahead])
            else:
                artificial_x = series[i]

            # check for drift using artificial point
            if i >= init_count and detector.check_drift(artificial_x) and (i - last_cp > args.min_distance):
                drift_points.append(i)
                last_cp = i

        runtime = time.time() - start_time
        exit_success(data, raw_args, vars(args), drift_points, runtime, __file__)

    except Exception as e:
        exit_with_error(data, raw_args, vars(args), str(e), __file__)

if __name__ == "__main__":
    main()
