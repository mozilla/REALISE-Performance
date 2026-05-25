import argparse
import re
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def parse_latex_table(filepath):
    """Extract method -> (Best F1, Best Precision@F1max, Best Recall@F1max)."""
    with open(filepath, "r") as f:
        content = f.read()

    # Columns in order:
    # method | Def F1 | Def Prec | Def Rec | Best F1 | Best Prec | Best Rec | Best Prec(F1max) | Best Rec(F1max) | Ora F1 | Ora Prec | Ora Rec
    row_pattern = re.compile(
        r"^\s*([a-zA-Z0-9_]+)\s*&"  # method name
        r"\s*([\d.]+)\s*&"           # Default F1
        r"\s*([\d.]+)\s*&"           # Default Precision
        r"\s*([\d.]+)\s*&"           # Default Recall
        r"\s*([\d.]+)\s*&"           # Best F1          <- group 5
        r"\s*([\d.]+)\s*&"           # Best Precision
        r"\s*([\d.]+)\s*&"           # Best Recall
        r"\s*([\d.]+)\s*&"           # Best Precision (F1 max)  <- group 8
        r"\s*([\d.]+)\s*&"           # Best Recall (F1 max)     <- group 9
        r".*?\\\\",
        re.MULTILINE,
    )

    results = {}
    for m in row_pattern.finditer(content):
        method = re.sub(r"_advanced$", "", m.group(1).strip(), flags=re.IGNORECASE).upper()
        results[method] = {
            "F1":        float(m.group(5)),
            "Precision": float(m.group(8)),
            "Recall":    float(m.group(9)),
        }

    return results


METRICS = ["F1", "Precision", "Recall"]
METRIC_COLORS = {"F1": "#2196F3", "Precision": "#4CAF50", "Recall": "#FF5722"}


def main():
    parser = argparse.ArgumentParser(
        description="Plot Best F1 / Precision(F1max) / Recall(F1max) evolution across numbered txt files."
    )
    parser.add_argument("--input-folder", required=True, help="Folder containing 1.txt ... N.txt")
    parser.add_argument("--output-png",   required=True, help="Path for the output PNG file")
    args = parser.parse_args()

    folder = Path(args.input_folder)
    txt_files = sorted(
        [f for f in folder.glob("*.txt") if f.stem.isdigit()],
        key=lambda f: int(f.stem),
    )

    if not txt_files:
        raise FileNotFoundError(f"No numbered .txt files found in {folder}")

    file_indices = [int(f.stem) for f in txt_files]

    # all_data[method][metric] = [val_file1, val_file2, ...]
    all_data = {}
    for fpath in txt_files:
        parsed = parse_latex_table(fpath)
        for method, metrics in parsed.items():
            if method not in all_data:
                all_data[method] = {m: [] for m in METRICS}
            for metric in METRICS:
                all_data[method][metric].append(metrics[metric])

    methods = sorted(all_data.keys())
    n_methods = len(methods)

    if n_methods == 0:
        raise ValueError("No methods parsed. Check file format.")

    # Grid: each method = 1 row, each metric = 1 column
    n_rows = n_methods
    n_cols = len(METRICS)

    fig, axes = plt.subplots(
        n_rows, n_cols,
        figsize=(n_cols * 3.6, n_rows * 2.8),
        sharex=True,
    )

    # Normalise axes to always be 2-D
    axes = np.array(axes)
    if axes.ndim == 1 and n_rows == 1:
        axes = axes[np.newaxis, :]
    elif axes.ndim == 1 and n_cols == 1:
        axes = axes[:, np.newaxis]

    for row, method in enumerate(methods):
        for col, metric in enumerate(METRICS):
            ax = axes[row][col]
            vals = all_data[method][metric]
            color = METRIC_COLORS[metric]

            ax.plot(file_indices, vals, marker="o", linewidth=2,
                    markersize=5, color=color)
            ax.fill_between(file_indices, vals, alpha=0.12, color=color)

            ax.set_ylim(0, 1.05)
            ax.set_xticks(file_indices)
            ax.grid(True, linestyle="--", alpha=0.45)
            ax.tick_params(labelsize=8)

            # Left-edge: method label
            if col == 0:
                ax.set_ylabel(method, fontsize=10, fontweight="bold", labelpad=8)

            # Top-edge: metric label
            if row == 0:
                ax.set_title(metric, fontsize=11, fontweight="bold", color=color)

            # Bottom-edge: x label only on last row
            if row == n_rows - 1:
                ax.set_xlabel("File index", fontsize=8)

    fig.suptitle(
        "Best Configuration — F1 / Precision(F1max) / Recall(F1max) per Method",
        fontsize=13, fontweight="bold", y=1.01,
    )
    plt.tight_layout()
    plt.savefig(args.output_png, dpi=150, bbox_inches="tight")
    print(f"Saved plot to {args.output_png}")


if __name__ == "__main__":
    main()