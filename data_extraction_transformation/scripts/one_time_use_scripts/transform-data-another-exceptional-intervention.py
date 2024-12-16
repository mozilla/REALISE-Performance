import os
import pandas as pd

alert_status_mapping = {
    0: "untriaged",
    1: "downstream",
    2: "reassigned",
    3: "invalid",
    4: "improvement",
    5: "investigating",
    6: "wontfix",
    7: "fixed",
    8: "backedout"
}

category_mapping = {
    'investigating': 'SP', # 'SP' stands for 'Still Processing'
    'reassigned': 'TP',
    'invalid': 'FP',
    'improvement': 'TP',
    'fixed': 'TP',
    'wontfix': 'TP',
    'untriaged': 'SP',
    'backedout': 'TP'
}

# Paths for original and refined datasets
original_folder = '../datasets-refined-status'
refined_folder = '../datasets-refined-status-2'
alerts_df_path = '../datasets/1_rectified_alerts_data.csv'

# Load alerts_df as a reference DataFrame
alerts_df = pd.read_csv(alerts_df_path)
alerts_df['alert_status'] = alerts_df['alert_status'].map(alert_status_mapping)
alerts_df['test_status'] = alerts_df['test_status'].map(alert_status_mapping)
alerts_df = alerts_df.rename(columns={'test_status': 'test_status_general'})
alerts_df['alert_status'] = alerts_df['alert_status'].replace(category_mapping)
alerts_df['test_status_general'] = alerts_df['test_status_general'].replace(category_mapping)
os.makedirs(refined_folder, exist_ok=True)

def process_and_refine_file(file_path):
    df = pd.read_csv(file_path)
    
    df = df.merge(
        alerts_df[['test_id', 'alert_status', 'test_status_general']],
        on='test_id',
        how='left',
        suffixes=('', '_alert')
    )
    
    mask_fn = (df['alert_status'] == 'FN')
    df.loc[mask_fn, 'alert_status'] = df.loc[mask_fn, 'alert_status_alert']
    df.loc[mask_fn, 'test_status_general'] = df.loc[mask_fn, 'test_status_general_alert']
    
    # Drop the extra columns from alerts_df after merging
    df = df.drop(columns=['alert_status_alert', 'test_status_general_alert'])
    
    # Set 'alert_status' and 'test_status_general' to 'FN' for rows created manually
    mask_manual = df['test_manually_created'] == True
    df.loc[mask_manual, ['alert_status', 'test_status_general']] = 'FN'
    
    # Replicating the directory structure in the refined folder
    relative_path = os.path.relpath(file_path, original_folder)
    refined_file_path = os.path.join(refined_folder, relative_path)
    refined_dir = os.path.dirname(refined_file_path)
    
    # Create the directories if they don't exist
    os.makedirs(refined_dir, exist_ok=True)
    
    # Save the transformed DataFrame to the refined directory
    df.to_csv(refined_file_path, index=False)

# Loop through the filesystem and process each file
for root, dirs, files in os.walk(original_folder):
    for filename in files:
        if filename.endswith('.csv'):
            file_path = os.path.join(root, filename)
            process_and_refine_file(file_path)

print("Data transformation and saving completed successfully in the refined folder.")
