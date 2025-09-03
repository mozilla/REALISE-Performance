#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Kolmogorov–Smirnov (KS) test based performance regression detection
Author: Mohamed Bilel Besbes
Date: 2025-08-26
"""

import functools
import argparse
import time
import copy
import numpy as np
from datetime import datetime
from cpdbench_utils import load_dataset, exit_success, exit_with_error
from collections import defaultdict, namedtuple
import moz_measure_noise
import json
import os
import newrelic.agent
import logging
from scipy import stats


def analyze(revision_data):
    """Flatten all values for average, n, and variance."""
    all_data = [v for datum in revision_data for v in datum.values]
    if not all_data:
        return {"avg": 0.0, "n": 0, "variance": 0.0}

    avg = np.mean(all_data)
    var = np.var(all_data, ddof=1) if len(all_data) > 1 else 0.0
    return {"avg": avg, "n": len(all_data), "variance": var}


def geomean(iterable):
    a = np.array(iterable)
    return a.prod() ** (1.0 / len(a))


@functools.total_ordering
class RevisionDatum:
    """Represents a specific revision and the set of values for it."""

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

    def __repr__(self):
        values_csv = ", ".join([f"{value:.3f}" for value in self.values])
        values_str = f"[ {values_csv} ]"
        return f"<{self.push_timestamp}: {self.push_id}, {values_str}, KS={self.stat:.3f}, p={self.p:.3f}, change={self.change_detected}>"


def detect_changes(data, min_back_window=12, max_back_window=24, fore_window=12, alpha=0.05):
    # Use Kolmogorov–Smirnov test (two-sample, nonparametric)
    data = sorted(data)
    last_seen_regression = 0

    for i in range(1, len(data)):
        di = data[i]

        # back window
        jw = []
        di.amount_prev_data = 0
        prev_ind = i - 1
        while (
            di.amount_prev_data < max_back_window
            and prev_ind >= 0
            and (
                (i - prev_ind)
                <= min(max(last_seen_regression, min_back_window), max_back_window)
            )
        ):
            jw.append(data[prev_ind])
            di.amount_prev_data += len(jw[-1].values)
            prev_ind -= 1

        # forward window
        kw = []
        di.amount_next_data = 0
        next_ind = i
        while di.amount_next_data < fore_window and next_ind < len(data):
            kw.append(data[next_ind])
            di.amount_next_data += len(kw[-1].values)
            next_ind += 1

        di.historical_stats = analyze(jw)
        di.forward_stats = analyze(kw)

        # run KS test if we have enough data
        jw_values = [v for datum in jw for v in datum.values]
        kw_values = [v for datum in kw for v in datum.values]
        if len(jw_values) > 1 and len(kw_values) > 1:
            stat, p_val = stats.ks_2samp(jw_values, kw_values)
            di.stat = stat
            di.p = p_val
        else:
            di.stat = 0
            di.p = 1.0

        if di.p < alpha:
            last_seen_regression = 0
        else:
            last_seen_regression += 1

    # Detect change points (p-value criterion + local max stat)
    for i in range(1, len(data)):
        di = data[i]
        if di.amount_prev_data < min_back_window or di.amount_next_data < fore_window:
            continue
        if di.p >= alpha:
            continue

        prev = data[i - 1]
        if prev.p < di.p:
            continue
        if (i + 1) < len(data):
            nxt = data[i + 1]
            if nxt.p < di.p:
                continue

        di.change_detected = True

    return data


def parse_args():
    parser = argparse.ArgumentParser(description="Run Kolmogorov–Smirnov test algorithm on a time series dataset.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output file.")
    parser.add_argument('-a', '--signatures-attributes', help="JSON file of signatures attributes")
    parser.add_argument('--min-back-window', type=int, default=12, help="Minimum lookback window size (default: 12).")
    parser.add_argument('--max-back-window', type=int, default=24, help="Maximum lookback window size (default: 24).")
    parser.add_argument('--fore-window', type=int, default=12, help="Forecast/forward window size (default: 12).")
    parser.add_argument('--alpha', type=float, default=0.05, help="Significance level for KS test (default: 0.05).")
    parser.add_argument('--alert-threshold', default="2", help="Alert threshold value (default: 2).")
    return parser.parse_args()


def get_alert_properties(prev_value, new_value, lower_is_better):
    AlertProperties = namedtuple(
        "AlertProperties", "pct_change delta is_regression prev_value new_value"
    )
    pct_change = 100.0 * abs(new_value - prev_value) / float(prev_value) if prev_value != 0 else 0.0
    delta = new_value - prev_value
    is_regression = (delta > 0 and lower_is_better) or (delta < 0 and not lower_is_better)
    return AlertProperties(pct_change, delta, is_regression, prev_value, new_value)


def main():
    logger = logging.getLogger(__name__)
    args = parse_args()
    data, mat = load_dataset(args.input)
    raw_data = data.copy()
    start_time = time.time()

    with open(args.signatures_attributes, 'r') as file:
        signatures_attributes = json.load(file)
    signature_id = os.path.splitext(os.path.basename(args.input))[0]
    signature_attributes = signatures_attributes[signature_id]
    Signature = namedtuple('Signature', signature_attributes.keys())
    signature = Signature(**signature_attributes)

    series = data['series'][0]['raw']
    push_timestamp = data['time']['raw']
    push_timestamp = [datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in push_timestamp]
    unique_push_timestamp = sorted(set(push_timestamp))
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
    )

    locations = []
    for prev, cur in zip(analyzed_series, analyzed_series[1:]):
        if cur.change_detected:
            prev_value = cur.historical_stats["avg"]
            new_value = cur.forward_stats["avg"]
            alert_properties = get_alert_properties(
                prev_value, new_value, signature.lower_is_better
            )
            noise_profile = "N/A"
            try:
                noise_data = []
                for point in analyzed_series:
                    if point == cur:
                        break
                    noise_data.append(geomean(point.values))
                noise_profile, _ = moz_measure_noise.deviance(noise_data)
                if not isinstance(noise_profile, str):
                    raise Exception(
                        f"Expecting a string as a noise profile, got: {type(noise_profile)}"
                    )
            except Exception:
                newrelic.agent.notice_error()
                logger.error("Failed to obtain a noise profile.")

            ALERT_PCT = 0
            ALERT_ABS = 1
            if args.alert_threshold != "disabled":
                if (
                    (
                        signature.alert_change_type is None
                        or signature.alert_change_type == ALERT_PCT
                    )
                    and alert_properties.pct_change < int(args.alert_threshold)
                ) or (
                    signature.alert_change_type == ALERT_ABS
                    and abs(alert_properties.delta) < int(args.alert_threshold)
                ):
                    continue

            locations += [i for i, ts in enumerate(unique_push_timestamp) if ts == cur.push_timestamp]

    stop_time = time.time()
    runtime = stop_time - start_time
    exit_success(raw_data, copy.deepcopy(args), vars(args), locations, runtime, __file__)


if __name__ == "__main__":
    main()
