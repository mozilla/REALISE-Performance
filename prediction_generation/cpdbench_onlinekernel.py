#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import time
import copy
import numpy as np
from cpdbench_utils import load_dataset, exit_success, exit_with_error
from alibi_detect.cd import MMDDriftOnline

def parse_args():
    parser = argparse.ArgumentParser(description="Run Online Kernel MMD Drift Detection on a time series dataset.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output JSON file.")
    parser.add_argument('--ert', type=int, default=50,
                        help="Expected Run Time (ERT) to control false alarm rate (default: 50)")
    parser.add_argument('--window-size', type=int, default=50,
                        help="Sliding window size for recent samples (default: 50)")
    parser.add_argument('--init-size', type=float, default=10.0,
                        help="Initial window size as percentage of dataset for reference (default: 10.0)")
    parser.add_argument('--sigma', type=str, default=None,
                        help="Kernel bandwidth sigma (float) or None for median heuristic (default: None)")
    parser.add_argument('--backend', type=str, default='tensorflow',
                        help="Backend framework: tensorflow or pytorch (default: tensorflow)")
    return parser.parse_args()

def main():
    args = parse_args()
    data, mat = load_dataset(args.input)
    raw_args = copy.deepcopy(args)

    try:
        # Convert sigma argument from string to float or None
        if args.sigma is not None and args.sigma.lower() != 'none':
            sigma_val = float(args.sigma)
        else:
            sigma_val = None

        series = data['series'][0]['raw']
        n_points = len(series)

        init_count = max(1, int((args.init_size / 100.0) * n_points))
        if init_count + args.window_size > n_points:
            raise ValueError("init_size + window_size too large for the dataset")

        # Reference window
        x_ref = np.array(series[:init_count])

        # Initialize detector
        detector = MMDDriftOnline(
            x_ref=x_ref,
            ert=args.ert,
            window_size=args.window_size,
            backend=args.backend,
            sigma=sigma_val,
            verbose=False
        )

        drift_points = []
        last_cp = -args.window_size  # enforce min distance ~ window_size

        start_time = time.time()

        # Slide over data after reference window
        for i in range(init_count, n_points):
            x = np.array([series[i]])
            preds = detector.predict(x)

            if preds['data']['is_drift'] and (i - last_cp > args.window_size):
                drift_points.append(i)
                last_cp = i

        runtime = time.time() - start_time

        exit_success(data, raw_args, vars(args), drift_points, runtime, __file__)

    except Exception as e:
        exit_with_error(data, raw_args, vars(args), str(e), __file__)

if __name__ == "__main__":
    main()
