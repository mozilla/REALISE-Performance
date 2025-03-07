import sys
import json
import requests
import re
import pandas as pd
from pathlib import Path

'''
Class for the AnnotateChange import format.
'''
class AnnotateChange:

    def __init__(self, name, data):
        self.n_dim = 1
        self.name = name
        self.longname = self.name
        measurements = data
        self.series = [{
            'label': 'V1',
            'type': 'float',
            'raw': measurements
        }]
        self.n_obs = len(measurements)
        self.time = {'index': [i for i in range(self.n_obs)]}

'''
Manages login and uploading of datasets.
'''
class Upload:

    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password

        # Initialize the session
        self.session = requests.Session()

    def login(self):
        login_url = self.base_url + 'auth/login'

        # Get the csrf_token
        r = self.session.get(login_url)
        self.token = re.search(r'"csrf_token" type="hidden" value="([^"]+)"',
                r.text).group(1)

        # Login
        payload = {
            'csrf_token': self.token,
            'username': self.username,
            'password': self.password,
            'submit': 'Sign+In',
        }
        r = self.session.post(login_url, data=payload)

        if 'Welcome to' not in r.text:
            return False
        return True

    def upload(self, data):
        payload = {
            'csrf_token': self.token,
            'submit': 'Upload',
        }
        files = {
            'file_': ('test.json', json.dumps(data), 'application/json'),
        }
        r = self.session.post(self.base_url + 'admin/add',
                files=files, data=payload)

        m = re.search(r'"help-block">([^<]+)<', r.text)
        if m is not None:
            print(m.group(1))
            return False
        return True


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print('Usage:\npython {} <*-.csv> <base url> <username> <password>'\
                .format(sys.argv[0]))
        exit(0)

    # Read the CSV
    csv_file = sys.argv[1]
    data = pd.read_csv(csv_file)

    # Login to AnnotateChange
    up = Upload(sys.argv[2], sys.argv[3], sys.argv[4])
    if not up.login():
        print('Unable to login.')
        exit(1)

    for dataset in data['id'].unique():

        # Convert to the AnnotateChange object
        df = data[data['id'] == dataset]
        name = '{}_{}'.format(Path(csv_file).with_suffix('').name.lower(), dataset)
        series = AnnotateChange(name, df['value'].to_list())

        # Upload the dataset
        if not up.upload(series.__dict__):
            print('Unable to upload:', name)
            exit(1)
        print('Uploaded:', name)

        break
