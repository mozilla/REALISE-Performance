import os
import pandas as pd
import time
import argparse
from scipy.ndimage import gaussian_filter1d
import argparse

def apply_gaussian_smoothing(df, column, sigma):
    """
    Apply Gaussian smoothing to the specified column in the DataFrame.
    """
    df[column] = gaussian_filter1d(df[column], sigma=sigma)
    return df

def process_folder(input_folder, output_folder, sigma):
    """
    Process each file in the folder, apply Gaussian smoothing, and save the result.
    """
    for signature_file in os.listdir(input_folder):
        print(f"Processing: {signature_file}")
        df = pd.read_csv(os.path.join(input_folder, signature_file), index_col=False)
        
        # Specify the column to smooth
        column_to_smooth = 'value'
        
        # Apply Gaussian smoothing to the specified column
        df = apply_gaussian_smoothing(df, column_to_smooth, sigma)
        
        # Save the smoothed DataFrame to output directory
        os.makedirs(output_folder, exist_ok=True)
        df.to_csv(os.path.join(output_folder, signature_file), index=False)

def main():
    parser = argparse.ArgumentParser(description="Apply Gaussian smoothing to time series data.")
    parser.add_argument('-i', '--input_folder', type=str, required=True, help="Input folder containing CSV files")
    parser.add_argument('-o' ,'--output_folder', type=str, required=True, help="Output folder to save smoothed CSV files")
    parser.add_argument('-s' ,'--sigma', type=float, default=1.0, help="Standard deviation for Gaussian smoothing")

    args = parser.parse_args()

    # The following usage projects_folders_mapping in case the names of the subfolders does not reflect the names of the projects. The code is designed to handle this change.
    #projects_folders_mapping = {"autoland": ["autoland1", "autoland2", "autoland3", "autoland4"], "firefox-android": ["firefox-android"], "mozilla-beta": ["mozilla-beta"], "mozilla-release": ["mozilla-release"], "mozilla-central": ["mozilla-central"]}

    projects_folders_mapping = {name: [name] for name in os.listdir(args.input_folder) if os.path.isdir(os.path.join(args.input_folder, name))}

    # Process each subfolder
    for project in projects_folders_mapping:
        for folder in projects_folders_mapping[project]:
            input_folder = os.path.join(args.input_folder, folder)
            output_folder = os.path.join(args.output_folder, folder)
            process_folder(input_folder, output_folder, args.sigma)

if __name__ == "__main__":
    main()

# python3 smoothe.py --input_folder ../datasets-normalized --output_folder ../datasets-aggregated-smoothed --sigma 2

# python3 smoothe.py --input_folder ../datasets-original-annotated-aggregated --output_folder ../datasets-original-annotated-aggregated-smoothed --sigma 2
