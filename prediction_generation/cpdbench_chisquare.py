#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import time
import copy
import numpy as np
from scipy.stats import chisquare
from collections import deque
from cpdbench_utils import load_dataset, exit_success, exit_with_error

# There is no direct implementation of Sliding Window Chi-Square Test for Change Point Detection specifically for univariate timeseries
def parse_args():
    parser = argparse.ArgumentParser(description="Run Sliding Window Chi-Square Test on a time series dataset.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output JSON file.")
    parser.add_argument('--window-size', type=float, default=5.0,
                        help="Sliding window size as a percentage of dataset length (default: 5.0%%)")
    parser.add_argument('--num-bins', type=int, default=10,
                        help="Number of bins for histogram (default: 10)")
    parser.add_argument('--p-threshold', type=float, default=0.01,
                        help="Chi-Square p-value threshold to detect change (default: 0.01)")
    parser.add_argument('--min-distance', type=int, default=30,
                        help="Minimum distance between change points (default: 30)")
    return parser.parse_args()

def main():
    args = parse_args()
    data, mat = load_dataset(args.input)
    raw_args = copy.deepcopy(args)

    try:
        series = data['series'][0]['raw']
        n_points = len(series)

        win_size = max(1, int((args.window_size / 100.0) * n_points))
        if 2 * win_size >= n_points:
            raise ValueError("Window size too large for the dataset. Reduce window-size.")

        drift_points = []
        last_cp = -args.min_distance

        ref_win = deque(series[:win_size], maxlen=win_size)
        curr_win = deque(series[win_size:2*win_size], maxlen=win_size)

        start_time = time.time()

        for i in range(2 * win_size, n_points):
            data_min, data_max = min(series), max(series)

            hist_ref, _ = np.histogram(ref_win, bins=args.num_bins, range=(data_min, data_max))
            hist_curr, _ = np.histogram(curr_win, bins=args.num_bins, range=(data_min, data_max))

            # Avoid zeros for expected frequencies (to prevent division by zero)
            hist_ref = np.where(hist_ref == 0, 1e-6, hist_ref)
            hist_curr = np.where(hist_curr == 0, 1e-6, hist_curr)

            # Scale hist_curr so sums match hist_ref exactly to avoid scipy error
            sum_ref = hist_ref.sum()
            sum_curr = hist_curr.sum()

            if sum_ref != sum_curr:
                hist_curr = hist_curr * (sum_ref / sum_curr)

            stat, p_val = chisquare(f_obs=hist_curr, f_exp=hist_ref)

            if p_val < args.p_threshold and (i - last_cp > args.min_distance):
                drift_points.append(i)
                last_cp = i
                # Reset windows after detection
                ref_win = deque(series[i - 2*win_size:i - win_size], maxlen=win_size)
                curr_win = deque(series[i - win_size:i], maxlen=win_size)
            else:
                # Slide windows forward by one
                ref_win.append(curr_win.popleft())
                curr_win.append(series[i])

        runtime = time.time() - start_time
        exit_success(data, raw_args, vars(args), drift_points, runtime, __file__)

    except Exception as e:
        exit_with_error(data, raw_args, vars(args), str(e), __file__)

if __name__ == "__main__":
    main()
