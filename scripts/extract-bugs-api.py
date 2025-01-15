#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author: Mohamed Bilel Besbes
Date: 2025-01-02
"""

import argparse
import csv
import json
import requests
import pandas as pd

def parse_args():
    parser = argparse.ArgumentParser(description="Fetch bug details from an API and save to a CSV file.")
    parser.add_argument('-a', '--alerts-file', help="Path to the input CSV alerts file.")
    parser.add_argument('-b', '--bugs-file', help="Path to the output CSV bugs file.")
    return parser.parse_args()

def fetch_json_from_api(api_url):
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return None

def flatten_json(bug):
    try:
        flat_bug = {
            'id': bug.get('id'),
            'type': bug.get('type'),
            'summary': bug.get('summary'),
            'status': bug.get('status'),
            'priority': bug.get('priority'),
            'severity': bug.get('severity'),
            'creator': bug.get('creator'),
            'assigned_to': bug.get('assigned_to'),
            'creation_time': bug.get('creation_time'),
            'last_change_time': bug.get('last_change_time'),
            'component': bug.get('component'),
            'product': bug.get('product'),
            'resolution': bug.get('resolution'),
            'is_confirmed': bug.get('is_confirmed'),
            'platform': bug.get('platform'),
            'op_sys': bug.get('op_sys'),
            'assigned_to_name': bug.get('assigned_to_detail', {}).get('real_name', None),
            'assigned_to_email': bug.get('assigned_to_detail', {}).get('email', None),
            'cc': ', '.join(bug.get('cc', [])),
            'cc_detail': ', '.join([cc.get('email', '') for cc in bug.get('cc_detail', [])]),
            'flags': ', '.join([flag.get('name', '') for flag in bug.get('flags', [])]),
            'classification': bug.get('classification', None),
            'triage_owner': bug.get('triage_owner', None),
            'comment_count': bug.get('comment_count', None),
            'keywords': ', '.join(bug.get('keywords', [])),
            'depends_on': ', '.join(map(str, bug.get('depends_on', []))),
            'blocks': ', '.join(map(str, bug.get('blocks', []))),
            'duplicates': ', '.join(map(str, bug.get('duplicates', []))),
            'creator_name': bug.get('creator_detail', {}).get('real_name', None),
            'creator_email': bug.get('creator_detail', {}).get('email', None)
        }
        return flat_bug
    except Exception as e:
        print(f"Error flattening bug: {e}")
        return {}

def write_to_csv(bugs, csv_file):
    try:
        with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
            if bugs:
                writer = csv.DictWriter(file, fieldnames=bugs[0].keys())
                writer.writeheader()
                writer.writerows(bugs)
        print(f"Data has been written to {csv_file}")
    except Exception as e:
        print(f"Error writing to CSV: {e}")

def main():
    args = parse_args()
    alerts_file = args.alerts_file
    bugs_file = args.bugs_file

    try:
        # Read the alerts DataFrame
        alerts_df = pd.read_csv(alerts_file)

        # Process the bug IDs
        bug_ids = set(alerts_df['alert_summary_bug_number'].dropna().astype(int).tolist())

        all_bugs = []
        print("INITIATING RESPONSE COLLECTION FROM API")
        for bug_id in bug_ids:
            print(bug_id)
            # Prepare API URL for each bug ID
            api_url = f"https://bugzilla.mozilla.org/rest/bug?id={bug_id}"

            # Fetch JSON data for the bug
            json_data = fetch_json_from_api(api_url)
            if json_data and 'bugs' in json_data:
                for bug in json_data['bugs']:
                    flat_bug = flatten_json(bug)
                    all_bugs.append(flat_bug)
            else:
                print(f"No data found for bug ID {bug_id}.")
        print("DATA COLLECTION DONE")
        print("INTIATING DATA FLATTENING")
        # Write all collected and flattened bugs to CSV
        if all_bugs:
            write_to_csv(all_bugs, bugs_file)
        else:
            print("No bugs to write to the CSV file.")

    except Exception as e:
        print(f"Error in processing: {e}")

if __name__ == "__main__":
    main()
