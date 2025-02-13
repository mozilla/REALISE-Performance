import os
import json
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tslearn.metrics import cdist_dtw
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
from scipy.spatial.distance import pdist, squareform

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Cluster time series based on suite, platform, repository, and application using Euclidean distance and Agglomerative Clustering.")
    parser.add_argument('-i', '--input-folder', required=True, help="Path to the folder containing time series CSV files.")
    parser.add_argument('-c', '--characteristics', required=True, help="Path to JSON file with time series metadata.")
    parser.add_argument('-o', '--output-folder', required=True, help="Path to output folder for results.")
    parser.add_argument('-k', '--max-clusters', type=int, default=15, help="Maximum number of clusters to evaluate.")
    parser.add_argument('-s', '--signature-ids-file', help="Path to a text file containing specific signature IDs (optional).")
    parser.add_argument('-m', '--manual-k', help="Path to a JSON file containing manual k values for each repository-application compound.")
    return parser.parse_args()

def categorize_platform(platform):
    platform_lower = platform.lower()

    if 'win' in platform_lower:
        return 'Windows'
    elif 'osx' in platform_lower or 'osx' in platform_lower:
        return 'macOS'
    elif 'linux' in platform_lower:
        return 'Linux'
    elif 'android' in platform_lower:
        return 'Android'
    else:
        return 'Others'

def load_signature_ids(file_path):
    """Load signature IDs from a file (one ID per line)."""
    with open(file_path, 'r') as f:
        signature_ids = [line.strip() for line in f.readlines()]
    return [int(id) for id in signature_ids if id.isdigit()]

def load_time_series(input_folder, signature_ids_to_consider=None):
    """Recursively loads all available time series from the input folder and subfolders, filtering by provided signature IDs."""
    time_series_dict = {}
    for root, _, files in os.walk(input_folder):
        for filename in files:
            if filename.endswith("_timeseries_data.csv"):
                sig_id = int(filename.split("_")[0])
                # Only load the file if its signature ID is in the provided list, or if no filter is applied
                if signature_ids_to_consider is not None and sig_id not in signature_ids_to_consider:
                    continue
                df = pd.read_csv(os.path.join(root, filename))
                if "push_timestamp" in df.columns and "value" in df.columns:
                    df = df.sort_values(by="push_timestamp")
                    time_series_dict[sig_id] = df["value"].dropna().values
    return time_series_dict

def compute_dtw_matrix(time_series):
    """Computes DTW distance matrix."""
    return cdist_dtw(time_series)


def best_silhouette_score(distance_matrix, max_clusters, manual_k=None):
    """Finds the best number of clusters using Silhouette Score."""
    n_samples = distance_matrix.shape[0]
    if n_samples < 2:
        return 2, [], []  # Not enough data to cluster

    # If manual_k is provided, just return that value and skip silhouette score calculation
    # if manual_k:
    #     return manual_k, [], []  # No need to calculate scores, just return manual_k
    
    best_k, best_score, scores = 2, -1, []
    inertia = []
    max_k = min(max_clusters, n_samples - 1)  # Ensure valid k range

    for k in range(2, max_k + 1):
        clustering = AgglomerativeClustering(n_clusters=k, metric='precomputed', linkage='average')
        labels = clustering.fit_predict(distance_matrix)
        
        if len(set(labels)) < 2:
            continue  # Silhouette score requires at least 2 clusters
        
        score = silhouette_score(distance_matrix, labels, metric='precomputed')
        scores.append(score)
        inertia.append(np.sum(distance_matrix[labels == labels[:, None]]))

        if score > best_score:
            best_score, best_k = score, k

    # Ensure scores and inertia are not empty before returning
    if not scores:
        return 2, [], []  # Return default values if no valid clustering

    return best_k, scores, inertia


def save_statistics(stats, output_folder):
    """Saves statistical summary to a JSON file."""
    with open(os.path.join(output_folder, "clustering_statistics.json"), "w") as f:
        json.dump(stats, f, indent=4)

def save_cluster_assignments(group_name, signature_ids, labels, output_folder):
    """Saves the cluster assignments into a CSV."""
    df = pd.DataFrame({
        "signature_id": signature_ids,
        "cluster": labels
    })
    os.makedirs(os.path.join(output_folder, group_name), exist_ok=True)
    df.to_csv(os.path.join(output_folder, group_name, "cluster_assignments.csv"), index=False)

def plot_silhouette_score(scores, output_folder, group_name):
    """Generates and saves a silhouette score plot."""
    plt.figure(figsize=(10, 7))
    plt.plot(range(2, len(scores) + 2), scores, marker='o')
    plt.title(f"Silhouette Score for {group_name}")
    plt.xlabel("Number of Clusters (k)")
    plt.ylabel("Silhouette Score")
    plt.xticks(ticks=[tick for tick in plt.xticks()[0] if tick % 10 == 0])
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, group_name, "silhouette_score_plot.png"))
    plt.close()

