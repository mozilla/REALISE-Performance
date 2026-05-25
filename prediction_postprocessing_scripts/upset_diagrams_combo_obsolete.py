#!/usr/bin/env python3
"""
Generate a stacked UpSet plot with two panels:
  - TOP:    prod results from a voting-system CSV (upset_csv logic)
  - BOTTOM: experimental results from a folder of JSON files (upset_diagram logic)

The top panel's bar order (descending count) drives the column layout.
The bottom panel uses the same column ordering for direct comparison.

STUDENT in the prod CSV is treated as an alias for MOZILLA (mozilla_rep in exp).
All display labels use MOZILLA for this detector in both panels.

Usage:
    python upset_merged.py \
        --input           alerts.csv \
        --input-folder    /path/to/input \
        --output-png      upset_merged.png \
        --methods         cvm_advanced ks_advanced mwu_advanced welch_advanced mozilla_rep \
        [--margin 5] \
        [--variant default|best|both] \
        [--show-zero-counts]
"""

import argparse
import ast
import csv
import itertools
import json
from collections import defaultdict
from pathlib import Path
from statistics import median

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec


# ===========================================================================
# Name normalisation
# ===========================================================================

# Any key in this map found in prod CSV method names gets renamed to its value.
# Applied after uppercasing.
PROD_RENAME = {
    "STUDENT": "MOZILLA",
}


def normalise_prod_method(name):
    """Uppercase and apply PROD_RENAME aliases."""
    return PROD_RENAME.get(name.upper(), name.upper())


def display_name_exp(method):
    """Strip _advanced/_rep suffix then uppercase."""
    name = method
    for suffix in ("_advanced", "_rep"):
        if name.lower().endswith(suffix):
            name = name[: -len(suffix)]
            break
    return name.upper()


# ===========================================================================
# Shared helpers
# ===========================================================================

def all_combos_for_methods(methods):
    result = []
    for size in range(2, len(methods) + 1):
        for combo in itertools.combinations(methods, size):
            result.append(frozenset(combo))
    return result


# ===========================================================================
# CSV / prod data loading
# ===========================================================================

def load_combos_csv(csv_path):
    """
    Returns:
        combo_counts : frozenset(display_names) -> int
        all_methods  : sorted list of all (renamed/normalised) method names seen
    """
    combo_counts = defaultdict(int)
    all_methods = set()

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw = row.get("confidences", "")
            try:
                d = ast.literal_eval(raw)
            except Exception:
                continue
            if not isinstance(d, dict):
                continue

            all_methods |= {normalise_prod_method(m) for m in d}

            fired = frozenset(
                normalise_prod_method(m) for m, v in d.items()
                if isinstance(v, dict) and v.get("change_detected") is True
            )
            if len(fired) >= 2:
                combo_counts[fired] += 1

    return combo_counts, sorted(all_methods)


# ===========================================================================
# JSON / experimental data loading
# ===========================================================================

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


