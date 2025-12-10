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
    """
    raw could be like:
        'ks_advanced'
        'levene_advanced'
        'rep_mwu'
        'rep_ks'
    Goal: extract the true name and capitalize first letter.
    """
    # strip known prefixes
    if raw.endswith("_rep"):
        raw = raw.replace("_rep", "")
    if raw.endswith("_advanced"):
        raw = raw.replace("_advanced", "")

    return raw.capitalize()


def expand_with_tolerance(indices, window):
    expanded = set()
    for idx in indices:
        for x in range(idx - window, idx + window + 1):
            expanded.add(x)
    return expanded


def jaccard(a, b):
    if not a and not b:
        return 1.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union > 0 else 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-folder", required=True)
    parser.add_argument("--output-heatmap", required=True)
    parser.add_argument("--window", type=int, required=False, default=5)
    args = parser.parse_args()

    root = Path(args.input_folder)
    ts_folders = [p for p in root.iterdir() if p.is_dir()]

    raw_methods = set()

    # Detect all "best_*" folders and extract raw method names
    for ts in ts_folders:
        for sub in ts.iterdir():
            if sub.is_dir() and sub.name.startswith("best_"):
                raw_methods.add(sub.name.replace("best_", ""))

    # Clean method names
    method_map = {raw: clean_method_name(raw) for raw in raw_methods}
    methods = [method_map[r] for r in sorted(raw_methods)]

    # For pairing matrix, we need consistent order
    similarities = {m1: {m2: [] for m2 in methods} for m1 in methods}

    for ts in ts_folders:
        method_cp = {}

        # Populate CP sets for this TS
        for sub in ts.iterdir():
            if sub.is_dir() and sub.name.startswith("best_"):
                raw = sub.name.replace("best_", "")
                pretty = method_map[raw]

                indices = load_cplocations(sub)
                method_cp[pretty] = expand_with_tolerance(indices, args.window)

        # Pairwise Jaccard per TS
        for i, m1 in enumerate(methods):
            for m2 in methods[i:]:
                a = method_cp.get(m1, set())
                b = method_cp.get(m2, set())
                sim = jaccard(a, b)

                similarities[m1][m2].append(sim)
                if m1 != m2:
                    similarities[m2][m1].append(sim)

    # Average matrix
    mat = np.zeros((len(methods), len(methods)))
    for i, m1 in enumerate(methods):
        for j, m2 in enumerate(methods):
            vals = similarities[m1][m2]
            mat[i, j] = np.mean(vals) if vals else 0.0

    # Plot heatmap with values
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(mat, interpolation="nearest")

    ax.set_xticks(range(len(methods)))
    ax.set_yticks(range(len(methods)))
    ax.set_xticklabels(methods, rotation=45, ha="right")
    ax.set_yticklabels(methods)
    plt.colorbar(im, ax=ax)

    # Add similarity numbers
    for i in range(len(methods)):
        for j in range(len(methods)):
            ax.text(
                j, i,
                f"{mat[i,j]:.2f}",
                ha="center", va="center",
                fontsize=8, color="white"
            )

    plt.tight_layout()
    plt.savefig(args.output_heatmap, dpi=300)


if __name__ == "__main__":
    main()
