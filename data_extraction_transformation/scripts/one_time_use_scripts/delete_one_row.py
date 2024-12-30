import os
import pandas as pd
import shutil
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Delete one row")
    parser.add_argument('-f', '--file-location', required=True, help="File location")
    parser.add_argument('-r', '--revision-value', required=True, help="Revision to delete")
    return parser.parse_args()

def main():
    args = parse_args()
    file_location = args.file_location
    revision_value = args.revision_value
    df = pd.read_csv(file_location)
    df = df[df['alert_revision'] != revision_value]
    df.to_csv(file_location, index=False)

if __name__ == "__main__":
    main()