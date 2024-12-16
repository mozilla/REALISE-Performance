import os
import shutil

# Define the paths
source_directory = 'project1/datasets-scaled'  # Directory containing the subdirectories
target_directory = 'scaled-merged'              # Directory to merge all files into

# Create target directory if it doesn't exist
os.makedirs(target_directory, exist_ok=True)

# Iterate through each subdirectory in the source directory
for subdir in os.listdir(source_directory):
    subdir_path = os.path.join(source_directory, subdir)
    
    # Only proceed if it is a directory
    if os.path.isdir(subdir_path):
        for filename in os.listdir(subdir_path):
            file_path = os.path.join(subdir_path, filename)
            
            # Move each file to the target directory
            if os.path.isfile(file_path):  # Ensure it's a file, not a directory
                shutil.move(file_path, os.path.join(target_directory, filename))
