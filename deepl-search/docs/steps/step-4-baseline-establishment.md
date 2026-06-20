# Step 4: Baseline Establishment

> Before any ML model is trained, establish the trivial baselines.
> A model that cannot beat these is not adding value.

---

## 1. Baseline Catalog

| # | Baseline | Description | Expected Accuracy | Why It Matters |
|---|----------|-------------|-------------------|----------------|
| B1 | Random (uniform) | Pick any of 8 L1 classes uniformly at random | 12.5% (L1) / 0.026% (L4) | Floor: any model must beat random |
| B2 | Random (frequency-weighted) | Pick L1 class proportional to its frequency | ~20-25% (L1) | Informed random: exploits class imbalance |
| B3 | Most-Frequent-L1 | Always predict the largest L1 class (Shopping & Commerce) | ~25-35% (L1) | Naive baseline: model must do better than always guessing "Shopping" |
| B4 | Most-Frequent-L2 | Always predict the largest L2 class within the largest L1 | ~15-20% (L2) | L2-level MFC |
| B5 | Most-Frequent-L4 | Always predict the single most common L4 leaf | ~1-3% (L4) | Shows L4 is not learnable without per-class signal |
| B6 | Lexical Keyword Match | Simple word-level overlap: query words vs class definition words | ~30-40% (L1) / ~15-20% (L2) | Tests whether surface-form matching carries signal |
| B7 | Embedding centroid (0-shot) | Current pipeline: cosine similarity to generic leaf centroids | ~7-12% (all levels) | Measured in Exp 3: near-random |
| B8 | LLM zero-shot | GPT-4o-mini with taxonomy prompt | ~50-65% (L1) / ~30-45% (L2) | State of the art without training; sets the "worth training" threshold |
| B9 | Embedding centroid (with real IAB-based descriptions) | Same as B7 but with real IAB-based class names | ~20-30% (L1) / ~15-20% (L2) | Measures how much the generic placeholder names cost us |

### B1-B5: Simple Statistical Baselines

These require no NLP — just knowledge of the class frequency distribution:

- **B1 (Uniform random)**: $\frac{1}{K}$
- **B3 (MFC)**: requires labeled training data to identify the most frequent class. If we had 10K labeled queries, the most frequent L1 class is estimated to be Shopping & Commerce at ~30% frequency.
- **B5 (Most-frequent-L4)**: With Zipf $\alpha=1.1$, the top L4 class covers ~0.5-1% of queries. This baseline is near-zero, demonstrating that L4 is not a viable prediction target without millions of labeled examples.

### B6: Lexical Keyword Match

Implementation: For each query, compute TF-IDF or simple word-overlap with each class definition. Assign to the class with highest overlap.

Rationale: If simple word overlap achieves 40% L1 accuracy, it means L1 is partially predictable from surface form, but deeper semantics are needed for the remaining 60%. If word overlap achieves 20% L1 accuracy, it means L1 requires genuine semantic understanding — the model must go beyond word matching.

Expected performance (estimated from prior work on web query classification):

| Level | Lexical Accuracy | Semantic Gain |
|-------|-----------------|---------------|
| L1 | 30-40% | 60-70% requires deeper features |
| L2 | 15-25% | 75-85% requires context or training |
| L4 | 2-5% | 95%+ requires rich training data |

### B7: Current Classifier (Measured)

From Phase 1 Exp 3, the current embedding classifier with generic placeholder descriptions:

| Level | Mean Max Confidence | Effective Accuracy (proxy) |
|-------|-------------------|---------------------------|
| L1 | 0.067 | Near-random (below B1) |
| L2 | 0.109 | Near-random |
| L3 | 0.116 | Near-random |
| L4 | 0.122 | Near-random |

The classifier performs **at or below random** across all levels. This is not a usable baseline; it is a reference point for "before fixing class descriptions."

### B8: LLM Zero-Shot (Estimated)

The LLM classifier (`classifier.py`, `LLMClassifier`) uses GPT-4o-mini with the full taxonomy in the prompt. Based on reported zero-shot text classification benchmarks (GPT-4o-mini achieves 50-70% accuracy on 5-way classification), we estimate:

| Level | Estimated Accuracy | Source |
|-------|-------------------|--------|
| L1 (8-way) | 50-65% | GPT-4o-mini benchmarks on fine-grained classification |
| L2 (64-way) | 30-45% | Degradation from increased class count |
| L4 (3843-way) | 5-15% | Too many classes for prompt-based classification |

**The LLM baseline is the "worth training" threshold.** If a trained model cannot significantly outperform the LLM's zero-shot accuracy, the training investment is not justified. For L1: trained model should exceed 65%. For L2: exceed 45%.

---

## 2. Baseline Results (When Available)

*To be filled:*

| Baseline | L1 Acc | L2 Acc | L3 Acc | L4 Acc | Latency | Cost/Query |
|----------|--------|--------|--------|--------|---------|-----------|
| B1: Uniform random | 12.5% | 1.56% | 0.20% | 0.026% | <1ms | $0 |
| B2: Frequency-weighted random | ~25% | ~5% | ~1% | ~0.1% | <1ms | $0 |
| B3: Most-frequent-L1 | ~30% | — | — | — | <1ms | $0 |
| B6: Lexical keyword match | — | — | — | — | <1ms | $0 |
| B7: Embedding (generic) | ~7% | ~11% | ~12% | ~12% | ~25ms | $0 |
| B8: LLM zero-shot | — | — | — | — | ~500ms | $0.001 |
| B9: Embedding (real IAB-based) | — | — | — | — | ~25ms | $0 |

---

## 3. Decision Rules

The ML model is worth training only if it exceeds the LLM baseline (B8) by a meaningful margin:

| Condition | Decision |
|-----------|----------|
| Trained model L1 accuracy > B8 L1 accuracy + 5% | Proceed with training; model adds value over zero-shot |
| Trained model L1 accuracy within B8 ± 5% | Deploy LLM; training not justified (use B8 as production) |
| Trained model L1 accuracy < B8 L1 accuracy | Reconsider the model architecture; embeddings may be misaligned |

For L2-L4, the bar is lower (LLM degrades with more classes) — training is justified if it beats B8 by any margin at these levels.

---

## 4. Implementation Plan

1. Compute B1-B5 analytically (requires only the class frequency distribution — estimated from literature, will be refined with real data)
2. Compute B6 with a simple TF-IDF or word-overlap script on the MS MARCO sample
3. Measure B7 from Phase 1 results (already done)
4. Run B8 with the LLMClassifier on 500 queries (requires API key: ~$0.50)
5. Compute B9 by replacing generic names with improved descriptions (requires IAB-based mapping or enhanced descriptions)
6. Compare all baselines and set the "worth training" threshold
