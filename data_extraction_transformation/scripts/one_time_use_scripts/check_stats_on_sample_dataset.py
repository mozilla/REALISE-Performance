import os 
import pandas as pd
import shutil
import argparse
 
def parse_args():
    parser = argparse.ArgumentParser(description="Provide stats on the sample dataset")
    parser.add_argument('-i', '--input-folder', help="Path to the input CSV timeseries folder")
    return parser.parse_args()

def process_folder(input_folder):
    global measurement_count
    global rev
    global avg_rev
    global uniq_sig
    for signature_file in os.listdir(input_folder):
        print(input_folder + '/' + signature_file)
        df = pd.read_csv(input_folder + '/' + signature_file, index_col=False)
        uniq_sig += 1
        measurement_count += len(df)
        avg_rev += df['revision'].nunique()
        rev = rev + df["revision"].unique().tolist()

def main():
    global measurement_count
    global rev
    global avg_rev
    global uniq_sig
    uniq_sig = 0
    measurement_count = 0
    rev = []
    args = parse_args()
    avg_rev = 0
    input_folder = args.input_folder
    process_folder(input_folder)
    print("Revision count")
    print(len(set(rev)))
    print("Revision average")
    print(avg_rev / uniq_sig)
    print("Measurement count")
    print(measurement_count)
    print("Unique signatures")
    print(uniq_sig)
    print("Average measurement count per time series")
    print(measurement_count / uniq_sig)
if __name__ == "__main__":
    main()