"""
Intent Topology: HDBSCAN Experiment (Track C2 - Empirical Validation)
====================================================================
HDBSCAN discovers clusters without prespecifying K.
Counts natural clusters in MS MARCO query embeddings and compares to
the predicted 3,843-leaf taxonomy size from the Octohedral Hypothesis.
"""

import numpy as np
from sklearn.preprocessing import normalize
from sentence_transformers import SentenceTransformer
import hdbscan
import time
import json
import os

BASE = "C:/Users/ALEJOO/Documents/Gym IG Content Landing Page/ai-models/deepl-search/experiments"
N_SAMPLE = 10000
RANDOM_SEED = 42

# Load queries
sample_path = os.path.join(BASE, "msmarco_sample.txt")
with open(sample_path, "r", encoding="utf-8") as f:
    queries = [line.strip() for line in f.readlines()[:N_SAMPLE]]
print(f"Loaded {len(queries)} queries")

# Embed (cached)
model = SentenceTransformer("all-MiniLM-L6-v2")
print(f"Embedding {len(queries)} queries...")
start = time.time()
embeddings = model.encode(queries, show_progress_bar=True, batch_size=256, convert_to_numpy=True)
print(f"Embedded in {time.time()-start:.1f}s, shape={embeddings.shape}")

# Normalize
embeddings = normalize(embeddings, norm='l2')
np.random.seed(RANDOM_SEED)
np.random.shuffle(embeddings)  # shuffle to avoid ordering bias

# Run HDBSCAN at multiple min_cluster_size values
MIN_CLUSTER_SIZES = [5, 10, 15, 25, 50, 100]
results = {}

for mcs in MIN_CLUSTER_SIZES:
    print(f"\nHDBSCAN min_cluster_size={mcs}...")
    start = time.time()
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=mcs,
        min_samples=None,
        metric='euclidean',
        core_dist_n_jobs=1,
        gen_min_span_tree=True
    )
    labels = clusterer.fit_predict(embeddings)
    elapsed = time.time() - start

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = int(np.sum(labels == -1))
    noise_pct = 100.0 * n_noise / len(labels)
    
    unique, counts = np.unique(labels, return_counts=True)
    if n_clusters > 0:
        cluster_sizes = [c for c in counts if c >= mcs]
        median_cluster_size = int(np.median(cluster_sizes)) if cluster_sizes else 0
        max_cluster_size = int(np.max(cluster_sizes)) if cluster_sizes else 0
    else:
        median_cluster_size = 0
        max_cluster_size = 0

    results[mcs] = {
        "n_clusters": n_clusters,
        "n_noise": n_noise,
        "noise_pct": round(noise_pct, 2),
        "median_cluster_size": median_cluster_size,
        "max_cluster_size": max_cluster_size,
        "time_s": round(elapsed, 1),
    }
    
    print(f"  Clusters: {n_clusters}, Noise: {n_noise} ({noise_pct:.1f}%)")
    print(f"  Median cluster size: {median_cluster_size}, Max: {max_cluster_size}")
    print(f"  Time: {elapsed:.1f}s")

# Interpret results
# For the optimum K prediction (3,843), we expect HDBSCAN to find ~50-500 clusters
# at min_cluster_size=5 (these are the "dense cores" that get further refined into L4 classes)
# Fewer clusters means the data is too coarse for 3,843 classes
# More clusters means the data supports finer granularity

print(f"\n{'='*60}")
print("INTERPRETATION")
print(f"{'='*60}")
print("The Octohedral Hypothesis predicts ~3,843 intent classes at L4.")
print("HDBSCAN at min_cluster_size=5 should find clusters that correspond")
print("to L3-level categories (~512), with each cluster containing ~6-8 sub-intents.")
print()
print("If HDBSCAN finds:")
print("  - 50-500 clusters: Consistent with L3-level (512) + noise")
print("  - <20 clusters: Suggests too little data for fine-grained taxonomy")
print("  - >1000 clusters: Suggests data supports more granularity than predicted")
print("  - >50% noise: Suggests a large fraction of queries are unclusterable")
print(f"{'='*60}")

best_mcs = min(MIN_CLUSTER_SIZES, key=lambda m: abs(results[m]["n_clusters"] - 512))
best_count = results[best_mcs]["n_clusters"]
ratio_to_512 = round(best_count / 512, 2) if best_count > 0 else 0

test_result = {
    "n_queries": N_SAMPLE,
    "embedding_model": "all-MiniLM-L6-v2",
    "hdbscan_results": results,
    "interpretation": {
        "n_clusters_at_mcs_5": results[5]["n_clusters"],
        "predicted_l3_count": 512,
        "closest_to_l3": {"mcs": best_mcs, "n_clusters": best_count, "ratio_to_512": ratio_to_512},
        "predicted_l4_count": 3843,
        "noise_at_mcs_5_pct": results[5]["noise_pct"],
    }
}

out_path = os.path.join(BASE, "hdbscan_results.json")
with open(out_path, "w") as f:
    json.dump(test_result, f, indent=2)
print(f"\nResults saved to {out_path}")
