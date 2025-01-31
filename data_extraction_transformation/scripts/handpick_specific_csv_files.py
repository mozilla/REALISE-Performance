import os
import shutil
import pandas as pd
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="Handpick specific timeseries CSV files along with their annotations.json to run them on TCPCBench.")
    parser.add_argument('-o', '--output-folder', help="Path to the output folder of time series CSV files.")
    parser.add_argument('-i', '--input-folder', help="Path to the input folder of time series CSV files.")
    parser.add_argument('-f', '--filtered-signatures-file', help="Path to the CSV file with the signatures to handpick (it has to have a column signature_id).")

    return parser.parse_args()

'''main_dir = "../datasets-original-annotated-2-aggregated-min-json"
dest = "../filtered-datasets-original-annotated-2-aggregated-min-json"
filtered_signatures_file = "../datasets/more_than_10_alert_summaries_speedometer3_tp6.csv"'''


def main():
    args = parse_args()
    main_dir = args.input_folder
    filtered_signatures_file = args.filtered_signatures_file
    dest = args.output_folder
    df = pd.read_csv(filtered_signatures_file)
    signatures = df['signature_id'].unique().tolist()
    signatures = list(map(str, signatures))


    subfolders = [os.path.join(main_dir, folder) for folder in os.listdir(main_dir) if os.path.isdir(os.path.join(main_dir, folder))]
    print(subfolders)
    if not os.path.exists(dest):
        os.makedirs(dest)
    counter = 0
    for subfolder in subfolders:
        for root, _, files in os.walk(subfolder):
            for file in files:
                if file.endswith(".csv"):
                    csv_file_path = os.path.join(root, file)
                    file_name = os.path.splitext(file)[0]
                    signature = file_name.split("_")[0]
                    if signature in signatures:
                        shutil.copy(csv_file_path, dest)
                        #print("df_list.append(pd.read_csv(\"" + "/content/" + file_name + ".csv" + "\"))")
                        counter += 1
    print("Number of copied CSV files:")
    print(counter)


if __name__ == "__main__":
    main() 