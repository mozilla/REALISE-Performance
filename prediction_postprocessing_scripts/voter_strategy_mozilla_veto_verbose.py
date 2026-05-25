#!/usr/bin/env python3
import json
import argparse
import itertools
from pathlib import Path


def load_json(path):
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


def vote_and_average_with_veto(cpd_points_dict, veto_points, veto_method, min_votes, margin):
    """
    Combine CP detections with a veto method (high-precision detector).
    - veto_points: CPs from the veto method — always included in the output.
    - cpd_points_dict: {method_name: [CPs]} for the voting methods.
    - Voting methods can also create CPs independently if >= min_votes agree,
      even without the veto method firing.

    Returns:
        merged_cps: sorted list of final changepoint locations
        contributions: dict mapping every method (including veto) -> count of
                       final CPs it contributed to. Each method counted at most
                       once per final CP so percentages stay <= 100%.
    """
    cp_to_methods = {}

    for v in veto_points:
        cp_to_methods[v] = {veto_method}

    all_points = sorted(set(p for cps in cpd_points_dict.values() for p in cps))
    if all_points:
        clusters = merge_close_points(all_points, margin)

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

                matching_veto = [v for v in veto_points if abs(avg_cp - v) <= margin]
                if matching_veto:
                    cp_to_methods[matching_veto[0]] |= methods_involved
                else:
                    matching_existing = [
                        cp for cp in cp_to_methods
                        if abs(avg_cp - cp) <= margin and veto_method not in cp_to_methods[cp]
                    ]
                    if matching_existing:
                        cp_to_methods[matching_existing[0]] |= methods_involved
                    else:
                        cp_to_methods[avg_cp] = methods_involved

    merged_cps = sorted(cp_to_methods.keys())

    all_methods = set(cpd_points_dict.keys()) | {veto_method}
    contributions = {m: 0 for m in all_methods}
    for methods in cp_to_methods.values():
        for m in methods:
            contributions[m] += 1

    return merged_cps, contributions


def log_contributions_table(global_contributions, global_total_cps):
    """Print the post-merging contribution table."""
    print(f"\n{'='*57}")
    print(f"  Global Contribution Summary — {global_total_cps} total final CPs")
    print(f"{'='*57}")
    col_w = max(len(m) for m in global_contributions) + 2
    print(f"  {'Method':<{col_w}}  {'Count':>8}  {'Contribution':>13}")
    print(f"  {'-'*col_w}  {'-'*8}  {'-'*13}")
    for method, count in sorted(global_contributions.items(), key=lambda x: x[1], reverse=True):
        pct = (count / global_total_cps * 100) if global_total_cps > 0 else 0.0
        print(f"  {method:<{col_w}}  {count:>8}  {pct:>12.2f}%")
    print(f"{'='*57}\n")


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


def collect_standalone_counts(ts_folder, all_methods, variant, standalone_counts):
    """
    For each method, sum the raw CP count across all its JSON files
    in this timeseries folder for the given variant. Accumulates into
    standalone_counts[variant][method].
    """
    for m in all_methods:
        subdir = ts_folder / f"{variant}_{m}"
        if subdir.exists():
            for f in sorted(subdir.glob("*.json")):
                cps, _, _ = load_json(f)
                standalone_counts[variant][m] = standalone_counts[variant].get(m, 0) + len(cps)


def process_variant(ts_folder, methods, veto_method, variant, out_root, min_votes, margin,
                    global_contributions, global_total_cps):
    """Process either 'default' or 'best' configurations."""
    all_methods = set(methods + [veto_method])
    method_files = {m: [] for m in all_methods}

    for m in all_methods:
        subdir = ts_folder / f"{variant}_{m}"
        if subdir.exists():
            for f in sorted(subdir.glob("*.json")):
                method_files[m].append(f)

    if not method_files[veto_method]:
        print(f"    Skipping '{variant}' — dataset '{ts_folder}' veto method '{veto_method}' missing results.")
        return

    if any(len(v) == 0 for m, v in method_files.items() if m != veto_method):
        print(f"    Dataset '{ts_folder}' skipping '{variant}' — some voting methods missing results.")
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
                for k, v in sub_args.items():
                    merged_args[f"{method}_{k}"] = v
                for k, v in sub_params.items():
                    merged_params[f"{method}_{k}"] = v

            for k, v in veto_args.items():
                merged_args[f"{veto_method}_{k}"] = v
            for k, v in veto_params.items():
                merged_params[f"{veto_method}_{k}"] = v

            merged_cps, contributions = vote_and_average_with_veto(
                cpd_points, veto_cps, veto_method, min_votes, margin
            )

            global_total_cps[0] += len(merged_cps)
            for m, count in contributions.items():
                global_contributions[m] = global_contributions.get(m, 0) + count

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


def main():
    parser = argparse.ArgumentParser(description="Voting-based CPD merger with veto method support")
    parser.add_argument("--input-folder", "-i", required=True)
    parser.add_argument("--output-folder", "-o", required=True)
    parser.add_argument("--methods", nargs="+", required=True)
    parser.add_argument("--veto-method", required=True)
    parser.add_argument("--min-votes", "-v", type=int, default=3)
    parser.add_argument("--margin", "-m", type=int, default=5)
    args = parser.parse_args()

    input_root = Path(args.input_folder)
    output_root = Path(args.output_folder)
    output_root.mkdir(parents=True, exist_ok=True)
    print(f"Starting voting-based CPD merging with veto method... for '{args.input_folder}'")

    all_methods = args.methods + [args.veto_method]

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

        process_variant(ts_folder, args.methods, args.veto_method, "default", dataset_out,
                        args.min_votes, args.margin, global_contributions, global_total_cps)
        process_variant(ts_folder, args.methods, args.veto_method, "best", dataset_out,
                        args.min_votes, args.margin, global_contributions, global_total_cps)

    # Print standalone raw counts table (split by variant)
    log_standalone_table(standalone_counts, all_methods)

    # Print post-merge contribution table
    log_contributions_table(global_contributions, global_total_cps[0])

    print("All datasets processed successfully.")


if __name__ == "__main__":
    main()