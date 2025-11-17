#!/usr/bin/env python3
import os
import json
import argparse
import itertools
from pathlib import Path


def load_json(path):
    """Load CPD result JSON file and return cps, args, and parameters."""
    with open(path, "r") as f:
        data = json.load(f)
    cps = data["result"].get("cplocations", [])
    args = data.get("args", {})
    params = data.get("parameters", {})
    return cps, args, params


def merge_close_points(points, margin):
    """Group nearby points (within margin) into clusters using centroid-based merging."""
    if not points:
        return []
    points = sorted(points)
    clusters = [[points[0]]]
    for p in points[1:]:
        cluster_center = sum(clusters[-1]) / len(clusters[-1])
        if abs(p - cluster_center) <= margin:
            clusters[-1].append(p)
        else:
            clusters.append([p])
    return clusters


def vote_and_average_with_veto(cpd_points_dict, veto_points, min_votes, margin):
    """
    Combine CP detections with a veto method (high-precision detector).
    - veto_points: list of CPs from the veto method.
    - cpd_points_dict: dict {method_name: [list of CPs]} for other methods.
    """
    merged_cps = set(veto_points)  # veto method’s CPs are always included

    # Gather all points from other methods
    all_points = sorted(set(p for cps in cpd_points_dict.values() for p in cps))
    if not all_points:
        return sorted(list(merged_cps))

    # Cluster them
    clusters = merge_close_points(all_points, margin)

    # Vote within clusters
    for cluster in clusters:
        members = []
        methods_involved = set()
        for method, cps in cpd_points_dict.items():
            close_points = [p for p in cps if any(abs(p - c) <= margin for c in cluster)]
            if close_points:
                members.extend(close_points)
                methods_involved.add(method)

        if len(methods_involved) >= min_votes:
            avg_cp = int(round(sum(members) / len(members)))

            # avoid duplication with veto CPs
            if not any(abs(avg_cp - v) <= margin for v in veto_points):
                merged_cps.add(avg_cp)

    return sorted(list(merged_cps))


def process_variant(ts_folder, methods, veto_method, variant, out_root, min_votes, margin):
    """Process either 'default' or 'best' configurations."""
    print(f"  Processing variant '{variant}'...")

    # Separate veto and regular methods
    all_methods = set(methods + [veto_method])
    method_files = {m: [] for m in all_methods}

    # Load method result files
    for m in all_methods:
        subdir = ts_folder / f"{variant}_{m}"
        if subdir.exists():
            for f in sorted(subdir.glob("*.json")):
                method_files[m].append(f)

    # Skip dataset if veto method missing
    if not method_files[veto_method]:
        print(f"    Skipping '{variant}' — veto method '{veto_method}' missing results.")
        return

    # Skip datasets missing some voting methods
    if any(len(v) == 0 for m, v in method_files.items() if m != veto_method):
        print(f"    Skipping '{variant}' — some voting methods missing results.")
        return

    combos = list(itertools.product(*[method_files[m] for m in methods]))
    veto_files = method_files[veto_method]
    out_dir = out_root / f"{variant}_veto_merged"
    out_dir.mkdir(parents=True, exist_ok=True)

    for veto_file in veto_files:
        veto_cps, veto_args, veto_params = load_json(veto_file)

        for combo in combos:
            cpd_points = {}
            merged_args = {}
            merged_params = {}

            for method, file_path in zip(methods, combo):
                cps, sub_args, sub_params = load_json(file_path)
                cpd_points[method] = cps

                # Prefix args/params
                for k, v in sub_args.items():
                    merged_args[f"{method}_{k}"] = v
                for k, v in sub_params.items():
                    merged_params[f"{method}_{k}"] = v

            # Add veto method args/params
            for k, v in veto_args.items():
                merged_args[f"{veto_method}_{k}"] = v
            for k, v in veto_params.items():
                merged_params[f"{veto_method}_{k}"] = v

            merged_cps = vote_and_average_with_veto(cpd_points, veto_cps, min_votes, margin)

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
            veto_name = Path(veto_file).stem
            output_path = out_dir / f"{veto_name}__{combo_name}.json"

            with open(output_path, "w") as out_f:
                json.dump(merged_json, out_f, indent=4)

    print(f"    Finished variant '{variant}' with {len(veto_files) * len(combos)} combinations.")
 

def main():
    parser = argparse.ArgumentParser(description="Voting-based CPD merger with veto method support")
    parser.add_argument("--input-folder", "-i", required=True, help="Folder containing timeseries subfolders")
    parser.add_argument("--output-folder", "-o", required=True, help="Folder to store merged outputs")
    parser.add_argument("--methods", nargs="+", required=True, help="List of CPD method names to combine (excluding veto)")
    parser.add_argument("--veto-method", required=True, help="High-precision veto method whose CPs are always kept")
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
        print(f"Processing dataset {dataset_id}...")

        dataset_out = output_root / dataset_id
        dataset_out.mkdir(parents=True, exist_ok=True)

        process_variant(ts_folder, args.methods, args.veto_method, "default", dataset_out, args.min_votes, args.margin)
        process_variant(ts_folder, args.methods, args.veto_method, "best", dataset_out, args.min_votes, args.margin)

    print("✅ All datasets processed successfully.")


if __name__ == "__main__":
    main()
