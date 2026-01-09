#!/usr/bin/env python3

"""
DEBUG VERSION – minimal but informative prints.

Goal:
- Inspect why Some/No FP/FN are always zero
- Print ONLY summary-level matching and alert-level matching counts
- Output is compact and copy-paste friendly

You can paste the CLI output back directly.
"""

import argparse
import json
import os
from datetime import datetime, timedelta
from statistics import median
import re

# ============================================================
# Utilities
# ============================================================

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def parse_ts(ts_str):
    return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")


def idx_to_ts(ts_json, idx):
    return parse_ts(ts_json["time"]["raw"][idx])


def within_time(t1, t2, hours):
    return abs(t1 - t2) <= timedelta(hours=hours)


def time_distance(t1, t2):
    return abs((t1 - t2).total_seconds())

def pretty_method_name(vm):
    s = re.sub(r"^(best_|default_)", "", vm)
    s = re.sub(r"(_advanced|_rep)$", "", s)
    return " ".join(p.capitalize() for p in s.split("_"))


# ============================================================
# Ground truth construction
# ============================================================

def merge_close_points(points, margin):
    clusters = []
    for p in sorted(points):
        if not clusters or abs(p - clusters[-1][-1]) > margin:
            clusters.append([p])
        else:
            clusters[-1].append(p)
    return clusters


def consolidate_method_points(points, margin):
    return [int(round(median(c))) for c in merge_close_points(points, margin)]


def vote_and_average(cpd_points_dict, min_votes, margin):
    consolidated = {
        u: consolidate_method_points(cps, margin)
        for u, cps in cpd_points_dict.items()
    }

    all_points = sorted({p for cps in consolidated.values() for p in cps})
    clusters = merge_close_points(all_points, margin)

    merged = []
    for cluster in clusters:
        voters, pts = set(), []
        for u, cps in consolidated.items():
            close = [p for p in cps if any(abs(p - c) <= margin for c in cluster)]
            if close:
                voters.add(u)
                pts.extend(close)
        if len(voters) >= min_votes:
            merged.append(int(round(median(pts))))

    return merged


# ============================================================
# Alert summaries
# ============================================================

def build_alert_summaries(alerts, buffer_hours):
    summaries = []
    alerts = sorted(alerts, key=lambda x: x["timestamp"])

    for a in alerts:
        placed = False
        for s in summaries:
            if (
                s["repository"] == a["repository"]
                and s["framework"] == a["framework"]
                and within_time(s["center"], a["timestamp"], buffer_hours)
            ):
                s["alerts"].append(a)
                times = [x["timestamp"] for x in s["alerts"]]
                s["center"] = min(times) + (max(times) - min(times)) / 2
                placed = True
                break

        if not placed:
            summaries.append({
                "repository": a["repository"],
                "framework": a["framework"],
                "center": a["timestamp"],
                "alerts": [a],
            })

    return summaries


# ============================================================
# Predictions
# ============================================================

def load_predictions(results_dir, ts_data, characteristics, variation, method):
    preds = []

    for ts_id, ts_json in ts_data.items():
        p = os.path.join(results_dir, ts_id, f"{variation}_{method}")
        if not os.path.isdir(p):
            continue

        for f in os.listdir(p):
            if not f.endswith(".json"):
                continue

            data = load_json(os.path.join(p, f))

            result = data.get("result", {})
            cplocs = result.get("cplocations", [])

            for cp in cplocs:
                ts = idx_to_ts(ts_json, cp)
                if ts is None:
                    continue

                preds.append({
                    "timestamp": ts,
                    "repository": characteristics[ts_id]["repository"],
                    "framework": characteristics[ts_id]["framework"],
                })

    return preds



# ============================================================
# DEBUG MATCHING
# ============================================================

def debug_matching(gt_summaries, pr_summaries, buffer_hours, max_print=5):
    print("\n=== DEBUG SUMMARY COUNTS ===")
    print(f"GT summaries: {len(gt_summaries)}")
    print(f"Pred summaries: {len(pr_summaries)}")

    matches = {}
    used_pred = set()

    for gi, gt in enumerate(gt_summaries):
        best = None
        best_d = None
        for pj, pr in enumerate(pr_summaries):
            if pj in used_pred:
                continue
            if (
                gt["repository"] == pr["repository"]
                and gt["framework"] == pr["framework"]
                and within_time(gt["center"], pr["center"], buffer_hours)
            ):
                d = time_distance(gt["center"], pr["center"])
                if best_d is None or d < best_d:
                    best_d = d
                    best = pj

        if best is not None:
            matches[gi] = best
            used_pred.add(best)

    print(f"Matched summary pairs: {len(matches)}")
    print(f"Unmatched GT summaries: {len(gt_summaries) - len(matches)}")
    print(f"Unmatched Pred summaries: {len(pr_summaries) - len(used_pred)}")

    print("\n=== SAMPLE MATCH DETAILS ===")
    for k, (gi, pj) in enumerate(matches.items()):
        if k >= max_print:
            break
        gt = gt_summaries[gi]
        pr = pr_summaries[pj]
        print(
            f"[{k}] GT alerts={len(gt['alerts'])}, "
            f"Pred alerts={len(pr['alerts'])}, "
            f"time_diff_h={(time_distance(gt['center'], pr['center'])/3600):.2f}"
        )

        gt_hits = sum(
            any(within_time(g["timestamp"], p["timestamp"], buffer_hours)
                for p in pr["alerts"])
            for g in gt["alerts"]
        )
        pr_hits = sum(
            any(within_time(p["timestamp"], g["timestamp"], buffer_hours)
                for g in gt["alerts"])
            for p in pr["alerts"]
        )

        print(f"    GT matched alerts: {gt_hits}/{len(gt['alerts'])}")
        print(f"    Pred matched alerts: {pr_hits}/{len(pr['alerts'])}")

    return matches


