# -*- coding: utf-8 -*-

"""
Script to generate the aggregate table (wide version)

Author: Gertjan van den Burg
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
        "--dcu",
        help="Path to json file with results for: default/cover/uni",
        required=True,
    )
    parser.add_argument(
        "--dfu",
        help="Path to json file with results for: default/f1/uni",
        required=True,
    )
    return parser.parse_args()


def load_json(filename):
    with open(filename, "r") as fp:
        return json.load(fp)


def make_table(uni_default_cover, uni_default_f1, uni_best_cover, uni_best_f1, methods):
    """Create part of the aggregate table
    """
    tex = []
    tex.append("%% This table requires booktabs!")

    tex.append("\\begin{tabular}{lrr|rrrr|rr}")
    superheader = (
        " & ".join(
            [
                "",
                "\\multicolumn{4}{c}{Univariate}",
                "\\multicolumn{4}{c}{Multivariate} \\\\",
            ]
        )
        + "\\cmidrule(lr){2-5}\\cmidrule(lr){6-9}"
    )
    tex.append(superheader)
    header = (
        " & ".join(
            [
                "",
                "\\multicolumn{2}{c}{Default}",
                "\\multicolumn{2}{c}{Best}",
                "\\multicolumn{2}{c}{Default}",
                "\\multicolumn{2}{c}{Best} \\\\",
            ]
        )
        + "\\cmidrule(lr){2-3}"
        + "\\cmidrule(lr){4-5}"
        + "\\cmidrule(lr){6-7}"
        + "\\cmidrule(lr){8-9}"
    )
    tex.append(header)
    subheader = (
        " & ".join(
            [
                "",
                "Cover",
                "F1",
                "Cover",
                "F1",
                "Cover",
                "F1",
                "Cover",
                "F1" + "\\\\",
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

    all_exps = [uni_default_cover, uni_default_f1, uni_best_cover, uni_best_f1]

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
    dcu = load_json(args.dcu)
    dfu = load_json(args.dfu)

    methods = sorted([m.name for m in Method])
    tex = make_table(dcu, dfu, bcu, bfu, methods)

    print("\n".join(tex))


if __name__ == "__main__":
    main()
