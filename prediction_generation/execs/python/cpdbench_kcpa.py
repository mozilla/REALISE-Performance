#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

Author: Simon Trapp
Date: 2021-08-25

"""
import argparse
import time
import ruptures as rpt
import copy
import numpy as np
from cpdbench_utils import load_dataset, exit_success, exit_with_error


def parse_args():
    parser = argparse.ArgumentParser(description="Run KCPA algorithm on a time series dataset.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output JSON file.")
    parser.add_argument('-L', '--maxcp', type=int, default=100, help="Maximum number of change points for KCPA (default is 100).")
    parser.add_argument('-m', '--minsize', type=float, help="Minimum size.", default=3)
    parser.add_argument('-k', '--kernel', type=str, help="Kernel.", default='linear')
    return parser.parse_args()


def main():
    args = parse_args()
    data, mat = load_dataset(args.input)
    start_time = time.time()
    raw_args = copy.deepcopy(args)
    try:
        series = data['series'][0]['raw']
        transformed_data = np.array(series).reshape(-1, 1)
        algo = rpt.KernelCPD(kernel=args.kernel, min_size=args.minsize).fit(transformed_data)
        locations = algo.predict(n_bkps=args.maxcp)
        stop_time = time.time()
        runtime = stop_time - start_time
        exit_success(data, raw_args, vars(args), locations, runtime, __file__)
    except Exception as e:
        exit_with_error(data, raw_args, vars(args), str(e), __file__)
if __name__ == "__main__":
    main()