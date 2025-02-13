import matplotlib.pyplot as plt
import pandas as pd
import argparse
import os

import pandas as pd
import matplotlib.pyplot as plt


def categorize_platform(platform):
    platform_lower = platform.lower()

    if 'win' in platform_lower:
        return 'Windows'
    elif 'osx' in platform_lower or 'osx' in platform_lower:
        return 'macOS'
    elif 'linux' in platform_lower:
        return 'Linux'
    elif 'android' in platform_lower:
        return 'Android'
    else:
        return 'Others'


def display_sample(dataf, output_folder):
    sig_id = dataf['signature_id'].unique()[0]
    machine_platform = dataf['machine_platform'].unique()[0]
    machine_platform_general = categorize_platform(machine_platform)
    framework_id = dataf['framework_id'].unique()[0]
    repository_name = dataf['repository_name'].unique()[0]
    test = dataf['test'].unique()[0]
    application = dataf['application'].unique()[0]
    suite = dataf['suite'].unique()[0]
    option_collection_hash = dataf['option_collection_hash'].unique()[0]
    TP = len(dataf[dataf['alert_summary_status_general'] == "TP"])
    FN = len(dataf[dataf['alert_summary_status_general'] == "FN"])
    FP = len(dataf[dataf['alert_summary_status_general'] == "FP"])
    SP = len(dataf[dataf['alert_summary_status_general'] == "SP"])

    sample_df = dataf.copy()
    sample_df['push_timestamp'] = pd.to_datetime(sample_df['push_timestamp'])
    sample_df.set_index('push_timestamp', inplace=True)
    
    # Sorting to maintain order
    sample_df.sort_index(inplace=True)

    # Define color mapping
    color_mapping = {
        'TP': 'green',
        'FP': 'red',
        'SP': 'grey',
        'TN': 'blue'
    }

    # Plotting
    plt.figure(figsize=(20, 10))
    
    # Plot all values as a scatter plot for better alignment
    plt.scatter(sample_df.index, sample_df['value'], 
                color=[color_mapping.get(status, 'black') for status in sample_df['alert_summary_status_general']], 
                alpha=0.6, label="Measurements")
    
    # Draw vertical lines for change points (TP, FP, SP)
    for status in ['TP', 'FP', 'SP']:
        change_points = sample_df[sample_df['alert_summary_status_general'] == status].index
        for cp in change_points:
            plt.axvline(x=cp, color=color_mapping[status], linestyle='--', alpha=0.6)

    plt.title('Time Series Plot')
    plt.xlabel('Date')
    plt.ylabel(f'Test measurement values associated with signature ID {sig_id}')
    plt.grid(axis='y')

    # Set limits
    plt.xlim(sample_df.index.min(), sample_df.index.max())
    plt.ylim(bottom=0, top=sample_df['value'].max() * 1.2)  # Slightly above max for visibility

    # X-axis formatting
    plt.xticks(pd.date_range(start=sample_df.index.min(), end=sample_df.index.max(), freq='W-MON'), 
               rotation=45)
    plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))

    # Add text box for metadata
    text_content = f"Framework ID: {framework_id}\n" \
                   f"Repository: {repository_name}\n" \
                   f"Platform (general): {machine_platform_general}\n" \
                   f"Platform: {machine_platform}\n" \
                   f"Test: {test}\n" \
                   f"Suite: {suite}\n" \
                   f"Application: {application}\n" \
                   f"TP count: {TP}\n" \
                   f"FP count: {FP}\n" \
                   f"FN count: {FN}\n" \
                   f"SP count: {SP}"

    plt.text(0.98, 0.98, text_content, ha='right', va='top', transform=plt.gca().transAxes, fontsize=12,
             family='monospace', bbox=dict(facecolor='white', alpha=0.7, edgecolor='black', boxstyle='round,pad=0.5'))


    output_path_per_repo = f"{output_folder}/per_repo/{repository_name}"
    os.makedirs(output_path_per_repo, exist_ok=True)
    plt.savefig(f"{output_path_per_repo}/signature_{sig_id}_plot.png", bbox_inches='tight')

    output_path_per_test = f"{output_folder}/per_test/{test}"
    os.makedirs(output_path_per_test, exist_ok=True)
    plt.savefig(f"{output_path_per_test}/signature_{sig_id}_plot.png", bbox_inches='tight')

    output_path_per_platform = f"{output_folder}/per_platform/{machine_platform_general}"
    os.makedirs(output_path_per_platform, exist_ok=True)
    plt.savefig(f"{output_path_per_platform}/signature_{sig_id}_plot.png", bbox_inches='tight')

    output_path_per_app = f"{output_folder}/per_app/{application}"
    os.makedirs(output_path_per_app, exist_ok=True)
    plt.savefig(f"{output_path_per_app}/signature_{sig_id}_plot.png", bbox_inches='tight')


    output_path_per_compound = f"{output_folder}/per_compound/{application}/{repository_name}/{machine_platform_general}"
    os.makedirs(output_path_per_compound, exist_ok=True)
    plt.savefig(f"{output_path_per_compound}/signature_{sig_id}_plot.png", bbox_inches='tight')
    plt.close()

def parse_args():
    parser = argparse.ArgumentParser(description="Handpick specific timeseries JSON files along with their annotations.json to run them on TCPCBench.")
    parser.add_argument('-i', '--input-folder', help="Path to the input folder of time series CSV files.")
    parser.add_argument('-s', '--filtered-signatures', help="Path to the input file having the specific signatures.")
    parser.add_argument('-o', '--output-folder', help="Path to the output folder of the images of the time series.")
    return parser.parse_args()

def main():
    args = parse_args()
    input_folder = args.input_folder
    filtered_signatures = args.filtered_signatures
    output_folder = args.output_folder
    os.makedirs(output_folder, exist_ok=True)
    subfolders = [os.path.join(input_folder, folder) for folder in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, folder))]
    if not subfolders:
        subfolders = [input_folder]  # Add input_folder if no subfolders exist
    attributes = dict()

    with open(filtered_signatures, 'r') as file:
            filtered_signatures_list = file.read().splitlines()
    for subfolder in subfolders:
        for root, _, files in os.walk(subfolder):
            for file in files:
                sig_id = file.split("_")[0]
                if sig_id in filtered_signatures_list:
                    csv_file_path = os.path.join(root, file)
                    df = pd.read_csv(csv_file_path)
                    display_sample(df, output_folder)

if __name__ == "__main__":
    main()