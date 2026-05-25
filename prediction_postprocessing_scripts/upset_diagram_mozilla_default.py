#!/usr/bin/env python3
"""
Generate an UpSet plot showing how often combinations of CPD methods agree.
Draws the plot manually to avoid the upsetplot NaN-color bug with newer
pandas/matplotlib versions.

Usage:
    python upset_diagram.py \
        --input-folder /path/to/input \
        --output-png   /path/to/output.png \
        --methods method1 method2 method3 method4 method5 \
        [--margin 5] [--variant default|best|both] [--show-zero-counts]
"""

import argparse
import itertools
import json
from pathlib import Path
from statistics import median
from collections import defaultdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec


# ---------------------------------------------------------------------------
# Data helpers (adapted from voter script)
# ---------------------------------------------------------------------------

def load_json(path):
    with open(path, "r") as f:
        data = json.load(f)
    return data["result"].get("cplocations", [])


def merge_close_points(points, margin):
    if not points:
        return []
    points = sorted(points)
    clusters = [[points[0]]]
    for p in points[1:]:
        if p - clusters[-1][0] <= margin:
            clusters[-1].append(p)
        else:
            clusters.append([p])
    return clusters


def consolidate(points, margin):
    if not points:
        return []
    return [int(round(median(c))) for c in merge_close_points(points, margin)]


def normalize_method(name):
    """Strip _advanced / _rep suffixes (case-insensitive) and uppercase."""
    import re
    return re.sub(r"_(advanced|rep)$", "", name, flags=re.IGNORECASE).upper()


# ---------------------------------------------------------------------------
# Agreement counting
# ---------------------------------------------------------------------------

def count_agreements(input_root, methods, variant, margin):
    """
    For every combination of >=2 methods, count changepoints where ALL methods
    in the combo agree (each has a point within `margin` of the anchor) AND
    ALL methods outside the combo disagree (have no point within `margin` of
    the anchor).  This gives true exclusive UpSet semantics: each changepoint
    contributes to exactly one combination bar.

    Anchors on the method with the fewest detections in each combo to avoid
    overcounting — agreement counts are bounded by the smallest method's
    detection count.

    Also computes a directional pairwise count:
        pairwise_counts[A][B] = number of A's detections that have a match in B

    Returns:
        combo_counts:             dict frozenset(methods) -> int  (all combos present, even zeros)
        method_detection_totals:  dict method -> int (raw detections per method)
        pairwise_counts:          dict method -> dict method -> int
    """
    combo_counts = defaultdict(int)
    method_detection_totals = defaultdict(int)
    # pairwise_counts[anchor][other] = agreements when anchoring on anchor
    pairwise_counts = defaultdict(lambda: defaultdict(int))

    for ts_folder in sorted(input_root.iterdir()):
        if not ts_folder.is_dir():
            continue

        variants_to_run = ["default", "best"] if variant == "both" else [variant]

        for var in variants_to_run:
            method_cps = {}
            for m in methods:
                effective_var = "default" if m == "mozilla_rep" else var
                subdir = ts_folder / f"{effective_var}_{m}"
                if not subdir.exists():
                    continue
                all_cps = []
                for f in sorted(subdir.glob("*.json")):
                    all_cps.extend(load_json(f))
                consolidated = consolidate(all_cps, margin)
                norm = normalize_method(m)
                method_cps[norm] = consolidated
                method_detection_totals[norm] += len(consolidated)

            available = list(method_cps.keys())
            if len(available) < 2:
                continue

            # Pairwise directional counts (both directions for every pair)
            for a, b in itertools.permutations(available, 2):
                for anchor in method_cps[a]:
                    if any(abs(anchor - p) <= margin for p in method_cps[b]):
                        pairwise_counts[a][b] += 1

            # Combo counts (anchor on smallest method)
            # A bar for combo X means: ALL methods in X agree AND ALL methods
            # outside X disagree (have no point within margin of the anchor).
            for size in range(2, len(available) + 1):
                for combo in itertools.combinations(available, size):
                    key = frozenset(combo)
                    outside = [m for m in available if m not in combo]
                    anchor_method = min(combo, key=lambda m: len(method_cps[m]))
                    anchors = method_cps[anchor_method]
                    agreed = sum(
                        1 for anchor in anchors
                        if all(
                            any(abs(anchor - p) <= margin for p in method_cps[m])
                            for m in combo if m != anchor_method
                        )
                        and all(
                            not any(abs(anchor - p) <= margin for p in method_cps[m])
                            for m in outside
                        )
                    )
                    combo_counts[key] += agreed

    return combo_counts, method_detection_totals, pairwise_counts


