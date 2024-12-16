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


def parse_args():
    parser = argparse.ArgumentParser(description="Wrapper for None-detector")
    parser.add_argument("-i", "--input", help="path to the input data file", required=True)
    parser.add_argument("-o", "--output", help="path to the output file")
    parser.add_argument("-p", "--pvalue", help="the significance cutoff for the algorithm for each test", default=0.01, type=float)
    parser.add_argument("-n", "--permutations", help="number of permutations for the data for each test", default=100, type=int)
    return parser.parse_args()


def main():
    args = parse_args()
    data, mat = load_dataset(args.input)
    start_time = time.time()

    # start changepoint detection
    series = data['series'][0]['raw']
    locations = energy_statistics.e_divisive(series, pvalue=args.pvalue, permutations=args.permutations)  # changepoints --> indices of time points [0,N-1]

    stop_time = time.time()
    runtime = stop_time - start_time
    exit_success(data, args, {}, locations, runtime, __file__)


if __name__ == "__main__":
    main()
