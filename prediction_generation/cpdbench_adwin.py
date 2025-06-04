#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import time
import copy
import numpy as np
from river.drift import ADWIN
from cpdbench_utils import load_dataset, exit_success, exit_with_error

def parse_args():
    parser = argparse.ArgumentParser(description="Run ADWIN (river) on a time series dataset.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output JSON file.")
    parser.add_argument('--delta', type=float, default=0.002, help="Delta value for ADWIN (default: 0.002)")
    return parser.parse_args()

def main():
    args = parse_args()
    data, mat = load_dataset(args.input)
    start_time = time.time()
    raw_args = copy.deepcopy(args)

    try:
        series = data['series'][0]['raw']
        detector = ADWIN(delta=args.delta)
        drift_points = []

        for i, val in enumerate(series):
            detector.update(val)
            if detector.drift_detected:
                drift_points.append(i)

        runtime = time.time() - start_time
        exit_success(data, raw_args, vars(args), drift_points, runtime, __file__)
    except Exception as e:
        exit_with_error(data, raw_args, vars(args), str(e), __file__)

if __name__ == "__main__":
    main()
