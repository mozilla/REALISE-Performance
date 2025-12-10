#!/usr/bin/env python3
import re
import argparse
from pathlib import Path
from collections import defaultdict

# -------------------------------------------------------------------
# ARGPARSE — read BASE_DIR from command line
# -------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Build LaTeX tables from .tex result files.")
parser.add_argument(
    "--base-dir",
    type=str,
    required=True,
    help="Path to the folder containing the .tex result files."
)
parser.add_argument(
    "--out-regular",
    type=str,
    default="table_regular.tex",
    help="Output file for regular mode table."
)
parser.add_argument(
    "--out-leveraged",
    type=str,
    default="table_leveraged.tex",
    help="Output file for leveraged mode table."
)

args = parser.parse_args()

BASE_DIR = Path(args.base_dir)
OUTPUT_REGULAR = args.out_regular
OUTPUT_LEVERAGED = args.out_leveraged

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------
strategies = ["intersect", "veto"]
mozilla_modes = ["regular", "leveraged"]
characteristics = ["platform", "repository", "suite", "test"]

# Data structure:
# results[mozilla_mode][strategy][min_x][characteristic] = (F1, Prec, Rec)
results = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

# -------------------------------------------------------------------
# STEP 1 — Parse all TEX files
# -------------------------------------------------------------------
pattern_filename = re.compile(r"^(intersect|veto)_(regular|leveraged)_(platform|repository|suite|test)\.tex$")
pattern_row = re.compile(
    r"^(intersect|veto)_(regular|leveraged)_(platform|repository|suite|test)_min_(\d+)\s*&(.+?)\\\\"
)

for tex_file in BASE_DIR.rglob("*.tex"):
    m = pattern_filename.match(tex_file.name)
    if not m:
        continue

    strategy, mozilla_mode, characteristic = m.groups()

    with open(tex_file, "r") as f:
        for line in f:
            line = line.strip()
            row = pattern_row.match(line)
            if not row:
                continue

            _, _, _, min_x, rest = row.groups()
            min_x = int(min_x)

            cols = [c.strip() for c in rest.split("&")]
            numeric_cols = [c for c in cols if re.match(r"^\d+\.\d+$", c)]
            if len(numeric_cols) < 3:
                print("WARNING: Row did not contain 3 final numeric columns:", line)
                continue

            f1, precision, recall = numeric_cols[-3:]
            results[mozilla_mode][strategy][min_x][characteristic] = (f1, precision, recall)


# -------------------------------------------------------------------
# Helper: write a table for one mozilla_mode
# -------------------------------------------------------------------
def build_table(mode):
    out = []
    out.append(r"\begin{table}[t!]")
    out.append(r"\centering")
    out.append(
        r"\begin{tabular}{|c|l||c|c|c|c|c|c|c|c|c|c|c|c|}"
    )
    out.append(r"\hline")
    out.append(
        r"\multirow{1}{*}{\rotatebox{90}{Strat.}} & Strategy variation & "
        r"\multicolumn{3}{c|}{Platform Results} & "
        r"\multicolumn{3}{c|}{Repository Results} & "
        r"\multicolumn{3}{c|}{Suite Results} & "
        r"\multicolumn{3}{c|}{Test Results} \\"
    )
    out.append(r"\cline{3-14}")
    out.append(
        r" &  & F1 & Precision & Recall  & F1 & Precision & Recall  & "
        r"F1 & Precision & Recall  & F1 & Precision & Recall \\"
    )
    out.append(r"\hline")

    for strategy in strategies:
        min_values = sorted(results[mode][strategy].keys())
        out.append(
            rf"\multirow{{{len(min_values)}}}{{*}}{{\rotatebox{{90}}{{{strategy}}}}}"
        )

        first = True
        for min_x in min_values:
            vals = []
            for char in characteristics:
                if char in results[mode][strategy][min_x]:
                    f1, p, r = results[mode][strategy][min_x][char]
                    vals.extend([f1, p, r])
                else:
                    vals.extend(["-", "-", "-"])

            line = f" & min {min_x} & " + " & ".join(vals) + r" \\"
            if first:
                out.append(line)
                first = False
            else:
                out.append(" " + line)
        out.append(r"\hline")

    out.append(r"\end{tabular}")
    out.append(rf"\caption{{Voting strategies results ({mode})}}")
    out.append(rf"\label{{tab:voting_strategies_results_{mode}}}")
    out.append(r"\end{table}")

    return "\n".join(out)


# -------------------------------------------------------------------
# STEP 3 — Write output LaTeX tables
# -------------------------------------------------------------------

with open(OUTPUT_REGULAR, "w") as f:
    f.write(build_table("regular"))

with open(OUTPUT_LEVERAGED, "w") as f:
    f.write(build_table("leveraged"))

print("Done! Tables written to:")
print(" -", OUTPUT_REGULAR)
print(" -", OUTPUT_LEVERAGED)
