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


def tolerance_jaccard(list_a, list_b, window):
    a = sorted(list_a)
    b = sorted(list_b)

    i = j = 0
    matched = 0
    used_b = set()

    while i < len(a) and j < len(b):
        if abs(a[i] - b[j]) <= window:
            if j not in used_b:
                matched += 1
                used_b.add(j)
                i += 1
                j += 1
            else:
                j += 1
        elif a[i] < b[j]:
            i += 1
        else:
            j += 1

    union = len(a) + len(b) - matched
    return matched / union if union > 0 else 1.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-folder", required=True)
    parser.add_argument("--output-heatmap", required=True)
    parser.add_argument("--window", type=int, required=True)
    args = parser.parse_args()

    root = Path(args.input_folder)
    ts_folders = [p for p in root.iterdir() if p.is_dir()]

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

        for i, m1 in enumerate(methods):
            for m2 in methods[i:]:
                a = method_cp.get(m1, [])
                b = method_cp.get(m2, [])

                sim = tolerance_jaccard(a, b, args.window)
                similarities[m1][m2].append(sim)
                if m1 != m2:
                    similarities[m2][m1].append(sim)

    mat = np.zeros((len(methods), len(methods)))
    for i, m1 in enumerate(methods):
        for j, m2 in enumerate(methods):
            vals = similarities[m1][m2]
            mat[i, j] = np.mean(vals) if vals else 0.0

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(mat, interpolation="nearest")

    ax.set_xticks(range(len(methods)))
    ax.set_yticks(range(len(methods)))
    ax.set_xticklabels(methods, rotation=45, ha="right")
    ax.set_yticklabels(methods)
    plt.colorbar(im, ax=ax)

    for i in range(len(methods)):
        for j in range(len(methods)):
            ax.text(j, i, f"{mat[i,j]:.2f}", ha="center", va="center",
                    fontsize=8, color="white")

    plt.tight_layout()
    plt.savefig(args.output_heatmap, dpi=300)


if __name__ == "__main__":
    main()
