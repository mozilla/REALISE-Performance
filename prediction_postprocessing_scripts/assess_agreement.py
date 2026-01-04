#!/usr/bin/env python3

import argparse
import json
import os
import glob
from collections import defaultdict, Counter
from typing import Dict, List, Set

import pandas as pd
import matplotlib.pyplot as plt


def parse_args():
    p = argparse.ArgumentParser(description="Evaluate a CPD method weekly with tolerance-based matching.")
    p.add_argument("--timeseries-data", required=True)
    p.add_argument("--results-dir", required=True)
    p.add_argument("--annotations-file", required=True)
    p.add_argument("--method", required=True)
    p.add_argument("--variation", choices=("best", "default"), default="best")
    p.add_argument("--margin", type=int, required=True,
                   help="Index tolerance margin k: |detected - annotated| <= margin.")
    p.add_argument("--output-folder", required=True)
    return p.parse_args()


def load_annotations(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_timeseries_meta(ts_json_path: str):
    with open(ts_json_path, "r", encoding="utf-8") as f:
        j = json.load(f)
    time_raw = j.get("time", {}).get("raw", [])
    return pd.to_datetime(time_raw, errors="coerce")


def find_method_result_json(results_subfolder: str):
    json_files = glob.glob(os.path.join(results_subfolder, "*.json"))
    for jf in json_files:
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "result" in data and "cplocations" in data["result"]:
                return jf
        except:
            pass
    return json_files[0] if json_files else None


def load_detected_cps(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "result" in data and "cplocations" in data["result"]:
            cps = data["result"]["cplocations"]
        else:
            cps = []
        return [int(i) for i in cps]
    except:
        return []


def week_label_from_timestamp(ts: pd.Timestamp):
    if pd.isna(ts):
        return None
    iso = ts.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def ensure_output_folder(path):
    os.makedirs(path, exist_ok=True)


# ============================================================
#           MATCHING WITH INDEX TOLERANCE MARGIN
# ============================================================
def tolerance_match(detected: Set[int], annotated: Set[int], margin: int):
    """
    Returns:
        matched_detected: set of detected indices that matched some annotation
        matched_annotated: set of annotated indices that matched some detection
    Ensures NO double-matching: once a detected index matches an annotation,
    both are removed from availability.
    """
    detected_sorted = sorted(detected)
    annotated_sorted = sorted(annotated)

    used_detected = set()
    used_annotated = set()

    j = 0
    for d in detected_sorted:
        while j < len(annotated_sorted) and annotated_sorted[j] < d - margin:
            j += 1
        k = j
        while k < len(annotated_sorted) and annotated_sorted[k] <= d + margin:
            a = annotated_sorted[k]
            if a not in used_annotated and d not in used_detected:
                used_detected.add(d)
                used_annotated.add(a)
                break
            k += 1

    return used_detected, used_annotated


def main():
    args = parse_args()
    ensure_output_folder(args.output_folder)

    annotations = load_annotations(args.annotations_file)

    weekly_validated = {x: Counter() for x in range(1, 7)}
    weekly_detected_not_validated = {x: Counter() for x in range(1, 7)}
    weekly_annotated_not_caught = {x: Counter() for x in range(1, 7)}

    ts_files = glob.glob(os.path.join(args.timeseries_data, "*.json"))
    if not ts_files:
        print("No timeseries JSONs found.")
        return

    for ts_file in ts_files:
        ts_id = os.path.splitext(os.path.basename(ts_file))[0]

        timestamps = load_timeseries_meta(ts_file)
        if len(timestamps) == 0:
            continue

        results_ts_folder = os.path.join(args.results_dir, ts_id)
        if not os.path.isdir(results_ts_folder):
            continue

        method_folder = os.path.join(results_ts_folder, f"{args.variation}_{args.method}")
        if not os.path.isdir(method_folder):
            poss = glob.glob(os.path.join(results_ts_folder, f"*{args.variation}_{args.method}*"))
            if poss:
                method_folder = poss[0]
            else:
                continue

        result_json = find_method_result_json(method_folder)
        if not result_json:
            continue

        detected_cps = load_detected_cps(result_json)
        detected_cps = {i for i in detected_cps if 0 <= i < len(timestamps)}

        ts_annotations = annotations.get(ts_id, {})
        annotation_count = Counter()

        for annotator, lst in ts_annotations.items():
            for idx in lst:
                try:
                    ii = int(idx)
                    if 0 <= ii < len(timestamps):
                        annotation_count[ii] += 1
                except:
                    pass

        annotated_by_ge = {
            x: {idx for idx, c in annotation_count.items() if c >= x}
            for x in range(1, 7)
        }

        indices_to_label = set(detected_cps)
        for x in range(1, 7):
            indices_to_label.update(annotated_by_ge[x])

        index_week = {}
        for idx in indices_to_label:
            ts = timestamps[idx]
            lbl = week_label_from_timestamp(ts)
            if lbl:
                index_week[idx] = lbl

        for x in range(1, 7):
            annotated_set = annotated_by_ge[x]

            matched_det, matched_ann = tolerance_match(detected_cps, annotated_set, args.margin)

            detected_not_validated = set(detected_cps) - matched_det
            annotated_not_caught = annotated_set - matched_ann

            for idx in matched_det:
                lbl = index_week.get(idx)
                if lbl:
                    weekly_validated[x][lbl] += 1

            for idx in detected_not_validated:
                lbl = index_week.get(idx)
                if lbl:
                    weekly_detected_not_validated[x][lbl] += 1

            for idx in annotated_not_caught:
                lbl = index_week.get(idx)
                if lbl:
                    weekly_annotated_not_caught[x][lbl] += 1

    all_weeks = set()
    for x in range(1, 7):
        all_weeks |= set(weekly_validated[x].keys())
        all_weeks |= set(weekly_detected_not_validated[x].keys())
        all_weeks |= set(weekly_annotated_not_caught[x].keys())

    def week_label_to_period(lbl):
        try:
            year, w = lbl.split("-W")
            return pd.Period(year=int(year), freq="W").start_time + pd.Timedelta(weeks=int(w) - 1)
        except:
            return pd.NaT

    week_sort = sorted(all_weeks, key=lambda w: week_label_to_period(w))
    week_dates = [week_label_to_period(w) for w in week_sort]

    for x in range(1, 7):
        vals1 = [weekly_validated[x].get(w, 0) for w in week_sort]
        vals2 = [weekly_detected_not_validated[x].get(w, 0) for w in week_sort]
        vals3 = [weekly_annotated_not_caught[x].get(w, 0) for w in week_sort]

        plt.figure(figsize=(14, 6))
        plt.plot(week_dates, vals1, marker="o", label=f"Detected & validated (≥{x} annotators)")
        plt.plot(week_dates, vals2, marker="o", label=f"Detected but NOT validated (≥{x})")
        plt.plot(week_dates, vals3, marker="o", label=f"Annotated (≥{x}) but NOT detected")

        plt.xlabel("Week")
        plt.ylabel("Count")
        plt.title(f"{args.method} ({args.variation}) — Weekly Performance (margin={args.margin}, ≥{x} annotators)")
        plt.legend()
        plt.grid(True, linestyle="--", linewidth=0.4)
        plt.tight_layout()

        out_path = os.path.join(args.output_folder, f"method_performance_at_{x}_least_annotators.png")
        plt.savefig(out_path)
        plt.close()

        print(f"Wrote {out_path}")

    print("Done.")


if __name__ == "__main__":
    main()
