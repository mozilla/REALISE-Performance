import os
import pandas as pd
import json


df_alerts = pd.read_csv('../datasets/rectified_alerts_data.csv', index_col=False)
projects_folders = ["autoland1", "autoland2", "autoland3", "autoland4", "firefox-android", "mozilla-central", "mozilla-beta", "mozilla-release"]
dest_folder = 'new-datasets-json'
os.makedirs('../' + dest_folder, exist_ok=True)

'''
with open('tp6_signatures.txt', 'r') as file:
    tp6_signatures = file.read().split(',')
with open('speedometer3_signatures.txt', 'r') as file:
    speedometer3_signatures = file.read().split(',')
'''

speedometer3_signatures = df_alerts[df_alerts['test_series_signature_suite'] == 'speedometer3']['test_series_signature_id'].unique().tolist()


desktop_list = ["amazon", "bing-search", "buzzfeed", "cnn", "docomo", "ebay", "espn", "expedia", "facebook", "fandom", "google-docs", "google-mail", "google-search", "google-slides", "imdb", "imgue", "instagram", "linkedin", "microsoft", "netflix", "nytimes", "office", "openai", "outlook", "paypal", "pinterest", "reddit", "samsung", "tiktok", "tumblr", "twitch", "twitter", "weather", "wikia", "wikipedia", "yahoo-mail", "youtube"]
mobile_list = ["allrecipes", "amazon", "amazon-search", "bild-de", "bing", "bing-search-restaurants", "booking", "cnn", "cnn-ampstories", "dailymail", "ebay-kleinanzeigen", "ebay-kleinanzeigen-search", "espn", "facebook", "facebook-cristiano", "google", "google-maps", "google-search-restaurants", "imdb", "instagram", "microsoft-support", "reddit", "sina", "stackoverflow", "wikipedia", "youtube", "youtube-watch"]
tp6_suites_list = list(set(desktop_list + mobile_list))
tp6_signatures = df_alerts[df_alerts['test_series_signature_suite'].isin(tp6_suites_list)]['test_series_signature_id'].unique().tolist()

filtered_signatures = speedometer3_signatures + tp6_signatures
filtered_signatures = [str(i) for i in filtered_signatures]

annotations = dict()
for project in projects_folders:
    for signature_file in os.listdir('../datasets/' + project):
        signature_id = signature_file.split("_")[0]
        if (isinstance(filtered_signatures, list) and signature_id in filtered_signatures):
            df = pd.read_csv('../datasets/' + project + '/' + signature_file)
            df['alert_status'] = df['alert_status'].apply(lambda x: 1 if x in ['TP', 'FN', 'SP'] else 0)
            df = df.sort_values(by='push_timestamp', ascending=True)
            indices = df.index[df['alert_status'] == 1].tolist()
            indices.sort()
            new_entry = {
                "1": indices
            }
            annotations[signature_id] = new_entry
            with open('../' + dest_folder + '/annotations.json', 'w') as file:
                json.dump(annotations, file, indent=4)
            n_obs = len(df)
            json_df = {
                "name": signature_id,
                "longname": f"{signature_id} timeseries",
                "n_obs": n_obs,
                "n_dim": 1,
                "time": {
                    "type": "string",
                    "format": "%Y-%m-%d %H:%M:%S",
                    "index": list(range(n_obs)),
                    "raw": df['push_timestamp'].tolist()
                },
                "series": [
                    {
                        "label": "Timeseries",
                        "type": "float",
                        "raw": df['value'].tolist()
                    }
                ]
            }
            signature_json_file = signature_id + ".json"
            os.makedirs('../' + dest_folder + '/' + project, exist_ok=True)
            with open('../' + dest_folder + '/' + project + '/' + signature_json_file, 'w') as file:
                json.dump(json_df, file, indent=4)