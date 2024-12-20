#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: Mohamed Bilel Besbes
Date: 2024-12-18
"""
import argparse
import pandas as pd
import os
import matplotlib.pyplot as plt


def parse_args():
    parser = argparse.ArgumentParser(description="Calculate distributions of distances of SP alerts from other ones")
    parser.add_argument('-i',
                        '--input-folder',
                        required=True,
                        help="Path to the input dataset folder")
    parser.add_argument('-c',
                        '--categories',
                        nargs='+',
                        required=True,
                        help="Categories of the alerts to take into account (space-separated categories)")
    parser.add_argument('-o',
                        '--output-file',
                        required=True,
                        help="Path to save the distribution plot (e.g., output.png or output.jpg)")
    return parser.parse_args()


def calculate_distances(df, categories):
    """
    Calculate the distances of SP alerts to the closest alert
    from the specified categories.

    Parameters:
        df (DataFrame): The input DataFrame.
        categories (list): List of categories to consider for distance calculation.

    Returns:
        DataFrame: DataFrame with 'signature_id', 'sp_alert_index', and 'distance' columns.
    """
    sp_alerts = df[df['alert_status_general'] == 'SP']
    other_alerts_indices = df[df['alert_status_general'].isin(categories)].index

    distances_list = []

    for sp_index in sp_alerts.index:
        if not other_alerts_indices.empty:
            # Find the closest alert's index distance
            min_distance = abs(other_alerts_indices - sp_index).min()
        else:
            # No relevant alerts found
            min_distance = -1

        # Add the SP alert details to the list
        distances_list.append({
            'signature_id': sp_alerts.loc[sp_index, 'signature_id'],
            'sp_alert_index': sp_index,
            'distance': min_distance
        })

    # Return a DataFrame with multiple entries for each SP alert
    return pd.DataFrame(distances_list)


def plot_distribution(distances, output_file, x_min=-20, x_max=900):
    """
    Plot the distribution of distances and save as an image.

    Parameters:
        distances (DataFrame): A DataFrame with 'distance' column.
        output_file (str): Path to save the plot.
        x_min (int): Minimum value for the x-axis.
        x_max (int): Maximum value for the x-axis.
    """
    if not distances.empty:
        # Ensure the 'distance' column exists
        if 'distance' in distances.columns:
            distances_values = distances['distance']  # Extract the distance column

            # Filter distances within the specified range
            filtered_distances = distances_values[(distances_values >= x_min) & (distances_values <= x_max)]

            # Create custom bin edges from -1000 to 900, with bins like -100 to -91, -90 to -81, ...
            bins = list(range(-100, 0, 10)) + list(range(0, 901, 10))

            # Plot the histogram
            plt.figure(figsize=(10, 6))
            plt.hist(filtered_distances, bins=bins, edgecolor='black', alpha=0.7)
            plt.title("Distribution of Distances")
            plt.xlabel("Distance (index difference)")
            plt.ylabel("Frequency")
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.xlim(x_min, x_max)  # Limit the x-axis
            plt.tight_layout()  # Adjust layout to prevent clipping
            plt.savefig(output_file)
            plt.close()
        else:
            print("The 'distance' column is missing in the distances DataFrame.")
    else:
        print(f"The distances DataFrame is empty. No plot will be generated.")


def process_folder(input_folder, folder, categories):
    folder_path = os.path.join(input_folder, folder)
    all_distances = pd.DataFrame(columns=['signature_id', 'sp_alert_index', 'distance'])

    for signature_file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, signature_file)
        df = pd.read_csv(file_path, index_col=False)
        df['push_timestamp'] = pd.to_datetime(df['push_timestamp'])
        df = df.sort_values(by='push_timestamp')

        if 'SP' in df['alert_status_general'].values:
            distances_df = calculate_distances(df, categories)
            all_distances = pd.concat([all_distances, distances_df], ignore_index=True)

    return all_distances


def main():
    args = parse_args()
    input_folder = args.input_folder
    categories = args.categories
    output_file = args.output_file

    projects_folders_mapping = {
        "autoland": ["autoland1", "autoland2", "autoland3", "autoland4"],
        "firefox-android": ["firefox-android"],
        "mozilla-beta": ["mozilla-beta"]
    }

    all_distances = pd.DataFrame(columns=['signature_id', 'sp_alert_index', 'distance'])

    for project in projects_folders_mapping:
        for folder in projects_folders_mapping[project]:
            distances_df = process_folder(input_folder, folder, categories)
            all_distances = pd.concat([all_distances, distances_df], ignore_index=True)

    # Plot the summary distribution for all distances
    plot_distribution(all_distances, output_file)


if __name__ == "__main__":
    main()
