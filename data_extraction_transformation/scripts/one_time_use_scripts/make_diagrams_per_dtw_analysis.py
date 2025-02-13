import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt

def parse_args():
    parser = argparse.ArgumentParser(description="Handpick specific timeseries JSON files along with their annotations.json to run them on TCPCBench.")
    parser.add_argument('-i', '--input-folder', required=True, help="Path to the input folder of time series CSV files.")
    parser.add_argument('-c', '--clustered-signatures', required=True, help="Path to the input folder having the specific signatures.")
    parser.add_argument('-o', '--output-folder', required=True, help="Path to the output folder of the images of the time series.")
    return parser.parse_args()

def categorize_platform(platform):
    return platform.split('-')[0]  # Example categorization

def process_sample(dataf, output_dir):
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

    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(f"{output_dir}/signature_{sig_id}_plot.png", bbox_inches='tight')

def main():
    args = parse_args()
    
    for cluster_folder in os.listdir(args.clustered_signatures):
        cluster_path = os.path.join(args.clustered_signatures, cluster_folder)
        if os.path.isdir(cluster_path):
            csv_path = os.path.join(cluster_path, "cluster_assignments.csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path, header=None)  # Read CSV without column names
                df.columns = ['signature_id', 'group_label']  # Assign column names manually
                
                output_subfolder = os.path.join(args.output_folder, cluster_folder)
                #os.makedirs(output_subfolder, exist_ok=True)
                
                for _, row in df.iterrows():
                    sig_id = row['signature_id']
                    group_label = row['group_label']
                    output_subsubfolder = os.path.join(output_subfolder, group_label)
                    input_subfolder = os.path.join(args.input_folder, cluster_folder)
                    for root, _, files in os.walk(args.input_folder):
                        for file in files:
                            sig_id_from_file = file.split("_")[0]
                            if file.endswith(".csv") and sig_id == sig_id_from_file:
                                file_path = os.path.join(root, file)
                                data = pd.read_csv(file_path)
                                process_sample(data, output_subsubfolder)

def categorize_platform(platform):
    return platform.split('-')[0] if '-' in platform else platform

if __name__ == "__main__":
    main()

