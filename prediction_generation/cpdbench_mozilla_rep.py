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
import moz_measure_noise
import json
import os
from collections import namedtuple
import newrelic.agent
import logging

def analyze(revision_data, weight_fn=None):
    """Returns the average and sample variance (s**2) of a list of floats.

    `weight_fn` is a function that takes a list index and a window width, and
    returns a weight that is used to calculate a weighted average.  For example,
    see `default_weights` or `linear_weights` below.  If no function is passed,
    `default_weights` is used and the average will be uniformly weighted.
    """
    if weight_fn is None:
        weight_fn = default_weights

    # get a weighted average for the full set of data -- this is complicated
    # by the fact that we might have multiple data points from each revision
    # which we would want to weight equally -- do this by creating a set of
    # weights only for each bucket containing (potentially) multiple results
    # for each value
    num_revisions = len(revision_data)
    weights = [weight_fn(i, num_revisions) for i in range(num_revisions)]
    weighted_sum = 0
    sum_of_weights = 0
    for i in range(num_revisions):
        weighted_sum += sum(value * weights[i] for value in revision_data[i].values)
        sum_of_weights += weights[i] * len(revision_data[i].values)
    weighted_avg = weighted_sum / sum_of_weights if num_revisions > 0 else 0.0

    # now that we have a weighted average, we can calculate the variance of the
    # whole series
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
    """Perform a Students t-test on the two sets of revision data.

    See the analyze() function for a description of the `weight_fn` argument.
    """
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
    """
    This class represents a specific revision and the set of values for it
    """

    def __init__(self, push_timestamp, push_id, values):
        # Date code was pushed
        self.push_timestamp = push_timestamp

        # What revision this data is for (usually, but not guaranteed
        # to be increasing with push_timestamp)
        self.push_id = push_id

        # data values associated with this revision
        self.values = copy.copy(values)

        # t-test score
        self.t = 0

        # Whether a perf regression or improvement was found
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
    # Analyze test data using T-Tests, comparing data[i-j:i] to data[i:i+k]
    data = sorted(data)

    last_seen_regression = 0
    for i in range(1, len(data)):
        di = data[i]

        # keep on getting previous data until we've either got at least 12
        # data points *or* we've hit the maximum back window
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

        # accumulate present + future data until we've got at least 12 values
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
        # add additional historical data points next time if we
        # haven't detected a likely regression
        if di.t > t_threshold:
            last_seen_regression = 0
        else:
            last_seen_regression += 1

    # Now that the t-test scores are calculated, go back through the data to
    # find where changes most likely happened.
    for i in range(1, len(data)):
        di = data[i]

        # if we don't have enough data yet, skip for now (until more comes
        # in)
        if di.amount_prev_data < min_back_window or di.amount_next_data < fore_window:
            continue

        if di.t <= t_threshold:
            continue

        # Check the adjacent points
        prev = data[i - 1]
        if prev.t > di.t:
            continue
        # next may or may not exist if it's the last in the series
        if (i + 1) < len(data):
            next = data[i + 1]
            if next.t > di.t:
                continue

        # This datapoint has a t value higher than the threshold and higher
        # than either neighbor.  Mark it as the cause of a regression.
        di.change_detected = True

    return data



def parse_args():
    parser = argparse.ArgumentParser(description="Run Mozilla algorithm on a time series dataset.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument("-o", "--output", help="path to the output file")
    parser.add_argument("-a", "--signatures-attributes", help="JSON file of signatures attributes")
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
    # print(len(data['time']['raw']))
    # print(len(data['series'][0]['raw']))
    raw_args = copy.deepcopy(args)
    #try:
    series = data['series'][0]['raw']
    push_timestamp = data['time']['raw']
    push_timestamp = [datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in push_timestamp]
    #unique_push_timestamp = sorted(set(datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in push_timestamp))
    unique_push_timestamp = sorted(set(push_timestamp))
    grouped_data = defaultdict(list)
    for ts, value in zip(push_timestamp, series):
        grouped_data[ts].append(value)
    data = [RevisionDatum(ts, ts, grouped_data[ts]) for ts in grouped_data]
    # data_sorted = sorted(data)
    # These values are the default taken from the Mozilla code, Note that min_back_window, max_back_window, and fore_window come from class Performancesignature, I did not find them on record in the signatures data we have o we will be using the defaults
    min_back_window=12
    max_back_window=24
    fore_window=12
    alert_threshold=2    
    analyzed_series = detect_changes(
        data,
        min_back_window=min_back_window,
        max_back_window=max_back_window,
        fore_window=fore_window,
    )
    locations = []
    #with transaction.atomic():
    for prev, cur in zip(analyzed_series, analyzed_series[1:]):
        if cur.change_detected:
            prev_value = cur.historical_stats["avg"]
            new_value = cur.forward_stats["avg"]
            alert_properties = get_alert_properties(
                prev_value, new_value, signature.lower_is_better
            )
            noise_profile = "N/A"
            try:
                # Gather all data up to the current data point that
                # shows the regression and obtain a noise profile on it.
                # This helps us to ignore this alert and others in the
                # calculation that could influence the profile.
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
                # Fail without breaking the alert computation
                newrelic.agent.notice_error()
                logger.error("Failed to obtain a noise profile.")

            # ignore regressions below the configured regression
            # threshold

            # ALERT_PCT, ALERT_ABS, and ALERT_CHANGE_TYPES come from the PerformanceSignature class in the Treeherder code
            ALERT_PCT = 0
            ALERT_ABS = 1
            ALERT_CHANGE_TYPES = ((ALERT_PCT, "percentage"), (ALERT_ABS, "absolute"))
            if (
                (
                    signature.alert_change_type is None
                    or signature.alert_change_type == ALERT_PCT
                )
                and alert_properties.pct_change < alert_threshold
            ) or (
                signature.alert_change_type == ALERT_ABS
                and abs(alert_properties.delta) < alert_threshold
            ):
                continue
            # summary, _ = PerformanceAlertSummary.objects.get_or_create(
            #     repository=signature.repository,
            #     framework=signature.framework,
            #     push_id=cur.push_id,
            #     prev_push_id=prev.push_id,
            #     defaults={
            #         "manually_created": False,
            #         "created": datetime.utcfromtimestamp(cur.push_timestamp),
            #     },
            # )

            # django/mysql doesn't understand "inf", so just use some
            # arbitrarily high value for that case
            t_value = cur.t
            if t_value == float("inf"):
                t_value = 1000



            # This is where we create the alert aka append its index in the locations list
            # locations += [str(i) + "/t_value/" + str(cur.t) + "/pct_value/" + str(alert_properties.pct_change) + "/prev_value/" + str(prev_value) + "/new_value/" + str(new_value) for i, ts in enumerate(unique_push_timestamp) if ts == cur.push_timestamp]
            locations += [i for i, ts in enumerate(unique_push_timestamp) if ts == cur.push_timestamp]
            
            # PerformanceAlert.objects.update_or_create(
            #     summary=summary,
            #     series_signature=signature,
            #     defaults={
            #         "noise_profile": noise_profile,
            #         "is_regression": alert_properties.is_regression,
            #         "amount_pct": alert_properties.pct_change,
            #         "amount_abs": alert_properties.delta,
            #         "prev_value": prev_value,
            #         "new_value": new_value,
            #         "t_value": t_value,
            #     },
            # )

    stop_time = time.time()
    runtime = stop_time - start_time
    exit_success(raw_data, raw_args, vars(args), locations, runtime, __file__)
    # except Exception as e:
    #     exit_with_error(raw_data, raw_args, vars(args), str(e), __file__)
if __name__ == "__main__":
    main()