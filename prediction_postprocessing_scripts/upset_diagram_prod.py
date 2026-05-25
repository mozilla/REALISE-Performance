#!/usr/bin/env python3
"""
Generate a stacked UpSet plot with three panels:
  - TOP:    equal_voting prod alerts    (drives column order)
  - MIDDLE: priority_voting prod alerts (columns aligned to top)
  - BOTTOM: experimental results from JSON folder (columns aligned to top)

Prod pipeline per detection-method bucket:
  1. Group rows by series_signature_id
  2. Within each signature, pool all per-method push_ids from confidences
  3. Consolidate each method's push_ids with margin (same logic as exp)
  4. Deduplicate any surviving identical (signature, push_id) pairs
  5. Cross-method exclusive agreement: abs(push_id_A - push_id_B) <= margin

STUDENT in prod CSV is aliased to MOZILLA (== mozilla_rep in exp).

Usage:
    python upset_merged.py \
        --input           alerts.csv \
        --input-folder    /path/to/exp/root \
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

PROD_RENAME = {"STUDENT": "MOZILLA"}


def normalise_prod_method(name):
    return PROD_RENAME.get(name.upper(), name.upper())


def display_name_exp(method):
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


def count_exclusive_agreements(method_cps, margin):
    """
    Given method_cps: dict display_name -> [consolidated positions],
    return combo_counts: frozenset -> int using exclusive UpSet semantics.
    Anchors on combo[0].
    """
    combo_counts = defaultdict(int)
    available = list(method_cps.keys())
    if len(available) < 2:
        return combo_counts

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
# CSV / prod data loading
# ===========================================================================

def load_combos_csv(csv_path, detection_method_substring, margin):
    """
    Load prod alerts for rows whose detection_method contains
    `detection_method_substring`.

    Pipeline per series_signature_id:
      - Pool all per-method push_ids from confidences across all matching rows
      - Consolidate each method's push_ids with margin
      - Deduplicate identical (signature, consolidated_push_id) pairs
      - Count exclusive cross-method agreements using push_id proximity

    Returns:
        combo_counts : frozenset(display_names) -> int
        all_methods  : sorted list of all normalised method names seen
    """
    # signature_id -> method_display_name -> [push_ids]
    sig_method_pushids = defaultdict(lambda: defaultdict(list))
    all_methods = set()

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            det_method = row.get("detection_method", "")
            if detection_method_substring not in det_method:
                continue

            sig_id = row.get("series_signature_id", "")
            raw = row.get("confidences", "")
            try:
                d = ast.literal_eval(raw)
            except Exception:
                continue
            if not isinstance(d, dict):
                continue

            for m, v in d.items():
                norm = normalise_prod_method(m)
                all_methods.add(norm)
                if not isinstance(v, dict):
                    continue
                push_id = v.get("push_id")
                if push_id is not None:
                    sig_method_pushids[sig_id][norm].append(push_id)

    # Now consolidate and count agreements per signature
    combo_counts = defaultdict(int)

    for sig_id, method_raw_pushids in sig_method_pushids.items():
        # Consolidate each method's push_ids within this signature
        method_cps = {}
        for norm, push_ids in method_raw_pushids.items():
            # Deduplicate raw push_ids before consolidation
            consolidated = consolidate(sorted(set(push_ids)), margin)
            if consolidated:
                method_cps[norm] = consolidated

        sig_counts = count_exclusive_agreements(method_cps, margin)
        for key, cnt in sig_counts.items():
            combo_counts[key] += cnt

    return combo_counts, sorted(all_methods)


# ===========================================================================
# JSON / experimental data loading
# ===========================================================================

def load_json(path):
    with open(path, "r") as f:
        data = json.load(f)
    return data["result"].get("cplocations", [])


def load_combos_folder(input_root, methods, variant, margin):
    """
    Exclusive UpSet semantics over JSON folder structure.
    Keys use display_name_exp() so they match normalised prod names.
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
                method_cps[display_name_exp(m)] = consolidate(all_cps, margin)

            sig_counts = count_exclusive_agreements(method_cps, margin)
            for key, cnt in sig_counts.items():
                combo_counts[key] += cnt

    return combo_counts


# ===========================================================================
# Column-order helpers
# ===========================================================================

def build_column_order(combo_counts, all_methods, show_zero_counts):
    """Build the master column list sorted by count descending."""
    if show_zero_counts:
        for key in all_combos_for_methods(sorted(all_methods)):
            combo_counts.setdefault(key, 0)
        combos = list(combo_counts.items())
    else:
        combos = [(c, n) for c, n in combo_counts.items() if n > 0]

    combos.sort(key=lambda x: -x[1])
    return combos


