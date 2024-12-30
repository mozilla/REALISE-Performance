'''
# List of provided elements
input_list = [
    'test_taskcluster_metadata_retry_id', 'test_backfill_record_total_actions_triggered',
    'alert_issue_tracker', 'alert_prev_push_id', 'alert_triage_due_date', 'test_series_signature_tags',
    'test_series_signature_option_collection_hash', 'test_t_value', 'alert_revision',
    'test_manually_created', 'test_backfill_record_status', 'test_series_signature_suite',
    'alert_creation_timestamp', 'test_series_signature_has_subtests',
    'test_series_signature_machine_platform', 'test_prev_taskcluster_metadata_task_id',
    'test_backfill_record_context', 'test_classifier_email', 'test_starred', 'test_noise_profile',
    'test_status', 'test_summary_id', 'test_amount_pct', 'test_classifier', 'alert_assignee_email',
    'alert_prev_push_revision', 'test_taskcluster_metadata_task_id',
    'test_backfill_record_total_backfills_failed', 'alert_repository',
    'test_series_signature_measurement_unit', 'alert_bug_due_date',
    'alert_related_alerts', 'alert_id', 'test_series_signature_framework_id', 'alert_status',
    'test_series_signature_signature_hash', 'alert_push_id', 'test_id', 'test_series_signature_test',
    'test_backfill_record_total_backfills_successful', 'test_prev_profile_url',
    'test_prev_taskcluster_metadata_retry_id', 'test_series_signature_suite_public_name',
    'alert_first_triaged', 'test_amount_abs', 'alert_bug_number',
    'test_series_signature_test_public_name', 'test_related_summary_id',
    'alert_bug_updated', 'alert_performance_tags', 'alert_notes', 'test_is_regression',
    'test_profile_url', 'alert_assignee_username', 'test_series_signature_extra_options',
    'test_prev_value', 'test_series_signature_lower_is_better', 'test_new_value',
    'test_backfill_record_total_backfills_in_progress', 'alert_framework'
]

# Create the dictionary with the transformation rules
output_dict = {}

for item in input_list:
    if item.startswith('alert_'):
        # If it starts with 'alert_', prefix with 'alert_summary_'
        new_key = 'alert_summary_' + item[6:]  # Remove 'alert_' and add 'alert_summary_'
    elif item.startswith('test_'):
        # If it starts with 'test_', prefix with 'single_alert_'
        new_key = 'single_alert_' + item[5:]  # Remove 'test_' and add 'single_alert_'
    else:
        # If no prefix is found (though it's not expected here)
        new_key = item
    
    # Add to the dictionary
    output_dict[item] = new_key

# Sort the dictionary by the keys alphabetically and create a new dictionary
sorted_output_dict = {key: output_dict[key] for key in sorted(output_dict)}

# Print the resulting dictionary with sorted keys
for key, value in sorted_output_dict.items():
    print(f"'{key}': '{value}',")
'''

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