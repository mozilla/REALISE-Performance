import os
import argparse

def count_files_in_subfolders(input_folder):
    subfolder_counts = {}

    for entry in os.scandir(input_folder):
        if entry.is_dir():
            subfolder = entry.path
            count = sum(
                len(files) for _, _, files in os.walk(subfolder)
            )
            subfolder_counts[entry.name] = count

    return subfolder_counts

def main():
    parser = argparse.ArgumentParser(description="Count the number of files in each subfolder of a given folder.")
    parser.add_argument('-i', '--input-folder', help='Path to the input folder', required=True)
    args = parser.parse_args()

    counts = count_files_in_subfolders(args.input_folder)

    for subfolder, count in counts.items():
        print(f"{subfolder}: {count} files")

if __name__ == "__main__":
    main()
