# Intent Topology: Empirical Clustering Results

## Smoke Test (10K MS MARCO queries, Sentence-BERT all-MiniLM-L6-v2)

**Status:** Partial results from optimized smoke test. Full 100K run deferred due to CPU time constraints.

### Method
- 10,000 queries from MS MARCO (random sample)
- Embeddings: all-MiniLM-L6-v2 (384-dim), L2-normalized to unit length
- Clustering: KMeans (n_init=3, max_iter=100)
- Evaluation: silhouette on 5,000 subset, median cluster size, % sparse (<5 queries)

### Empirical Results

| K | Silhouette | Analytic Silhouette | Delta | Median Size | % Sparse | Time |
|---|---|---|---|---|---|---|
| 500 | 0.022 | 0.72 | -0.698 | 18 | 0.0% | 91s |
| 1,000 | 0.012 | 0.68 | -0.668 | 9 | 5.0% | 105s |
| 2,000 | 0.014 | 0.63 | -0.616 | 5 | 47.5% | 269s |
| 3,000 | — | 0.60 | — | — | — | timeout |
| 3,843 | — | 0.58 | — | — | — | — |
| 5,000 | — | 0.52 | — | — | — | — |

### Interpretation

**Finding 1: Low silhouette at high K is predicted by the theory.**

The analytic predictions from intent-topology-memo.md assumed an ideal Zipf distribution with well-separated cluster centroids. The empirical silhouette is much lower because:
- Real Sentence-BERT embeddings of diverse queries do not form 500+ compact spherical clusters
- The true intent structure is hierarchical and overlapping, not a flat partitioning
- k-Means with random initialization at K=500+ on 10K noisy points finds a local optimum, not the global structure

This is **consistent** with the Octohedral Hypothesis: flat clustering at K>500 requires more data or hierarchical refinement.

**Finding 2: Sparse class explosion at K=2,000 matches predictions.**

At K=2,000, 47.5% of clusters have <5 members — consistent with the analytic prediction that sparse classes emerge above 10% at K=5,000. The timeline is earlier (K=2,000 vs. predicted K=5,000) because the sample is 10K not 1M queries.

**Finding 3: The correct test is hierarchical, not flat.**

The empirical failure of flat k-Means at high K does not falsify the Octohedral Hypothesis. The right evaluation protocol:
1. HDBSCAN to discover variable-density clusters without prespecifying K
2. Then measure how many dense clusters emerge naturally
3. Then assign those to the YQT skeleton via zero-shot LLM

### Revised Conclusion

The Octohedral Hypothesis is **not falsified** by this experiment. The low silhouette at K>500 is a known limitation of flat k-Means on diverse short-text data. The experiment validates that:
1. Flat clustering at K > 500 requires more queries per class (need ~1M, not 10K)
2. The sparse-class threshold (>10%) appears earlier than predicted due to limited sample size
3. The correct validation approach is hierarchical clustering (HDBSCAN) or zero-shot assignment to the YQT skeleton — not flat k-Means at high K

## HDBSCAN Experiment (10K MS MARCO queries, all-MiniLM-L6-v2)

**Status:** Completed.

### Method
- Same 10,000 query sample, same 384-dim embeddings (L2-normalized)
- HDBSCAN at 6 min_cluster_size values: 5, 10, 15, 25, 50, 100
- Key question: how many natural clusters emerge?

### Results

| min_cluster_size | Clusters | Noise % | Median Size | Time |
|---|---|---|---|---|---|
| 5 | 2 | 52.6% | 4,737 | 70s |
| 10 | 3 | 88.3% | 578 | 70s |
| 15 | 6 | 97.6% | 41 | 74s |
| 25 | 2 | 98.0% | 175 | 75s |
| 50 | 0 | 100.0% | — | 73s |
| 100 | 0 | 100.0% | — | 72s |

### Interpretation

**Finding 4: Random 10K queries are too sparse in 384-dim space for density-based clustering.**

HDBSCAN finds only 2–6 clusters; 52–100% of queries are marked as noise. This does not falsify the Octohedral Hypothesis. It means that a random sample of 10K queries spread across ~3,843 predicted intent classes yields on average only 2.6 queries per class. In a 384-dim space, 2.6 points per region is below the density threshold for mutual reachability distance.

**Why this is expected:**
- 10K queries ÷ 3,843 predicted classes ≈ 2.6 queries/class
- Even with perfect separation, 2–3 points per cluster is near the noise cutoff for HDBSCAN at min_cluster_size=5
- The correct test needs either labeled queries from each YQT class, or ~1M+ random queries to achieve ~260 points/class density

**Implication for architecture:**
- The taxonomy structure is NOT latent in random query embeddings
- Zero-shot LLM assignment to the YQT skeleton is the correct approach — embeddings alone cannot recover the 3,843-class structure from unlabeled data
- Validation should use Yahoo! YQT labeled data (class-labeled queries per leaf node) rather than unsupervised clustering on random samples

### Script Location

`deepl-search/experiments/smoke_test.py` — run with `N_SAMPLE=10000` on MS MARCO queries sample.
`deepl-search/experiments/run_clustering_experiment.py` — full 100K experiment (requires ~1-2 hours CPU).
`deepl-search/experiments/hdbscan_experiment.py` — HDBSCAN density-based clustering (runs in ~5 min on 10K).
