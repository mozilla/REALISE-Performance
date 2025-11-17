#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extract sub-subfolders matching given suffixes from baseline_folder into dest_folder.
Each ID folder in baseline_folder has multiple sub-subfolders, and only those
ending with the given suffixes (e.g., "mozilla_rep", "mozilla_rework") are copied.
"""

import argparse
import os
import shutil


def extract_subfolders(baseline_folder, dest_folder, suffixes):
    # Ensure destination folder exists
    os.makedirs(dest_folder, exist_ok=True)

    # Iterate over ID subfolders in baseline
    for id_name in os.listdir(baseline_folder):
        id_path = os.path.join(baseline_folder, id_name)
        if not os.path.isdir(id_path):
            continue  # skip non-directory files

        # Destination ID folder
        dest_id_path = os.path.join(dest_folder, id_name)
        os.makedirs(dest_id_path, exist_ok=True)

        # Iterate sub-subfolders inside each ID folder
        for sub_name in os.listdir(id_path):
            sub_path = os.path.join(id_path, sub_name)
            if not os.path.isdir(sub_path):
                continue

            # Copy only those ending with any of the suffixes
            if any(sub_name.endswith(suffix) for suffix in suffixes):
                dest_sub_path = os.path.join(dest_id_path, sub_name)

                # If it already exists, remove it first
                if os.path.exists(dest_sub_path):
                    shutil.rmtree(dest_sub_path)

                shutil.copytree(sub_path, dest_sub_path)
                print(f"Copied {sub_path} -> {dest_sub_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract sub-subfolders ending with one or more suffixes into dest_folder."
    )
    parser.add_argument("--baseline-folder", help="Path to baseline folder")
    parser.add_argument("--dest-folder", help="Path to destination folder")
    parser.add_argument(
        "--suffixes", nargs="+", help="One or more suffixes (e.g., mozilla_rep mozilla_rework)"
    )

    args = parser.parse_args()
    extract_subfolders(args.baseline_folder, args.dest_folder, args.suffixes)


if __name__ == "__main__":
    main()
