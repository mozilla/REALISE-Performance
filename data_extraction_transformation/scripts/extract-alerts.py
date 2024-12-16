import requests
from datetime import datetime, timedelta
import pandas as pd
import json
from helper import append_strings, get_json, txt_to_list

'''
This function is used in the get_alert_info function. Provided the JSON of alerts related to a specific alert, it gets their ID and make them into a pipe '|' separated string
'''
def extract_alert_ids(alerts):
    alert_ids = ""
    if (len(alerts) > 0):
        alert_ids = "|"
        for i in alerts:
            alert_ids = alert_ids + str(i['id']) + '|'
    return alert_ids


'''
This function is used for extracting timestamps with an exception handling as some entries have the %Y-%m-%dT%H:%M:%S.%f timestamp format and others (entries from 2019 and prior) have %Y-%m-%dT%H:%M:%Stimestamp format
'''
def parse_timestamp(timestamp_str):
    formats_to_try = ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"]
    
    for fmt in formats_to_try:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            pass
    
'''
This function takes a JSON of a specific test measurment associated with a performance-related alert and extracts its attributes
'''
def get_test_info(json_test):
    test_characteristics = {'test_id': json_test['id'], 
    'test_status': json_test['status'],
    'test_profile_url': json_test['profile_url'],
    'test_prev_profile_url': json_test['prev_profile_url'],
    'test_is_regression': json_test['is_regression'],
    'test_prev_value': json_test['prev_value'],
    'test_new_value': json_test['new_value'],
    'test_t_value': json_test['t_value'],
    'test_amount_abs': json_test['amount_abs'],
    'test_amount_pct': json_test['amount_pct'],
    'test_summary_id': json_test['summary_id'],
    'test_related_summary_id': json_test['related_summary_id'],
    'test_manually_created': json_test['manually_created'],
    'test_classifier': json_test['classifier'],
    'test_starred': json_test['starred'],
    'test_classifier_email': json_test['classifier_email'],
    'test_noise_profile': json_test['noise_profile']
    }
    if (json_test['series_signature'] != None):
        test_characteristics['test_series_signature_id'] = json_test['series_signature']['id']
        test_characteristics['test_series_signature_framework_id'] = json_test['series_signature']['framework_id']
        test_characteristics['test_series_signature_signature_hash'] = json_test['series_signature']['signature_hash']
        test_characteristics['test_series_signature_machine_platform'] = json_test['series_signature']['machine_platform']
        test_characteristics['test_series_signature_suite'] = json_test['series_signature']['suite']
        test_characteristics['test_series_signature_test'] = json_test['series_signature']['test']
        test_characteristics['test_series_signature_lower_is_better'] = json_test['series_signature']['lower_is_better']
        test_characteristics['test_series_signature_has_subtests'] = json_test['series_signature']['has_subtests']
        test_characteristics['test_series_signature_option_collection_hash'] = json_test['series_signature']['option_collection_hash']
        test_characteristics['test_series_signature_tags'] = append_strings(json_test['series_signature']['tags'])
        test_characteristics['test_series_signature_extra_options'] = append_strings(json_test['series_signature']['extra_options'])
        test_characteristics['test_series_signature_measurement_unit'] = json_test['series_signature']['measurement_unit']
        test_characteristics['test_series_signature_suite_public_name'] = json_test['series_signature']['suite_public_name']
        test_characteristics['test_series_signature_test_public_name'] = json_test['series_signature']['test_public_name']
    if (json_test['prev_taskcluster_metadata'] != None and len(json_test['prev_taskcluster_metadata']) > 0):
        test_characteristics['test_prev_taskcluster_metadata_task_id'] = json_test['prev_taskcluster_metadata']['task_id']
        test_characteristics['test_prev_taskcluster_metadata_retry_id'] = json_test['prev_taskcluster_metadata']['retry_id']
    if (json_test['taskcluster_metadata'] != None and len(json_test['taskcluster_metadata']) > 0):
        test_characteristics['test_taskcluster_metadata_task_id'] = json_test['taskcluster_metadata']['task_id']
        test_characteristics['test_taskcluster_metadata_retry_id'] = json_test['taskcluster_metadata']['retry_id']
    if (json_test['backfill_record'] != None):
        test_characteristics['test_backfill_record_context'] = json_test['backfill_record']['context'],
        test_characteristics['test_backfill_record_status'] = json_test['backfill_record']['status'],
        test_characteristics['test_backfill_record_total_actions_triggered'] = json_test['backfill_record']['total_actions_triggered'],
        test_characteristics['test_backfill_record_total_backfills_failed'] = json_test['backfill_record']['total_backfills_failed'],
        test_characteristics['test_backfill_record_total_backfills_successful'] = json_test['backfill_record']['total_backfills_successful'],
        test_characteristics['test_backfill_record_total_backfills_in_progress'] = json_test['backfill_record']['total_backfills_in_progress'],
    return test_characteristics

