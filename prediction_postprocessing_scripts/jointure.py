import os
import shutil
import argparse


'''
top_folder = "../../data/temp_data/clean_data/new_online_results"
dest = "../../data/temp_data/clean_data/joined_results_copy"
'''

parser = argparse.ArgumentParser(description="Copy nested directories from top_folder to dest, preserving structure.")
parser.add_argument('--top-folder', required=True, help='Path to the top-level folder containing method directories')
parser.add_argument('--dest', required=True, help='Destination directory for the copied data')

args = parser.parse_args()
top_folder = args.top_folder
dest = args.dest

for method_dir in os.listdir(top_folder):
    folder_path = os.path.join(top_folder, method_dir)
    if not os.path.isdir(folder_path):
        continue  # Skip files like .DS_Store

    print("method_dir: ")
    print(method_dir)

    for sig_dir in os.listdir(folder_path):
        subfolder_path = os.path.join(folder_path, sig_dir)
        if not os.path.isdir(subfolder_path):
            continue  # Skip files, specifically .DS_Store

        print("sig_dir: ")
        print(sig_dir)

        dest_path1 = os.path.join(dest, sig_dir)

        for bestdefaulmethod_dir in os.listdir(subfolder_path):
            source_path = os.path.join(subfolder_path, bestdefaulmethod_dir)
            if not os.path.isdir(source_path):
                continue  # Again, skip files

            print("bestdefaulmethod_dir: ")
            print(bestdefaulmethod_dir)
            print("source_path: ")
            print(source_path)

            dest_path = os.path.join(dest_path1, bestdefaulmethod_dir)
            print("dest_path: ")
            print(dest_path)

            if not os.path.isdir(dest_path):
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
