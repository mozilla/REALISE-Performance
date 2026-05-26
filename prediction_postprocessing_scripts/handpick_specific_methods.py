#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
select_specific_methods.py
--------------------------
Filters subfolders in a hierarchical directory structure based on suffixes
and copies them to a destination folder while preserving the ID-level structure.

Example usage:
    python select_specific_methods.py \
        --src_folder /path/to/src_folder \
        --dest_folder /path/to/dest_folder \
        --suffixes abc fgr
"""

import os
import shutil
import argparse


def filter_and_copy_subfolders(src_folder, dest_folder, suffixes):
    """
    Copy subsubfolders from src_folder to dest_folder based on specified suffixes.
    The folder structure of IDs is preserved.
    """
    os.makedirs(dest_folder, exist_ok=True)

    for id_folder in os.listdir(src_folder):
        id_path = os.path.join(src_folder, id_folder)
        if not os.path.isdir(id_path):
            continue

        dest_id_path = os.path.join(dest_folder, id_folder)
        os.makedirs(dest_id_path, exist_ok=True)

        for subfolder in os.listdir(id_path):
            subfolder_path = os.path.join(id_path, subfolder)
            if not os.path.isdir(subfolder_path):
                continue

            for suffix in suffixes:
                if subfolder.endswith(suffix):
                    dest_subfolder_path = os.path.join(dest_id_path, subfolder)
                    if not os.path.exists(dest_subfolder_path):
                        shutil.copytree(subfolder_path, dest_subfolder_path)
                        print(f"Copied: {subfolder_path} -> {dest_subfolder_path}")
                    else:
                        print(f"Skipped (already exists): {dest_subfolder_path}")
                    break


def main():
    parser = argparse.ArgumentParser(
        description="Filter and copy specific subfolders based on suffixes."
    )
    parser.add_argument(
        "--src-folder", required=True,
        help="Path to the source folder containing ID subfolders."
    )
    parser.add_argument(
        "--dest-folder", required=True,
        help="Path to the destination folder where filtered results are saved."
    )
    parser.add_argument(
        "--suffixes", nargs="+", required=True,
        help="List of suffixes to select (e.g., abc fgr)."
    )

    args = parser.parse_args()
    filter_and_copy_subfolders(args.src_folder, args.dest_folder, args.suffixes)


if __name__ == "__main__":
    main()
