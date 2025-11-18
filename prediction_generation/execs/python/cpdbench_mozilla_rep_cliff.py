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
#from django.db import transaction
from cliffs_delta import cliffs_delta
import moz_measure_noise
import json
import os
from collections import namedtuple
import newrelic.agent
import logging


CATEGORY_ORDER = {
    "negligible": 0,
    "small": 1,
    "medium": 2,
    "large": 3,
}


def analyze(revision_data, weight_fn=None):
    """Returns the average and sample variance (s**2) of a list of floats.

    `weight_fn` is a function that takes a list index and a window width, and
    returns a weight that is used to calculate a weighted average.  For example,
    see `default_weights` or `linear_weights` below.  If no function is passed,
    `default_weights` is used and the average will be uniformly weighted.
    """
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
    # Returns a geomean of a list of values.
    a = np.array(iterable)
    return a.prod() ** (1.0 / len(a))


def default_weights(i, n):
    """A window function that weights all points uniformly."""
    return 1.0


def linear_weights(i, n):
    """A window function that falls off arithmetically.

    This is used to calculate a weighted moving average (WMA) that gives higher
    weight to changes near the point being analyzed, and smooth out changes at
    the opposite edge of the moving window.  See bug 879903 for details.
    """
    if i >= n:
        return 0.0
    return float(n - i) / float(n)


def calc_t(w1, w2, weight_fn=None):
    """Perform a Students t-test on the two sets of revision data."""
    if not w1 or not w2:
        return 0

    s1 = analyze(w1, weight_fn)
    s2 = analyze(w2, weight_fn)
    delta_s = s2["avg"] - s1["avg"]

    if delta_s == 0:
        return 0
    if s1["variance"] == 0 and s2["variance"] == 0:
        return float("inf")

    return delta_s / (((s1["variance"] / s1["n"]) + (s2["variance"] / s2["n"])) ** 0.5)


@functools.total_ordering
class RevisionDatum:
    """This class represents a specific revision and the set of values for it"""

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


def detect_changes(data, min_back_window=12, max_back_window=24, fore_window=12, t_threshold=7):
    # Use T-Tests
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
        di.t = abs(calc_t(jw, kw, linear_weights))
        if di.t > t_threshold:
            last_seen_regression = 0
        else:
            last_seen_regression += 1

    for i in range(1, len(data)):
        di = data[i]
        if di.amount_prev_data < min_back_window or di.amount_next_data < fore_window:
            continue
        if di.t <= t_threshold:
            continue
        prev = data[i - 1]
        if prev.t > di.t:
            continue
        if (i + 1) < len(data):
            next = data[i + 1]
            if next.t > di.t:
                continue
        di.change_detected = True
    return data


def parse_args():
    parser = argparse.ArgumentParser(description="Run Mozilla algorithm on a time series dataset.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output file.")
    parser.add_argument('-a', '--signatures-attributes', help="JSON file of signatures attributes")
    parser.add_argument('--min-back-window', type=int, default=12, help="Minimum lookback window size (default: 12).")
    parser.add_argument('--max-back-window', type=int, default=24, help="Maximum lookback window size (default: 24).")
    parser.add_argument('--fore-window', type=int, default=12, help="Forecast/forward window size (default: 12).")
    parser.add_argument('--t-threshold', type=int, default=7, help="T statistic threshold for detection (default: 7).")
    parser.add_argument(
        '--alert-threshold',
        choices=["negligible", "small", "medium", "large"],
        default="small",
        help="Minimum Cliff's delta effect size category required to trigger an alert"
    )
    return parser.parse_args()


def get_alert_properties(prev_value, new_value, lower_is_better):
    AlertProperties = namedtuple(
        "AlertProperties", "pct_change delta is_regression prev_value new_value"
    )
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

    min_back_window=args.min_back_window
    max_back_window=args.max_back_window
    fore_window=args.fore_window
    t_threshold=args.t_threshold
    alert_threshold = args.alert_threshold
    analyzed_series = detect_changes(
        data,
        min_back_window=min_back_window,
        max_back_window=max_back_window,
        fore_window=fore_window,
        t_threshold=t_threshold,
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

            # ignore regressions below the configured regression threshold
            jw_values = [v for d in analyzed_series if d.push_timestamp <= prev.push_timestamp for v in d.values]
            kw_values = [v for d in analyzed_series if d.push_timestamp >= cur.push_timestamp for v in d.values]
            delta, category = cliffs_delta(jw_values, kw_values)
            if CATEGORY_ORDER[category] < CATEGORY_ORDER[alert_threshold]:
                continue

            t_value = cur.t
            if t_value == float("inf"):
                t_value = 1000

            locations += [i for i, ts in enumerate(unique_push_timestamp) if ts == cur.push_timestamp]

    stop_time = time.time()
    runtime = stop_time - start_time
    exit_success(raw_data, raw_args, vars(args), locations, runtime, __file__)


if __name__ == "__main__":
    main()
