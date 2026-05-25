#!/usr/bin/env python3
"""
Generate a stacked UpSet plot with three panels:
  - TOP:    equal_voting prod alerts    (drives column order)
  - MIDDLE: priority_voting prod alerts (columns aligned to top)
  - BOTTOM: experimental results from JSON folder (columns aligned to top)

Prod pipeline per detection-method bucket:
  1. Group rows by series_signature_id (skip non-autoland rows silently)
  2. Fetch the full push_id sequence for each signature from the Treeherder API
     (cached to disk; retried up to 3 times on failure)
  3. Within each signature, pool all per-method push_ids from confidences
  4. Consolidate: two push_ids are in the same cluster if their positions in the
     full sorted push_id sequence differ by <= margin
  5. Deduplicate any identical push_ids before consolidation
  6. Cross-method exclusive agreement: position(p2) - position(p1) <= margin

Adjacency stats (logged to console) measure within-method clustering on the
RAW (pre-consolidation) detections so consolidation does not mask the signal.
High adjacency rate = method fires multiple times in the same window (noisy).

STUDENT in prod CSV is aliased to MOZILLA (== mozilla_rep in exp).

Usage:
    python upset_merged.py \
        --input           alerts.csv \
        --input-folder    /path/to/exp/root \
        --output-png      upset_merged.png \
        --methods         cvm_advanced ks_advanced mwu_advanced welch_advanced mozilla_rep \
        [--margin 5] \
        [--variant default|best|both] \
        [--show-zero-counts] \
        [--cache-file push_id_cache.json]
"""

import argparse
import ast
import csv
import itertools
import json
import time
from collections import defaultdict
from pathlib import Path
from statistics import median

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec

try:
    import requests
except ImportError:
    requests = None


# ===========================================================================
# Name normalisation
# ===========================================================================

PROD_RENAME = {"STUDENT": "MOZILLA"}
AUTOLAND_PROJECT = "autoland"


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


# ===========================================================================
# Treeherder API — push_id sequence fetching
# ===========================================================================

TREEHERDER_SUMMARY_URL = (
    "https://treeherder.mozilla.org/api/performance/summary/"
    "?repository={project}&signature={signature_id}"
    "&framework={framework_id}&interval=126144000"
    "&all_data=true&replicates=false"
)
_HEADERS = {"User-Agent": "Mozilla/5.0"}
_MAX_RETRIES = 3
_RETRY_DELAY = 2


def _fetch_url(url):
    if requests is None:
        raise RuntimeError("The 'requests' library is required. pip install requests")
    last_exc = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY)
    raise last_exc


def fetch_push_id_sequence(signature_id, framework_id, cache, cache_path):
    cache_key = f"{signature_id}:{framework_id}"
    if cache_key in cache:
        return cache[cache_key]

    url = TREEHERDER_SUMMARY_URL.format(
        project=AUTOLAND_PROJECT,
        signature_id=signature_id,
        framework_id=framework_id,
    )
    try:
        data = _fetch_url(url)
    except Exception as exc:
        print(
            f"WARNING: failed to fetch push_ids for signature {signature_id} "
            f"(framework {framework_id}) after {_MAX_RETRIES} attempts: {exc}"
        )
        cache[cache_key] = None
        _save_cache(cache, cache_path)
        return None

    push_ids = sorted({
        int(pt["push_id"])
        for series in (data if isinstance(data, list) else [data])
        for pt in series.get("data", [])
        if pt.get("push_id") is not None
    })
    cache[cache_key] = push_ids
    _save_cache(cache, cache_path)
    return push_ids


