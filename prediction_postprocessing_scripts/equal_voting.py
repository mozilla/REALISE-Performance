#!/usr/bin/env python3
import os
import json
import argparse
import itertools
from pathlib import Path
from statistics import median


def load_json(path):
    """Load CPD result JSON file and return cps, args, and parameters."""
    with open(path, "r") as f:
        data = json.load(f)
    cps = data["result"].get("cplocations", [])
    args = data.get("args", {})
    params = data.get("parameters", {})
    return cps, args, params


def merge_close_points(points, margin):
    """Group nearby points (within margin) into clusters (no chaining)."""
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


def consolidate_method_points(points, margin, strategy="median"):
    if not points:
        return []
    clusters = merge_close_points(points, margin)
    reps = []
    for cluster in clusters:
        if strategy == "mean":
            reps.append(int(round(sum(cluster) / len(cluster))))
        elif strategy == "first":
            reps.append(cluster[0])
        else:  # median
            reps.append(int(round(median(cluster))))
    return reps


def vote_and_average(cpd_points_dict, min_votes, margin, strategy="median"):
    """
    Perform robust voting among distinct CPD methods.

    Returns:
        merged_cps_final: sorted list of final changepoint locations
        contributions: dict mapping method -> count of final CPs it contributed to
    """
    consolidated = {
        m: consolidate_method_points(cps, margin, strategy)
        for m, cps in cpd_points_dict.items()
    }

    all_points = sorted({p for cps in consolidated.values() for p in cps})
    if not all_points:
        return [], {m: 0 for m in cpd_points_dict}

    clusters = merge_close_points(all_points, margin)

    passing_clusters = []
    for cluster in clusters:
        methods_involved = set()
        cluster_points = []

        for method, cps in consolidated.items():
            close_points = [p for p in cps if any(abs(p - c) <= margin for c in cluster)]
            if close_points:
                methods_involved.add(method)
                cluster_points.extend(close_points)

        if len(methods_involved) >= min_votes:
            passing_clusters.append((int(round(median(cluster_points))), methods_involved))

    if not passing_clusters:
        return [], {m: 0 for m in cpd_points_dict}

    raw_cps = [cp for cp, _ in passing_clusters]
    merged_clusters = merge_close_points(sorted(raw_cps), margin)
    merged_cps_final = sorted(set(int(round(median(c))) for c in merged_clusters))

    contributions = {m: 0 for m in cpd_points_dict}
    for final_cp in merged_cps_final:
        methods_for_this_cp = set()
        for cp, methods_involved in passing_clusters:
            if abs(cp - final_cp) <= margin:
                methods_for_this_cp |= methods_involved
        for m in methods_for_this_cp:
            contributions[m] += 1

    return merged_cps_final, contributions


def log_standalone_table(standalone_counts, all_methods):
    """Print raw CP counts per method per variant, before any merging."""
    col_w = max(len(m) for m in all_methods) + 2
    for variant in ("default", "best"):
        counts = standalone_counts[variant]
        total = sum(counts.values())
        print(f"\n{'='*57}")
        print(f"  Standalone Raw CP Counts — variant '{variant}' — {total} total")
        print(f"{'='*57}")
        print(f"  {'Method':<{col_w}}  {'Raw CPs':>10}")
        print(f"  {'-'*col_w}  {'-'*10}")
        for method, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {method:<{col_w}}  {count:>10}")
        print(f"{'='*57}")


def log_contributions_table(global_contributions, global_total_cps, methods):
    """Print a single global contribution table across all timeseries and variants."""
    print(f"\n{'='*57}")
    print(f"  Global Contribution Summary — {global_total_cps} total final CPs")
    print(f"{'='*57}")
    col_w = max(len(m) for m in methods) + 2
    print(f"  {'Method':<{col_w}}  {'Count':>8}  {'Contribution':>13}")
    print(f"  {'-'*col_w}  {'-'*8}  {'-'*13}")
    sorted_methods = sorted(global_contributions.items(), key=lambda x: x[1], reverse=True)
    for method, count in sorted_methods:
        pct = (count / global_total_cps * 100) if global_total_cps > 0 else 0.0
        print(f"  {method:<{col_w}}  {count:>8}  {pct:>12.2f}%")
    print(f"{'='*57}\n")


