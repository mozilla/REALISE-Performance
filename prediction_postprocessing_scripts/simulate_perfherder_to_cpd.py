import os
import json
import random
import string
import argparse
from pathlib import Path
import csv
from collections import Counter

def random_hash(length=16):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def load_annotations(path):
    with open(path, 'r') as f:
        return json.load(f)

def ensure_dirs(output_base, timeseries_id):
    root = Path(output_base) / timeseries_id
    default_dir = root / "default_perfherder"
    best_dir = root / "best_perfherder"
    default_dir.mkdir(parents=True, exist_ok=True)
    best_dir.mkdir(parents=True, exist_ok=True)
    return default_dir, best_dir

def build_perfherder_json(timeseries_id, cplocations, alert_counts):
    return {
        "args": {},
        "command": "No command",
        "dataset": str(timeseries_id),
        "dataset_md5": str(timeseries_id),
        "error": None,
        "hostname": "No host",
        "parameters": {},
        "result": {
            "cplocations": cplocations,
            "runtime": 0.0
        },
        "script": "No script",
        "script_md5": str(timeseries_id),
        "status": "SUCCESS"
    }

def process_csv_file(csv_path, annotations, output_base):
    fname = os.path.basename(csv_path)
    if not fname.endswith("_timeseries_data.csv"):
        return
    timeseries_id = fname.split("_")[0]
    if timeseries_id not in annotations:
        return  # skip if not annotated

    default_dir, best_dir = ensure_dirs(output_base, timeseries_id)

    # Collect indices where alert_summary_status_general is SP, TP, or FP
    cplocations = []
    alert_summary = []
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for idx, row in enumerate(reader):
            status = row.get("alert_summary_status_general", "").strip()
            if status in {"SP", "TP", "FP"}:
                cplocations.append(idx)
            alert_summary.append(status)
    label_counts = Counter(alert_summary)

    # Build JSON and write to both folders
    for out_dir in (default_dir, best_dir):
        data = build_perfherder_json(timeseries_id, cplocations, dict(label_counts))
        # Optionally store the summary counts under parameters for traceability
        data["parameters"]["alert_summary_counts"] = dict(label_counts)
        hashname = random_hash() + ".json"
        out_path = out_dir / hashname
        with open(out_path, "w") as f:
            json.dump(data, f, indent=4)
        print(f"Wrote JSON for timeseries {timeseries_id} -> {out_path}")

def walk_and_process(csv_root, annotations_path, output_base):
    if not os.path.isfile(annotations_path):
        raise FileNotFoundError(f"annotations.json not found at {annotations_path}")
    annotations = load_annotations(annotations_path)

    # Ensure output base exists
    Path(output_base).mkdir(parents=True, exist_ok=True)

    for dirpath, _, filenames in os.walk(csv_root):
        for fn in filenames:
            if fn.endswith("_timeseries_data.csv"):
                csv_path = os.path.join(dirpath, fn)
                try:
                    process_csv_file(csv_path, annotations, output_base)
                except Exception as e:
                    print(f"Error processing {csv_path}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate perfherder JSONs from CSVs + annotations")
    parser.add_argument("--annotations", required=True, help="Path to annotations.json")
    parser.add_argument("--csv-root", required=True, help="Root folder containing subfolders with CSVs")
    parser.add_argument("--output-base", required=True, help="Where to emit <timeseries_id> directories")
    args = parser.parse_args()

    walk_and_process(args.csv_root, args.annotations, args.output_base)
