#!/usr/bin/env python3
"""
handpick_best_voting_config.py

Finds the best joint hyperparameter configuration for a voting system of
change point detection methods. Specifically:

  - Shared across all methods : (max_back_window, min_back_window, fore_window)
  - Per method                 : all remaining args keys after removing the shared
                                 window keys and known non-tunable keys (input,
                                 output, method, signatures_attributes, etc.)
                                 This handles method-specific naming (e.g. alpha
                                 vs t_threshold) automatically.

Algorithm
---------
1. Parse all summary JSONs (any *.json in --summary-dir) to collect, for every
   (ts_id, method, window_triplet, frozen_per_method_params), the F1 score.
   Method names are derived directly from the summary result keys (best_<method>).
   Only methods listed in --methods are considered.

2. For each unique window triplet W:
     For each cartesian-product assignment P of {method -> (alpha, alert_threshold)}:
       grand_mean_F1 = mean over all (method, ts) pairs that have data for (W, P[method])
     best_P_for_W  = argmax over P of grand_mean_F1
     best_score[W] = that grand_mean_F1

3. W* = argmax over W of best_score[W]
   P* = best_P_for_W*

4. For each ts, copy:
     - best_<method>/<task_file>  for the winning (W*, P*[method]) config
     - default_<method>/<task_file> verbatim
   mirroring the structure of handpick_best.py.

Usage:
    python handpick_best_voting_config.py \
      --input-dir   /path/to/experiments \
      --summary-dir /path/to/summaries \
      --output-dir  /path/to/output \
      --methods cvm_advanced mwu_advanced welch_advanced student_advanced \
      [--failure-threshold 0.05] \
      [--verbose]
"""

from pathlib import Path
from itertools import product
import argparse
import json
import os
import shutil
from collections import defaultdict
from typing import Optional, Dict, Any, Tuple, List


WINDOW_KEYS = ("max_back_window", "min_back_window", "fore_window")

# Keys in args that are NOT tunable hyperparameters and should be ignored
ARGS_BLOCKLIST = frozenset({
    "input", "output", "method", "signatures_attributes",
})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_window_triplet(args_dict: Dict[str, Any]) -> Optional[Tuple]:
    """Return (max_back_window, min_back_window, fore_window) or None if any key is missing."""
    try:
        return tuple(args_dict[k] for k in WINDOW_KEYS)
    except KeyError:
        return None


def extract_per_method_params(args_dict: Dict[str, Any]) -> Optional[tuple]:
    """Return a sorted, frozen tuple of (key, value) pairs for all tunable
    per-method params — i.e. everything in args except the shared window keys
    and the known non-tunable blocklist keys.
    Returns None if no tunable params are found."""
    skip = set(WINDOW_KEYS) | ARGS_BLOCKLIST
    tunable = tuple(sorted(
        (k, v) for k, v in args_dict.items() if k not in skip
    ))
    return tunable if tunable else None


