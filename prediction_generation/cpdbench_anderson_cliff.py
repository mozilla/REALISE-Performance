#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author: Mohamed Bilel Besbes
Date: 2025-01-28
"""

import functools
import argparse
import time
import copy
import numpy as np
from datetime import datetime
from cpdbench_utils import load_dataset, exit_success, exit_with_error
from collections import defaultdict
import moz_measure_noise
import json
import os
from collections import namedtuple
import newrelic.agent
import logging
from scipy import stats


def analyze(revision_data, weight_fn=None):
    if weight_fn is None:
        weight_fn = default_weights

    num_revisions = len(revision_data)
    weights = [weight_fn(i, num_revisions) for i in range(num_revisions)]
    weighted_sum = 0
    sum_of_weights = 0
    for i in range(num_revisions):
        weighted_sum += sum(value * weights[i] for value in revision_data[i].values)
        sum_of_weights += weights[i] * len(revision_data[i].values)
    weighted_avg = weighted_sum / sum_of_weights if num_revisions > 0 else 0.0

    all_data = [v for datum in revision_data for v in datum.values]
    variance = (
        (sum(pow(d - weighted_avg, 2) for d in all_data) / (len(all_data) - 1))
        if len(all_data) > 1
        else 0.0
    )
    return {"avg": weighted_avg, "n": len(all_data), "variance": variance}


def geomean(iterable):
    a = np.array(iterable)
    return a.prod() ** (1.0 / len(a))


def default_weights(i, n):
    return 1.0


def linear_weights(i, n):
    if i >= n:
        return 0.0
    return float(n - i) / float(n)


@functools.total_ordering
class RevisionDatum:
    def __init__(self, push_timestamp, push_id, values):
        self.push_timestamp = push_timestamp
        self.push_id = push_id
        self.values = copy.copy(values)
        self.t = 0
        self.change_detected = False

    def __eq__(self, o):
        return self.push_timestamp == o.push_timestamp

    def __lt__(self, o):
        return self.push_timestamp < o.push_timestamp

    def __repr__(self):
        values_csv = ", ".join([f"{value:.3f}" for value in self.values])
        values_str = f"[ {values_csv} ]"
        return f"<{self.push_timestamp}: {self.push_id}, {values_str}, {self.t:.3f}, {self.change_detected}>"


def detect_changes(data, min_back_window=12, max_back_window=24, fore_window=12, sig_level=0.05):
    data = sorted(data)
    last_seen_regression = 0

    for i in range(1, len(data)):
        di = data[i]
        jw = []
        di.amount_prev_data = 0
        prev_indice = i - 1
        while (
            di.amount_prev_data < max_back_window
            and prev_indice >= 0
            and (
                (i - prev_indice)
                <= min(max(last_seen_regression, min_back_window), max_back_window)
            )
        ):
            jw.append(data[prev_indice])
            di.amount_prev_data += len(jw[-1].values)
            prev_indice -= 1

        kw = []
        di.amount_next_data = 0
        next_indice = i
        while di.amount_next_data < fore_window and next_indice < len(data):
            kw.append(data[next_indice])
            di.amount_next_data += len(kw[-1].values)
            next_indice += 1

        di.historical_stats = analyze(jw)
        di.forward_stats = analyze(kw)

        if len(jw) > 0 and len(kw) > 0:
            jw_vals = [v for d in jw for v in d.values]
            kw_vals = [v for d in kw for v in d.values]

            try:
                res = stats.anderson_ksamp([jw_vals, kw_vals])
                di.statistic = res.statistic
                di.significance_level = res.significance_level / 100.0
                di.change_detected = di.significance_level < sig_level

                if di.change_detected:
                    last_seen_regression = 0
                else:
                    last_seen_regression += 1

            except Exception:
                di.statistic = 0
                di.significance_level = 1.0
                di.change_detected = False
                last_seen_regression += 1
        else:
            di.statistic = 0
            di.significance_level = 1.0
            di.change_detected = False
            last_seen_regression += 1

    return data


# ✅ Cliff's delta + category
def cliffs_delta(x, y):
    n = len(x)
    m = len(y)
    if n == 0 or m == 0:
        return 0.0

    greater = 0
    less = 0
    for xi in x:
        for yj in y:
            if xi > yj:
                greater += 1
            elif xi < yj:
                less += 1
    delta = (greater - less) / float(n * m)
    return abs(delta)


def cliffs_delta_category(delta):
    if delta < 0.147:
        return "negligible"
    elif delta < 0.33:
        return "small"
    elif delta < 0.474:
        return "medium"
    else:
        return "large"


def parse_args():
    parser = argparse.ArgumentParser(description="Run Mozilla algorithm on a time series dataset.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output file.")
    parser.add_argument('-a', '--signatures-attributes', help="JSON file of signatures attributes")
    parser.add_argument('--min-back-window', type=int, default=12)
    parser.add_argument('--max-back-window', type=int, default=24)
    parser.add_argument('--fore-window', type=int, default=12)
    parser.add_argument('--sig-level', type=float, default=0.05)

    # ✅ Change threshold arg to string category
    parser.add_argument(
        '--alert-threshold',
        choices=["negligible", "small", "medium", "large"],
        default="small",
        help="Minimum Cliff's delta effect size required to trigger an alert"
    )

    return parser.parse_args()


def get_alert_properties(prev_value, new_value, lower_is_better):
    AlertProperties = namedtuple("AlertProperties", "pct_change delta is_regression prev_value new_value")
    if prev_value != 0:
        pct_change = 100.0 * abs(new_value - prev_value) / float(prev_value)
    else:
        pct_change = 0.0
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

    raw_args = copy.deepcopy(args)
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
        sig_level=args.sig_level
    )

    threshold_order = ["negligible", "small", "medium", "large"]
    locations = []

    for prev, cur in zip(analyzed_series, analyzed_series[1:]):
        if cur.change_detected:
            prev_vals = [v for d in analyzed_series if d.push_timestamp < cur.push_timestamp for v in d.values]
            cur_vals = cur.values

            delta = cliffs_delta(prev_vals, cur_vals)
            category = cliffs_delta_category(delta)

            # Skip if delta category is less than threshold
            if threshold_order.index(category) < threshold_order.index(args.alert_threshold):
                continue

            prev_value = cur.historical_stats["avg"]
            new_value = cur.forward_stats["avg"]
            alert_properties = get_alert_properties(prev_value, new_value, signature.lower_is_better)

            try:
                noise_data = []
                for point in analyzed_series:
                    if point == cur:
                        break
                    noise_data.append(geomean(point.values))
                noise_profile, _ = moz_measure_noise.deviance(noise_data)
                if not isinstance(noise_profile, str):
                    raise Exception(f"Expecting string noise profile, got: {type(noise_profile)}")
            except Exception:
                newrelic.agent.notice_error()
                logger.error("Failed to obtain a noise profile.")

            # Append location if it passes all filters
            locations += [i for i, ts in enumerate(unique_push_timestamp) if ts == cur.push_timestamp]

    runtime = time.time() - start_time
    exit_success(raw_data, raw_args, vars(args), locations, runtime, __file__)


if __name__ == "__main__":
    main()
