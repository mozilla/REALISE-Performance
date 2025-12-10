#!/usr/bin/env python3
import subprocess

characteristics = ["test", "suite", "platform", "repository"]
mozilla_modes = ["regular", "leveraged"]
min_values_veto = range(1, 6)
min_values_intersect = range(1, 7)

# ------------------------
# 1) Mozilla veto strategy
# ------------------------
for characteristic in characteristics:
    for mozilla_mode in mozilla_modes:
        for min_nb in min_values_veto:

            cmd_veto = [
                "python3", "voter_strategy_mozilla_veto.py",
                "--input-folder", f"../data/temp_data/clean_data/{characteristic}/stat_methods_merged_per_{characteristic}_best_mozilla_{mozilla_mode}",
                "--output-folder", f"../data/temp_data/clean_data/{characteristic}/mozilla_{mozilla_mode}_veto/min_{min_nb}",
                "--veto-method", "mozilla_rep",
                "--methods", "cvm_advanced", "ks_advanced", "levene_advanced", "mwu_advanced", "welch_advanced",
                "--min-votes", str(min_nb),
                "--margin", "5",
            ]

            print("Running:", " ".join(cmd_veto))
            subprocess.run(cmd_veto, check=True)

# ---------------------------
# 2) Intersection strategy
# ---------------------------
for characteristic in characteristics:
    for mozilla_mode in mozilla_modes:
        for min_nb in min_values_intersect:

            cmd_intersect = [
                "python3", "voter_strategy_intersection.py",
                "--input-folder", f"../data/temp_data/clean_data/{characteristic}/stat_methods_merged_per_{characteristic}_best_mozilla_{mozilla_mode}",
                "--output-folder", f"../data/temp_data/clean_data/{characteristic}/mozilla_{mozilla_mode}_intersect/min_{min_nb}",
                "--methods", "cvm_advanced", "ks_advanced", "levene_advanced", "mwu_advanced", "welch_advanced", "mozilla_rep",
                "--min-votes", str(min_nb),
                "--margin", "5",
            ]

            print("Running:", " ".join(cmd_intersect))
            subprocess.run(cmd_intersect, check=True)
