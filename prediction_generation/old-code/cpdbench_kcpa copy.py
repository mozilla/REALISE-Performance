#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

Author: Simon Trapp
Date: 2021-08-25

"""
import argparse
import time
from signal_processing_algorithms.energy_statistics import energy_statistics
from cpdbench_utils import load_dataset, exit_success
import copy


def parse_args():
    parser = argparse.ArgumentParser(description="Run KCPA algorithm on a time series dataset.")
    parser.add_argument('-i', '--input', required=True, help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', required=True, help="Path to the output JSON file.")
    parser.add_argument('-L', '--maxcp', type=int, default=100, help="Maximum number of change points for KCPA (default is 100).")
    parser.add_argument('-C', '--cost', type=float, help="Cost parameter for KCPA.", default=1.0)
    parser.add_argument('-m', '--minsize', type=float, help="Minimum size.", default=3)
    parser.add_argument('-k', '--kernel', type=float, help="Kernel.", default='linear')
    return parser.parse_args()


def main():
    args = parse_args()
    data, mat = load_dataset(args.input)
    start_time = time.time()
    raw_args = copy.deepcopy(args)
    try:
        series = data['series'][0]['raw']
        transformed_data = np.array(time_series_values).reshape(-1, 1)
        algo = rpt.KernelCPD(kernel=args.kernel, min_size=args.minsize, cost=args.cost).fit(transformed_data)
        locations = algo.predict(n_bkps=args.maxcp)
        stop_time = time.time()
        runtime = stop_time - start_time
        exit_success(data, raw_args, args, locations, runtime, __file__)
    except Exception as e:
        exit_with_error(data, raw_args, args, str(e), __file__)
if __name__ == "__main__":
    main()