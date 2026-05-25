#!/usr/bin/env python3
"""
Copy an input folder to an output folder, excluding all variant subfolders
for a given method (i.e. default_<method> and best_<method>).

Usage:
    python delete_method.py \
        --input-folder  /path/to/input \
        --output-folder /path/to/output \
        --method        cpnp
"""

import argparse
import shutil
from pathlib import Path


def should_exclude(folder_name: str, method: str) -> bool:
    """Return True if this folder is a variant folder for the given method."""
    method_lower = method.strip().lower()
    folder_lower = folder_name.lower()
    return folder_lower in (f"default_{method_lower}", f"best_{method_lower}")


def copy_without_method(input_root: Path, output_root: Path, method: str):
    removed = []

    for dataset_dir in sorted(input_root.iterdir()):
        if not dataset_dir.is_dir():
            # Copy top-level files as-is
            shutil.copy2(dataset_dir, output_root / dataset_dir.name)
            continue

        dest_dataset = output_root / dataset_dir.name
        dest_dataset.mkdir(parents=True, exist_ok=True)

        for sub in sorted(dataset_dir.iterdir()):
            if not sub.is_dir():
                shutil.copy2(sub, dest_dataset / sub.name)
                continue

            if should_exclude(sub.name, method):
                removed.append(sub)
                continue

            # Copy the whole subfolder tree
            shutil.copytree(sub, dest_dataset / sub.name)

    return removed


def main():
    parser = argparse.ArgumentParser(
        description="Copy dataset folder tree, dropping all variant folders for a given method."
    )
    parser.add_argument("--input-folder",  "-i", required=True,
                        help="Root input folder")
    parser.add_argument("--output-folder", "-o", required=True,
                        help="Root output folder (must not already exist)")
    parser.add_argument("--method", "-m", required=True,
                        help="Method name to remove (e.g. cpnp)")
    args = parser.parse_args()

    input_root  = Path(args.input_folder).resolve()
    output_root = Path(args.output_folder).resolve()
    method      = args.method.strip()

    if not input_root.exists():
        raise FileNotFoundError(f"Input folder not found: {input_root}")
    if output_root.exists():
        raise FileExistsError(
            f"Output folder already exists: {output_root}\n"
            "Please choose a new path or remove it first."
        )

    output_root.mkdir(parents=True)

    print(f"Input  : {input_root}")
    print(f"Output : {output_root}")
    print(f"Dropping folders: default_{method.lower()}  /  best_{method.lower()}")
    print()

    removed = copy_without_method(input_root, output_root, method)

    if removed:
        print(f"Excluded {len(removed)} folder(s):")
        for p in removed:
            print(f"  - {p.relative_to(input_root)}")
    else:
        print("No matching folders found — nothing was excluded.")

    print("\nDone.")


if __name__ == "__main__":
    main()