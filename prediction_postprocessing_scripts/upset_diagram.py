#!/usr/bin/env python3
"""
Generate an UpSet plot showing how often combinations of CPD methods agree.
Draws the plot manually to avoid the upsetplot NaN-color bug with newer
pandas/matplotlib versions.

A bar for combo X means: ALL methods in X agree AND ALL methods outside X
disagree — true exclusive UpSet semantics. Each changepoint contributes to
exactly one combination bar.

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


# ---------------------------------------------------------------------------
# Display name helper
# ---------------------------------------------------------------------------

def display_name(method):
    """Return a display-friendly name: strip _advanced/_rep suffix, then uppercase."""
    name = method
    for suffix in ("_advanced", "_rep"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    return name.upper()


# ---------------------------------------------------------------------------
# Combo helpers
# ---------------------------------------------------------------------------

def all_combos_for_methods(methods):
    """Return all frozensets of size >=2 for the given method list."""
    result = []
    for size in range(2, len(methods) + 1):
        for combo in itertools.combinations(methods, size):
            result.append(frozenset(combo))
    return result


# ---------------------------------------------------------------------------
# Agreement counting
# ---------------------------------------------------------------------------

def count_agreements(input_root, methods, variant, margin):
    """
    For every combination of >=2 methods, count changepoints where ALL methods
    in the combo agree (each has a point within `margin` of the anchor) AND
    ALL methods outside the combo disagree (have no point within `margin` of
    the anchor).  True exclusive UpSet semantics: each changepoint contributes
    to exactly one combination bar.

    Anchors on the first method in each combo (consistent with original).

    Returns dict: frozenset(methods) -> int
    """
    combo_counts = defaultdict(int)

    for ts_folder in sorted(input_root.iterdir()):
        if not ts_folder.is_dir():
            continue

        variants_to_run = ["default", "best"] if variant == "both" else [variant]

        for var in variants_to_run:
            method_cps = {}
            for m in methods:
                subdir = ts_folder / f"{var}_{m}"
                if not subdir.exists():
                    continue
                all_cps = []
                for f in sorted(subdir.glob("*.json")):
                    all_cps.extend(load_json(f))
                method_cps[m] = consolidate(all_cps, margin)

            available = list(method_cps.keys())
            if len(available) < 2:
                continue

            for size in range(2, len(available) + 1):
                for combo in itertools.combinations(available, size):
                    key = frozenset(combo)
                    outside = [m for m in available if m not in combo]
                    anchors = method_cps[combo[0]]
                    agreed = sum(
                        1 for anchor in anchors
                        if all(
                            any(abs(anchor - p) <= margin for p in method_cps[m])
                            for m in combo[1:]
                        )
                        and all(
                            not any(abs(anchor - p) <= margin for p in method_cps[m])
                            for m in outside
                        )
                    )
                    combo_counts[key] += agreed

    return combo_counts


# ---------------------------------------------------------------------------
# Manual UpSet renderer
# ---------------------------------------------------------------------------

def build_upset(combo_counts, methods, output_png, show_zero_counts=False):

    if show_zero_counts:
        for key in all_combos_for_methods(methods):
            if key not in combo_counts:
                combo_counts[key] = 0
        combos = list(combo_counts.items())
    else:
        combos = [(combo, cnt) for combo, cnt in combo_counts.items() if cnt > 0]

    if not combos:
        print("No agreements found — nothing to plot.")
        return

    combos.sort(key=lambda x: -x[1])

    n_methods = len(methods)
    method_order      = list(methods)
    method_order_disp = [display_name(m) for m in methods]
    n_combos = len(combos)

    # totals bar: total agreements per method across all combos
    method_totals = defaultdict(int)
    for combo, cnt in combos:
        for m in combo:
            method_totals[m] += cnt

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
    BAR_ZERO = "#B0B8D0"
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
        [method_order_disp[n_methods - 1 - i] for i in range(n_methods)],
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
    ax_totals.set_xlabel("Method total", fontsize=9)
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

    # Print text summary
    print(f"\n{'Combination':<55}  {'Agreements':>10}")
    print("-" * 68)
    for combo, cnt in sorted(combo_counts.items(), key=lambda x: (-len(x[0]), -x[1])):
        label = " & ".join(display_name(m) for m in sorted(combo))
        print(f"  {label:<53}  {cnt:>10}")


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

    combo_counts = count_agreements(
        input_root, args.methods, args.variant, args.margin
    )
    build_upset(combo_counts, args.methods, args.output_png,
                show_zero_counts=args.show_zero_counts)


if __name__ == "__main__":
    main()