def _load_cache(cache_path):
    p = Path(cache_path)
    if p.exists():
        try:
            with open(p, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_cache(cache, cache_path):
    with open(cache_path, "w") as f:
        json.dump(cache, f)


# ===========================================================================
# Position-based helpers
# ===========================================================================

def position_in_sequence(push_id, sorted_sequence):
    import bisect
    idx = bisect.bisect_left(sorted_sequence, push_id)
    if idx >= len(sorted_sequence):
        return len(sorted_sequence) - 1
    if sorted_sequence[idx] == push_id:
        return idx
    if idx == 0:
        return 0
    before = idx - 1
    after  = idx
    if (push_id - sorted_sequence[before]) <= (sorted_sequence[after] - push_id):
        return before
    return after


def consolidate_by_position(push_ids, sorted_sequence, margin):
    if not push_ids:
        return []
    pos_pid = sorted(
        {position_in_sequence(p, sorted_sequence): p for p in push_ids}.items()
    )
    clusters = [[pos_pid[0]]]
    for pos, pid in pos_pid[1:]:
        if pos - clusters[-1][0][0] <= margin:
            clusters[-1].append((pos, pid))
        else:
            clusters.append([(pos, pid)])
    result = []
    for cluster in clusters:
        mid = len(cluster) // 2
        result.append(cluster[mid][1])
    return result


def positions_within_margin(pid_a, pid_b, sorted_sequence, margin):
    pa = position_in_sequence(pid_a, sorted_sequence)
    pb = position_in_sequence(pid_b, sorted_sequence)
    return abs(pa - pb) <= margin


# ===========================================================================
# Adjacency stats — within-method, on RAW pre-consolidation detections
# ===========================================================================

def update_adjacency_stats(method_raw, sorted_sequence, margin, stats):
    """
    For each method, count how many of its RAW (pre-consolidation) detections
    are within `margin` positions of another of its OWN raw detections.

    Using raw detections is essential: consolidation by definition removes
    points that are within margin of each other, so checking post-consolidation
    points would always yield 0.

    High rate = method fires multiple times in the same window (noisy).
    """
    for method, raw_push_ids in method_raw.items():
        detections = sorted(set(raw_push_ids))  # deduplicated but not consolidated
        adjacent = sum(
            1 for i, d in enumerate(detections)
            if any(
                positions_within_margin(d, other_d, sorted_sequence, margin)
                for j, other_d in enumerate(detections)
                if i != j
            )
        )
        s = stats[method]
        s["total"]    += len(detections)
        s["adjacent"] += adjacent
        s["sigs"]     += 1


def update_adjacency_stats_abs(method_raw, margin, stats):
    """
    Same as update_adjacency_stats but uses absolute numeric proximity
    for the exp panel (index positions, no push_id sequence needed).
    Also operates on RAW pre-consolidation detections.
    """
    for method, raw_detections in method_raw.items():
        detections = sorted(set(raw_detections))
        adjacent = sum(
            1 for i, d in enumerate(detections)
            if any(
                abs(d - other_d) <= margin
                for j, other_d in enumerate(detections)
                if i != j
            )
        )
        s = stats[method]
        s["total"]    += len(detections)
        s["adjacent"] += adjacent
        s["sigs"]     += 1


def print_adjacency_stats(stats, label, margin):
    print(f"\n=== ADJACENCY STATS — {label} (margin={margin}) ===")
    print(
        f"  A detection is 'adjacent' if within {margin} positions of another\n"
        f"  detection from the SAME method (measured on raw pre-consolidation points).\n"
        f"  High rate = method fires multiple times in the same window (noisy).\n"
    )
    header = (
        f"  {'Method':<12}  {'Signatures':>10}  "
        f"{'Total det.':>10}  {'Avg det./sig':>12}  "
        f"{'Adjacent':>10}  {'Avg adj./sig':>12}  {'Adj. rate':>10}"
    )
    print(header)
    print("  " + "-" * (len(header) - 2))
    for method in sorted(stats):
        s = stats[method]
        if s["sigs"] == 0:
            continue
        avg_total = s["total"]    / s["sigs"]
        avg_adj   = s["adjacent"] / s["sigs"]
        rate      = 100.0 * s["adjacent"] / s["total"] if s["total"] > 0 else 0.0
        print(
            f"  {method:<12}  {s['sigs']:>10}  {s['total']:>10}  "
            f"{avg_total:>12.2f}  {s['adjacent']:>10}  "
            f"{avg_adj:>12.2f}  {rate:>9.1f}%"
        )


# ===========================================================================
# Exclusive agreement counters
# ===========================================================================

def count_exclusive_agreements_pos(method_cps, sorted_sequence, margin):
    """Position-based proximity — used by prod panels."""
    combo_counts = defaultdict(int)
    available = list(method_cps.keys())
    if len(available) < 2:
        return combo_counts

    for size in range(2, len(available) + 1):
        for combo in itertools.combinations(available, size):
            key     = frozenset(combo)
            outside = [m for m in available if m not in combo]
            anchors = method_cps[combo[0]]
            agreed  = sum(
                1 for anchor in anchors
                if all(
                    any(
                        positions_within_margin(anchor, p, sorted_sequence, margin)
                        for p in method_cps[m]
                    )
                    for m in combo[1:]
                )
                and all(
                    not any(
                        positions_within_margin(anchor, p, sorted_sequence, margin)
                        for p in method_cps[m]
                    )
                    for m in outside
                )
            )
            combo_counts[key] += agreed

    return combo_counts


def count_exclusive_agreements(method_cps, margin):
    """Absolute numeric proximity — used by exp panel."""
    combo_counts = defaultdict(int)
    available = list(method_cps.keys())
    if len(available) < 2:
        return combo_counts

    for size in range(2, len(available) + 1):
        for combo in itertools.combinations(available, size):
            key     = frozenset(combo)
            outside = [m for m in available if m not in combo]
            anchors = method_cps[combo[0]]
            agreed  = sum(
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

def load_combos_csv(csv_path, detection_method_substring, margin, cache, cache_path):
    """
    Returns combo_counts, all_methods, adjacency_stats.
    Agreement counting uses consolidated push_ids.
    Adjacency stats use raw (pre-consolidation) push_ids.
    """
    sig_method_pushids = defaultdict(lambda: defaultdict(list))
    sig_framework      = {}
    all_methods        = set()

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            det_method = row.get("detection_method", "")
            if detection_method_substring not in det_method:
                continue

            repo_name = row.get("repository_name", "") or row.get("repository_id11", "")
            if repo_name and repo_name != AUTOLAND_PROJECT and repo_name != "77":
                continue

            sig_id       = row.get("series_signature_id", "").strip()
            framework_id = row.get("framework_id", "").strip()
            if not sig_id:
                continue

            sig_framework[sig_id] = framework_id

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
                    sig_method_pushids[sig_id][norm].append(int(push_id))

    combo_counts    = defaultdict(int)
    adjacency_stats = defaultdict(lambda: {"total": 0, "adjacent": 0, "sigs": 0})
    n_sigs          = len(sig_method_pushids)
    failed_sigs     = []

    print(f"    Fetching push_id sequences for {n_sigs} signatures …")
    for i, (sig_id, method_raw_pushids) in enumerate(sig_method_pushids.items(), 1):
        framework_id = sig_framework.get(sig_id, "1")

        seq = fetch_push_id_sequence(sig_id, framework_id, cache, cache_path)
        if seq is None:
            failed_sigs.append(sig_id)
            continue
        if not seq:
            continue

        print(f"    [{i}/{n_sigs}] sig {sig_id}: {len(seq)} push_ids", end="\r")

        # Build both raw and consolidated dicts
        method_cps = {}   # consolidated — for agreement counting
        method_raw = {}   # raw deduped  — for adjacency stats

        for norm, push_ids in method_raw_pushids.items():
            deduped      = list(set(push_ids))
            consolidated = consolidate_by_position(deduped, seq, margin)
            if consolidated:
                method_cps[norm] = consolidated
                method_raw[norm] = deduped
        # Agreement counts use consolidated points
        sig_counts = count_exclusive_agreements_pos(method_cps, seq, margin)
        for key, cnt in sig_counts.items():
            combo_counts[key] += cnt

        # Adjacency stats use raw points
        update_adjacency_stats(method_raw, seq, margin, adjacency_stats)

    print()
    if failed_sigs:
        print(f"    WARNING: skipped {len(failed_sigs)} signatures due to API failures: "
              f"{failed_sigs}")

    return combo_counts, sorted(all_methods), adjacency_stats


# ===========================================================================
# JSON / experimental data loading
# ===========================================================================

def load_json_file(path):
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
    """Returns combo_counts, adjacency_stats."""
    combo_counts    = defaultdict(int)
    adjacency_stats = defaultdict(lambda: {"total": 0, "adjacent": 0, "sigs": 0})

    for ts_folder in sorted(input_root.iterdir()):
        if not ts_folder.is_dir():
            continue
        variants_to_run = ["default", "best"] if variant == "both" else [variant]
        for var in variants_to_run:
            method_cps = {}   # consolidated
            method_raw = {}   # raw pre-consolidation

            for m in methods:
                subdir = ts_folder / f"{var}_{m}"
                if not subdir.exists():
                    continue
                all_cps = []
                for f in sorted(subdir.glob("*.json")):
                    all_cps.extend(load_json_file(f))

                raw_deduped  = sorted(set(all_cps))
                consolidated = consolidate(all_cps, margin)
                disp = display_name_exp(m)
                method_cps[disp] = consolidated
                method_raw[disp] = raw_deduped

            sig_counts = count_exclusive_agreements(method_cps, margin)
            for key, cnt in sig_counts.items():
                combo_counts[key] += cnt

            # Adjacency on raw points
            update_adjacency_stats_abs(method_raw, margin, adjacency_stats)

    return combo_counts, adjacency_stats


# ===========================================================================
# Column-order helpers
# ===========================================================================

def build_column_order(combo_counts, all_methods, show_zero_counts):
    if show_zero_counts:
        for key in all_combos_for_methods(sorted(all_methods)):
            combo_counts.setdefault(key, 0)
        combos = list(combo_counts.items())
    else:
        combos = [(c, n) for c, n in combo_counts.items() if n > 0]
    combos.sort(key=lambda x: -x[1])
    return combos


def align_to_columns(combo_counts, column_order, all_methods, show_zero_counts):
    prod_combos = [c for c, _ in column_order]
    if show_zero_counts:
        for key in all_combos_for_methods(sorted(all_methods)):
            combo_counts.setdefault(key, 0)
    aligned = [(combo, combo_counts.get(combo, 0)) for combo in prod_combos]
    seen    = set(prod_combos)
    extras  = sorted(
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
    combos, method_order, ylabel, totals_label, method_totals,
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

    ax_matrix.set_xlim(-0.5, n_combos - 0.5)
    ax_matrix.set_ylim(-0.5, n_methods - 0.5)
    for mi, method in enumerate(method_order):
        y = n_methods - 1 - mi
        ax_matrix.axhline(y, color="#E0E3EE", linewidth=0.8, zorder=1)
        for ci, (combo, cnt) in enumerate(combos):
            active = method in combo
            color  = (ACTIVE if cnt > 0 else BAR_ZERO) if active else INACTIVE
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
        [method_order[n_methods - 1 - i] for i in range(n_methods)], fontsize=9
    )
    ax_matrix.yaxis.set_tick_params(length=0)
    ax_matrix.spines[:].set_visible(False)
    ax_matrix.set_aspect("equal", adjustable="box")

    ys_tot   = np.arange(n_methods)
    tot_vals = [
        method_totals.get(method_order[n_methods - 1 - i], 0)
        for i in range(n_methods)
    ]
    max_tot = max(tot_vals) if any(v > 0 for v in tot_vals) else 1
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
    combo_counts_equal,    all_methods_equal,
    combo_counts_priority, all_methods_priority,
    combo_counts_exp,      methods_exp_display,
    output_png,
    show_zero_counts=False,
):
    master_combos = build_column_order(
        combo_counts_equal, all_methods_equal, show_zero_counts
    )
    if not master_combos:
        print("equal_voting panel: no data to plot.")
        return

    priority_combos = align_to_columns(
        combo_counts_priority, master_combos, all_methods_priority, show_zero_counts
    )
    exp_combos = align_to_columns(
        combo_counts_exp, master_combos, methods_exp_display, show_zero_counts
    )

    equal_method_totals = defaultdict(int)
    for combo, cnt in master_combos:
        for m in combo:
            equal_method_totals[m] += cnt

    all_display_methods = sorted(
        set(all_methods_equal) | set(all_methods_priority) | set(methods_exp_display),
        key=lambda m: -equal_method_totals.get(m, 0),
    )

    def method_totals_from(combos):
        t = defaultdict(int)
        for combo, cnt in combos:
            for m in combo:
                t[m] += cnt
        return t

    priority_method_totals = method_totals_from(priority_combos)
    exp_method_totals      = method_totals_from(exp_combos)

    n_combos  = len(master_combos)
    n_methods = len(all_display_methods)
    bar_h     = 3.0
    mat_h     = n_methods * 0.62 + 0.4
    totals_w  = 2.0
    main_w    = max(9, n_combos * 0.52 + 1.5)
    gap       = 0.6
    panel_h   = bar_h + mat_h

    fig = plt.figure(figsize=(totals_w + main_w, 3 * panel_h + 2 * gap + 0.8))

    outer = GridSpec(
        5, 1, figure=fig,
        height_ratios=[panel_h, gap, panel_h, gap, panel_h],
        hspace=0.0,
    )

    def make_inner(cell):
        return GridSpecFromSubplotSpec(
            2, 2, subplot_spec=cell,
            width_ratios=[totals_w, main_w],
            height_ratios=[bar_h, mat_h],
            hspace=0.05, wspace=0.03,
        )

    def add_axes(gs):
        return (
            fig.add_subplot(gs[0, 0]),
            fig.add_subplot(gs[0, 1]),
            fig.add_subplot(gs[1, 0]),
            fig.add_subplot(gs[1, 1]),
        )

    ax_eq_blank,  ax_eq_bar,  ax_eq_tot,  ax_eq_mat  = add_axes(make_inner(outer[0]))
    ax_pr_blank,  ax_pr_bar,  ax_pr_tot,  ax_pr_mat  = add_axes(make_inner(outer[2]))
    ax_exp_blank, ax_exp_bar, ax_exp_tot, ax_exp_mat = add_axes(make_inner(outer[4]))

    render_panel(ax_eq_bar,  ax_eq_mat,  ax_eq_tot,  ax_eq_blank,
                 master_combos,   all_display_methods,
                 "Alerts (equal voting)",     "Method total", equal_method_totals)
    render_panel(ax_pr_bar,  ax_pr_mat,  ax_pr_tot,  ax_pr_blank,
                 priority_combos, all_display_methods,
                 "Alerts (priority voting)",  "Method total", priority_method_totals)
    render_panel(ax_exp_bar, ax_exp_mat, ax_exp_tot, ax_exp_blank,
                 exp_combos,      all_display_methods,
                 "Agreed changepoints (exp)", "Method total", exp_method_totals)

    ax_eq_bar.set_title(
        "EQUAL VOTING  —  prod alerts",
        fontsize=10, fontweight="bold", loc="left", pad=6)
    ax_pr_bar.set_title(
        "PRIORITY VOTING  —  prod alerts",
        fontsize=10, fontweight="bold", loc="left", pad=6)
    ax_exp_bar.set_title(
        "EXPERIMENTAL  —  historical changepoints",
        fontsize=10, fontweight="bold", loc="left", pad=6)

    fig.suptitle(
        "Method Agreement UpSet Plot  "
        "(bars = exclusive agreements; columns aligned for direct comparison)",
        fontsize=11, fontweight="bold", y=1.002,
    )

    plt.savefig(output_png, dpi=150, bbox_inches="tight")
    print(f"\nSaved merged UpSet plot → {output_png}")


# ===========================================================================
# CLI
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Three-panel stacked UpSet plot: "
            "equal_voting (top) + priority_voting (middle) + experimental (bottom). "
            "STUDENT in prod is treated as MOZILLA."
        )
    )
    parser.add_argument("--input",        "-i", required=True)
    parser.add_argument("--input-folder", "-f", required=True)
    parser.add_argument("--methods",      nargs="+", required=True)
    parser.add_argument("--margin",       "-m", type=int, default=5)
    parser.add_argument("--variant",      choices=["default", "best", "both"],
                        default="best")
    parser.add_argument("--output-png",   "-o", required=True)
    parser.add_argument("--cache-file",   default="push_id_cache.json")
    parser.add_argument("--show-zero-counts", action="store_true", default=False)
    args = parser.parse_args()

    cache = _load_cache(args.cache_file)
    print(f"Push_id cache: {args.cache_file} ({len(cache)} entries cached)")

    print(f"\nLoading prod CSV: {args.input}  margin={args.margin}")

    print("  Processing equal_voting rows …")
    combo_counts_equal, all_methods_equal, adj_stats_equal = load_combos_csv(
        args.input, "equal_voting", args.margin, cache, args.cache_file
    )
    print(f"    {sum(combo_counts_equal.values())} agreements, "
          f"{len(combo_counts_equal)} combos, "
          f"methods: {', '.join(all_methods_equal)}")

    print("  Processing priority_voting rows …")
    combo_counts_priority, all_methods_priority, adj_stats_priority = load_combos_csv(
        args.input, "priority_voting", args.margin, cache, args.cache_file
    )
    print(f"    {sum(combo_counts_priority.values())} agreements, "
          f"{len(combo_counts_priority)} combos, "
          f"methods: {', '.join(all_methods_priority)}")

    print(f"\nScanning exp folder: {args.input_folder}")
    print(f"  methods={args.methods}  variant={args.variant}  margin={args.margin}")
    combo_counts_exp, adj_stats_exp = load_combos_folder(
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

    # --- combination summaries ------------------------------------------
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

    # --- adjacency stats ------------------------------------------------
    print_adjacency_stats(adj_stats_equal,    "EQUAL VOTING",    args.margin)
    print_adjacency_stats(adj_stats_priority, "PRIORITY VOTING", args.margin)
    print_adjacency_stats(adj_stats_exp,      "EXPERIMENTAL",    args.margin)


if __name__ == "__main__":
    main()