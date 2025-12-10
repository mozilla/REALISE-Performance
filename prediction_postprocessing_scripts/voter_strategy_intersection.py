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
        # Compare to the first element of the current cluster to avoid chaining
        if p - clusters[-1][0] <= margin:
            clusters[-1].append(p)
        else:
            clusters.append([p])
    return clusters


def consolidate_method_points(points, margin, strategy="median"):
    """
    Consolidate a single method's detections:
    - Group points within margin into local clusters.
    - Replace each cluster with a representative (median | mean | first).
    """
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
    Perform robust voting among distinct CPD methods:
    1. Each method first consolidates its detections locally.
    2. Global clusters are built across all methods.
    3. Clusters supported by >= min_votes distinct methods are kept.
    """
    # Step 1: Consolidate per-method detections
    consolidated = {
        m: consolidate_method_points(cps, margin, strategy)
        for m, cps in cpd_points_dict.items()
    }

    # Flatten all consolidated detections
    all_points = sorted({p for cps in consolidated.values() for p in cps})
    if not all_points:
        return []

    # Step 2: Global clustering
    clusters = merge_close_points(all_points, margin)
    merged_cps = []

    # Step 3: Distinct-method voting
    for cluster in clusters:
        methods_involved = set()
        cluster_points = []

        for method, cps in consolidated.items():
            close_points = [p for p in cps if any(abs(p - c) <= margin for c in cluster)]
            if close_points:
                methods_involved.add(method)
                cluster_points.extend(close_points)

        if len(methods_involved) >= min_votes:
            merged_cps.append(int(round(median(cluster_points))))

    # Final cleanup and deduplication
    merged_clusters = merge_close_points(sorted(merged_cps), margin)
    merged_cps_final = [int(round(median(c))) for c in merged_clusters]
    return sorted(set(merged_cps_final))


def process_variant(ts_folder, methods, variant, out_root, min_votes, margin):
    """Process either 'default' or 'best' configurations separately."""
    # print(f"  Processing variant '{variant}'...")
    method_files = {m: [] for m in methods}

    # Load files for each method
    for m in methods:
        subdir = ts_folder / f"{variant}_{m}"
        if subdir.exists():
            for f in sorted(subdir.glob("*.json")):
                method_files[m].append(f)

    # Skip if any method is missing
    if any(len(v) == 0 for v in method_files.values()):
        print(f"    Skipping variant '{variant}', missing method results.")
        return

    combos = list(itertools.product(*method_files.values()))
    out_dir = out_root / f"{variant}_voter_merged"
    out_dir.mkdir(parents=True, exist_ok=True)

    for combo in combos:
        cpd_points = {}
        merged_args = {}
        merged_params = {}

        for method, file_path in zip(methods, combo):
            cps, sub_args, sub_params = load_json(file_path)
            cpd_points[method] = cps

            # Prefix parameters and args with method name
            for k, v in sub_args.items():
                merged_args[f"{method}_{k}"] = v
            for k, v in sub_params.items():
                merged_params[f"{method}_{k}"] = v

        merged_cps = vote_and_average(cpd_points, min_votes, margin)

        merged_json = {
            "args": {
                "methods": methods,
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

    # print(f"    Finished variant '{variant}' with {len(combos)} combinations.")


def main():
    parser = argparse.ArgumentParser(description="Voting-based CPD merger for multiple methods")
    parser.add_argument("--input-folder", "-i", required=True, help="Folder containing timeseries subfolders")
    parser.add_argument("--output-folder", "-o", required=True, help="Folder to store merged outputs")
    parser.add_argument("--methods", nargs="+", required=True, help="List of CPD method names to combine")
    parser.add_argument("--min-votes", "-v", type=int, default=3, help="Minimum number of methods voting for a CP")
    parser.add_argument("--margin", "-m", type=int, default=5, help="Allowed margin for close detections")
    args = parser.parse_args()

    input_root = Path(args.input_folder)
    output_root = Path(args.output_folder)
    output_root.mkdir(parents=True, exist_ok=True)

    for ts_folder in sorted(input_root.iterdir()):
        if not ts_folder.is_dir():
            continue
        dataset_id = ts_folder.name
        # print(f"Processing dataset {dataset_id}...")

        dataset_out = output_root / dataset_id
        dataset_out.mkdir(parents=True, exist_ok=True)

        process_variant(ts_folder, args.methods, "default", dataset_out, args.min_votes, args.margin)
        process_variant(ts_folder, args.methods, "best", dataset_out, args.min_votes, args.margin)

    print("All datasets processed successfully.")


if __name__ == "__main__":
    main()
