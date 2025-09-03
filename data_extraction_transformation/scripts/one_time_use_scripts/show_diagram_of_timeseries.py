#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import argparse
import matplotlib.pyplot as plt
import matplotlib.cm as cm

# --- User ID to name mapping ---
user_id_mapping = {
    1: "REALISEAdmin",
    2: "bilel",
    3: "DiegoEliasCosta",
    4: "acreskey",
    5: "davehunt",
    6: "mayankleoboy1",
    7: "mohamedbilelbesbes",
    8: "bdekoz",
    9: "bkoz",
    10: "beatriceacasandrei",
    11: "sparky",
    12: "justinlink77",
    13: "alexfinder",
    14: "aesanu",
    15: "fbilt",
    16: "animalan"
}

def plot_timeseries_with_annotations(ts_name, ts_data, annotations, output_folder):
    """
    ts_name: name (string) of the timeseries (from file name without .json)
    ts_data: loaded JSON dict of the timeseries
    annotations: dict of userID -> list of annotation indices
    output_folder: folder path to save plot
    """
    # --- Extract timeseries values ---
    ts_values = ts_data["series"][0]["raw"]
    x_values = list(range(len(ts_values)))

    # --- Unique annotators and color map ---
    annotators = list(annotations.keys())
    cmap = cm.get_cmap('tab10', len(annotators))
    annotator_colors = {uid: cmap(i) for i, uid in enumerate(annotators)}

    # --- Plotting ---
    plt.figure(figsize=(16, 6))
    plt.scatter(x_values, ts_values, label="Raw Timeseries", color='black', s=10)

    # --- Annotator change points ---
    for uid in annotators:
        cp_list = annotations[uid]
        for idx in cp_list:
            try:
                idx = int(idx)
                plt.axvline(x=idx, color=annotator_colors[uid], linestyle='--', alpha=0.8)
            except ValueError:
                continue  # Skip if not integer
        name = user_id_mapping.get(uid, f"User_{uid}")
        plt.plot([], [], color=annotator_colors[uid], linestyle='--', label=f"{name} (ID {uid})")

    # --- Final touches ---
    plt.title(f"Timeseries: {ts_name} with Annotator Change Points", fontsize=16)
    plt.xlabel("Time Step", fontsize=14)
    plt.ylabel("Value", fontsize=14)
    plt.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
    plt.grid(True)
    plt.tight_layout()

    # --- Save plot ---
    out_path = os.path.join(output_folder, f"{ts_name}.png")
    plt.savefig(out_path, dpi=300)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Plot timeseries with human annotations")
    parser.add_argument("--input-folder", required=True, help="Folder containing timeseries JSON files")
    parser.add_argument("--annotations-file", required=True, help="Path to annotations.json file")
    parser.add_argument("--output-folder", required=True, help="Folder to save output PNG plots")
    args = parser.parse_args()

    os.makedirs(args.output_folder, exist_ok=True)

    # --- Load annotations file ---
    with open(args.annotations_file, "r") as f:
        annotations_data = json.load(f)

    # --- Loop over annotated timeseries only ---
    for ts_name, annot_dict in annotations_data.items():
        ts_file_path = os.path.join(args.input_folder, f"{ts_name}.json")
        if not os.path.exists(ts_file_path):
            print(f"Warning: JSON file for {ts_name} not found, skipping.")
            continue

        # Convert annotation keys to integers (user IDs)
        annotations_clean = {}
        for uid_str, cp_list in annot_dict.items():
            try:
                uid = int(uid_str)
                annotations_clean[uid] = cp_list
            except ValueError:
                continue

        with open(ts_file_path, "r") as f:
            ts_data = json.load(f)

        plot_timeseries_with_annotations(ts_name, ts_data, annotations_clean, args.output_folder)


if __name__ == "__main__":
    main()
