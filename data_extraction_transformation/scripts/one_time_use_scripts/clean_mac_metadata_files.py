import os
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Script to do sanity checks on the data for the artifact challenge submission")
    parser.add_argument('-i', '--input-folder', required=True, help="Path to the input dataset folder (labeled data)")
    return parser.parse_args()
    
def main():
    args = parse_args()
    input_folder = args.input_folder
    for subdir, dirs, files in os.walk(input_folder):
        for file in files:
            if file.startswith('._'):
                file_path = os.path.join(subdir, file)
                os.remove(file_path)
                print(f"Deleted: {file_path}")

if __name__ == "__main__":
    main()