def load_combos_folder(input_root, methods, variant, margin):
    """
    Exclusive UpSet semantics. Internal keys use display_name_exp() so they
    match the normalised prod names (e.g. mozilla_rep -> MOZILLA).
    Returns combo_counts: frozenset(display_names) -> int
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
                # Use display name as key so it matches prod naming
                method_cps[display_name_exp(m)] = consolidate(all_cps, margin)

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


# ===========================================================================
# Column-order helpers
# ===========================================================================

def build_column_order_from_prod(combo_counts_prod, all_methods_prod, show_zero_counts):
    if show_zero_counts:
        for key in all_combos_for_methods(all_methods_prod):
            combo_counts_prod.setdefault(key, 0)
        combos = list(combo_counts_prod.items())
    else:
        combos = [(c, n) for c, n in combo_counts_prod.items() if n > 0]

    combos.sort(key=lambda x: -x[1])
    return combos


def align_exp_to_columns(combo_counts_exp, column_order, all_methods_exp, show_zero_counts):
    """
    Return exp counts in exactly the same column order as prod.
    Prod columns absent from exp get count 0.
    Exp-only columns are appended at the end (sorted descending).
    """
    prod_combos = [c for c, _ in column_order]

    if show_zero_counts:
        for key in all_combos_for_methods(all_methods_exp):
            combo_counts_exp.setdefault(key, 0)

    aligned = [(combo, combo_counts_exp.get(combo, 0)) for combo in prod_combos]

    seen = set(prod_combos)
    extras = sorted(
        [(c, n) for c, n in combo_counts_exp.items() if c not in seen],
        key=lambda x: -x[1],
    )
    aligned.extend(extras)

    return aligned


# ===========================================================================
# Single-panel renderer
# ===========================================================================

def render_panel(
    ax_bar, ax_matrix, ax_totals, ax_blank,
    combos,
    method_order,       # display-name strings, top-to-bottom
    ylabel,
    totals_label,
    method_totals,
):
    ACTIVE   = "#2C3E7A"
    INACTIVE = "#D8DCE8"
    BAR_CLR  = "#2C3E7A"
    BAR_ZERO = "#B0B8D0"
    TOT_CLR  = "#4A6FA5"
    DOT_R    = 0.28

    n_methods = len(method_order)
    n_combos  = len(combos)
    counts    = [cnt for _, cnt in combos]
    max_count = max(counts) if any(c > 0 for c in counts) else 1
    xs        = np.arange(n_combos)

    ax_blank.axis("off")

    # --- bar chart -------------------------------------------------------
    bar_colors = [BAR_CLR if cnt > 0 else BAR_ZERO for cnt in counts]
    bars = ax_bar.bar(xs, counts, color=bar_colors, width=0.6, zorder=3)
    for bar, cnt in zip(bars, counts):
        ax_bar.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max_count * 0.01,
            str(cnt), ha="center", va="bottom", fontsize=7,
            color="#888" if cnt == 0 else "#222",
        )
    ax_bar.set_xlim(-0.5, n_combos - 0.5)
    ax_bar.set_ylim(0, max_count * 1.18)
    ax_bar.set_xticks([])
    ax_bar.set_ylabel(ylabel, fontsize=9)
    ax_bar.yaxis.set_label_position("left")
    ax_bar.spines[["top", "right", "bottom"]].set_visible(False)
    ax_bar.yaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)
    ax_bar.set_axisbelow(True)

    # --- dot matrix ------------------------------------------------------
    ax_matrix.set_xlim(-0.5, n_combos - 0.5)
    ax_matrix.set_ylim(-0.5, n_methods - 0.5)

    for mi, method in enumerate(method_order):
        y = n_methods - 1 - mi
        ax_matrix.axhline(y, color="#E0E3EE", linewidth=0.8, zorder=1)
        for ci, (combo, cnt) in enumerate(combos):
            active = method in combo
            color = (ACTIVE if cnt > 0 else BAR_ZERO) if active else INACTIVE
            ax_matrix.add_patch(plt.Circle((ci, y), DOT_R, color=color, zorder=3))

    for ci, (combo, cnt) in enumerate(combos):
        active_ys = [n_methods - 1 - mi for mi, m in enumerate(method_order) if m in combo]
        if len(active_ys) >= 2:
            ax_matrix.plot(
                [ci, ci], [min(active_ys), max(active_ys)],
                color=ACTIVE if cnt > 0 else BAR_ZERO, linewidth=2.0, zorder=2,
            )

    ax_matrix.set_xticks([])
    ax_matrix.set_yticks(range(n_methods))
    ax_matrix.set_yticklabels(
        [method_order[n_methods - 1 - i] for i in range(n_methods)],
        fontsize=9,
    )
    ax_matrix.yaxis.set_tick_params(length=0)
    ax_matrix.spines[:].set_visible(False)
    ax_matrix.set_aspect("equal", adjustable="box")

    # --- method totals ---------------------------------------------------
    ys_tot   = np.arange(n_methods)
    tot_vals = [method_totals.get(method_order[n_methods - 1 - i], 0) for i in range(n_methods)]
    max_tot  = max(tot_vals) if any(v > 0 for v in tot_vals) else 1
    ax_totals.barh(ys_tot, tot_vals, color=TOT_CLR, height=0.55, zorder=3)
    for y_t, val in zip(ys_tot, tot_vals):
        ax_totals.text(val + max_tot * 0.01, y_t, str(val),
                       va="center", ha="left", fontsize=7.5, color="#222")
    ax_totals.set_ylim(-0.5, n_methods - 0.5)
    ax_totals.set_xlim(max_tot * 1.25, 0)
    ax_totals.set_yticks([])
    ax_totals.set_xlabel(totals_label, fontsize=9)
    ax_totals.spines[["top", "left", "bottom"]].set_visible(False)
    ax_totals.xaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)
    ax_totals.set_axisbelow(True)
    ax_totals.invert_xaxis()


# ===========================================================================
# Main figure builder
# ===========================================================================

def build_merged_figure(
    combo_counts_prod, all_methods_prod,
    combo_counts_exp,
    methods_exp_display,   # display names (after display_name_exp), in CLI order
    output_png,
    show_zero_counts=False,
):
    # ---- prod column order (master) ------------------------------------
    prod_combos = build_column_order_from_prod(
        combo_counts_prod, all_methods_prod, show_zero_counts
    )
    if not prod_combos:
        print("Prod panel: no data to plot.")
        return

    # ---- exp columns aligned to prod ----------------------------------
    exp_combos = align_exp_to_columns(
        combo_counts_exp, prod_combos, methods_exp_display, show_zero_counts
    )

    # ---- shared method row order: driven by prod totals ---------------
    prod_method_totals = defaultdict(int)
    for combo, cnt in prod_combos:
        for m in combo:
            prod_method_totals[m] += cnt

    # Order by prod total descending; include all methods from both panels
    all_display_methods = sorted(
        set(all_methods_prod) | set(methods_exp_display),
        key=lambda m: -prod_method_totals.get(m, 0),
    )

    # Exp method totals (for the left-side bars in exp panel)
    exp_method_totals = defaultdict(int)
    for combo, cnt in exp_combos:
        for m in combo:
            exp_method_totals[m] += cnt

    n_combos = len(prod_combos)
    n_methods = len(all_display_methods)

    # ---- figure geometry -----------------------------------------------
    bar_h    = 3.0
    mat_h    = n_methods * 0.62 + 0.4
    totals_w = 2.0
    main_w   = max(9, n_combos * 0.52 + 1.5)
    gap      = 0.7

    fig_w = totals_w + main_w
    fig_h = 2 * (bar_h + mat_h) + gap + 0.8

    fig = plt.figure(figsize=(fig_w, fig_h))

    outer = GridSpec(
        3, 1, figure=fig,
        height_ratios=[bar_h + mat_h, gap, bar_h + mat_h],
        hspace=0.0,
    )

    def make_inner(outer_cell):
        return GridSpecFromSubplotSpec(
            2, 2,
            subplot_spec=outer_cell,
            width_ratios=[totals_w, main_w],
            height_ratios=[bar_h, mat_h],
            hspace=0.05,
            wspace=0.03,
        )

    gs_prod = make_inner(outer[0])
    gs_exp  = make_inner(outer[2])

    ax_prod_blank  = fig.add_subplot(gs_prod[0, 0])
    ax_prod_bar    = fig.add_subplot(gs_prod[0, 1])
    ax_prod_totals = fig.add_subplot(gs_prod[1, 0])
    ax_prod_matrix = fig.add_subplot(gs_prod[1, 1])

    ax_exp_blank   = fig.add_subplot(gs_exp[0, 0])
    ax_exp_bar     = fig.add_subplot(gs_exp[0, 1])
    ax_exp_totals  = fig.add_subplot(gs_exp[1, 0])
    ax_exp_matrix  = fig.add_subplot(gs_exp[1, 1])

    # ---- render prod panel ---------------------------------------------
    render_panel(
        ax_prod_bar, ax_prod_matrix, ax_prod_totals, ax_prod_blank,
        combos        = prod_combos,
        method_order  = all_display_methods,
        ylabel        = "Alerts (prod)",
        totals_label  = "Method total",
        method_totals = prod_method_totals,
    )

    # ---- render exp panel ----------------------------------------------
    render_panel(
        ax_exp_bar, ax_exp_matrix, ax_exp_totals, ax_exp_blank,
        combos        = exp_combos,
        method_order  = all_display_methods,   # same order as prod
        ylabel        = "Agreed changepoints (exp)",
        totals_label  = "Method total",
        method_totals = exp_method_totals,
    )

    # ---- titles --------------------------------------------------------
    ax_prod_bar.set_title(
        "PROD  —  method agreement on live alerts",
        fontsize=10, fontweight="bold", loc="left", pad=6,
    )
    ax_exp_bar.set_title(
        "EXPERIMENTAL  —  method agreement on historical changepoints",
        fontsize=10, fontweight="bold", loc="left", pad=6,
    )

    fig.suptitle(
        "Method Agreement UpSet Plot  "
        "(bars = exclusive agreements; columns aligned for direct comparison)",
        fontsize=11, fontweight="bold", y=1.002,
    )

    plt.savefig(output_png, dpi=150, bbox_inches="tight")
    print(f"Saved merged UpSet plot → {output_png}")

    # ---- text summaries ------------------------------------------------
    print("\n=== PROD combinations ===")
    print(f"{'Combination':<55}  {'Alerts':>8}")
    print("-" * 66)
    for combo, cnt in sorted(combo_counts_prod.items(), key=lambda x: (-len(x[0]), -x[1])):
        print(f"  {'  &  '.join(sorted(combo)):<53}  {cnt:>8}")

    print("\n=== EXPERIMENTAL combinations ===")
    print(f"{'Combination':<55}  {'Agreements':>10}")
    print("-" * 68)
    for combo, cnt in sorted(combo_counts_exp.items(), key=lambda x: (-len(x[0]), -x[1])):
        print(f"  {'  &  '.join(sorted(combo)):<53}  {cnt:>10}")


# ===========================================================================
# CLI
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Stacked UpSet plot: prod CSV (top) + experimental folder (bottom), "
            "columns aligned for direct comparison. "
            "STUDENT in prod is treated as MOZILLA."
        )
    )
    parser.add_argument("--input",        "-i", required=True,
                        help="Path to prod alerts CSV")
    parser.add_argument("--input-folder", "-f", required=True,
                        help="Root folder containing per-timeseries subfolders")
    parser.add_argument("--methods",      nargs="+", required=True,
                        help="Method names for the experimental panel (e.g. mozilla_rep)")
    parser.add_argument("--margin",       "-m", type=int, default=5)
    parser.add_argument("--variant",      choices=["default", "best", "both"],
                        default="best")
    parser.add_argument("--output-png",   "-o", required=True)
    parser.add_argument("--show-zero-counts", action="store_true", default=False,
                        help="Show zero-count combinations (muted colour).")
    args = parser.parse_args()

    print(f"Loading prod CSV:    {args.input}")
    combo_counts_prod, all_methods_prod = load_combos_csv(args.input)
    print(f"  {sum(combo_counts_prod.values())} multi-method alerts, "
          f"{len(combo_counts_prod)} unique combos, "
          f"methods: {', '.join(all_methods_prod)}")

    print(f"\nScanning exp folder: {args.input_folder}")
    print(f"  methods={args.methods}  margin={args.margin}  variant={args.variant}")
    combo_counts_exp = load_combos_folder(
        Path(args.input_folder), args.methods, args.variant, args.margin
    )
    # Display names for exp methods (used as keys in combo_counts_exp)
    methods_exp_display = [display_name_exp(m) for m in args.methods]
    print(f"  {sum(combo_counts_exp.values())} agreed changepoints, "
          f"{len(combo_counts_exp)} unique combos, "
          f"display names: {', '.join(methods_exp_display)}")

    build_merged_figure(
        combo_counts_prod, all_methods_prod,
        combo_counts_exp,  methods_exp_display,
        args.output_png,
        show_zero_counts=args.show_zero_counts,
    )


if __name__ == "__main__":
    main()