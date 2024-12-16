import os
import shutil

top_folder = "aaaa"

dest = "bbbb"

for method_dir in os.listdir(top_folder):
    print("method_dir: ")
    print(method_dir)
    folder_path = os.path.join(top_folder, method_dir)
    for sig_dir in os.listdir(folder_path):
        print("sig_dir: ")
        print(sig_dir)
        subfolder_path = os.path.join(folder_path, sig_dir)
        dest_path1 = os.path.join(dest, sig_dir)
        for bestdefaulmethod_dir in os.listdir(subfolder_path):
            print("bestdefaulmethod_dir: ")
            print(bestdefaulmethod_dir)
            dest_path = os.path.join(dest_path1, bestdefaulmethod_dir)
            source_path = os.path.join(subfolder_path, bestdefaulmethod_dir)
            print("source_path: ")
            print(source_path)
            print("dest_path: ")
            print(dest_path)
            if os.path.isdir(source_path):
                if not os.path.isdir(dest_path):
                    shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
