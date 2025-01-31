import os 
import pandas as pd
import shutil
import argparse
 
def parse_args():
    parser = argparse.ArgumentParser(description="Aggregate the measurements of time series.")
    parser.add_argument('-i', '--input-folder', help="Path to the input CSV timeseries folder")
    parser.add_argument('-o', '--output-folder', help="Path to the output CSV timeseries folder")
    parser.add_argument('-a', '--aggregation-method', help="Aggregation method (mean, min, max)", choices=['mean', 'min', 'max'], default='mean')
    parser.add_argument('-g', '--grouped', help="CSVs are grouped by project or not", choices=["True", "False"])
    return parser.parse_args()

def select_favorable_status(status_series):
    # Return the status with the highest priority (lowest number in `status_priority`)
    return sorted(status_series, key=lambda x: status_priority.get(x, float('inf')))[0]

def process_folder(input_folder, output_folder, folder=None, aggregation_method='mean'):
    if folder:
        for signature_file in os.listdir(input_folder + '/' + folder):
            print(folder + '/' + signature_file)
            df = pd.read_csv(input_folder + '/' + folder + '/' + signature_file, index_col=False)
            df_grouped = df.groupby('revision').agg({
                'value': aggregation_method,
                **{col: 'first' for col in df.columns if col not in ['revision', 'value']}
            }).reset_index()
            # Sort by push_timestamp if it exists, otherwise omit this step
            if 'push_timestamp' in df_grouped.columns:
                df_grouped = df_grouped.sort_values(by='push_timestamp')
            
            # Save the processed DataFrame
            output_path = f'{output_folder}/{folder}/{signature_file}'
            df_grouped.to_csv(output_path, index=False)
    else:
        for signature_file in os.listdir(input_folder):
            print(input_folder + '/' + signature_file)
            df = pd.read_csv(input_folder + '/' + signature_file, index_col=False)
            df_grouped = df.groupby('revision').agg({
                'value': aggregation_method,
                **{col: 'first' for col in df.columns if col not in ['revision', 'value']}
            }).reset_index()
            # Sort by push_timestamp if it exists, otherwise omit this step
            if 'push_timestamp' in df_grouped.columns:
                df_grouped = df_grouped.sort_values(by='push_timestamp')
            
            # Save the processed DataFrame
            output_path = f'{output_folder}/{signature_file}'
            df_grouped.to_csv(output_path, index=False)

def main():
    args = parse_args()
    input_folder = args.input_folder
    output_folder = args.output_folder
    aggregation_method = args.aggregation_method
    grouped = args.grouped
    # Define folders mapping
    projects_folders_mapping = {
        "autoland": ["autoland1", "autoland2", "autoland3", "autoland4"],
        "firefox-android": ["firefox-android"],
        "mozilla-beta": ["mozilla-beta"],
        "mozilla-central": ["mozilla-central"],
        "mozilla-release": ["mozilla-release"],
    }
    # for ome reason, argparse couldn't get the grouped values as a boolean, so I made it into a string, although this should be properly done
    if grouped == "True":
        # Process each project and folder
        for project in projects_folders_mapping:
            for folder in projects_folders_mapping[project]:
                os.makedirs(f'{output_folder}/{folder}', exist_ok=True)
                process_folder(input_folder, output_folder, folder, aggregation_method)
    else:
        os.makedirs(output_folder, exist_ok=True)
        process_folder(input_folder, output_folder, None, aggregation_method)
if __name__ == "__main__":
    main()