import os
import pandas as pd
import json

def overlap(A, B):
    return len(A.intersection(B)) / len(A.union(B))


def cover_single(Sprime, S):
    T = sum(map(len, Sprime))
    assert T == sum(map(len, S))
    C = 0
    for R in S:
        C += len(R) * max(overlap(R, Rprime) for Rprime in Sprime)
    C /= T
    return C


def partition_from_cps(locations, n_obs):
    T = n_obs
    partition = []
    current = set()

    all_cps = iter(sorted(set(locations)))
    cp = next(all_cps, None)
    for i in range(T):
        if i == cp:
            if current:
                partition.append(current)
            current = set()
            cp = next(all_cps, None)
        current.add(i)
    partition.append(current)
    return partition


def covering(annotations, predictions, n_obs):
    Ak = {
        k + 1: partition_from_cps(annotations[uid], n_obs)
        for k, uid in enumerate(annotations)
    }
    pX = partition_from_cps(predictions, n_obs)

    Cs = [cover_single(pX, Ak[k]) for k in Ak]
    return sum(Cs) / len(Cs)


projects_folders = ["autoland1", "autoland2", "autoland3", "autoland4", "firefox-android", "mozilla-central", "mozilla-beta", "mozilla-release"]
annotations = dict()
covering_metric_values = dict()
for project in projects_folders:
    for signature_file in os.listdir('../datasets/' + project):
        signature_id = signature_file.split("_")[0]
        df = pd.read_csv('../datasets/' + project + '/' + signature_file)
        true_change_points = df.index[df['alert_status'].isin(['TP'])].tolist()
        predicted_change_points = df.index[df['alert_status'].isin(['TP', 'FP'])].tolist()
        n_obs = len(df)
        if (n_obs == 0):
            continue
        annotations = {1: true_change_points}
        covering_metric = covering(annotations, predicted_change_points, n_obs)
        covering_metric_values[signature_id] = covering_metric
        #print(f"Covering Metric for {signature_id}: {covering_metric}")
average_covering_metric = sum(covering_metric_values.values()) / len(covering_metric_values)
print(f"Average covering metric: {average_covering_metric}")