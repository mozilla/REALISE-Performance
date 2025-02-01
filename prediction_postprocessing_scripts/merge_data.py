import os
import shutil

# Define the base folder and the subfolders you want to merge
base_dir = "../data/temp_data/copy_results_average_aggregated_195"
ding_dir = os.path.join(base_dir, "all_best_default_mixed_5_cpd")
os.makedirs(ding_dir, exist_ok=True)

# List of subfolders to merge into 'ding'
folders_to_merge = ["all_best_default"]
# folders_to_merge = ["union_kcpa_bocpd", "union_mongodb_bocpd","union_mongodb_kcpa","union_mongodb_pelt","union_pelt_bocpd","union_pelt_kcpa"]
# Helper function to merge the contents of two directories
def merge_folders(src_dir, dest_dir):
    for root, dirs, files in os.walk(src_dir):
        # Get the relative path of the current folder from the source directory
        relative_path = os.path.relpath(root, src_dir)
        
        # Construct the corresponding destination directory path
        dest_folder = os.path.join(dest_dir, relative_path)
        
        # Create the destination directory if it doesn't exist
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)
        
        # Move or copy files from the source to the destination
        for file in files:
            # Skip files that start with '._'
            if file.startswith("._"):
                continue
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest_folder, file)
            
            # If file already exists, skip (to avoid overwriting)
            if not os.path.exists(dest_file):
                shutil.copy2(src_file, dest_file)

# Merge each folder in the list into 'ding'
for folder_name in folders_to_merge:
    folder_path = os.path.join(base_dir, folder_name)
    for subfolder in os.listdir(folder_path):
        subfolder_path = os.path.join(folder_path, subfolder)
        if os.path.isdir(subfolder_path):
            merge_folders(subfolder_path, os.path.join(ding_dir, subfolder))

print('Merge complete')
