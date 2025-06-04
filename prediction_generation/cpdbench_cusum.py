#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

Author: Simon Trapp (adapted for Alibi-Detect CUSUM)
Date: 2021-08-25

"""
import argparse
import time
import copy
import numpy as np
from alibi_detect.cd import CUSUMDrift
from cpdbench_utils import load_dataset, exit_success, exit_with_error


def parse_args():
    parser = argparse.ArgumentParser(description="Run Alibi-Detect CUSUM algorithm on a time series dataset.")
    parser.add_argument('-i', '--input', help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output JSON file.")
    parser.add_argument('-t', '--threshold', type=float, default=5.0, help="CUSUM detection threshold (default: 5.0).")
    parser.add_argument('--drift-type', type=str, default='mean', choices=['mean', 'variance'], help="Type of drift to detect (default: mean).")
    parser.add_argument('--reset', action='store_true', help="Reset detector after drift detected.")
    return parser.parse_args()


def main():
    args = parse_args()
    data, mat = load_dataset(args.input)
    start_time = time.time()
    raw_args = copy.deepcopy(args)
    try:
        series = data['series'][0]['raw']
        # Prepare data for CUSUMDrift: 2D array (n_samples, n_features)
        transformed_data = np.array(series).reshape(-1, 1)
        
        # Initialize the detector with the reference data (using the full series as baseline)
        cd = CUSUMDrift(X_ref=transformed_data,
                        threshold=args.threshold,
                        drift_type=args.drift_type,
                        reset_at_drift=args.reset)
        
        # Run prediction on the same data (or you could split input)
        preds = cd.predict(transformed_data)
        
        # Extract detected drift points (indices where drift detected)
        # Alibi returns drift boolean per point; get indices where True
        drift_points = [i for i, is_drift in enumerate(preds['is_drift']) if is_drift]
        
        stop_time = time.time()
        runtime = stop_time - start_time
        
        exit_success(data, raw_args, vars(args), drift_points, runtime, __file__)
    except Exception as e:
        exit_with_error(data, raw_args, vars(args), str(e), __file__)


if __name__ == "__main__":
    main()