def copy_file(input_path: str, output_path: str) -> None:
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        shutil.copy2(input_path, output_path)
    except FileNotFoundError:
        print(f"[ERROR] Input file not found: '{input_path}'")
    except PermissionError:
        print(f"[ERROR] Permission denied copying: '{input_path}'")
    except Exception as e:
        print(f"[ERROR] copying file: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True,
                        help="Directory of raw experiment result folders (named by timeseries id).")
    parser.add_argument("--summary-dir", required=True,
                        help="Directory containing summary JSON files (any *.json).")
    parser.add_argument("--output-dir", required=True,
                        help="Directory where winning experiment files will be copied.")
    parser.add_argument("--methods", required=True, nargs="+",
                        help="Methods to include in the voting system (e.g. --methods cvm ttest mwu welch). "
                             "Each value must match the <method> part of best_<method> keys in the summary JSONs.")
    parser.add_argument("--failure-threshold", type=float, default=0.05,
                        help="Max fraction of datasets allowed to be missing for a config to be considered (default: 0.05).")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    input_dir         = Path(args.input_dir)
    summary_dir       = Path(args.summary_dir)
    output_dir        = Path(args.output_dir)
    methods_filter    = set(args.methods)
    failure_threshold = args.failure_threshold
    verbose           = args.verbose

    for p, label in [(input_dir, "input-dir"), (summary_dir, "summary-dir")]:
        if not p.exists():
            raise SystemExit(f"[ERROR] {label} not found: {p}")
    output_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"Methods restricted to: {sorted(methods_filter)}")

    # ------------------------------------------------------------------
    # STEP 1 – Load all summary JSONs
    # ------------------------------------------------------------------
    datasets_metrics: List[Dict] = []
    for summary_file in sorted(summary_dir.iterdir()):
        if not summary_file.is_file() or summary_file.suffix != ".json":
            continue
        try:
            datasets_metrics.append(load_json(summary_file))
        except Exception as e:
            if verbose:
                print(f"[WARN] failed to load {summary_file}: {e}")

    if not datasets_metrics:
        raise SystemExit("[ERROR] No summary JSON files found in --summary-dir.")

    nb_datasets = len(datasets_metrics)
    nb_datasets_threshold = nb_datasets * (1.0 - failure_threshold)

    if verbose:
        print(f"Loaded {nb_datasets} summary files. Min dataset count threshold: {nb_datasets_threshold:.1f}")

    # ------------------------------------------------------------------
    # STEP 2 – Collect F1 scores and task file paths from summaries
    # ------------------------------------------------------------------
    # f1_table[(ts_id, method, window_triplet, per_method_params)] = f1
    # per_method_params is a sorted tuple of (key, value) pairs for all
    # tunable args (everything except window keys and blocklisted keys)
    f1_table: Dict[Tuple, float] = {}

    # task_file_index[(ts_id, method, window_triplet, per_method_params)] = task_file name
    task_file_index: Dict[Tuple, str] = {}

    # default_task_files[(ts_id, method)] = task_file name
    default_task_files: Dict[Tuple, str] = {}

    # per_method_params_seen[method] = set of per_method_params tuples
    per_method_params_seen: Dict[str, set] = defaultdict(set)

    for dataset_metrics in datasets_metrics:
        ts_id = str(dataset_metrics.get("dataset", ""))
        if not ts_id:
            if verbose:
                print("[WARN] summary entry missing 'dataset' field, skipping")
            continue

        results = dataset_metrics.get("results", {})
        if not isinstance(results, dict):
            continue

        # Collect default task files (one entry per default method per ts)
        for key, entries in results.items():
            if not key.startswith("default_"):
                continue
            method = key[len("default_"):]
            if method not in methods_filter:
                continue
            if not isinstance(entries, list) or not entries:
                continue
            task_file = entries[0].get("task_file")
            if task_file:
                default_task_files[(ts_id, method)] = task_file

        # Collect best entries (all hyperparameter configurations)
        for key, entries in results.items():
            if not key.startswith("best_"):
                continue
            method = key[len("best_"):]
            if method not in methods_filter:
                continue
            if not isinstance(entries, list):
                continue

            for entry in entries:
                if entry.get("status") != "SUCCESS":
                    continue

                scores = entry.get("scores") or {}
                f1 = scores.get("f1")
                if f1 is None:
                    continue

                args_dict = entry.get("args") or {}
                task_file = entry.get("task_file")

                window = extract_window_triplet(args_dict)
                per_method = extract_per_method_params(args_dict)

                if window is None or per_method is None:
                    if verbose:
                        print(f"[INFO] missing window or tunable params in ts={ts_id} "
                              f"method={method}, skipping entry")
                    continue

                lookup_key = (ts_id, method, window, per_method)
                f1_table[lookup_key] = float(f1)
                if task_file:
                    task_file_index[lookup_key] = task_file
                per_method_params_seen[method].add(per_method)

    if not f1_table:
        raise SystemExit("[ERROR] No F1 data collected. Check --summary-dir and --methods.")

    if verbose:
        print(f"Collected {len(f1_table)} (ts, method, window, per_method_params) F1 entries.")
        for m, params in sorted(per_method_params_seen.items()):
            print(f"  {m}: tunable param combos ({len(params)}):")
            for p in sorted(params)[:5]:
                print(f"    {dict(p)}")
            if len(params) > 5:
                print(f"    ... and {len(params) - 5} more")

    methods_list = sorted(methods_filter & set(per_method_params_seen.keys()))

    if not methods_list:
        raise SystemExit("[ERROR] None of the specified --methods were found in the summary files.")

    # ------------------------------------------------------------------
    # STEP 3 – For each window, independently find the best per-method
    #          param combo (by mean F1 across datasets), then score the
    #          window as the average of those per-method best F1s.
    #          Pick the window with the highest score.
    #
    #          This is equivalent to running the old handpick_best script
    #          once per window and averaging the "Best F1" across methods.
    # ------------------------------------------------------------------
    import time

    all_windows: List[Tuple] = sorted({key[2] for key in f1_table})

    print(f"\n[STEP 3] Search space: {len(all_windows)} windows, "
          f"each solved independently per method (no cartesian product)")
    print(f"         Methods: {methods_list}")
    print(f"         Per-method param combos (before coverage filter):")
    for m in methods_list:
        print(f"           {m}: {len(per_method_params_seen[m])} combos")

    best_global_score   = -1.0
    best_global_window: Optional[Tuple] = None
    best_global_params: Optional[Dict[str, tuple]] = None  # method -> best per_method_params tuple

    search_start = time.time()

    for w_idx, window in enumerate(all_windows):
        window_start = time.time()

        # For each method: find the param combo with the highest mean F1
        # across datasets, subject to the coverage filter (mirrors process_best).
        best_params_for_window: Dict[str, tuple] = {}
        per_method_best_f1:     Dict[str, float] = {}

        for method in methods_list:
            # Collect all F1 values per param combo for this (method, window)
            combo_f1s: Dict[tuple, List[float]] = defaultdict(list)
            for key, f1 in f1_table.items():
                _, method_, window_, combo_ = key
                if method_ == method and window_ == window:
                    combo_f1s[combo_].append(f1)

            # Apply coverage filter
            eligible = {
                combo: f1s
                for combo, f1s in combo_f1s.items()
                if len(f1s) > nb_datasets_threshold
            }

            if not eligible:
                if verbose:
                    print(f"    {method}: no combos pass coverage filter for window={window}")
                continue

            # Pick the combo with the highest mean F1
            best_combo    = max(eligible, key=lambda c: sum(eligible[c]) / len(eligible[c]))
            best_mean_f1  = sum(eligible[best_combo]) / len(eligible[best_combo])

            best_params_for_window[method] = best_combo
            per_method_best_f1[method]     = best_mean_f1

            if verbose:
                print(f"    {method}: best combo={dict(best_combo)}  "
                      f"mean_f1={best_mean_f1:.4f}  "
                      f"(over {len(eligible[best_combo])} datasets)",
                      flush=True)

        if not per_method_best_f1:
            print(f"  [{w_idx+1}/{len(all_windows)}] window={window} -> skipped "
                  f"(no method has eligible combos)")
            continue

        # Window score = average of per-method best F1s
        window_score   = sum(per_method_best_f1.values()) / len(per_method_best_f1)
        window_elapsed = time.time() - window_start

        print(f"  [{w_idx+1}/{len(all_windows)}] window={window} -> "
              f"avg_best_f1={window_score:.4f}  "
              f"({len(per_method_best_f1)}/{len(methods_list)} methods eligible, "
              f"{window_elapsed:.2f}s)  "
              f"per-method: { {m: f'{v:.4f}' for m, v in per_method_best_f1.items()} }",
              flush=True)

        if window_score > best_global_score:
            best_global_score  = window_score
            best_global_window = window
            best_global_params = best_params_for_window

    total_elapsed = time.time() - search_start
    print(f"\n[STEP 3] Done in {total_elapsed:.1f}s")


    if best_global_window is None or best_global_params is None:
        raise SystemExit("[ERROR] Could not determine a winning configuration.")

    print("\n=== Winning configuration ===")
    print(f"  max_back_window  : {best_global_window[0]}")
    print(f"  min_back_window  : {best_global_window[1]}")
    print(f"  fore_window      : {best_global_window[2]}")
    print(f"  grand mean F1    : {best_global_score:.4f}")
    print("  per-method tunable params:")
    for method, combo in sorted(best_global_params.items()):
        print(f"    {method}: {dict(combo)}")

    # ------------------------------------------------------------------
    # STEP 4 – Build path lists and copy files
    # ------------------------------------------------------------------
    best_paths: List[str]    = []
    default_paths: List[str] = []

    all_ts_ids = {str(d.get("dataset", "")) for d in datasets_metrics if d.get("dataset")}

    for ts_id in sorted(all_ts_ids):
        for method, combo in best_global_params.items():
            lookup_key = (ts_id, method, best_global_window, combo)
            task_file = task_file_index.get(lookup_key)
            if task_file:
                best_paths.append(f"{ts_id}/best_{method}/{task_file}")
            elif verbose:
                print(f"[WARN] no task_file for ts={ts_id} method={method} "
                      f"window={best_global_window} params={dict(combo)}")

        for method in sorted(methods_filter):
            task_file = default_task_files.get((ts_id, method))
            if task_file:
                default_paths.append(f"{ts_id}/default_{method}/{task_file}")

    if verbose:
        print(f"\nBest paths to copy   : {len(best_paths)}")
        print(f"Default paths to copy: {len(default_paths)}")

    for rel_path in best_paths:
        copy_file(str(input_dir / rel_path), str(output_dir / rel_path))

    for rel_path in default_paths:
        copy_file(str(input_dir / rel_path), str(output_dir / rel_path))

    # ------------------------------------------------------------------
    # STEP 5 – Write winning config JSON
    # ------------------------------------------------------------------
    winning_summary = {
        "grand_mean_f1": best_global_score,
        "window": {k: best_global_window[i] for i, k in enumerate(WINDOW_KEYS)},
        "per_method_params": {
            method: dict(combo)
            for method, combo in best_global_params.items()
        },
    }
    summary_out = output_dir / "winning_config.json"
    with summary_out.open("w", encoding="utf-8") as f:
        json.dump(winning_summary, f, indent=2, sort_keys=True)

    print(f"\nWinning config written to {summary_out}")
    print("All done.")


if __name__ == "__main__":
    main()