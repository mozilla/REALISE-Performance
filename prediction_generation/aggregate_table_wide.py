# -*- coding: utf-8 -*-

"""
Script to generate the aggregate table (univariate version)

Author: Refactored by ChatGPT
Original Author: Gertjan van den Burg
Copyright (c) 2020 - The Alan Turing Institute
License: See the LICENSE file.

"""

import argparse
import json
import tabulate

from enum import Enum


class Method(Enum):
    amoc = "amoc"
    binseg = "binseg"
    bocpd = "bocpd"
    bocpdms = "bocpdms"
    cpnp = "cpnp"
    ecp = "ecp"
    kcpa = "kcpa"
    pelt = "pelt"
    prophet = "prophet"
    rbocpdms = "rbocpdms"
    rfpop = "rfpop"
    segneigh = "segneigh"
    wbs = "wbs"
    zero = "zero"
    mongodb = "mongodb"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bcu",
        help="Path to json file with results for: best/cover/uni",
        required=True,
    )
    parser.add_argument(
        "--bfu",
        help="Path to json file with results for: best/f1/uni",
        required=True,
    )
    parser.add_argument(
        "--bpu",
        help="Path to json file with results for: best/precision/uni",
        required=True,
    )
    parser.add_argument(
        "--bru",
        help="Path to json file with results for: best/recall/uni",
        required=True,
    )
    parser.add_argument(
        "--dcu",
        help="Path to json file with results for: default/cover/uni",
        required=True,
    )
    parser.add_argument(
        "--dfu",
        help="Path to json file with results for: default/f1/uni",
        required=True,
    )
    parser.add_argument(
        "--dpu",
        help="Path to json file with results for: default/precision/uni",
        required=True,
    )
    parser.add_argument(
        "--dru",
        help="Path to json file with results for: default/recall/uni",
        required=True,
    )
    return parser.parse_args()


def load_json(filename):
    with open(filename, "r") as fp:
        return json.load(fp)


def make_table(uni_default_f1, uni_default_cover, uni_default_precision, uni_default_recall,
               uni_best_f1, uni_best_cover, uni_best_precision, uni_best_recall, methods):
    """Create part of the aggregate table
    """
    tex = []
    tex.append("%% This table requires booktabs!")

    tex.append("\\begin{tabular}{lrrrr|rrrr}")
    superheader = (
        " & ".join(
            [
                "",
                "\\multicolumn{4}{c}{Default}",
                "\\multicolumn{4}{c}{Best} \\\\",
            ]
        )
        + "\\cmidrule(lr){2-5}\\cmidrule(lr){6-9}"
    )
    tex.append(superheader)
    subheader = (
        " & ".join(
            [
                "",
                "F1",
                "Cover",
                "Precision",
                "Recall",
                "F1",
                "Cover",
                "Precision",
                "Recall" + "\\\\",
            ]
        )
        + "\\cmidrule(r){1-1}"
        + "\\cmidrule(lr){2-5}"
        + "\\cmidrule(l){6-9}"
    )
    tex.append(subheader)

    table = []

    L = max(map(len, methods))
    textsc = lambda m: "\\textsc{%s}%s" % (m, (L - len(m)) * " ")
    table.append(list(map(textsc, methods)))

    all_exps = [uni_default_f1, uni_default_cover, uni_default_precision, uni_default_recall,
                uni_best_f1, uni_best_cover, uni_best_precision, uni_best_recall]

    for exp in all_exps:
        row = []
        maxscore = max((exp[m] for m in methods if m in exp))
        for m in methods:
            if m not in exp:
                row.append(5 * " ")
                continue
            score = exp[m]
            scorestr = tabulate._format(
                score, tabulate._float_type, ".3f", ""
            )
            if score == maxscore:
                row.append("\\textbf{%s}" % scorestr)
            else:
                row.append(scorestr)
        table.append(row)

    transposed = list(zip(*table))
    for row in transposed:
        tex.append(" & ".join(row) + " \\\\")
    tex.append("\\cmidrule(r){1-1}\\cmidrule(lr){2-5}\\cmidrule(l){6-9}")
    tex.append("\\end{tabular}")

    return tex


def main():
    args = parse_args()

    bcu = load_json(args.bcu)
    bfu = load_json(args.bfu)
    bpu = load_json(args.bpu)
    bru = load_json(args.bru)
    dcu = load_json(args.dcu)
    dfu = load_json(args.dfu)
    dpu = load_json(args.dpu)
    dru = load_json(args.dru)

    methods = sorted([m.name for m in Method])
    tex = make_table(dfu, dcu, dpu, dru, bfu, bcu, bpu, bru, methods)

    print("\n".join(tex))


if __name__ == "__main__":
    main()
