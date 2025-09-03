#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from scipy.stats import ttest_rel

def load_cplocations(root: Path) -> dict[str, list[int]]:
    id_to_cps = {}
    for ts_dir in root.iterdir():
        if not ts_dir.is_dir():
            continue
        rep_dir = ts_dir / "default_mozilla_rep"
        json_candidates = sorted(rep_dir.glob("*.json")) if rep_dir.exists() else []
        if not json_candidates:
            continue
        with open(json_candidates[0], "r", encoding="utf-8") as f:
            data = json.load(f)
        cps = data.get("result", {}).get("cplocations", [])
        cps = [int(x) for x in cps]
        # get timeseries length if stored, else fallback to max index
        length = data.get("n_obs", max(cps) + 1 if cps else 0)
        id_to_cps[ts_dir.name] = (cps, length)
    return id_to_cps

def jaccard_similarity(cps1, cps2):
    set1, set2 = set(cps1), set(cps2)
    if not set1 and not set2:
        return 1.0
    return len(set1 & set2) / len(set1 | set2)

def f1_score_sets(cps1, cps2):
    set1, set2 = set(cps1), set(cps2)
    tp = len(set1 & set2)
    fp = len(set1 - set2)
    fn = len(set2 - set1)
    if tp == 0:
        return 0.0
    return 2 * tp / (2 * tp + fp + fn)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset1", type=Path)
    ap.add_argument("--dataset2", type=Path)
    ap.add_argument("--metric", choices=["jaccard", "f1"], default="jaccard",
                    help="Similarity metric to compare CP sets")
    args = ap.parse_args()

    d1 = load_cplocations(args.dataset1)
    d2 = load_cplocations(args.dataset2)

    common_ids = sorted(set(d1.keys()) & set(d2.keys()))

    sims1, sims2 = [], []
    for ts_id in common_ids:
        cps1, _ = d1[ts_id]
        cps2, _ = d2[ts_id]
        if args.metric == "jaccard":
            score = jaccard_similarity(cps1, cps2)
        else:
            score = f1_score_sets(cps1, cps2)
        # compare each dataset to itself? No, we just need one vector of scores.
        # For t-test, we compare raw indicator similarities? 
        # Actually we need a per-dataset score vs. ground truth; here we do symmetric similarity
        sims1.append(score)  # dataset1 vs dataset2 similarity
        sims2.append(score)  # identical because metric is symmetric

    # Actually, since similarity is symmetric, you'd instead compute
    # a distance vector between dataset1 and dataset2 *per timeseries*
    # then run t-test on something else (like counts). Here’s example for counts:

    counts1 = [len(d1[ts_id][0]) for ts_id in common_ids]
    counts2 = [len(d2[ts_id][0]) for ts_id in common_ids]
    t_stat, p_val = ttest_rel(counts1, counts2)

    print(f"Compared {len(common_ids)} timeseries")
    print("Counts t-test: t-stat =", t_stat, "p-value =", p_val)

if __name__ == "__main__":
    main()
