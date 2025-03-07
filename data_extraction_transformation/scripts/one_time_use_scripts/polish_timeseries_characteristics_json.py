import argparse
import os
import json

def parse_args():
    parser = argparse.ArgumentParser(description="Polish the entries in the JSON file of the time series characteristics.")
    parser.add_argument('-i', '--input-file', help="Path to the input JSON file.")
    parser.add_argument('-o', '--output-file', help="Path to the output JSON file.")
    return parser.parse_args()


def main():
    args = parse_args()
    input_file = args.input_file
    output_file = args.output_file

    framework_mapping = {
        1: "Talos",
        2: "Build Metrics",
        4: "AWSY",
        6: "Platform Microbench",
        10: "Raptor",
        11: "JS Bench",
        12: "DevTools",
        13: "Browsertime",
        15: "MozPerfTest",
        16: "FXRecord"
    }

    repository_mapping = {
        "mozilla-release": "Mozilla Release",
        "mozilla-central": "Mozilla Central",
        "firefox-android": "Firefox Android",
        "mozilla-beta": "Mozilla Beta",
        "autoland": "Autoland"
    }

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    for key, entry in data.items():
        if "framework" in entry and entry["framework"] in framework_mapping:
            entry["framework"] = framework_mapping[entry["framework"]]
        if "repository" in entry and entry["repository"] in repository_mapping:
            entry["repository"] = repository_mapping[entry["repository"]]
        if "platform" in entry and entry["platform"]:
            entry["platform"] = entry["platform"].replace("-", " ").title()
        if "tags" in entry and isinstance(entry["tags"], str):
            entry["tags"] = entry["tags"].replace("|", "")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print("Transformation complete. Data saved to 'transformed_data.json'.")

if __name__ == "__main__":
    main()