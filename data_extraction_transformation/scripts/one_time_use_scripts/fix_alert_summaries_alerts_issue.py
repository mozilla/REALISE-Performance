import os
import pandas as pd

# Unified status category mapping
status_category_mapping = {
    'investigating': 'SP',  # 'SP' stands for 'Still Processing'
    'reassigned': 'TP',
    'invalid': 'FP',
    'improvement': 'TP',
    'fixed': 'TP',
    'wontfix': 'TP',
    'untriaged': 'SP',
    'backedout': 'TP',
    'acknowledged': 'TP'
}

# Mappings for raw statuses
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

test_status_mapping = {
    0: "untriaged",
    1: "downstream",
    2: "reassigned",
    3: "invalid",
    4: "acknowledged"
}

# Paths
original_folder = '../datasets-refined-status'
refined_folder = '../datasets-refined-status-2'
alerts_df_path = '../datasets/1_rectified_alerts_data.csv'

# Load and preprocess alerts_df
alerts_df = pd.read_csv(alerts_df_path)

# Apply mappings to preserve original statuses
alerts_df['alert_status_original'] = alerts_df['alert_status'].map(alert_status_mapping)
alerts_df['test_status_original'] = alerts_df['test_status'].map(test_status_mapping)

# Apply unified category mapping
alerts_df['alert_status'] = alerts_df['alert_status_original'].replace(status_category_mapping)
alerts_df['test_status_general'] = alerts_df['test_status_original'].replace(status_category_mapping)

# Ensure output directory exists
os.makedirs(refined_folder, exist_ok=True)

def process_and_refine_file(file_path):
    df = pd.read_csv(file_path)
    
    # Merge with alerts_df to reset all statuses
    df = df.merge(
        alerts_df[['test_id', 'alert_status', 'test_status_general', 'alert_status_original', 'test_status_original']],
        on='test_id',
        how='left',
        suffixes=('', '_alert')
    )
    df['alert_status'] = df['alert_status_alert']
    df['test_status_general'] = df['test_status_general_alert']
    
    # Retain original alert and test statuses in the file
    df['alert_status_original'] = df['alert_status_original_alert']
    df['test_status_original'] = df['test_status_original_alert']
    
    # Drop extra columns from alerts_df after merging
    df = df.drop(columns=['alert_status_alert', 'test_status_general_alert', 'alert_status_original_alert', 'test_status_original_alert'])
    
    # Override for manually created tests
    mask_manual = df['test_manually_created'] == True
    df.loc[mask_manual, ['alert_status', 'test_status_general']] = 'FN'
    
    # Save the transformed DataFrame to the refined directory
    relative_path = os.path.relpath(file_path, original_folder)
    refined_file_path = os.path.join(refined_folder, relative_path)
    refined_dir = os.path.dirname(refined_file_path)
    os.makedirs(refined_dir, exist_ok=True)
    df.to_csv(refined_file_path, index=False)

# Loop through the filesystem and process each file
for root, dirs, files in os.walk(original_folder):
    for filename in files:
        if filename.endswith('.csv'):
            file_path = os.path.join(root, filename)
            process_and_refine_file(file_path)

print("Data transformation and saving completed successfully in the refined folder.")
