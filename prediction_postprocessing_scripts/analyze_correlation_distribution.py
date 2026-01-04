#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import combinations

# -------------------------
# Event-level PRF with empty=perfect agreement
# -------------------------
def event_level_prf(gt, pred, window):
    if len(gt) == 0 and len(pred) == 0:
        return 1.0, 1.0, 1.0  # precision, recall, f1
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
    return prec, rec, f1

# -------------------------
# Clean method name
# -------------------------
def clean_method(folder_name):
    m = folder_name.replace("best_", "")
    if m.endswith("_advanced"):
        m = m.replace("_advanced", "")
    if m.startswith("rep_"):
        m = m.replace("rep_", "")
    return m.capitalize()

# -------------------------
# Load first JSON from folder
# -------------------------
def load_cps(folder):
    files = list(folder.glob("*.json"))
    if not files:
        return None
    try:
        with open(files[0]) as f:
            data = json.load(f)
        arr = data.get("result", {}).get("cplocations", [])
        arr = [int(x) for x in arr]
        return sorted(set(arr))
    except Exception:
        return None

# -------------------------
# Plot heatmap
# -------------------------
def plot_heatmap(matrix, methods, output_file, vmin=0, vmax=1):
    plt.figure(figsize=(max(6, len(methods)*0.8), max(5, len(methods)*0.6)))
    sns.heatmap(matrix, annot=True, fmt=".2f",
                xticklabels=methods, yticklabels=methods,
                annot_kws={"color": "white", "size": 8},
                vmin=vmin, vmax=vmax, cmap="viridis")
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()

# -------------------------
# Plot distribution histograms
# -------------------------
def plot_distributions(dist_dict, methods, output_subfolder):
    Path(output_subfolder).mkdir(parents=True, exist_ok=True)
    for m1, m2 in combinations(methods, 2):
        values = dist_dict[m1][m2]
        if not values:
            continue
        plt.figure(figsize=(6,4))
        plt.hist(values, bins=20, color='skyblue', edgecolor='black')
        plt.title(f"{m1} vs {m2}")
        plt.xlabel("Value")
        plt.ylabel("Frequency")
        plt.xlim(0,1)
        plt.tight_layout()
        plt.savefig(Path(output_subfolder)/f"{m1}_{m2}.png", dpi=300)
        plt.close()

# -------------------------
# MAIN
# -------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-folder", required=True)
    parser.add_argument("--window", type=int, default=5)
    parser.add_argument("--output-folder", required=True)
    args = parser.parse_args()

    root = Path(args.input_folder)
    out_root = Path(args.output_folder)
    out_root.mkdir(parents=True, exist_ok=True)
    window = args.window

    # discover method names
    methods = set()
    for ts_folder in root.iterdir():
        if not ts_folder.is_dir():
            continue
        for m in ts_folder.iterdir():
            if m.is_dir() and m.name.startswith("best_"):
                methods.add(clean_method(m.name))
    methods = sorted(methods)
    M = len(methods)
    print("Methods discovered:", methods)

    # initialize matrices and distributions
    prec_mat = np.zeros((M, M))
    rec_mat = np.zeros((M, M))
    f1_mat = np.zeros((M, M))
    counts = np.zeros((M, M), dtype=int)

    prec_dist = {m1:{m2:[] for m2 in methods} for m1 in methods}
    rec_dist  = {m1:{m2:[] for m2 in methods} for m1 in methods}
    f1_dist   = {m1:{m2:[] for m2 in methods} for m1 in methods}

    # process each timeseries
    for ts_folder in root.iterdir():
        if not ts_folder.is_dir():
            continue
        cps = {}
        for sub in ts_folder.iterdir():
            if not sub.is_dir() or not sub.name.startswith("best_"):
                continue
            method = clean_method(sub.name)
            arr = load_cps(sub)
            if arr is None:
                continue
            cps[method] = arr

        # compute pairwise PRF
        for i, m1 in enumerate(methods):
            for j, m2 in enumerate(methods):
                if m1 not in cps or m2 not in cps:
                    continue
                p, r, f = event_level_prf(cps[m1], cps[m2], window)
                prec_mat[i,j] += p
                rec_mat[i,j] += r
                f1_mat[i,j] += f
                counts[i,j] += 1
                # store for distributions (only unique pairs later)
                prec_dist[m1][m2].append(p)
                rec_dist[m1][m2].append(r)
                f1_dist[m1][m2].append(f)

    # average matrices
    avg_prec = np.divide(prec_mat, counts, out=np.zeros_like(prec_mat), where=counts>0)
    avg_rec  = np.divide(rec_mat, counts, out=np.zeros_like(rec_mat), where=counts>0)
    avg_f1   = np.divide(f1_mat, counts, out=np.zeros_like(f1_mat), where=counts>0)

    # heatmaps
    plot_heatmap(avg_prec, methods, out_root/"precision_heatmap.png")
    plot_heatmap(avg_rec,  methods, out_root/"recall_heatmap.png")
    plot_heatmap(avg_f1,   methods, out_root/"f1_heatmap.png")

    # distribution plots (only unique unordered pairs, exclude diagonals)
    plot_distributions(prec_dist, methods, out_root/"precision_dist")
    plot_distributions(rec_dist, methods, out_root/"recall_dist")
    plot_distributions(f1_dist, methods, out_root/"f1_dist")

if __name__ == "__main__":
    main()
