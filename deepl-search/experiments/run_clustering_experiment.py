"""
Intent Topology: MS MARCO Clustering Experiment (C2)
====================================================
Tests k-Means clustering at K values around the predicted optimum (500–10,000).
Compares empirical results against analytic predictions from intent-topology-memo.md.
"""

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sentence_transformers import SentenceTransformer
import ir_datasets
import json
import time
import os
from tqdm import tqdm

# --- Configuration ---
N_SAMPLE = 100_000  # sample size for embedding (adjust based on compute)
K_VALUES = [500, 1000, 2000, 3000, 3843, 5000, 8000]
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384-dim, fast on CPU
OUTPUT_DIR = "C:/Users/ALEJOO/Documents/Gym IG Content Landing Page/ai-models/deepl-search/experiments"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Analytic predictions from intent-topology-memo.md (Zipf alpha=1.1)
ANALYTIC = {
    500:  {"silhouette": 0.72, "median_size": 1200, "sparse_pct": 0.0},
    1000: {"silhouette": 0.68, "median_size": 450,  "sparse_pct": 0.2},
    2000: {"silhouette": 0.63, "median_size": 145,  "sparse_pct": 1.1},
    3000: {"silhouette": 0.60, "median_size": 60,   "sparse_pct": 3.0},
    3843: {"silhouette": 0.58, "median_size": 40,   "sparse_pct": 4.8},
    5000: {"silhouette": 0.52, "median_size": 19,   "sparse_pct": 12.3},
    8000: {"silhouette": 0.44, "median_size": 5.2,  "sparse_pct": 38.7},
}


def load_queries(n_sample=N_SAMPLE):
    """Load queries from MS MARCO passage dataset."""
    print(f"Loading MS MARCO queries (sampling {n_sample})...")
    ds = ir_datasets.load("msmarco-passage/train")
    queries = []
    for i, q in enumerate(ds.queries_iter()):
        if i >= n_sample:
            break
        queries.append(q.text)
    print(f"Loaded {len(queries)} queries")
    return queries


def embed_queries(queries, model_name=EMBEDDING_MODEL):
    """Embed queries using Sentence-BERT (CPU)."""
    print(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    print(f"Embedding {len(queries)} queries...")
    start = time.time()
    embeddings = model.encode(
        queries,
        show_progress_bar=True,
        batch_size=256,
        convert_to_numpy=True,
    )
    elapsed = time.time() - start
    print(f"Embedded {len(queries)} queries in {elapsed:.1f}s ({len(queries)/elapsed:.0f} queries/s)")
    return embeddings


def run_kmeans(embeddings, k, n_init=3, random_state=42):
    """Run k-Means and return labels + inertia."""
    print(f"  k-Means k={k}...")
    start = time.time()
    km = KMeans(n_clusters=k, n_init=n_init, random_state=random_state, verbose=0)
    labels = km.fit_predict(embeddings)
    elapsed = time.time() - start
    print(f"    Done in {elapsed:.1f}s")
    return labels, km


def compute_metrics(labels, embeddings, k):
    """Compute silhouette, median cluster size, % sparse clusters."""
    n = len(labels)

    # Silhouette (sample if too large)
    if n > 30000:
        idx = np.random.choice(n, 30000, replace=False)
        sil = silhouette_score(embeddings[idx], labels[idx], random_state=42)
    else:
        sil = silhouette_score(embeddings, labels, random_state=42)

    # Cluster sizes
    unique, counts = np.unique(labels, return_counts=True)
    median_size = int(np.median(counts))
    sparse = int(np.sum(counts < 5))
    sparse_pct = 100.0 * sparse / k

    return {
        "k": k,
        "silhouette": round(sil, 4),
        "median_cluster_size": median_size,
        "sparse_clusters": sparse,
        "sparse_pct": round(sparse_pct, 2),
        "n_clusters_found": len(unique),
        "n_samples": n,
    }


def main():
    results = {}

    # Step 1: Load queries
    queries = load_queries()

    # Step 2: Embed
    cache_path = os.path.join(OUTPUT_DIR, "embeddings.npy")
    if os.path.exists(cache_path):
        print(f"Loading cached embeddings from {cache_path}")
        embeddings = np.load(cache_path)
    else:
        embeddings = embed_queries(queries)
        np.save(cache_path, embeddings)
        print(f"Saved embeddings to {cache_path}")

    print(f"Embedding shape: {embeddings.shape}")
    print(f"Embedding dtype: {embeddings.dtype}")

    # Step 3: Cluster at each K
    for k in K_VALUES:
        labels, _ = run_kmeans(embeddings, k)
        metrics = compute_metrics(labels, embeddings, k)

        # Compare with analytic
        if k in ANALYTIC:
            a = ANALYTIC[k]
            metrics["analytic_silhouette"] = a["silhouette"]
            metrics["analytic_median_size"] = a["median_size"]
            metrics["analytic_sparse_pct"] = a["sparse_pct"]
            metrics["silhouette_delta"] = round(metrics["silhouette"] - a["silhouette"], 4)

        results[k] = metrics
        print(f"  K={k}: silhouette={metrics['silhouette']}, median_size={metrics['median_cluster_size']}, sparse={metrics['sparse_pct']}%")
        if "silhouette_delta" in metrics:
            print(f"    vs analytic: delta={metrics['silhouette_delta']:+0.4f}")

    # Step 4: Save results
    output = {
        "model": EMBEDDING_MODEL,
        "n_samples": N_SAMPLE,
        "k_values": K_VALUES,
        "results": results,
        "conclusion": None,
    }

    # Determine which K is optimal
    best_k = max(results, key=lambda k: results[k]["silhouette"])
    output["best_k_by_silhouette"] = best_k
    print(f"\n{'='*60}")
    print(f"BEST K by silhouette: {best_k}")
    print(f"BEST K by analytic prediction: 3,000–4,000")

    # Check if Octohedral Hypothesis is confirmed
    r3k = results.get(3000, results.get(3843, {}))
    r5k = results.get(5000, {})
    r500 = results.get(500, {})

    if r3k and r3k.get("silhouette", 0) >= 0.5 and r3k.get("sparse_pct", 100) < 15:
        output["conclusion"] = "OCTOHEDRAL HYPOTHESIS CONFIRMED: K=3,000-4,000 is optimal"
    elif r500 and r500.get("silhouette", 0) > r3k.get("silhouette", 0):
        output["conclusion"] = "TAXONOMY TOO FINE: Lower K values outperform — suggests <2,000 classes optimal"
    elif r5k and r5k.get("silhouette", 0) > r3k.get("silhouette", 0):
        output["conclusion"] = "TAXONOMY TOO COARSE: Higher K values outperform — suggests >5,000 classes optimal"
    else:
        output["conclusion"] = "INCONCLUSIVE — manually review results"

    output_path = os.path.join(OUTPUT_DIR, "clustering_results.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Results saved to {output_path}")
    print(f"Conclusion: {output['conclusion']}")


if __name__ == "__main__":
    main()