def summary_center(summary):
    # summary["alerts"] is a list of alerts with "timestamp"
    ts = [a["timestamp"] for a in summary["alerts"]]
    return min(ts) + (max(ts) - min(ts)) / 2


def match_summaries(gt_summaries, pred_summaries, delta):
    gt_centers = [summary_center(s) for s in gt_summaries]
    pred_centers = [summary_center(s) for s in pred_summaries]

    gt_matched = set()
    pred_matched = {}
    matches = []

    for pi, pc in enumerate(pred_centers):
        best_gi = None
        best_dist = None
        for gi, gc in enumerate(gt_centers):
            if gi in gt_matched:
                continue
            dist = abs(pc - gc)
            if dist <= delta and (best_dist is None or dist < best_dist):
                best_dist = dist
                best_gi = gi

        if best_gi is not None:
            gt_matched.add(best_gi)
            pred_matched[pi] = best_gi
            matches.append((gt_summaries[best_gi], pred_summaries[pi]))

    unmatched_gt = [s for i, s in enumerate(gt_summaries) if i not in gt_matched]
    unmatched_pred = [s for i, s in enumerate(pred_summaries) if i not in pred_matched]

    return matches, unmatched_gt, unmatched_pred


def match_alerts(gt_alerts, pred_alerts, delta):
    gt_used = set()
    matched = 0

    for pa in pred_alerts:
        for i, ga in enumerate(gt_alerts):
            if i in gt_used:
                continue
            if abs(pa["timestamp"] - ga["timestamp"]) <= delta:
                matched += 1
                gt_used.add(i)
                break

    fp = len(pred_alerts) - matched
    fn = len(gt_alerts) - matched
    return matched, fp, fn


def compute_fp_fn(gt_summaries, pred_summaries, delta):
    all_fp = all_fn = some_fp = some_fn = no_fp = no_fn = 0

    matches, unmatched_gt, unmatched_pred = match_summaries(
        gt_summaries, pred_summaries, delta
    )

    # unmatched summaries
    all_fp += len(unmatched_pred)
    all_fn += len(unmatched_gt)

    # matched summaries → alert-level comparison
    for gt_s, pr_s in matches:
        _, fp, fn = match_alerts(gt_s["alerts"], pr_s["alerts"], delta)

        if fp == 0:
            no_fp += 1
        else:
            some_fp += 1

        if fn == 0:
            no_fn += 1
        else:
            some_fn += 1

    return {
        "all_fp": all_fp,
        "some_fp": some_fp,
        "no_fp": no_fp,
        "all_fn": all_fn,
        "some_fn": some_fn,
        "no_fn": no_fn,
        "total": len(gt_summaries),
    }


def print_latex_table(results):
    print(r"\begin{tabular}{l|cc|ccc|ccc}")
    print(r"\hline")
    print(
        r"Method "
        r"& \multicolumn{1}{c}{GT} "
        r"& \multicolumn{1}{c|}{Pred} "
        r"& \multicolumn{3}{c|}{False Positives} "
        r"& \multicolumn{3}{c}{False Negatives} \\"
    )
    print(r"& & & All & Some & None & All & Some & None \\")
    print(r"\hline")


    for r in results:
        print(
        f"{r['method']} "
        f"& {r['total']} "
        f"& {r['pred_total']} "
        f"& {r['all_fp']} & {r['some_fp']} & {r['no_fp']} "
        f"& {r['all_fn']} & {r['some_fn']} & {r['no_fn']} \\\\"
    )

    print(r"\hline")
    print(r"\end{tabular}")

# ============================================================
# Main
# ============================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--annotations", required=True)
    ap.add_argument("--timeseries-json-dir", required=True)
    ap.add_argument("--characteristics", required=True)
    ap.add_argument("--results-dir", required=True)
    ap.add_argument("--vars-methods", nargs="+", required=True)
    ap.add_argument("--delta", type=int, default=5)
    ap.add_argument("--min-annotators", type=int, default=3)
    ap.add_argument("--buffer-hours", type=int, default=24)
    args = ap.parse_args()

    annotations = load_json(args.annotations)
    characteristics = load_json(args.characteristics)
    delta = timedelta(hours=args.delta)


    ts_data = {}
    for f in os.listdir(args.timeseries_json_dir):
        if f.endswith(".json"):
            ts = load_json(os.path.join(args.timeseries_json_dir, f))
            ts_data[ts["name"]] = ts

    gt_alerts = []
    for ts_id, users in annotations.items():
        cps = vote_and_average(users, args.min_annotators, args.delta)
        for cp in cps:
            gt_alerts.append({
                "timestamp": idx_to_ts(ts_data[ts_id], cp),
                "repository": characteristics[ts_id]["repository"],
                "framework": characteristics[ts_id]["framework"],
            })

    gt_summaries = build_alert_summaries(gt_alerts, args.buffer_hours)

    results = []

    for vm in args.vars_methods:
        variation, method = vm.split("_", 1)

        pred_alerts = load_predictions(
            args.results_dir, ts_data, characteristics, variation, method
        )

        pr_summaries = build_alert_summaries(
            pred_alerts, args.buffer_hours
        )

        stats = compute_fp_fn(gt_summaries, pr_summaries, delta)

        stats["method"] = pretty_method_name(vm)
        stats["pred_total"] = len(pr_summaries)
        results.append(stats)
    print_latex_table(results)


if __name__ == "__main__":
    main()