def all_combos_for_methods(methods):
    """Return all frozensets of size >=2 for the given method list."""
    result = []
    for size in range(2, len(methods) + 1):
        for combo in itertools.combinations(methods, size):
            result.append(frozenset(combo))
    return result


# ---------------------------------------------------------------------------
# Manual UpSet renderer
# ---------------------------------------------------------------------------

def build_upset(combo_counts, method_detection_totals, pairwise_counts, methods,
                output_png, show_zero_counts=False):

    if show_zero_counts:
        # Ensure every possible combo is represented, even if count is 0
        for key in all_combos_for_methods(methods):
            if key not in combo_counts:
                combo_counts[key] = 0
        combos = list(combo_counts.items())
    else:
        combos = [(combo, cnt) for combo, cnt in combo_counts.items() if cnt > 0]

    if not combos:
        print("No agreements found — nothing to plot.")
        return

    # Sort by count descending; zero-count combos cluster at the right
    combos.sort(key=lambda x: -x[1])

    n_methods = len(methods)
    method_order = list(methods)
    n_combos = len(combos)

    # Left-side bars use raw detection totals
    method_totals = method_detection_totals

    # --- layout ---------------------------------------------------------
    bar_h    = 3.5
    matrix_h = n_methods * 0.55 + 0.4
    totals_w = 1.8
    main_w   = max(8, n_combos * 0.52 + 1.5)

    fig_w = totals_w + main_w
    fig_h = bar_h + matrix_h + 0.6

    fig = plt.figure(figsize=(fig_w, fig_h))

    gs = GridSpec(
        2, 2,
        figure=fig,
        width_ratios=[totals_w, main_w],
        height_ratios=[bar_h, matrix_h],
        hspace=0.05,
        wspace=0.03,
    )

    ax_totals = fig.add_subplot(gs[1, 0])
    ax_bar    = fig.add_subplot(gs[0, 1])
    ax_matrix = fig.add_subplot(gs[1, 1])
    ax_blank  = fig.add_subplot(gs[0, 0])
    ax_blank.axis("off")

    ACTIVE   = "#2C3E7A"
    INACTIVE = "#D8DCE8"
    BAR_CLR  = "#2C3E7A"
    BAR_ZERO = "#B0B8D0"   # muted colour for zero-count bars
    TOT_CLR  = "#4A6FA5"

    xs = np.arange(n_combos)

    # --- top bar chart --------------------------------------------------
    counts = [cnt for _, cnt in combos]
    max_count = max(counts) if max(counts) > 0 else 1
    bar_colors = [BAR_CLR if cnt > 0 else BAR_ZERO for cnt in counts]

    bars = ax_bar.bar(xs, counts, color=bar_colors, width=0.6, zorder=3)
    for bar, cnt in zip(bars, counts):
        ax_bar.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max_count * 0.01,
            str(cnt), ha="center", va="bottom", fontsize=7.5,
            color="#888" if cnt == 0 else "#222"
        )
    ax_bar.set_xlim(-0.5, n_combos - 0.5)
    ax_bar.set_ylim(0, max_count * 1.18)
    ax_bar.set_xticks([])
    ax_bar.set_ylabel("Agreed changepoints", fontsize=9)
    ax_bar.yaxis.set_label_position("left")
    ax_bar.spines[["top", "right", "bottom"]].set_visible(False)
    ax_bar.yaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)
    ax_bar.set_axisbelow(True)

    # --- dot matrix -----------------------------------------------------
    DOT_R = 0.28
    ax_matrix.set_xlim(-0.5, n_combos - 0.5)
    ax_matrix.set_ylim(-0.5, n_methods - 0.5)

    for mi, method in enumerate(method_order):
        y = n_methods - 1 - mi

        ax_matrix.axhline(y, color="#E0E3EE", linewidth=0.8, zorder=1)

        for ci, (combo, cnt) in enumerate(combos):
            active = method in combo
            if active:
                color = ACTIVE if cnt > 0 else BAR_ZERO
            else:
                color = INACTIVE
            circle = plt.Circle((ci, y), DOT_R, color=color, zorder=3)
            ax_matrix.add_patch(circle)

    for ci, (combo, cnt) in enumerate(combos):
        active_ys = [
            n_methods - 1 - mi
            for mi, m in enumerate(method_order) if m in combo
        ]
        if len(active_ys) >= 2:
            line_color = ACTIVE if cnt > 0 else BAR_ZERO
            ax_matrix.plot(
                [ci, ci], [min(active_ys), max(active_ys)],
                color=line_color, linewidth=2.0, zorder=2
            )

    ax_matrix.set_xticks([])
    ax_matrix.set_yticks(range(n_methods))
    ax_matrix.set_yticklabels(
        [method_order[n_methods - 1 - i] for i in range(n_methods)],
        fontsize=9
    )
    ax_matrix.yaxis.set_tick_params(length=0)
    ax_matrix.spines[:].set_visible(False)
    ax_matrix.set_aspect("equal", adjustable="box")

    # --- method totals (horizontal bars, left panel) --------------------
    ys_tot = np.arange(n_methods)
    tot_vals = [method_totals.get(method_order[n_methods - 1 - i], 0)
                for i in range(n_methods)]
    max_tot = max(tot_vals) if max(tot_vals) > 0 else 1
    ax_totals.barh(ys_tot, tot_vals, color=TOT_CLR, height=0.55, zorder=3)
    for y_t, val in zip(ys_tot, tot_vals):
        ax_totals.text(val + max_tot * 0.01, y_t, str(val),
                       va="center", ha="left", fontsize=7.5, color="#222")
    ax_totals.set_ylim(-0.5, n_methods - 0.5)
    ax_totals.set_xlim(max_tot * 1.25, 0)
    ax_totals.set_yticks([])
    ax_totals.set_xlabel("Total detections", fontsize=9)
    ax_totals.spines[["top", "left", "bottom"]].set_visible(False)
    ax_totals.xaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)
    ax_totals.set_axisbelow(True)
    ax_totals.invert_xaxis()

    # --- title ----------------------------------------------------------
    fig.suptitle(
        "Method Agreement UpSet Plot  "
        "(bar = # changepoints agreed exclusively by the highlighted methods)",
        fontsize=11, fontweight="bold", y=0.995,
    )

    plt.savefig(output_png, dpi=150, bbox_inches="tight")
    print(f"Saved UpSet plot → {output_png}")

    # --- Print combination agreement summary ----------------------------
    print(f"\n{'Combination':<55}  {'Agreements':>10}")
    print("-" * 68)
    for combo, cnt in sorted(combo_counts.items(), key=lambda x: (-len(x[0]), -x[1])):
        label = " & ".join(sorted(combo))
        print(f"  {label:<53}  {cnt:>10}")

    # --- Print per-method detection totals ------------------------------
    print(f"\n{'Method':<30}  {'Detections':>10}")
    print("-" * 42)
    for method in sorted(methods):
        detections = method_detection_totals.get(method, 0)
        print(f"  {method:<28}  {detections:>10}")

    # --- Print pairwise agreement rate matrix ---------------------------
    # Cell [row=A, col=B] = "X / Y (ZZ%)" where:
    #   X = A detections that have a match in B
    #   Y = total A detections
    #   ZZ% = X/Y
    # A high value means "most of A's detections are corroborated by B"
    # Asymmetry reveals which method is the permissive/dense one.
    sorted_methods = sorted(methods)
    col_w = 18  # width per cell

    print("\nPairwise agreement rate matrix")
    print("  Row = anchor method (% of its detections matched by column method)")
    print()

    # Header
    header = f"  {'':20s}" + "".join(f"{m:>{col_w}}" for m in sorted_methods)
    print(header)
    print("  " + "-" * (20 + col_w * len(sorted_methods)))

    for a in sorted_methods:
        a_total = method_detection_totals.get(a, 0)
        row = f"  {a:<20s}"
        for b in sorted_methods:
            if a == b:
                row += f"{'—':>{col_w}}"
            else:
                agreed = pairwise_counts[a][b]
                if a_total > 0:
                    pct = 100.0 * agreed / a_total
                    cell = f"{agreed}/{a_total} ({pct:.0f}%)"
                else:
                    cell = "n/a"
                row += f"{cell:>{col_w}}"
        print(row)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="UpSet plot of CPD method agreement across changepoint clusters."
    )
    parser.add_argument("--input-folder", "-i", required=True)
    parser.add_argument("--output-png",   "-o", required=True)
    parser.add_argument("--methods", nargs="+", required=True)
    parser.add_argument("--margin",  "-m", type=int, default=5)
    parser.add_argument("--variant", choices=["default", "best", "both"], default="both")
    parser.add_argument(
        "--show-zero-counts",
        action="store_true",
        default=False,
        help="Include combinations with zero agreements in the plot (shown in muted colour).",
    )
    args = parser.parse_args()

    input_root = Path(args.input_folder)
    print(f"Scanning {input_root}  methods={args.methods}  "
          f"margin={args.margin}  variant={args.variant}  "
          f"show_zero_counts={args.show_zero_counts} …")

    combo_counts, method_detection_totals, pairwise_counts = count_agreements(
        input_root, args.methods, args.variant, args.margin
    )
    normalized_methods = [normalize_method(m) for m in args.methods]
    build_upset(
        combo_counts, method_detection_totals, pairwise_counts,
        normalized_methods, args.output_png,
        show_zero_counts=args.show_zero_counts,
    )


if __name__ == "__main__":
    main()