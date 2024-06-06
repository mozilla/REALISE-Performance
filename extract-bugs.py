from bugbug import bugzilla, db, bug_features
import pandas as pd

# Downland the latest version if the data set if it is not already downloaded
#db.download(bugzilla.BUGS_DB)

def append_strings(tags):
    if tags:
        return ", ".join(str(item) for item in tags)
    return ""

def process_element(the_json, the_attribute):
    try:
        return the_json[the_attribute]
    except:
        return ""

def extract_row(json_bug, isperfbug):
    bug_row = {'bug_id': process_element(json_bug, 'id'),
    'bug_resolution': process_element(json_bug, 'resolution'),
    'bug_type': process_element(json_bug, 'type'),
    'bug_component': process_element(json_bug, 'component'),
    'bug_summary': process_element(json_bug, 'summary'),
    'bug_classification': process_element(json_bug, 'classification'),
    'bug_status': process_element(json_bug, 'status'),
    'bug_creation_time': process_element(json_bug, 'creation_time'),
    'bug_url': process_element(json_bug, 'url'),
    'bug_last_change_time': process_element(json_bug, 'last_change_time'),
    'bug_severity': process_element(json_bug, 'severity'),
    'bug_priority': process_element(json_bug, 'priority'),
    'bug_product': process_element(json_bug, 'product'),
    'bug_is_confirmed': process_element(json_bug, 'is_confirmed'),
    'bug_votes': process_element(json_bug, 'votes'),
    'bug_is_open': process_element(json_bug, 'is_open'),
    'bug_assigned_to': process_element(json_bug, 'assigned_to'),
    'bug_cf_last_resolved': process_element(json_bug, 'cf_last_resolved'),
    'bug_cf_performance_impact': process_element(json_bug, 'cf_performance_impact'),
    'bug_version': process_element(json_bug, 'version'),
    'bug_whiteboard': process_element(json_bug, 'whiteboard'),
    'bug_platform': process_element(json_bug, 'platform'),
    'bug_keywords': append_strings(json_bug['keywords']),
    'IsPerformanceBug': isperfbug
    }
    return bug_row
columns = [
    'bug_id',
    'bug_resolution',
    'bug_type',
    'bug_component',
    'bug_summary',
    'bug_classification',
    'bug_status',
    'bug_creation_time',
    'bug_url',
    'bug_last_change_time',
    'bug_severity',
    'bug_priority',
    'bug_product',
    'bug_is_confirmed',
    'bug_votes',
    'bug_is_open',
    'bug_assigned_to',
    'bug_cf_last_resolved',
    'bug_cf_performance_impact',
    'bug_version',
    'bug_whiteboard',
    'bug_platform',
    'bug_keywords',
    'IsPerformanceBug'
]

df = pd.DataFrame(columns=columns)
for bug in bugzilla.get_bugs():
    '''
    if(bug_features.IsPerformanceBug().__call__(bug)):
        print("##################################")
        new_row = extract_row(bug)
        print(bug)
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    '''
    isperfbug = False
    if(bug_features.IsPerformanceBug().__call__(bug)):
        isperfbug = False
    new_row = extract_row(bug, isperfbug)
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
df.to_csv('all_bugs_data.csv', index=False)