def collect_standalone_counts(ts_folder, all_methods, variant, standalone_counts):
    """
    Sum raw CP counts from each method's individual JSON files for this
    timeseries folder and variant, before any merging. Mutates standalone_counts.
    """
    for m in all_methods:
        subdir = ts_folder / f"{variant}_{m}"
        if subdir.exists():
            for f in sorted(subdir.glob("*.json")):
                cps, _, _ = load_json(f)
                standalone_counts[variant][m] = standalone_counts[variant].get(m, 0) + len(cps)


def process_variant(ts_folder, methods, variant, out_root, min_votes, margin,
                    global_contributions, global_total_cps):
    """
    Process either 'default' or 'best' configurations separately.
    Accumulates contributions into the passed-in global dicts (mutates them).
    """
    method_files = {m: [] for m in methods}

    for m in methods:
        subdir = ts_folder / f"{variant}_{m}"
        if subdir.exists():
            for f in sorted(subdir.glob("*.json")):
                method_files[m].append(f)

    available_methods = {m: files for m, files in method_files.items() if len(files) > 0}
    missing_methods = [m for m, files in method_files.items() if len(files) == 0]

    if missing_methods:
        print(f"    Warning: missing results for methods {missing_methods} in variant '{variant}'")

    if len(available_methods) < min_votes:
        print(f"    Skipping variant '{variant}', not enough methods available after filtering.")
        return

    method_files = available_methods
    active_methods = list(method_files.keys())

    combos = list(itertools.product(*method_files.values()))
    out_dir = out_root / f"{variant}_voter_merged"
    out_dir.mkdir(parents=True, exist_ok=True)

    for combo in combos:
        cpd_points = {}
        merged_args = {}
        merged_params = {}

        for method, file_path in zip(active_methods, combo):
            cps, sub_args, sub_params = load_json(file_path)
            cpd_points[method] = cps

            for k, v in sub_args.items():
                merged_args[f"{method}_{k}"] = v
            for k, v in sub_params.items():
                merged_params[f"{method}_{k}"] = v

        merged_cps, contributions = vote_and_average(cpd_points, min_votes, margin)

        global_total_cps[0] += len(merged_cps)
        for m, count in contributions.items():
            global_contributions[m] = global_contributions.get(m, 0) + count

        merged_json = {
            "args": {
                "methods": active_methods,
                "min_votes": min_votes,
                "margin": margin,
                **merged_args,
            },
            "parameters": merged_params,
            "dataset": ts_folder.name,
            "result": {
                "cplocations": merged_cps,
                "runtime": None,
            },
            "status": "SUCCESS",
        }

        combo_name = "_".join(Path(f).stem for f in combo)
        output_path = out_dir / f"{combo_name}.json"
        with open(output_path, "w") as out_f:
            json.dump(merged_json, out_f, indent=4)


def main():
    parser = argparse.ArgumentParser(description="Voting-based CPD merger for multiple methods")
    parser.add_argument("--input-folder", "-i", required=True)
    parser.add_argument("--output-folder", "-o", required=True)
    parser.add_argument("--methods", nargs="+", required=True)
    parser.add_argument("--min-votes", "-v", type=int, default=3)
    parser.add_argument("--margin", "-m", type=int, default=5)
    args = parser.parse_args()

    input_root = Path(args.input_folder)
    output_root = Path(args.output_folder)
    output_root.mkdir(parents=True, exist_ok=True)

    all_methods = args.methods

    # Global accumulators for post-merge contribution table
    global_contributions = {m: 0 for m in all_methods}
    global_total_cps = [0]

    # Global accumulators for pre-merge standalone raw CP counts, split by variant
    standalone_counts = {
        "default": {m: 0 for m in all_methods},
        "best":    {m: 0 for m in all_methods},
    }

    for ts_folder in sorted(input_root.iterdir()):
        if not ts_folder.is_dir():
            continue

        dataset_out = output_root / ts_folder.name
        dataset_out.mkdir(parents=True, exist_ok=True)

        # Collect raw standalone counts before any merging
        collect_standalone_counts(ts_folder, all_methods, "default", standalone_counts)
        collect_standalone_counts(ts_folder, all_methods, "best",    standalone_counts)

        process_variant(ts_folder, all_methods, "best", dataset_out, args.min_votes, args.margin,
                        global_contributions, global_total_cps)

    # Print standalone raw counts table (split by variant)
    log_standalone_table(standalone_counts, all_methods)

    # Print post-merge contribution table
    log_contributions_table(global_contributions, global_total_cps[0], all_methods)

    print("All datasets processed successfully.")


if __name__ == "__main__":
    main()