"""Intent Topology: Smoke Test (normalized embeddings, KMeans)"""
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import normalize
from sentence_transformers import SentenceTransformer
import time, json, os

BASE = "C:/Users/ALEJOO/Documents/Gym IG Content Landing Page/ai-models/deepl-search/experiments"

with open(os.path.join(BASE, "msmarco_sample.txt"), "r", encoding="utf-8") as f:
    queries = [line.strip() for line in f.readlines()[:10000]]
print(f"Loaded {len(queries)} queries")

model = SentenceTransformer("all-MiniLM-L6-v2")
print(f"Embedding {len(queries)} queries...")
start = time.time()
embeddings = model.encode(queries, show_progress_bar=True, batch_size=256, convert_to_numpy=True)
print(f"Embedded in {time.time()-start:.1f}s, shape={embeddings.shape}")

# Normalize to unit length (cosine similarity)
embeddings = normalize(embeddings, norm='l2')

# Sub-sample for silhouette
np.random.seed(42)
sil_idx = np.random.choice(10000, 5000, replace=False)
emb_small = embeddings[sil_idx]

K_VALUES = [500, 1000, 2000, 3000, 3843, 5000]
ANALYTIC_SIL = {500: 0.72, 1000: 0.68, 2000: 0.63, 3000: 0.60, 3843: 0.58, 5000: 0.52}

results = {}
for k in K_VALUES:
    print(f"\nk={k}...", end=" ", flush=True)
    start = time.time()
    km = KMeans(n_clusters=k, n_init=3, random_state=42, max_iter=100)
    labels = km.fit_predict(embeddings)
    t_cluster = time.time() - start

    sil = float(silhouette_score(emb_small, labels[sil_idx], random_state=42))
    unique, counts = np.unique(labels, return_counts=True)
    median_size = int(np.median(counts))
    sparse = int(np.sum(counts < 5))
    sparse_pct = 100.0 * sparse / k

    results[k] = {"silhouette": round(sil, 4), "median_size": median_size,
                  "sparse_pct": round(sparse_pct, 2), "time_s": round(t_cluster, 1)}
    delta = round(sil - ANALYTIC_SIL[k], 4)
    print(f"sil={sil:.4f} (analytic={ANALYTIC_SIL[k]}, delta={delta:+0.4f}) median={median_size} sparse={sparse_pct:.1f}% t={t_cluster:.0f}s")

best_k = max(results, key=lambda k: results[k]["silhouette"])
print(f"\nBEST K by silhouette: {best_k}")
if best_k in [2000, 3000, 3843]:
    print("CONCLUSION: Octohedral Hypothesis supported")
elif best_k >= 5000:
    print("CONCLUSION: Higher K than predicted")
else:
    print("CONCLUSION: Lower K than predicted")

out_path = os.path.join(BASE, "smoke_test_results.json")
with open(out_path, "w") as f:
    json.dump({"n": 10000, "k_values": K_VALUES, "results": results,
               "analytic_sil": ANALYTIC_SIL, "best_k": best_k}, f, indent=2)
print(f"Results saved to {out_path}")
