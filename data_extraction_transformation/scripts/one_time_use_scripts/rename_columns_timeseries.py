#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: Mohamed Bilel Besbes
Date: 2024-12-18
"""
import argparse
import pandas as pd
import os


def parse_args():
    parser = argparse.ArgumentParser(description="Check if there are alerts adjacent to the SP datapoints")
    parser.add_argument('-i', '--input-folder', required=True, help="Path to the input timeseries folder")
    parser.add_argument('-o', '--input-folder', required=True, help="Path to the output timeseries folder")
    return parser.parse_args()

def process_folder(input_folder, output_folder, folder):
    common_mapping_record = {
        'alert_assignee_email': 'alert_summary_assignee_email',
        'alert_assignee_username': 'alert_summary_assignee_username',
        'alert_bug_due_date': 'alert_summary_bug_due_date',
        'alert_bug_number': 'alert_summary_bug_number',
        'alert_bug_updated': 'alert_summary_bug_updated',
        'alert_creation_timestamp': 'alert_summary_creation_timestamp',
        'alert_first_triaged': 'alert_summary_first_triaged',
        'alert_framework': 'alert_summary_framework',
        'alert_id': 'alert_summary_id',
        'alert_issue_tracker': 'alert_summary_issue_tracker',
        'alert_notes': 'alert_summary_notes',
        'alert_performance_tags': 'alert_summary_performance_tags',
        'alert_prev_push_id': 'alert_summary_prev_push_id',
        'alert_prev_push_revision': 'alert_summary_prev_push_revision',
        'alert_push_id': 'alert_summary_push_id',
        'alert_related_alerts': 'alert_summary_related_alerts',
        'alert_repository': 'alert_summary_repository',
        'alert_revision': 'alert_summary_revision',
        'alert_status': 'alert_summary_status',
        'alert_triage_due_date': 'alert_summary_triage_due_date',
        'test_amount_abs': 'single_alert_amount_abs',
        'test_amount_pct': 'single_alert_amount_pct',
        'test_backfill_record_context': 'single_alert_backfill_record_context',
        'test_backfill_record_status': 'single_alert_backfill_record_status',
        'test_backfill_record_total_actions_triggered': 'single_alert_backfill_record_total_actions_triggered',
        'test_backfill_record_total_backfills_failed': 'single_alert_backfill_record_total_backfills_failed',
        'test_backfill_record_total_backfills_in_progress': 'single_alert_backfill_record_total_backfills_in_progress',
        'test_backfill_record_total_backfills_successful': 'single_alert_backfill_record_total_backfills_successful',
        'test_classifier': 'single_alert_classifier',
        'test_classifier_email': 'single_alert_classifier_email',
        'test_id': 'single_alert_id',
        'test_is_regression': 'single_alert_is_regression',
        'test_manually_created': 'single_alert_manually_created',
        'test_new_value': 'single_alert_new_value',
        'test_noise_profile': 'single_alert_noise_profile',
        'test_prev_profile_url': 'single_alert_prev_profile_url',
        'test_prev_taskcluster_metadata_retry_id': 'single_alert_prev_taskcluster_metadata_retry_id',
        'test_prev_taskcluster_metadata_task_id': 'single_alert_prev_taskcluster_metadata_task_id',
        'test_prev_value': 'single_alert_prev_value',
        'test_profile_url': 'single_alert_profile_url',
        'test_related_summary_id': 'single_alert_related_summary_id',
        'test_series_signature_extra_options': 'single_alert_series_signature_extra_options',
        'test_series_signature_framework_id': 'single_alert_series_signature_framework_id',
        'test_series_signature_has_subtests': 'single_alert_series_signature_has_subtests',
        'test_series_signature_lower_is_better': 'single_alert_series_signature_lower_is_better',
        'test_series_signature_machine_platform': 'single_alert_series_signature_machine_platform',
        'test_series_signature_measurement_unit': 'single_alert_series_signature_measurement_unit',
        'test_series_signature_option_collection_hash': 'single_alert_series_signature_option_collection_hash',
        'test_series_signature_signature_hash': 'single_alert_series_signature_signature_hash',
        'test_series_signature_suite': 'single_alert_series_signature_suite',
        'test_series_signature_suite_public_name': 'single_alert_series_signature_suite_public_name',
        'test_series_signature_tags': 'single_alert_series_signature_tags',
        'test_series_signature_test': 'single_alert_series_signature_test',
        'test_series_signature_test_public_name': 'single_alert_series_signature_test_public_name',
        'test_starred': 'single_alert_starred',
        'test_status': 'single_alert_status',
        'test_summary_id': 'single_alert_summary_id',
        'test_t_value': 'single_alert_t_value',
        'test_taskcluster_metadata_retry_id': 'single_alert_taskcluster_metadata_retry_id',
        'test_taskcluster_metadata_task_id': 'single_alert_taskcluster_metadata_task_id'
    }
    alerts_csv_specific_mapping = {
        'alert_push_timestamp': 'push_timestamp',
        'test_series_signature_id': 'signature_id'
    }
    timeseries_specific_mapping = {
        'alert_status_general': 'alert_summary_status_general',
        'test_status_general': 'single_alert_status_general'
    }
    all_cols_renaming = {**common_mapping_record, **timeseries_specific_mapping}
    for signature_file in os.listdir(input_folder + '/' + folder):
        df = pd.read_csv(input_folder + '/' + folder + '/' + signature_file, index_col=False)
        df.rename(columns=all_cols_renaming, inplace=True)
        df = df.drop(columns=['single_alert_status_general'])
        df.to_csv(output_folder + '/' + folder + '/' + signature_file, index_col=False)



def main():
    args = parse_args()
    input_folder = args.input_folder
    output_folder = args.output_folder
    projects_folders_mapping = {"autoland": ["autoland1", "autoland2", "autoland3", "autoland4"], "firefox-android": ["firefox-android"], "mozilla-beta": ["mozilla-beta"]}
    if projects_folders_mapping:
        for project in projects_folders_mapping:
            for folder in projects_folders_mapping[project]:
                process_folder(input_folder, output_folder, folder)
if __name__ == "__main__":
    main()