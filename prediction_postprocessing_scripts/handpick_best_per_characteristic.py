#!/usr/bin/env python3
"""
handpick_best_per_characteristic.py

Usage:
python handpick_best_per_characteristic.py \
  --input-dir /path/to/experiments \
  --summary-dir /path/to/summaries \
  --output-dir /path/to/output \
  --characteristic suite \
  --characteristics-json /path/to/characteristics.json \
  [--verbose]
"""

from pathlib import Path
import argparse
import json
import os
import shutil
from collections import defaultdict
from typing import Optional, Dict, Any


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def safe_dump_json(obj) -> str:
    return json.dumps(obj, sort_keys=True)


def strip_irrelevant_params(d: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy with keys removed that should not participate in matching."""
    if not isinstance(d, dict):
        return {}
    dd = dict(d)
    dd.pop("input", None)
    dd.pop("output", None)
    return dd


def loose_params_match(wanted: Dict[str, Any], candidate: Dict[str, Any]) -> bool:
    """
    Compare two parameter dictionaries loosely: all keys in `wanted` must be present in `candidate`
    and stringified values must match.
    """
    if not isinstance(wanted, dict) or not isinstance(candidate, dict):
        return False

    wanted_clean = strip_irrelevant_params(wanted)
    candidate_clean = strip_irrelevant_params(candidate)

    for k, v in wanted_clean.items():
        if k not in candidate_clean:
            return False
        if str(candidate_clean[k]) != str(v):
            return False
    return True


def find_taskfile_method(ts_input_dir: Path, task_file_name: str) -> Optional[str]:
    """
    Search inside ts_input_dir for the provided task_file_name.
    If found inside a folder named best_<method> or default_<method>,
    return the method string (<method>).
    """
    if not ts_input_dir.exists() or not ts_input_dir.is_dir():
        return None

    # quick direct checks
    for child in ts_input_dir.iterdir():
        if not child.is_dir():
            continue
        candidate = child / task_file_name
        if candidate.exists():
            name = child.name
            if name.startswith("best_"):
                return name[len("best_") :]
            if name.startswith("default_"):
                return name[len("default_") :]
            return name

    # recursive fallback
    for root, _, files in os.walk(ts_input_dir):
        if task_file_name in files:
            folder = Path(root).name
            if folder.startswith("best_"):
                return folder[len("best_") :]
            if folder.startswith("default_"):
                return folder[len("default_") :]
            return folder
    return None


def find_experiment_by_params_in_dir(exp_dir: Path, wanted_params: Dict[str, Any], verbose=False) -> Optional[Path]:
    """
    Search for a JSON experiment file inside exp_dir whose `parameters` or `args` match wanted_params
    using loose_params_match. Return path to file if found.
    """
    if not exp_dir.exists() or not exp_dir.is_dir():
        return None

    for fp in exp_dir.glob("*.json"):
        try:
            data = load_json(fp)
        except Exception:
            if verbose:
                print(f"[WARN] cannot load experiment json {fp}")
            continue

        candidate_params = data.get("parameters") or data.get("args") or {}
        if loose_params_match(wanted_params, candidate_params):
            return fp

    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True,
                        help="Directory containing raw experiment result JSON files (folders named by timeseries id).")
    parser.add_argument("--summary-dir", required=True,
                        help="Directory containing summary_<tsid>.json files (one per timeseries).")
    parser.add_argument("--output-dir", required=True,
                        help="Directory where best-per-characteristic results will be copied.")
    parser.add_argument("--characteristic", required=True,
                        help="Characteristic to use (e.g., suite, platform, repository, test).")
    parser.add_argument("--characteristics-json", required=True,
                        help="JSON mapping timeseries id -> characteristic dict (e.g. {\"2780728\": {\"suite\":\"decision\"}, ...}).")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    summary_dir = Path(args.summary_dir)
    output_dir = Path(args.output_dir)
    characteristic = args.characteristic
    char_json_path = Path(args.characteristics_json)
    verbose = args.verbose

    # Validate inputs
    if not input_dir.exists() or not input_dir.is_dir():
        raise SystemExit(f"input-dir not found or not a directory: {input_dir}")
    if not summary_dir.exists() or not summary_dir.is_dir():
        raise SystemExit(f"summary-dir not found or not a directory: {summary_dir}")
    if not char_json_path.exists():
        raise SystemExit(f"characteristics json not found: {char_json_path}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load characteristics mapping
    char_map = load_json(char_json_path)

    # ------------------------------------------------------------------
    # STEP A: Aggregate F1 scores per (characteristic_value, method, params)
    # ------------------------------------------------------------------
    per_char_method_params_f1 = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    # per_char_method_params_f1[char_value][method][params_json] -> [f1, ...]

    # iterate summary files
    for summary_file in summary_dir.iterdir():
        if not summary_file.is_file():
            continue
        if not summary_file.name.startswith("summary_") or not summary_file.name.endswith(".json"):
            continue

        try:
            summary = load_json(summary_file)
        except Exception as e:
            if verbose:
                print(f"[WARN] failed to load {summary_file}: {e}")
            continue

        ts_id = str(summary.get("dataset") or summary_file.name.replace("summary_", "").replace(".json", ""))
        if ts_id not in char_map:
            if verbose:
                print(f"[INFO] timeseries {ts_id} not in characteristics map -> skipping")
            continue

        # Get characteristic value; if None use the string "null"
        raw_char_value = char_map[ts_id].get(characteristic)
        char_value = raw_char_value if raw_char_value is not None else "null"
        if raw_char_value is None and verbose:
            print(f"[INFO] timeseries {ts_id} has the characteristic '{characteristic}' as None -> treating as 'null' group")

        # extract results
        results_obj = summary.get("results", {})
        if not isinstance(results_obj, dict):
            continue

        ts_input_dir = input_dir / ts_id

        for voter_key, entries in results_obj.items():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                scores = entry.get("scores") or {}
                f1 = scores.get("f1")
                if f1 is None:
                    continue

                # prefer "parameters" then "args"
                params = entry.get("parameters") or entry.get("args") or {}
                task_file = entry.get("task_file")

                # determine method by task_file lookup
                method = None
                if task_file:
                    method = find_taskfile_method(ts_input_dir, task_file)
                    if method is None and verbose:
                        print(f"[INFO] task_file {task_file} for ts {ts_id} not found under {ts_input_dir}")
                if method is None:
                    # skip entries we cannot attribute to a method
                    continue

                params_key = safe_dump_json(strip_irrelevant_params(params))
                per_char_method_params_f1[char_value][method][params_key].append(float(f1))

    if verbose:
        print("Finished aggregating F1 scores per characteristic-method-params.")

    # ------------------------------------------------------------------
    # Compute best params per method for each characteristic
    # ------------------------------------------------------------------
    best_params_per_char = {}  # best_params_per_char[char_value][method] = {"params":..., "avg_f1":...}
    for char_value, method_dict in per_char_method_params_f1.items():
        # char_value is already "null" for None cases
        best_params_per_char[char_value] = {}
        for method, params_dict in method_dict.items():
            best_avg = -1.0
            best_params = None
            for params_key, f1_list in params_dict.items():
                avg = sum(f1_list) / len(f1_list)
                if avg > best_avg:
                    best_avg = avg
                    try:
                        best_params = json.loads(params_key)
                    except Exception:
                        best_params = {}
            if best_params is not None:
                best_params_per_char[char_value][method] = {"params": best_params, "avg_f1": best_avg}

    if verbose:
        print("Best params per characteristic computed:")
        for ch, md in best_params_per_char.items():
            print(f"  char={ch}: methods={list(md.keys())}")

    # ------------------------------------------------------------------
    # STEP B: For each timeseries folder, copy default_ and best_ accordingly
    # ------------------------------------------------------------------
    for ts_folder in input_dir.iterdir():
        if not ts_folder.is_dir():
            continue
        ts_id = ts_folder.name
        if ts_id not in char_map:
            if verbose:
                print(f"[INFO] timeseries {ts_id} missing in characteristics map — skipping copying")
            continue

        raw_char_value = char_map[ts_id].get(characteristic)
        char_value = raw_char_value if raw_char_value is not None else "null"
        if raw_char_value is None and verbose:
            print(f"[INFO] timeseries {ts_id} has the characteristic '{characteristic}' as None -> treating as 'null' group")

        out_ts_dir = output_dir / ts_id
        out_ts_dir.mkdir(parents=True, exist_ok=True)

        # discover method names from folder prefixes
        folder_names = [p.name for p in ts_folder.iterdir() if p.is_dir()]
        methods = set()
        for name in folder_names:
            if name.startswith("best_"):
                methods.add(name[len("best_"):])
            elif name.startswith("default_"):
                methods.add(name[len("default_"):])

        if not methods:
            if verbose:
                print(f"[WARN] no method folders found inside {ts_folder} (expected best_/default_ prefixed folders).")
            # ensure placeholder to avoid empty dir
            (out_ts_dir / ".placeholder").write_text("no method folders found\n")
            continue

        for method in methods:
            src_default = ts_folder / f"default_{method}"
            dst_default = out_ts_dir / f"default_{method}"
            if src_default.exists():
                try:
                    shutil.copytree(src_default, dst_default, dirs_exist_ok=True)
                    if verbose:
                        print(f"Copied default folder {src_default} -> {dst_default}")
                except Exception as e:
                    print(f"[ERROR] copying default folder {src_default}: {e}")

            src_best = ts_folder / f"best_{method}"
            dst_best = out_ts_dir / f"best_{method}"
            dst_best.mkdir(parents=True, exist_ok=True)

            method_best_info = best_params_per_char.get(char_value, {}).get(method)
            if method_best_info is None:
                if verbose:
                    print(f"[INFO] No best params computed for char={char_value}, method={method}. leaving best_{method} empty.")
                continue

            # remove input/output before matching
            wanted_params = strip_irrelevant_params(method_best_info["params"])

            matched = find_experiment_by_params_in_dir(src_best, wanted_params, verbose=verbose)
            if matched:
                try:
                    shutil.copy2(matched, dst_best / matched.name)
                    if verbose:
                        print(f"Copied best experiment {matched} -> {dst_best}")
                except Exception as e:
                    print(f"[ERROR] copying matched file {matched}: {e}")
            else:
                if verbose:
                    print(f"[WARN] No matching experiment file found in {src_best} for ts={ts_id} method={method} matching params={wanted_params}")

        # ensure output ts folder not empty: if it ends up empty, create a .placeholder
        if not any(out_ts_dir.iterdir()):
            (out_ts_dir / ".placeholder").write_text("no files copied for this timeseries\n")

    print("All done.")


if __name__ == "__main__":
    main()
