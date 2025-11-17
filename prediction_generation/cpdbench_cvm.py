#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import time
import copy
import numpy as np
from alibi_detect.cd import CVMDriftOnline
from cpdbench_utils import load_dataset, exit_success, exit_with_error


def parse_args():
    parser = argparse.ArgumentParser(description="Run Online CVMDrift on a time series dataset.")
    parser.add_argument("-i", "--input", help="Path to the input JSON dataset file.")
    parser.add_argument("-o", "--output", help="Path to the output JSON file.")
    parser.add_argument("--ert", type=float, default=200.0,
                        help="Expected Run-Time (ERT) in absence of drift (default: 200.0)")
    parser.add_argument("--window-sizes", nargs='+', default=["20", "50"],
                        help="List of window sizes for sliding test windows (default: [20, 50])")
    parser.add_argument("--min-distance", type=int, default=30,
                        help="Minimum distance between detected change points (default: 30)")
    parser.add_argument("--n-bootstraps", type=int, default=1000,
                        help="Number of bootstrap simulations for threshold configuration (default: 1000)")
    return parser.parse_args()


def main():
    args = parse_args()
    data, mat = load_dataset(args.input)
    raw_args = copy.deepcopy(args)

    try:
        # Load and shape data
        series = np.array(data["series"][0]["raw"]).reshape(-1, 1)
        args.window_sizes = list(map(int, args.window_sizes))
        max_win = max(args.window_sizes)

        # Check for sufficient data
        if series.shape[0] < max_win + 1:
            raise ValueError(
                f"Not enough data points ({series.shape[0]}) for the largest window size ({max_win})."
            )

        # Reference window (x_ref)
        x_ref = series[:max_win]
        if x_ref.ndim != 2 or x_ref.shape[1] != 1:
            raise ValueError(f"x_ref shape must be (n, 1), got {x_ref.shape}")

        # Initialize detector
        detector = CVMDriftOnline(
            x_ref=x_ref,
            ert=args.ert,
            window_sizes=args.window_sizes,
            n_bootstraps=args.n_bootstraps,
            verbose=False,
        )

        drift_points = []
        last_cp = -args.min_distance
        start_time = time.time()

        # Stream data sequentially
        for i in range(max_win, len(series)):
            x_t = series[i].reshape(1, 1)

            try:
                pred = detector.predict(x_t, return_test_stat=True)
            except Exception as e:
                raise RuntimeError(f"Error at t={i}: {str(e)}")

            is_drift = int(pred["data"]["is_drift"])

            if is_drift and (i - last_cp > args.min_distance):
                drift_points.append(i)
                last_cp = i

        runtime = time.time() - start_time
        exit_success(data, raw_args, vars(args), drift_points, runtime, __file__)

    except Exception as e:
        exit_with_error(data, raw_args, vars(args), str(e), __file__)


if __name__ == "__main__":
    main()
