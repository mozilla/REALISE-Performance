import json
import os
import argparse
import sys
import random
import string
import decimal

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input-directory",
        help="Path of results input directory",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output-directory",
        help="Path of results output directory",
        required=True,
    )
    parser.add_argument(
        "-f",
        "--first-method",
        help="First method",
        required=True
    )
    parser.add_argument(
        "-om",
        "--other-methods",
        help="Other methods (space-separated)",
        nargs="+",
        required=True
    )
    parser.add_argument(
        "-t",
        "--threshold",
        help="Threshold of methods that have to agree with frst method to validate prediction (in decimal percentage)",
        required=True
    )
    parser.add_argument(
        "-m,
        "--margin",
        help="Margin to account for to conduct the comparison between the first method and the other ones",
        required=True
    )
    return parser.parse_args()


def main():
    args = parse_args()
    root = args.input_directory
    output_dir = args.output_directory
    first_method = args.first_method
    other_methods = args.other_methods
    threshold = args.threshold * len(other_methods)
    margin = args.margin
    # for signature_path in os.listdir(root):
    #     process_signature(root, signature_path, args.first_method, args.other_methods, args.output_directory, 'best')
    #     process_signature(root, signature_path, args.first_method, args.other_methods, args.output_directory, 'default')

if __name__ == "__main__":
    main()