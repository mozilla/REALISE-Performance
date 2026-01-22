#!/usr/bin/env python3

import os
import json
import argparse
from collections import defaultdict
import math


def parse_args():
    parser = argparse.ArgumentParser(
        description="Average F1 / Precision / Recall per CPD method (LaTeX output)"
    )
    parser.add_argument("--input-folder", required=True)
    return parser.parse_args()


def load_metrics(input_folder: str):
    """
    Aggregate F1, precision, recall across all datasets and
    hyperparameter configurations for each method.
    """
    agg = defaultdict(lambda: {"f1": [], "precision": [], "recall": []})

    for fname in os.listdir(input_folder):
        if not fname.endswith(".json"):
            continue

        with open(os.path.join(input_folder, fname), "r") as f:
            data = json.load(f)

        for method_name, runs in data.get("results", {}).items():
            if not method_name.startswith("best_"):
                continue

            for run in runs:
                if run.get("status") != "SUCCESS":
                    continue

                scores = run.get("scores", {})
                if not scores:
                    continue

                # scores are guaranteed to exist as shown
                agg[method_name]["f1"].append(scores["f1"])
                agg[method_name]["precision"].append(scores["precision"])
                agg[method_name]["recall"].append(scores["recall"])

    return agg


def mean(xs):
    return sum(xs) / len(xs) if xs else math.nan


def print_latex_table(agg):
    methods = sorted(agg.keys())

    print(r"\begin{tabular}{lcccc}")
    print(r"\toprule")
    print(r"Method & Avg. F1 & Avg. Precision & Avg. Recall & \#Experiments \\")
    print(r"\midrule")

    for method in methods:
        f1 = mean(agg[method]["f1"])
        prec = mean(agg[method]["precision"])
        rec = mean(agg[method]["recall"])
        n = len(agg[method]["f1"])

        print(
            f"{method} & "
            f"{f1:.3f} & "
            f"{prec:.3f} & "
            f"{rec:.3f} & "
            f"{n} \\\\"
        )

    print(r"\bottomrule")
    print(r"\end{tabular}")


def main():
    args = parse_args()

    agg = load_metrics(args.input_folder)
    print_latex_table(agg)


if __name__ == "__main__":
    main()
