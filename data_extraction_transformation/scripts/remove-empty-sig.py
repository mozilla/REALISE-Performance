import pandas as pd
import os

projects_folders = ["autoland1", "autoland2", "autoland3", "autoland4", "firefox-android", "mozilla-central", "mozilla-beta", "mozilla-release"]


for project in projects_folders:
    for signature_file in os.listdir('../datasets/' + project):
        signature_id = signature_file.split("_")[0]
        df = pd.read_csv('../datasets/' + project + '/' + signature_file)
        if (df.shape[0] == 0):
            os.remove('../datasets/' + project + '/' + signature_file)
            json_path = '../datasets-json/' + project + '/' + signature_id + '.json'
            if (os.path.exists(json_path)):
              os.remove(json_path)