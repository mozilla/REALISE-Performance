#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

Author: Mohamed Bilel Besbes
Date: 2024-10-13
"""
import argparse
import time
import ruptures as rpt
import copy
import numpy as np
from cpdbench_utils import load_dataset, exit_success, exit_with_error


def parse_args():
    parser = argparse.ArgumentParser(description="Run KCPA algorithm on a time series dataset.")
    parser.add_argument('-i', '--input', required=True, help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output JSON file.")
    parser.add_argument('--alpha', type=float, help="Alpha parameter for e.divisive.", default=1.0)
    parser.add_argument('--minsize', type=int, help="Minimum segment size.", default=2)
    parser.add_argument('-R', '--runs', type=int, help="Number of runs for the algorithm.", default=20)
    parser.add_argument('--siglvl', type=float, help="Significance level for e.divisive.", default=0.05)
    return parser.parse_args()

def e_divisive(data, alpha, minsize, siglvl, runs):
    algo = rpt.Edivisive(alpha=alpha, min_size=minsize, significance_level=siglvl).fit(data)
    return algo.predict(n_bkps=runs)

def main():
    args = parse_args()
    data, mat = load_dataset(args.input)
    start_time = time.time()
    raw_args = copy.deepcopy(args)
    try:
        series = data['series'][0]['raw']
        transformed_data = np.array(series).reshape(-1, 1)
        result = e_divisive(transformed_data, alpha=args.alpha, runs=args.runs, minsize=args.minsize, siglvl=args.siglvl)
        locations = list(map(int, result))
        stop_time = time.time()
        runtime = stop_time - start_time
        exit_success(data, raw_args, vars(args), locations, runtime, __file__)
    except Exception as e:
        exit_with_error(data, raw_args, vars(args), str(e), __file__)
if __name__ == "__main__":
    main()