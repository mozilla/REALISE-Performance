from bugbug import bugzilla, db, bug_features
import pandas as pd
import helper

'''
This function is dedicated for extracting JSON attrbutes that do not exist always with exception handling
'''
def process_element(the_json, the_attribute):
    try:
        return the_json[the_attribute]
    except:
        return ""

'''
Thsi function extracts the attributes of a given bug from the provided JSON and labels it as a performance-related bug or not. It reutrns a dictionary to be appended into the bug dataframe to be converted into a CSV
'''
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

'''
The following list contains the columns names of the CSV to be generated through this script
'''
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


'''
Downlanding the latest version of bugs data using bugbug
'''
db.download(bugzilla.BUGS_DB)
df = pd.DataFrame(columns=columns)

'''
Only bugs that are asosciated with alerts extracted through extract-alerts.py will be kept. note that bugs.txt contains the IDs of bugs associated with alerts obtained from the same Python script previously mentioned
'''
bugs_ids = txt_to_list("bugs.txt")

for bug in bugzilla.get_bugs():
    if str(bug["id"]) in bugs_ids:
        isperfbug = False
        if(bug_features.IsPerformanceBug().__call__(bug)):
            isperfbug = True
        new_row = extract_row(bug, isperfbug)
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
df.to_csv('../datasets/bugs_data.csv', index=False)