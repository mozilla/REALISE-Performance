'''
Provided the JSON of tags related to a specific alertand make them into a comma-separated string
'''
def append_strings(tags):
    if tags:
        return ", ".join(str(item) for item in tags)
    return ""

'''
This function takes an API endpoint URL, gets its response payload JSON, and returns it 
'''
def get_json(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        json_data = response.json()
        return json_data
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None

'''
Given a text file of comma-separated IDs, it extracts them and converts them into a list
'''
def txt_to_list(filename):
    with open(filename, 'r') as file:
        content = file.read().strip()
        ids = content.split(',')
        return ids