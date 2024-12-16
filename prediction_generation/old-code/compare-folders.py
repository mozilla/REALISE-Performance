import os
import sys

def compare_subfolders(folder1, folder2):
    # Get the subfolder names for each folder, excluding files
    subfolders1 = set([name for name in os.listdir(folder1) if os.path.isdir(os.path.join(folder1, name))])
    subfolders2 = set([name for name in os.listdir(folder2) if os.path.isdir(os.path.join(folder2, name))])

    # Find unique subfolders in each folder
    unique_to_folder1 = subfolders1 - subfolders2
    unique_to_folder2 = subfolders2 - subfolders1

    # Display results
    if unique_to_folder1:
        print(f"Subfolders unique to {folder1}:")
        for folder in unique_to_folder1:
            print(f"  - {folder}")
    else:
        print(f"No unique subfolders in {folder1}.")

    if unique_to_folder2:
        print(f"\nSubfolders unique to {folder2}:")
        for folder in unique_to_folder2:
            print(f"  - {folder}")
    else:
        print(f"No unique subfolders in {folder2}.")

    # Check for subfolders present in both
    common_subfolders = subfolders1 & subfolders2
    if common_subfolders:
        print(f"\nSubfolders common to both {folder1} and {folder2}:")
        for folder in common_subfolders:
            print(f"  - {folder}")
    else:
        print("No common subfolders found.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare_subfolders.py <folder1_path> <folder2_path>")
        sys.exit(1)

    folder1 = sys.argv[1]
    folder2 = sys.argv[2]

    if not os.path.isdir(folder1) or not os.path.isdir(folder2):
        print("Both arguments must be valid directory paths.")
        sys.exit(1)

    compare_subfolders(folder1, folder2)