'''
This function takes a JSON of a specific performance-related alert and extracts its attributes
'''
def get_alert_info(json_alert):
    alert_characteristics = {'alert_id': json_alert['id'], 
    'alert_push_id': json_alert['push_id'],
    'alert_prev_push_id': json_alert['prev_push_id'],
    'alert_creation_timestamp': json_alert['created'],
    'alert_first_triaged': json_alert['first_triaged'],
    'alert_triage_due_date': json_alert['triage_due_date'],
    'alert_repository': json_alert['repository'],
    'alert_framework': json_alert['framework'],
    'alert_triage_due_date': json_alert['triage_due_date'],
    'alert_related_alerts': extract_alert_ids(json_alert['related_alerts']),
    'alert_status': json_alert['status'],
    'alert_bug_number': json_alert['bug_number'],
    'alert_bug_due_date': json_alert['bug_due_date'],
    'alert_bug_updated': json_alert['bug_updated'],
    'alert_issue_tracker': json_alert['issue_tracker'],
    'alert_notes': json_alert['notes'],
    'alert_revision': json_alert['revision'],
    'alert_push_timestamp': json_alert['push_timestamp'],
    'alert_prev_push_revision': json_alert['prev_push_revision'],
    'alert_assignee_username': json_alert['assignee_username'],
    'alert_assignee_email': json_alert['assignee_email'],
    'alert_performance_tags': append_strings(json_alert['performance_tags'])
    }
    return alert_characteristics

url = "https://treeherder.mozilla.org/api/performance/alertsummary/"
json_data = get_json(url)
current_timestamp = datetime.now()
comp_time_stamp = current_timestamp
'''
This script extracts the perofrmance-related alerts from the time of running the script down until around 365 days ago
'''
threshold_timestamp = current_timestamp - timedelta(days=365)
'''
The following list contains the columns names of the CSV to be generated through this script
'''
columns = ['alert_id',
'alert_push_id',
'alert_prev_push_id',
'alert_creation_timestamp',
'alert_first_triaged',
'alert_triage_due_date',
'alert_repository',
'alert_framework',
'test_id',
'test_status',
'test_series_signature_id',
'test_series_signature_framework_id',
'test_series_signature_signature_hash',
'test_series_signature_machine_platform',
'test_series_signature_test',
'test_series_signature_suite',
'test_series_signature_lower_is_better',
'test_series_signature_has_subtests',
'test_series_signature_option_collection_hash',
'test_series_signature_tags',
'test_series_signature_extra_options',
'test_series_signature_measurement_unit',
'test_series_signature_suite_public_name',
'test_series_signature_test_public_name',
'test_prev_taskcluster_metadata_task_id',
'test_prev_taskcluster_metadata_retry_id',
'test_taskcluster_metadata_task_id',
'test_taskcluster_metadata_retry_id',
'test_profile_url',
'test_prev_profile_url',
'test_is_regression',
'test_prev_value',
'test_new_value',
'test_t_value',
'test_amount_abs',
'test_amount_pct',
'test_summary_id',
'test_related_summary_id',
'test_manually_created',
'test_classifier',
'test_starred',
'test_classifier_email',
'test_backfill_record_context',
'test_backfill_record_status',
'test_backfill_record_total_actions_triggered',
'test_backfill_record_total_backfills_failed',
'test_backfill_record_total_backfills_successful',
'test_backfill_record_total_backfills_in_progress',
'test_noise_profile',
'alert_related_alerts',
'alert_status',
'alert_bug_number',
'alert_bug_due_date',
'alert_bug_updated',
'alert_issue_tracker',
'alert_notes',
'alert_revision',
'alert_push_timestamp',
'alert_prev_push_revision',
'alert_assignee_username',
'alert_assignee_email',
'alert_performance_tags'
]
unique_signatures = set()
df = pd.DataFrame(columns=columns)
while ((comp_time_stamp >= threshold_timestamp) and (url != None)):
    payload = get_json(url)
    '''
    the API works in a pagination style, so each API response contains, along with a handful of data entries, the URL for the API endpoint containing the next data entries and so on and so fourth
    '''
    url = payload['next']
    '''
    earliest_date will be used to determine when to stop the alerts data extraction
    '''
    earliest_date = payload['results'][-1]['created']
    comp_time_stamp = parse_timestamp(earliest_date)
    '''the following loop will extract the alerts data obtained from one given API call
    '''
    for i in payload['results']:
        alert_info = get_alert_info(i)
        for j in i['alerts']:
            test_info = get_test_info(j)
            new_row = {}
            new_row.update(alert_info)
            new_row.update(test_info)
            unique_signatures.add(new_row['test_series_signature_id'])
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
df.to_csv('../datasets/alerts_data.csv', index=False)
sig_ids_str = ", ".join(list(list(map(lambda id: str(id), unique_signatures))))
'''
The signatures.txt file contains the signature IDs associated with performance alerts extracted through this script. This file will be used in the extract-timeseries.py file
'''
with open("signatures.txt", "w") as file:
    file.write(sig_ids_str)
