import argparse
import time
import pandas as pd
from prophet import Prophet
import json
import sys
import copy

from cpdbench_utils import load_dataset, exit_success, make_param_dict, exit_with_error

def parse_args():
    parser = argparse.ArgumentParser(description="Wrapper for Prophet")
    parser.add_argument("-i", "--input", help="path to the input data file", required=True)
    parser.add_argument("-o", "--output", help="path to the output file")
    parser.add_argument("-N", "--Nmax", help="maximum number of changepoints", choices=['default', 'max'])
    parser.add_argument("-w", "--WeeklySeasonality", type=bool, help="Weekly Seasonality")
    parser.add_argument("-d", "--DailySeasonality", type=bool, help="Daily Seasonality")
    parser.add_argument("-r", "--ChangepointRange", type=float, help="Changepoint Range")
    parser.add_argument("-p", "--ChangepointPriorScale", type=float, help="Changepoint Prior Scale")
    parser.add_argument("-t", "--IntervalWidth", type=float, help="Interval Width")
    parser.add_argument("-g", "--growth", type=str, help="Growth type: 'linear' or 'logistic'", choices=['linear', 'logistic'])
    parser.add_argument("-c", "--cap", type=float, help="Capacity for logistic growth (required for logistic growth)")

    return parser.parse_args()

# Function to convert Timestamp objects to a JSON serializable format
def convert_timestamps(obj):
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()  # Convert to ISO 8601 string format
    elif isinstance(obj, list):
        return [convert_timestamps(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_timestamps(value) for key, value in obj.items()}
    else:
        return obj

def main():
    args = parse_args()
    raw_args = copy.deepcopy(args)

    # Load the dataset (using a Python equivalent of your R helper function)
    data, mat = load_dataset(args.input)

    start_time = time.time()

    if args.Nmax == 'default':
        args.Nmax = 25
    else:
        args.Nmax = data['n_obs'] - 1  # Adjusted from 'original' to the main data structure

    # Check if 'series' is in data and extract appropriately
    if 'series' not in data or len(data['series']) == 0:
        exit_with_error(data, raw_args, vars(args), "No time series data available.")

    # Prepare the DataFrame for Prophet
    df = pd.DataFrame({
        'ds': data['time']['raw'],  # Time column
        'y': data['series'][0]['raw']  # Series values
    })

    # Handle logistic growth by adding 'cap'
    if args.growth == 'logistic':
        if args.cap is None:
            exit_with_error(data, raw_args, vars(args), "Capacity ('cap') must be provided for logistic growth.")
        
        # Add the capacity column to the DataFrame
        df['cap'] = args.cap

    # Fit the Prophet model
    try:
        model = Prophet(
            changepoint_range=args.ChangepointRange,
            n_changepoints=args.Nmax,
            weekly_seasonality=args.WeeklySeasonality,
            daily_seasonality=args.DailySeasonality,
            growth=args.growth,  # 'linear' or 'logistic'
            changepoint_prior_scale=args.ChangepointPriorScale,
            interval_width=args.IntervalWidth
        )
        model.fit(df)

        # Retrieve changepoints (timestamps)
        changepoints = model.changepoints
        locs = changepoints.index.tolist()

    except Exception as e:
        exit_with_error(data, raw_args, vars(args), str(e), __file__)

    stop_time = time.time()
    runtime = stop_time - start_time

    locs = convert_timestamps(locs)
    data = convert_timestamps(data)

    exit_success(data, raw_args, vars(args), locs, runtime, __file__)

if __name__ == "__main__":
    main()