def plot_elbow_method(inertia, output_folder, group_name):
    """Generates and saves an elbow method plot."""
    plt.figure(figsize=(10, 7))
    plt.plot(range(2, len(inertia) + 2), inertia, marker='o')
    plt.title(f"Elbow Method for {group_name}")
    plt.xlabel("Number of Clusters (k)")
    plt.ylabel("Inertia (Sum of Squared Distances)")
    plt.xticks(ticks=[tick for tick in plt.xticks()[0] if tick % 10 == 0])
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, group_name, "elbow_method_plot.png"))
    plt.close()

def main():
    args = parse_args()

    print("[INFO] Loading time series metadata...")
    with open(args.characteristics) as f:
        data = json.load(f)
    df_characteristics = pd.DataFrame.from_dict(data, orient="index").reset_index()
    df_characteristics.rename(columns={"index": "signature_id", "product": "application"}, inplace=True)
    df_characteristics["signature_id"] = pd.to_numeric(df_characteristics["signature_id"], errors="coerce").astype("Int64")
    platforms = df_characteristics['platform'].unique()
    segmented = {category: [] for category in ['Windows', 'macOS', 'Linux', 'Android', 'Others']}
    for platform in platforms:
        category = categorize_platform(platform)
        segmented[category].append(platform)
    df_characteristics['platform_category'] = df_characteristics['platform'].apply(categorize_platform)

    # Load manual k values if provided
    manual_k = {}
    if args.manual_k:
        with open(args.manual_k) as f:
            manual_k = json.load(f)

    print("[INFO] Loading available time series...")
    time_series_dict = load_time_series(args.input_folder)
    os.makedirs(args.output_folder, exist_ok=True)

    silhouette_scores, inertia_scores = [], []
    stats = dict()

    # Check if the signature IDs file is provided
    if args.signature_ids_file:
        print("[INFO] Loading signature IDs from file...")
        signature_ids_to_process = load_signature_ids(args.signature_ids_file)
    else:
        print("[INFO] Processing all available time series...")
        signature_ids_to_process = list(time_series_dict.keys())

    for (repo, application), group in df_characteristics.groupby(["repository", "application"]):
        signature_ids = group["signature_id"].tolist()
        available_ids = [sig_id for sig_id in signature_ids if sig_id in signature_ids_to_process]
        time_series = [time_series_dict[sig_id] for sig_id in available_ids]
        if not time_series:
            print(f"[INFO] Skipping ({repo}, {application}) - No available time series.")
            continue
        else:
            print(f"[INFO] Processing ({repo}, {application}) - {len(time_series)} available time series.")
        
        distance_matrix = compute_dtw_matrix(time_series)
        # Pass manual_k if it's provided; otherwise, it will default to None
        optimal_clusters, scores, inertia = best_silhouette_score(distance_matrix, args.max_clusters, manual_k=args.manual_k)

        # Ensure that scores are not empty before proceeding
        if not scores:
            print(f"[WARNING] Skipping clustering for ({repo}, {application}) - No valid silhouette score.")
            continue
        
        # Collect statistics for each repository-application pair
        stats[f"{repo}_{application}"] = {
            "optimal_clusters": optimal_clusters,
            "silhouette_score": {
                "min": np.min(scores) if scores else None,
                "max": np.max(scores) if scores else None,
                "mean": np.mean(scores) if scores else None,
                "median": np.median(scores) if scores else None
            },
            "inertia": {
                "min": np.min(inertia) if inertia else None,
                "max": np.max(inertia) if inertia else None,
                "mean": np.mean(inertia) if inertia else None,
                "median": np.median(inertia) if inertia else None
            }
        }

        # Proceed with clustering using the best number of clusters
        optimal_clusters = np.argmax(scores) + 2 if not manual_k else manual_k[f"{repo}_{application}"]
        clustering = AgglomerativeClustering(n_clusters=optimal_clusters, metric='precomputed', linkage='average')
        labels = clustering.fit_predict(distance_matrix)

        # Save the cluster assignments to CSV
        save_cluster_assignments(f"{repo}_{application}_{len(time_series)}", available_ids, labels, args.output_folder)

        # Generate and save the two plots (Silhouette and Elbow)
        plot_silhouette_score(scores, args.output_folder, f"{repo}_{application}_{len(time_series)}")
        plot_elbow_method(inertia, args.output_folder, f"{repo}_{application}_{len(time_series)}")

    # Save statistics to JSON
    save_statistics(stats, args.output_folder)

if __name__ == "__main__":
    main()
