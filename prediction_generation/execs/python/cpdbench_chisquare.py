#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools
import argparse
import time
import copy
import numpy as np
from scipy.stats import chisquare
from cpdbench_utils import load_dataset, exit_success, exit_with_error
from collections import defaultdict
from collections import namedtuple


def parse_args():
    parser = argparse.ArgumentParser(description="Run statistical test on a time series dataset.")
    parser.add_argument('-i', '--input', required=True, help="Path to input JSON dataset.")
    parser.add_argument('-o', '--output', help="Path to output file.")
    parser.add_argument('-a', '--signatures-attributes', required=True, help="JSON file of signatures attributes")
    parser.add_argument("--bins", type=int, default=10, help="Number of bins for histogram.")
    parser.add_argument('--min-back-window', type=int, default=12)
    parser.add_argument('--max-back-window', type=int, default=24)
    parser.add_argument('--fore-window', type=int, default=12)
    parser.add_argument('--alpha', type=float, default=0.05)
    parser.add_argument('--alert-threshold', default="2")
    return parser.parse_args()


@functools.total_ordering
class RevisionDatum:
    def __init__(self, push_timestamp, push_id, values):
        self.push_timestamp = push_timestamp
        self.push_id = push_id
        self.values = copy.copy(values)
        self.stat = 0
        self.p = 1.0
        self.change_detected = False

    def __eq__(self, o):
        return self.push_timestamp == o.push_timestamp

    def __lt__(self, o):
        return self.push_timestamp < o.push_timestamp


def run_test(bins, jw, kw):
    # Extract values from the windows
    jw_values = [v for datum in jw for v in datum.values]
    kw_values = [v for datum in kw for v in datum.values]

    hist_ref, _ = np.histogram(jw_values, bins=bins)
    hist_curr, _ = np.histogram(kw_values, bins=bins)

    hist_ref = np.where(hist_ref == 0, 1e-6, hist_ref)
    hist_curr = np.where(hist_curr == 0, 1e-6, hist_curr)

    # Scale reference to match current window total
    scaling_factor = np.sum(hist_curr) / np.sum(hist_ref)
    hist_ref_scaled = hist_ref * scaling_factor

    stat, p_val = chisquare(f_obs=hist_curr, f_exp=hist_ref_scaled)
    return stat, p_val


def detect_changes(data, min_back_window=12, max_back_window=24, fore_window=12, alpha=0.05, bins=10):
    data = sorted(data)
    last_seen_regression = 0

    for i in range(1, len(data)):
        di = data[i]

        # Reference window (jw) from past
        jw = []
        di.amount_prev_data = 0
        prev_indice = i - 1
        while (
            di.amount_prev_data < max_back_window
            and prev_indice >= 0
            and (i - prev_indice <= min(max(last_seen_regression, min_back_window), max_back_window))
        ):
            jw.append(data[prev_indice])
            di.amount_prev_data += len(jw[-1].values)
            prev_indice -= 1

        # Current window (kw) from present/future
        kw = []
        di.amount_next_data = 0
        next_indice = i
        while di.amount_next_data < fore_window and next_indice < len(data):
            kw.append(data[next_indice])
            di.amount_next_data += len(kw[-1].values)
            next_indice += 1

        if len(jw) > 1 and len(kw) > 1:
            di.stat, di.p = run_test(bins, jw, kw)
        else:
            di.stat, di.p = 0, 1.0

        last_seen_regression = 0 if di.p < alpha else last_seen_regression + 1

    # Detect significant change points
    for i in range(1, len(data)):
        di = data[i]
        if di.amount_prev_data < min_back_window or di.amount_next_data < fore_window:
            continue
        if di.p >= alpha:
            continue
        prev = data[i - 1]
        if prev.p < di.p:
            continue
        if (i + 1) < len(data) and data[i + 1].p < di.p:
            continue
        di.change_detected = True

    return data


def main():
    args = parse_args()
    data_raw, mat = load_dataset(args.input)
    raw_data = copy.deepcopy(data_raw)

    series = data_raw['series'][0]['raw']
    push_timestamp = [ts for ts in data_raw['time']['raw']]

    grouped_data = defaultdict(list)
    for ts, value in zip(push_timestamp, series):
        grouped_data[ts].append(value)

    data = [RevisionDatum(ts, ts, grouped_data[ts]) for ts in grouped_data]

    analyzed_series = detect_changes(
        data,
        min_back_window=args.min_back_window,
        max_back_window=args.max_back_window,
        fore_window=args.fore_window,
        alpha=args.alpha,
        bins=args.bins
    )

    # Collect detected change points
    locations = [i for i, point in enumerate(analyzed_series) if point.change_detected]

    runtime = time.time() - time.time()
    exit_success(raw_data, args, vars(args), locations, runtime, __file__)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        exit_with_error(None, None, None, str(e), __file__)
