import argparse
import json

def main():
    # Parse the annotations.json path
    parser = argparse.ArgumentParser(description="List sig_IDs from annotations.json in quoted format.")
    parser.add_argument('--annotations', required=True, help='Path to annotations.json file')
    args = parser.parse_args()

    # Load JSON
    with open(args.annotations, 'r') as f:
        annotations = json.load(f)

    # Get sig_IDs as quoted strings
    sig_ids = [f'"{sig_id}"' for sig_id in annotations.keys()]
    output = ", ".join(sig_ids)

    print(output)

if __name__ == "__main__":
    main()
