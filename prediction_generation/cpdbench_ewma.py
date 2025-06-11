#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import time
import copy
from river.drift import HDDM_W
from cpdbench_utils import load_dataset, exit_success, exit_with_error

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def parse_args():
    parser = argparse.ArgumentParser(description="Run EWMA (HDDM_W from river) on a time series dataset.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output JSON file.")
    parser.add_argument('--drift_confidence', type=float, default=0.001, help="Drift confidence (default: 0.001)")
    parser.add_argument('--warning_confidence', type=float, default=0.005, help="Warning confidence (default: 0.005)")
    parser.add_argument('--lambda_val', type=float, default=0.05, help="Weight for recent data (default: 0.05)")
    parser.add_argument('--two_sided_test', type=str2bool, default=False, help="Enable two-sided test (True/False)")
    return parser.parse_args()

def main():
    args = parse_args()
    data, mat = load_dataset(args.input)
    start_time = time.time()
    raw_args = copy.deepcopy(args)

    try:
        series = data['series'][0]['raw']
        # Ensure input is a binary stream: 0 for correct, 1 for error
        if not all(x in [0, 1] for x in series):
            raise ValueError("HDDM_W requires a binary stream of 0s and 1s.")

        detector = HDDM_W(
            drift_confidence=args.drift_confidence,
            warning_confidence=args.warning_confidence,
            lambda_val=args.lambda_val,
            two_sided_test=args.two_sided_test
        )

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
