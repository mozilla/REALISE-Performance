#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt


def load_cplocations(folder):
    for file in folder.iterdir():
        if file.suffix.lower() == ".json":
            with open(file, "r") as f:
                data = json.load(f)
            return data.get("result", {}).get("cplocations", [])
    return []


def clean_method_name(raw):
    if raw.endswith("_rep"):
        raw = raw.replace("_rep", "")
    if raw.endswith("_advanced"):
        raw = raw.replace("_advanced", "")
    return raw.capitalize()


# ----------------------------
# MCC logic (same logic as in
# voter_system_all_cpd_results_mcc_based_correlation.py)
# ----------------------------
def cps_to_binary(cps, length, window):
    y = np.zeros(length, dtype=int)
    for cp in cps:
        start = max(0, cp - window)
        end = min(length, cp + window + 1)
        y[start:end] = 1
    return y


def mcc_safe(x, y):
    tp = np.sum((x == 1) & (y == 1))
    tn = np.sum((x == 0) & (y == 0))
    fp = np.sum((x == 0) & (y == 1))
    fn = np.sum((x == 1) & (y == 0))

    denom = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
    if denom == 0:
        return 0.0

    return (tp * tn - fp * fn) / np.sqrt(denom)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-folder", required=True)
    parser.add_argument("--output-heatmap", required=True)
    parser.add_argument("--window", type=int, required=True)
    args = parser.parse_args()

    root = Path(args.input_folder)
    ts_folders = [p for p in root.iterdir() if p.is_dir()]

    # Discover methods from best_* folders
    raw_methods = set()
    for ts in ts_folders:
        for sub in ts.iterdir():
            if sub.is_dir() and sub.name.startswith("best_"):
                raw_methods.add(sub.name.replace("best_", ""))

    method_map = {raw: clean_method_name(raw) for raw in raw_methods}
    methods = [method_map[r] for r in sorted(raw_methods)]

    similarities = {m1: {m2: [] for m2 in methods} for m1 in methods}

    for ts in ts_folders:
        method_cp = {}

        for sub in ts.iterdir():
            if sub.is_dir() and sub.name.startswith("best_"):
                raw = sub.name.replace("best_", "")
                pretty = method_map[raw]
                method_cp[pretty] = load_cplocations(sub)

        # infer binary vector length for this TS
        max_cp = 0
        for cps in method_cp.values():
            if cps:
                max_cp = max(max_cp, max(cps))
        length = max_cp + args.window + 2

        binaries = {
            m: cps_to_binary(method_cp.get(m, []), length, args.window)
            for m in methods
        }

        for i, m1 in enumerate(methods):
            for m2 in methods[i:]:
                if m1 == m2:
                    sim = 1.0
                else:
                    sim = mcc_safe(binaries[m1], binaries[m2])

                similarities[m1][m2].append(sim)
                if m1 != m2:
                    similarities[m2][m1].append(sim)
                    
    mat = np.zeros((len(methods), len(methods)))
    for i, m1 in enumerate(methods):
        for j, m2 in enumerate(methods):
            vals = similarities[m1][m2]
            mat[i, j] = np.mean(vals) if vals else 0.0

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(mat, interpolation="nearest", vmin=-1, vmax=1, cmap="coolwarm")

    ax.set_xticks(range(len(methods)))
    ax.set_yticks(range(len(methods)))
    ax.set_xticklabels(methods, rotation=45, ha="right")
    ax.set_yticklabels(methods)
    plt.colorbar(im, ax=ax, label="Average MCC")

    for i in range(len(methods)):
        for j in range(len(methods)):
            ax.text(j, i, f"{mat[i,j]:.2f}", ha="center", va="center",
                    fontsize=8, color="white")

    plt.tight_layout()
    plt.savefig(args.output_heatmap, dpi=300)


if __name__ == "__main__":
    main()
