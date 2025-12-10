#!/usr/bin/env python3
import subprocess
import time
from pathlib import Path
import argparse

IMAGE = "mohamedbilelbesbes/selected_174_online_extension:rectifications"


# ---------------------
# Helpers
# ---------------------
def run(cmd, capture_output=False):
    """Run command and stream or capture output."""
    if capture_output:
        return subprocess.check_output(cmd, shell=True).decode().strip()
    else:
        subprocess.check_call(cmd, shell=True)


def get_container_id():
    """Return the ID of the most recently created container."""
    return run("docker ps -l -q", capture_output=True)


def extract_and_append_row(src_tex: Path, combined_tex: Path, row_prefix: str):
    """
    Extract the voter_merged row from latex_summary.tex and append it to the combined file.
    The original row looks like:
    voter_merged & a & b & c & ... \\

    We rewrite it as:
    {row_prefix} & a & b & c & ... \\
    """

    if not src_tex.exists():
        print(f"⚠️  Missing latex_summary.tex at {src_tex}")
        return

    text = src_tex.read_text()

    # find the voter_merged row
    row = None
    for line in text.splitlines():
        if line.strip().startswith("voter_merged &") or line.strip().startswith("veto_merged &"):
            row = line.strip()
            break

    if row is None:
        print(f"⚠️  No voter_merged row found in {src_tex}")
        return

    # Replace voter_merged → row_prefix
    if line.strip().startswith("voter_merged &"):
        row = row.replace("voter_merged", row_prefix, 1)
    elif line.strip().startswith("veto_merged &"):
        row = row.replace("veto_merged", row_prefix, 1)

    # Append to combined file
    with combined_tex.open("a") as f:
        f.write(row + "\n")

    print(f"→ Appended row to {combined_tex.name}")


# ---------------------
# Main container process
# ---------------------
def process_one_folder(input_path: Path, summaries_base: Path):
    """
    Run the docker process on one folder:
    - start container
    - remove abed_results
    - docker cp input folder
    - make mozillasummary
    - copy the produced latex_summary.tex
    """

    print(f"\n=== Processing {input_path} ===")

    # create unique output folder: repository_mozilla_regular_intersect_min_6
    parts = input_path.parts[-3:]
    output_name = "_".join(parts)
    output_folder = summaries_base / output_name
    output_folder.mkdir(parents=True, exist_ok=True)

    # 1. Start container
    print("→ Starting container...")
    run(f"docker run -d -it {IMAGE} /bin/bash")
    container_id = get_container_id()
    print(f"   Container ID = {container_id}")

    # 2. Cleanup inside container
    print("→ Removing old abed_results inside container...")
    run(f"docker exec {container_id} rm -rf /TCPDBench/abed_results")

    # 3. Copy input folder into container
    print("→ Copying input folder into container...")
    run(f"docker cp {input_path} {container_id}:/TCPDBench/abed_results")

    # 4. Run make mozillasummary
    print("→ Running `make mozillasummary` inside container...")
    run(f"docker exec {container_id} make mozillasummary")

    # 5. Wait 20 seconds
    print("→ Waiting 20 seconds for output generation...")
    time.sleep(1)

    # 6. Copy output latex_summary.tex
    src_file = "/TCPDBench/analysis/output/tables/latex_summary.tex"
    dst_file = output_folder / "latex_summary.tex"

    print("→ Copying output file back to host...")
    run(f"docker cp {container_id}:{src_file} {dst_file}")

    print(f"→ Output saved at: {dst_file}")

    # 7. Remove container
    print("→ Removing container...")
    run(f"docker rm -f {container_id}")

    print(f"=== Done with {input_path.name} ===\n")

    return dst_file  # return generated tex path


# ---------------------
# CLI
# ---------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate summary extraction from containers.")

    parser.add_argument(
        "--summaries-dir",
        required=True,
        type=str,
        help="Base folder where summaries will be written."
    )

    parser.add_argument(
        "--input-base",
        required=True,
        type=str,
        help="Base directory of input folders."
    )

    args = parser.parse_args()

    summaries_base = Path(args.summaries_dir).resolve()
    input_base = Path(args.input_base).resolve()

    strategies = ["intersect", "veto"]
    mozilla_modes = ["regular", "leveraged"]
    characteristics = ["test", "suite", "platform", "repository"]

    for strategy in strategies:
        for mode in mozilla_modes:
            for charac in characteristics:

                # how many min folders?
                if strategy == "veto":
                    min_nb_list = range(1, 6)
                else:
                    min_nb_list = range(1, 7)

                # combined output file for (strategy, mode, charac)
                combined_filename = f"{strategy}_{mode}_{charac}.tex"
                combined_tex = summaries_base / combined_filename

                print(f"\n### Building combined file: {combined_tex.name} ###\n")

                for min_nb in min_nb_list:

                    # build path: charac/mozilla_mode_strategy/min_x
                    fname = f"{charac}/mozilla_{mode}_{strategy}/min_{min_nb}"

                    input_path = input_base / fname
                    tex_path = process_one_folder(input_path, summaries_base)

                    # prefix in combined table
                    row_prefix = f"{strategy}_{mode}_{charac}_min_{min_nb}"

                    extract_and_append_row(tex_path, combined_tex, row_prefix)

    print("\n✔ All processing done.\n")






                    # python3 extract_summaries_in_bulk.py --summaries-dir ../data/temp_data/clean_data/summaries --input-base ../data/temp_data/clean_data


