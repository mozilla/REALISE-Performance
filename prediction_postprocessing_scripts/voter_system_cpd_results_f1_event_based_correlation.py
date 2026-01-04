#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt


'''
def event_level_prf(gt_cps, pred_cps, window):
    gt = sorted(sorted(set(int(x) for x in gt_cps)))
    pred = sorted(sorted(set(int(x) for x in pred_cps)))

    matched_gt = set()
    tp = 0
    for p in pred:
        for g in gt:
            if g in matched_gt:
                continue
            if abs(p - g) <= window:
                matched_gt.add(g)
                tp += 1
                break

    fp = len(pred) - tp
    fn = len(gt) - tp

    prec = tp / (tp + fp) if tp + fp > 0 else 0.0
    rec  = tp / (tp + fn) if tp + fn > 0 else 0.0
    f1   = (2*prec*rec)/(prec+rec) if prec+rec > 0 else 0.0

    return prec, rec, f1
'''

def event_level_prf(gt, pred, window):
    # perfect agreement case (both empty)
    if len(gt) == 0 and len(pred) == 0:
        return 1.0

    gt = sorted(set(gt))
    pred = sorted(set(pred))

    matched_gt = set()
    tp = 0

    for p in pred:
        for g in gt:
            if g in matched_gt:
                continue
            if abs(p - g) <= window:
                matched_gt.add(g)
                tp += 1
                break

    fp = len(pred) - tp
    fn = len(gt) - tp

    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec  = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1   = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0

    return f1


def clean_method(method_folder):
    m = method_folder.replace("best_", "")
    if m.endswith("_advanced"):
        m = m.replace("_advanced", "")
    if m.startswith("rep_"):
        m = m.replace("rep_", "")
    return m.capitalize()

def load_first_json(folder):
    files = list(folder.glob("*.json"))
    if not files:
        return None
    try:
        with open(files[0]) as f:
            data = json.load(f)
        return data.get("result", {}).get("cplocations", [])
    except Exception:
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-folder", required=True)
    parser.add_argument("--metadata-json", required=False)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--window", type=int, default=5)
    args = parser.parse_args()

    input_folder = Path(args.input_folder)
    window = args.window

    # discover methods
    methods = set()
    for ts_folder in input_folder.iterdir():
        if not ts_folder.is_dir():
            continue
        for m in ts_folder.iterdir():
            if m.is_dir() and m.name.startswith("best_"):
                methods.add(clean_method(m.name))
    methods = sorted(methods)
    M = len(methods)

    mat = np.zeros((M, M))
    counts = np.zeros((M, M), dtype=int)

    # per-TS processing
    for ts_folder in input_folder.iterdir():
        if not ts_folder.is_dir():
            continue

        # load all available CPs for this TS
        cps = {}
        for m in ts_folder.iterdir():
            if not m.is_dir() or not m.name.startswith("best_"):
                continue
            clean = clean_method(m.name)
            arr = load_first_json(m)
            if arr is None:
                continue
            # coerce to unique ints
            try:
                arr = sorted(set(int(x) for x in arr))
            except Exception:
                continue
            cps[clean] = arr

        # compute F1 for every pair where both exist
        for i, m1 in enumerate(methods):
            for j, m2 in enumerate(methods):
                if m1 not in cps or m2 not in cps:
                    continue
                f1 = event_level_prf(gt=cps[m1], pred=cps[m2], window=window)
                mat[i, j] += f1
                counts[i, j] += 1

    # safe averaging: where count==0 set value to np.nan (or 0)
    with np.errstate(invalid='ignore', divide='ignore'):
        avg = np.divide(mat, counts, where=counts>0)
    avg[counts == 0] = np.nan  # optional: show missing as NaN

    # plot heatmap (NaNs will be blank)
    plt.figure(figsize=(max(6, M*0.8), max(5, M*0.6)))
    ax = sns.heatmap(avg, annot=True, fmt=".2f",
                     xticklabels=methods, yticklabels=methods,
                     annot_kws={"color": "white", "size": 8},
                     vmin=0.0, vmax=1.0, cmap="viridis")
    plt.tight_layout()
    plt.savefig(args.output_file, dpi=300)
    plt.close()

if __name__ == "__main__":
    main()