def align_to_columns(combo_counts, column_order, all_methods, show_zero_counts):
    """
    Return counts in the same column order as column_order.
    Missing combos get 0. Panel-only extras appended at the end.
    """
    prod_combos = [c for c, _ in column_order]

    if show_zero_counts:
        for key in all_combos_for_methods(sorted(all_methods)):
            combo_counts.setdefault(key, 0)

    aligned = [(combo, combo_counts.get(combo, 0)) for combo in prod_combos]

    seen = set(prod_combos)
    extras = sorted(
        [(c, n) for c, n in combo_counts.items() if c not in seen],
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
    method_order,
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
        active_ys = [
            n_methods - 1 - mi
            for mi, m in enumerate(method_order) if m in combo
        ]
        if len(active_ys) >= 2:
            ax_matrix.plot(
                [ci, ci], [min(active_ys), max(active_ys)],
                color=ACTIVE if cnt > 0 else BAR_ZERO,
                linewidth=2.0, zorder=2,
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
    tot_vals = [
        method_totals.get(method_order[n_methods - 1 - i], 0)
        for i in range(n_methods)
    ]
    max_tot = max(tot_vals) if any(v > 0 for v in tot_vals) else 1
    ax_totals.barh(ys_tot, tot_vals, color=TOT_CLR, height=0.55, zorder=3)
    for y_t, val in zip(ys_tot, tot_vals):
        ax_totals.text(
            val + max_tot * 0.01, y_t, str(val),
            va="center", ha="left", fontsize=7.5, color="#222",
        )
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
    combo_counts_equal,    all_methods_equal,
    combo_counts_priority, all_methods_priority,
    combo_counts_exp,      methods_exp_display,
    output_png,
    show_zero_counts=False,
):
    # ---- master column order from equal_voting -------------------------
    master_combos = build_column_order(
        combo_counts_equal, all_methods_equal, show_zero_counts
    )
    if not master_combos:
        print("equal_voting panel: no data to plot.")
        return

    # ---- align priority and exp to master columns ----------------------
    priority_combos = align_to_columns(
        combo_counts_priority, master_combos, all_methods_priority, show_zero_counts
    )
    exp_combos = align_to_columns(
        combo_counts_exp, master_combos, methods_exp_display, show_zero_counts
    )

    # ---- shared method row order: driven by equal_voting totals --------
    equal_method_totals = defaultdict(int)
    for combo, cnt in master_combos:
        for m in combo:
            equal_method_totals[m] += cnt

    all_display_methods = sorted(
        set(all_methods_equal) | set(all_methods_priority) | set(methods_exp_display),
        key=lambda m: -equal_method_totals.get(m, 0),
    )

    # per-panel method totals (for left-side bars)
    def method_totals_from(combos):
        t = defaultdict(int)
        for combo, cnt in combos:
            for m in combo:
                t[m] += cnt
        return t

    priority_method_totals = method_totals_from(priority_combos)
    exp_method_totals      = method_totals_from(exp_combos)

    # ---- figure geometry -----------------------------------------------
    n_combos  = len(master_combos)
    n_methods = len(all_display_methods)

    bar_h    = 3.0
    mat_h    = n_methods * 0.62 + 0.4
    totals_w = 2.0
    main_w   = max(9, n_combos * 0.52 + 1.5)
    gap      = 0.6
    panel_h  = bar_h + mat_h

    fig_w = totals_w + main_w
    fig_h = 3 * panel_h + 2 * gap + 0.8

    fig = plt.figure(figsize=(fig_w, fig_h))

    outer = GridSpec(
        5, 1, figure=fig,
        height_ratios=[panel_h, gap, panel_h, gap, panel_h],
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

    gs_equal    = make_inner(outer[0])
    gs_priority = make_inner(outer[2])
    gs_exp      = make_inner(outer[4])

    def add_axes(gs):
        return (
            fig.add_subplot(gs[0, 0]),  # blank
            fig.add_subplot(gs[0, 1]),  # bar
            fig.add_subplot(gs[1, 0]),  # totals
            fig.add_subplot(gs[1, 1]),  # matrix
        )

    ax_eq_blank,  ax_eq_bar,  ax_eq_tot,  ax_eq_mat  = add_axes(gs_equal)
    ax_pr_blank,  ax_pr_bar,  ax_pr_tot,  ax_pr_mat  = add_axes(gs_priority)
    ax_exp_blank, ax_exp_bar, ax_exp_tot, ax_exp_mat = add_axes(gs_exp)

    # ---- render each panel ---------------------------------------------
    render_panel(
        ax_eq_bar, ax_eq_mat, ax_eq_tot, ax_eq_blank,
        combos        = master_combos,
        method_order  = all_display_methods,
        ylabel        = "Alerts (equal voting)",
        totals_label  = "Method total",
        method_totals = equal_method_totals,
    )
    render_panel(
        ax_pr_bar, ax_pr_mat, ax_pr_tot, ax_pr_blank,
        combos        = priority_combos,
        method_order  = all_display_methods,
        ylabel        = "Alerts (priority voting)",
        totals_label  = "Method total",
        method_totals = priority_method_totals,
    )
    render_panel(
        ax_exp_bar, ax_exp_mat, ax_exp_tot, ax_exp_blank,
        combos        = exp_combos,
        method_order  = all_display_methods,
        ylabel        = "Agreed changepoints (exp)",
        totals_label  = "Method total",
        method_totals = exp_method_totals,
    )

    # ---- panel titles --------------------------------------------------
    ax_eq_bar.set_title(
        "EQUAL VOTING  —  prod alerts",
        fontsize=10, fontweight="bold", loc="left", pad=6,
    )
    ax_pr_bar.set_title(
        "PRIORITY VOTING  —  prod alerts",
        fontsize=10, fontweight="bold", loc="left", pad=6,
    )
    ax_exp_bar.set_title(
        "EXPERIMENTAL  —  historical changepoints",
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
    for label, cc in [
        ("EQUAL VOTING",    combo_counts_equal),
        ("PRIORITY VOTING", combo_counts_priority),
        ("EXPERIMENTAL",    combo_counts_exp),
    ]:
        print(f"\n=== {label} combinations ===")
        print(f"{'Combination':<55}  {'Count':>8}")
        print("-" * 66)
        for combo, cnt in sorted(cc.items(), key=lambda x: (-len(x[0]), -x[1])):
            print(f"  {'  &  '.join(sorted(combo)):<53}  {cnt:>8}")


# ===========================================================================
# CLI
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Three-panel stacked UpSet plot: "
            "equal_voting (top) + priority_voting (middle) + experimental (bottom). "
            "Columns aligned to equal_voting for direct comparison. "
            "STUDENT in prod is treated as MOZILLA."
        )
    )
    parser.add_argument("--input",        "-i", required=True,
                        help="Path to prod alerts CSV")
    parser.add_argument("--input-folder", "-f", required=True,
                        help="Root folder containing per-timeseries exp subfolders")
    parser.add_argument("--methods",      nargs="+", required=True,
                        help="Exp method names (e.g. cvm_advanced mozilla_rep)")
    parser.add_argument("--margin",       "-m", type=int, default=5)
    parser.add_argument("--variant",      choices=["default", "best", "both"],
                        default="best")
    parser.add_argument("--output-png",   "-o", required=True)
    parser.add_argument("--show-zero-counts", action="store_true", default=False,
                        help="Show zero-count combinations in muted colour.")
    args = parser.parse_args()

    print(f"Loading prod CSV: {args.input}  margin={args.margin}")

    print("  Processing equal_voting rows …")
    combo_counts_equal, all_methods_equal = load_combos_csv(
        args.input, "equal_voting", args.margin
    )
    print(f"    {sum(combo_counts_equal.values())} agreements, "
          f"{len(combo_counts_equal)} combos, "
          f"methods: {', '.join(all_methods_equal)}")

    print("  Processing priority_voting rows …")
    combo_counts_priority, all_methods_priority = load_combos_csv(
        args.input, "priority_voting", args.margin
    )
    print(f"    {sum(combo_counts_priority.values())} agreements, "
          f"{len(combo_counts_priority)} combos, "
          f"methods: {', '.join(all_methods_priority)}")

    print(f"\nScanning exp folder: {args.input_folder}")
    print(f"  methods={args.methods}  variant={args.variant}")
    combo_counts_exp = load_combos_folder(
        Path(args.input_folder), args.methods, args.variant, args.margin
    )
    methods_exp_display = [display_name_exp(m) for m in args.methods]
    print(f"  {sum(combo_counts_exp.values())} agreed changepoints, "
          f"{len(combo_counts_exp)} combos, "
          f"display names: {', '.join(methods_exp_display)}")

    build_merged_figure(
        combo_counts_equal,    all_methods_equal,
        combo_counts_priority, all_methods_priority,
        combo_counts_exp,      methods_exp_display,
        args.output_png,
        show_zero_counts=args.show_zero_counts,
    )


if __name__ == "__main__":
    main()