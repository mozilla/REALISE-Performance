#!/usr/bin/env python3

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta

# ============================================================
# Utilities
# ============================================================

def parse_time(ts):
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")


def cluster_indices(indices, delta):
    indices = sorted(indices)
    clusters = []
    current = [indices[0]]

    for i in indices[1:]:
        if abs(i - current[-1]) <= delta:
            current.append(i)
        else:
            clusters.append(current)
            current = [i]
    clusters.append(current)
    return clusters

def extract_change_points(exp_json):
    """
    Extract CP locations from a TCPDBench experiment JSON.
    """
    if "result" not in exp_json:
        return []

    return exp_json["result"].get("cplocations", [])


# ============================================================
# Ground truth: consensus alerts
# ============================================================

def build_consensus_alerts(annotations, delta, min_annotators):
    consensus = defaultdict(list)

    for ts_id, annots in annotations.items():
        idx_to_users = defaultdict(set)
        for user, cps in annots.items():
            for cp in cps:
                idx_to_users[cp].add(user)

        clusters = cluster_indices(list(idx_to_users.keys()), delta)

        for cl in clusters:
            users = set()
            for p in cl:
                users |= idx_to_users[p]

            if len(users) >= min_annotators:
                consensus_idx = int(sum(cl) / len(cl))
                consensus[ts_id].append(consensus_idx)

    return consensus


# ============================================================
# Index → timestamp
# ============================================================

def index_to_timestamp(ts_json, idx):
    return parse_time(ts_json["time"]["raw"][idx])


# ============================================================
# Alert summaries (cross–time series)
# ============================================================

def build_alert_summaries(alerts, ts_data, hours_buffer):
    all_alerts = []

    for ts_id, indices in alerts.items():
        if ts_id not in ts_data:
            continue
        for idx in indices:
            ts = index_to_timestamp(ts_data[ts_id], idx)
            all_alerts.append((ts_id, ts))

    all_alerts.sort(key=lambda x: x[1])
    summaries = []
    buffer_td = timedelta(hours=hours_buffer)

    for alert in all_alerts:
        if not summaries:
            summaries.append([alert])
            continue

        last_time = summaries[-1][-1][1]
        if abs(alert[1] - last_time) <= buffer_td:
            summaries[-1].append(alert)
        else:
            summaries.append([alert])

    return summaries


# ============================================================
# Matching summaries
# ============================================================

def summary_center(summary):
    times = [t for _, t in summary]
    return min(times) + (max(times) - min(times)) / 2


def match_summaries(gt, pred, hours_buffer):
    buffer_td = timedelta(hours=hours_buffer)
    matched_gt = set()
    matched_pred = set()

    for i, g in enumerate(gt):
        g_c = summary_center(g)
        for j, p in enumerate(pred):
            p_c = summary_center(p)
            if abs(g_c - p_c) <= buffer_td:
                matched_gt.add(i)
                matched_pred.add(j)

    return matched_gt, matched_pred


# ============================================================
# Summary-level FP / FN metrics
# ============================================================

def compute_summary_metrics(gt, pred, hours_buffer):
    matched_gt, matched_pred = match_summaries(gt, pred, hours_buffer)

    fp_all = fp_some = fp_none = 0
    fn_all = fn_some = fn_none = 0

    for j in range(len(pred)):
        if j not in matched_pred:
            fp_all += 1
        else:
            fp_none += 1

    for i in range(len(gt)):
        if i not in matched_gt:
            fn_all += 1
        else:
            fn_none += 1

    return {
        "FP_all": fp_all,
        "FP_some": fp_some,
        "FP_none": fp_none,
        "FN_all": fn_all,
        "FN_some": fn_some,
        "FN_none": fn_none,
    }


# ============================================================
# F1 computation (for BEST selection)
# ============================================================

def tp_with_margin(gt, pred, delta):
    matched = set()
    for g in gt:
        for p in pred:
            if abs(g - p) <= delta and p not in matched:
                matched.add(p)
                break
    return len(matched)


def compute_f1(pred, gt, delta):
    if not pred and not gt:
        return 1.0
    if not pred or not gt:
        return 0.0

    tp = tp_with_margin(gt, pred, delta)
    p = tp / len(pred) if pred else 0
    r = tp / len(gt) if gt else 0
    return (2 * p * r) / (p + r) if (p + r) else 0.0


def select_best_experiment(results_dir, annotations, delta, variation, method):
    """
    Selects ONE experiment name globally (shared across all time series)
    """
    scores = defaultdict(list)

    for ts_id, annots in annotations.items():
        ts_path = os.path.join(results_dir, ts_id, f"{variation}_{method}")
        if not os.path.isdir(ts_path):
            continue

        for fname in os.listdir(ts_path):
            with open(os.path.join(ts_path, fname)) as f:
                exp = json.load(f)

            pred = extract_change_points(exp)
            gt = []
            for cps in annots.values():
                gt.extend(cps)

            f1 = compute_f1(pred, gt, delta)
            scores[fname].append(f1)

    avg_scores = {
        k: sum(v) / len(v) for k, v in scores.items() if v
    }

    return max(avg_scores, key=avg_scores.get)


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--timeseries-dir", required=True)
    parser.add_argument("--results-dir", required=True)
    parser.add_argument("--method", required=True)
    parser.add_argument("--variation", required=True)
    parser.add_argument("--delta", type=int, default=5)
    parser.add_argument("--min-annotators", type=int, default=3)
    parser.add_argument("--hours-buffer", type=float, default=24.0)

    args = parser.parse_args()

    # Load annotations
    with open(args.annotations) as f:
        annotations = json.load(f)

    # Load time series data
    ts_data = {}
    for fname in os.listdir(args.timeseries_dir):
        if fname.endswith(".json"):
            with open(os.path.join(args.timeseries_dir, fname)) as f:
                ts = json.load(f)
                ts_data[ts["name"]] = ts

    # Select best experiment if needed
    if args.variation == "best":
        best_exp_name = select_best_experiment(
            args.results_dir, annotations, args.delta, args.variation, args.method
        )
    else:
        best_exp_name = None

    # Load predictions
    predictions = {}

    for ts_id in annotations.keys():
        path = os.path.join(
            args.results_dir, ts_id, f"{args.variation}_{args.method}"
        )
        if not os.path.isdir(path):
            continue

        if args.variation == "best":
            fname = best_exp_name
        else:
            fname = os.listdir(path)[0]

        with open(os.path.join(path, fname)) as f:
            exp = json.load(f)
            predictions[ts_id] =  extract_change_points(exp)

    # Build GT summaries
    consensus = build_consensus_alerts(
        annotations, args.delta, args.min_annotators
    )
    gt_summaries = build_alert_summaries(
        consensus, ts_data, args.hours_buffer
    )

    # Build predicted summaries
    pred_summaries = build_alert_summaries(
        predictions, ts_data, args.hours_buffer
    )

    metrics = compute_summary_metrics(
        gt_summaries, pred_summaries, args.hours_buffer
    )

    # LaTeX row
    print(
        f"{args.method} & {args.variation} & "
        f"{metrics['FP_all']} & {metrics['FP_some']} & {metrics['FP_none']} & "
        f"{metrics['FN_all']} & {metrics['FN_some']} & {metrics['FN_none']} \\\\"
    )


if __name__ == "__main__":
    main()
