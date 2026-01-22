#!/usr/bin/env python3

import os
import json
import argparse
import itertools
from collections import defaultdict
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# ----------------------------
# argparse
# ----------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Pairwise average MCC between CPD methods"
    )
    parser.add_argument("--input-folder", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--window", type=int, default=5)
    return parser.parse_args()


# ----------------------------
# helpers
# ----------------------------
def args_to_key(args: Dict) -> Tuple:
    """
    Convert hyperparameter dictionary to a hashable key,
    removing method-specific entries.
    """
    args = dict(args)
    args.pop("method", None)
    return tuple(sorted(args.items()))


def cps_to_binary(cps, length: int, window: int) -> np.ndarray:
    y = np.zeros(length, dtype=int)
    for cp in cps:
        start = max(0, cp - window)
        end = min(length, cp + window + 1)
        y[start:end] = 1
    return y


def mcc_safe(x: np.ndarray, y: np.ndarray) -> float:
    """
    Matthews Correlation Coefficient for two binary vectors.
    Returns NaN if undefined.
    """
    tp = np.sum((x == 1) & (y == 1))
    tn = np.sum((x == 0) & (y == 0))
    fp = np.sum((x == 0) & (y == 1))
    fn = np.sum((x == 1) & (y == 0))

    denom = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
    if denom == 0:
        return np.nan

    return (tp * tn - fp * fn) / np.sqrt(denom)

def clean_method_name(raw):
    name = raw
    name = name.removeprefix("best_")
    name = name.removesuffix("_advanced")
    name = name.removesuffix("_rep")
    name = name.replace("_", " ")
    return name.title()

# ----------------------------
# loading
# ----------------------------
def load_experiments(input_folder: str, window: int):
    """
    Load experiments from per-timeseries JSON files.

    Returns:
      (method, dataset, hyperparam_key) -> binary prediction vector
    """
    experiments = {}

    for fname in os.listdir(input_folder):
        if not fname.endswith(".json"):
            continue

        with open(os.path.join(input_folder, fname), "r") as f:
            data = json.load(f)

        dataset = data["dataset"]
        nobs = data["dataset_nobs"]

        for method_name, runs in data.get("results", {}).items():
            if not method_name.startswith("best_"):
                continue

            for run in runs:
                if run.get("status") != "SUCCESS":
                    continue

                hkey = args_to_key(run.get("args", {}))
                cps = run.get("cplocations", [])

                y_pred = cps_to_binary(cps, nobs, window)
                experiments[(method_name, dataset, hkey)] = y_pred

    return experiments


# ----------------------------
# MCC aggregation
# ----------------------------
def compute_pairwise_average_mcc(experiments):
    """
    Compute average MCC for each method pair,
    matched by (dataset, hyperparameters).
    """
    methods = sorted({k[0] for k in experiments})
    grouped = defaultdict(dict)

    for (method, dataset, hkey), vec in experiments.items():
        grouped[(dataset, hkey)][method] = vec

    pair_values = defaultdict(list)

    for method_map in grouped.values():
        if len(method_map) < 2:
            continue

        for m1, m2 in itertools.combinations(method_map.keys(), 2):
            mcc = mcc_safe(method_map[m1], method_map[m2])
            if not np.isnan(mcc):
                pair_values[(m1, m2)].append(mcc)
                pair_values[(m2, m1)].append(mcc)

        for m in method_map.keys():
            pair_values[(m, m)].append(1.0)

    mat = pd.DataFrame(index=methods, columns=methods, dtype=float)

    for m1 in methods:
        for m2 in methods:
            vals = pair_values.get((m1, m2), [])
            mat.loc[m1, m2] = np.mean(vals) if vals else np.nan

    return mat


# ----------------------------
# plotting
# ----------------------------
def plot_heatmap(matrix: pd.DataFrame, output_file: str):
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        matrix,
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        square=True,
        annot=True,
        fmt=".2f",
        cbar_kws={"label": "Average MCC"},
    )
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()


# ----------------------------
# main
# ----------------------------
def main():
    args = parse_args()

    experiments = load_experiments(
        input_folder=args.input_folder,
        window=args.window,
    )

    mcc_matrix = compute_pairwise_average_mcc(experiments)
    pretty_names = {m: clean_method_name(m) for m in mcc_matrix.index}
    mcc_matrix = mcc_matrix.rename(index=pretty_names, columns=pretty_names)

    plot_heatmap(mcc_matrix, args.output_file)

if __name__ == "__main__":
    main()
