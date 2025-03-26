import os
import shutil
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Copy JSON files based on a list of signature IDs")
    parser.add_argument('-i', '--input-folder', required=True, help="Path to the input JSON timeseries folder")
    parser.add_argument('-t', '--text-file', required=True, help="Path to the text file containing the signature IDs")
    parser.add_argument('-o', '--output-folder', required=True, help="Path to the output folder")
    return parser.parse_args()

def process_folder(input_folder, output_folder, text_file):
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Read the signature IDs from the text file
    try:
        with open(text_file, "r") as f:
            signature_ids = {line.strip() for line in f if line.strip()}  # Remove empty lines
    except Exception as e:
        print(f"Error reading text file: {e}")
        return

    # Copy matching JSON files
    copied_files = 0
    for signature_id in signature_ids:
        input_file = os.path.join(input_folder, f"{signature_id}.json")
        output_file = os.path.join(output_folder, f"{signature_id}.json")

        if os.path.exists(input_file):
            try:
                shutil.copy2(input_file, output_file)
                copied_files += 1
            except Exception as e:
                print(f"Error copying {input_file}: {e}")
        else:
            print(f"File not found: {input_file}")

    print(f"Copied {copied_files}/{len(signature_ids)} files.")

def main():
    args = parse_args()
    process_folder(args.input_folder, args.output_folder, args.text_file)

if __name__ == "__main__":
    main()
