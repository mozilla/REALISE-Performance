import os 
import pandas as pd
import shutil


input_files = 'datasets-original-annotated-2'
output_files = 'datasets-original-annotated-2-aggregated-min'
agg_method = 'min'

def select_favorable_status(status_series):
    # Return the status with the highest priority (lowest number in `status_priority`)
    return sorted(status_series, key=lambda x: status_priority.get(x, float('inf')))[0]

def process_folder(folder):
    for signature_file in os.listdir('../' + input_files + '/' + folder):
        print(folder + '/' + signature_file)
        df = pd.read_csv('../' + input_files + '/' + folder + '/' + signature_file, index_col=False)
        df_grouped = df.groupby('revision').agg({
            'value': agg_method,
            **{col: 'first' for col in df.columns if col not in ['revision', 'value']}
        }).reset_index()
        
        # Sort by push_timestamp if it exists, otherwise omit this step
        if 'push_timestamp' in df_grouped.columns:
            df_grouped = df_grouped.sort_values(by='push_timestamp')
        
        # Save the processed DataFrame
        output_path = f'../{output_files}/{folder}/{signature_file}'
        df_grouped.to_csv(output_path, index=False)

# Define folders mapping

projects_folders_mapping = {
    "autoland": ["autoland1", "autoland2", "autoland3", "autoland4"],
    "firefox-android": ["firefox-android"],
    "mozilla-beta": ["mozilla-beta"]
}


# Process each project and folder
for project in projects_folders_mapping:
    for folder in projects_folders_mapping[project]:
        os.makedirs(f'../{output_files}/{folder}', exist_ok=True)
        process_folder(folder)
