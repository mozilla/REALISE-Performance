#!/usr/bin/env python3

import os
import json
import argparse
from datetime import datetime, timedelta
from collections import defaultdict
from statistics import median

# ------------------------------------------------------------
# Utilities
# ------------------------------------------------------------

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def parse_ts(ts):
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")


def extract_cps(exp):
    if exp.get("status") != "SUCCESS":
        return []
    return exp.get("result", {}).get("cplocations", [])


def idx_to_ts(ts_json, idx):
    return parse_ts(ts_json["time"]["raw"][idx])


# ------------------------------------------------------------
# Ground truth (≥ min_annotators within delta)
# ------------------------------------------------------------

def merge_close_points(points, margin):
    clusters = []
    for p in sorted(points):
        if not clusters or abs(p - clusters[-1][-1]) > margin:
            clusters.append([p])
        else:
            clusters[-1].append(p)
    return clusters


def consolidate_method_points(points, margin, strategy="median"):
    clusters = merge_close_points(points, margin)
    if strategy == "median":
        return [int(round(median(c))) for c in clusters]
    elif strategy == "mean":
        return [int(round(sum(c) / len(c))) for c in clusters]
    else:
        raise ValueError(f"Unknown strategy: {strategy}")


def vote_and_average(cpd_points_dict, min_votes, margin, strategy="median"):
    """
    cpd_points_dict: {annotator_id: [cp_indices]}
    """
    consolidated = {
        m: consolidate_method_points(cps, margin, strategy)
        for m, cps in cpd_points_dict.items()
    }

    all_points = sorted({p for cps in consolidated.values() for p in cps})
    if not all_points:
        return []

    clusters = merge_close_points(all_points, margin)
    merged_cps = []

    for cluster in clusters:
        voters = set()
        cluster_points = []

        for annotator, cps in consolidated.items():
            close = [p for p in cps if any(abs(p - c) <= margin for c in cluster)]
            if close:
                voters.add(annotator)
                cluster_points.extend(close)

        if len(voters) >= min_votes:
            merged_cps.append(int(round(median(cluster_points))))

    final_clusters = merge_close_points(sorted(merged_cps), margin)
    return sorted(
        {int(round(median(c))) for c in final_clusters}
    )


# ------------------------------------------------------------
# DROP-IN REPLACEMENT for baseline construction
# ------------------------------------------------------------

def build_gt_per_ts(annotations, delta, min_annotators):
    """
    annotations:
      {
        ts_id: {
          annotator_id: [cp_idx, ...],
          ...
        }
      }
    """
    gt = {}
    for ts_id, annotator_points in annotations.items():
        gt[ts_id] = vote_and_average(
            cpd_points_dict=annotator_points,
            min_votes=min_annotators,
            margin=delta,
            strategy="median"
        )
    return gt

# ------------------------------------------------------------
# Alert summaries (timestamp-based)
# ------------------------------------------------------------

def build_alert_summaries(alerts, hours_buffer):
    summaries = []
    buf = timedelta(hours=hours_buffer)

    for ts_id, ts, kind in sorted(alerts, key=lambda x: x[1]):
        placed = False
        for s in summaries:
            if abs(ts - s["center"]) <= buf:
                s["alerts"].append((ts_id, ts, kind))
                placed = True
                break
        if not placed:
            summaries.append({
                "center": ts,
                "alerts": [(ts_id, ts, kind)]
            })
    return summaries


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()

    ap.add_argument("--annotations", required=True)
    ap.add_argument("--timeseries-dir", required=True)
    ap.add_argument("--results-dir", required=True)

    ap.add_argument("--delta", type=int, default=5)
    ap.add_argument("--min-annotators", type=int, default=3)
    ap.add_argument("--hours-buffer", type=int, default=24)

    ap.add_argument("--vars-methods", nargs="+", required=True)

    args = ap.parse_args()

    annotations = load_json(args.annotations)
    gt_per_ts = build_gt_per_ts(
        annotations, args.delta, args.min_annotators
    )

    ts_jsons = {}
    for ts_id in gt_per_ts:
        path = os.path.join(args.timeseries_dir, f"{ts_id}.json")
        if os.path.exists(path):
            ts_jsons[ts_id] = load_json(path)

    # --------------------------------------------------------
    # Baseline alert summaries (constant total)
    # --------------------------------------------------------

    baseline_alerts = []
    for ts_id, cps in gt_per_ts.items():
        if ts_id not in ts_jsons:
            continue
        for cp in cps:
            baseline_alerts.append(
                (ts_id, idx_to_ts(ts_jsons[ts_id], cp), "gt")
            )

    baseline_summaries = build_alert_summaries(
        baseline_alerts, args.hours_buffer
    )
    total_baseline = len(baseline_summaries)

    rows = []

    # --------------------------------------------------------
    # Per (variation, method)
    # --------------------------------------------------------

    for vm in args.vars_methods:
        variation, method = vm.split("_", 1)

        all_alerts = []

        for ts_id, gt_cps in gt_per_ts.items():
            if ts_id not in ts_jsons:
                continue

            ts_json = ts_jsons[ts_id]

            for cp in gt_cps:
                all_alerts.append(
                    (ts_id, idx_to_ts(ts_json, cp), "gt")
                )

            base = os.path.join(
                args.results_dir, ts_id, f"{variation}_{method}"
            )
            if not os.path.isdir(base):
                continue

            files = [f for f in os.listdir(base) if f.endswith(".json")]
            if not files:
                continue

            # best_* folders contain exactly one file
            exp = load_json(os.path.join(base, files[0]))
            for cp in extract_cps(exp):
                all_alerts.append(
                    (ts_id, idx_to_ts(ts_json, cp), "pred")
                )

        summaries = build_alert_summaries(
            all_alerts, args.hours_buffer
        )

        afp = sfp = nfp = afn = sfn = nfn = 0
        for s in summaries:
            has_gt = any(a[2] == "gt" for a in s["alerts"])
            has_pr = any(a[2] == "pred" for a in s["alerts"])

            if has_pr and not has_gt:
                afp += 1
            elif has_pr and has_gt:
                nfp += 1
            else:
                sfp += 1

            if has_gt and not has_pr:
                afn += 1
            elif has_gt and has_pr:
                nfn += 1
            else:
                sfn += 1

        rows.append(
            (vm, total_baseline, afp, sfp, nfp, afn, sfn, nfn)
        )

    # --------------------------------------------------------
    # LaTeX
    # --------------------------------------------------------

    print("\\begin{tabular}{lccccccc}")
    print("\\toprule")
    print("Method & Total & AFP & SFP & NFP & AFN & SFN & NFN \\\\")
    print("\\midrule")
    for r in rows:
        print(
            f"{r[0]} & {r[1]} & {r[2]} & {r[3]} & {r[4]} & "
            f"{r[5]} & {r[6]} & {r[7]} \\\\"
        )
    print("\\bottomrule")
    print("\\end{tabular}")


if __name__ == "__main__":
    main()
