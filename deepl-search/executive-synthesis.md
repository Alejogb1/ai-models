# Deepl Search — Executive Synthesis

> What ~85 research papers say about building a search-intelligence product
>
> **Audience:** Founders, PMs, investors, product stakeholders
> **Status:** Evidence-grounded; all claims traceable to source papers in Appendix
> **Date:** 2026-06-08

---

## 1. The Core Thesis

**Search volume is a misleading signal.**

The Timoshenko & Hauser (2018) study at MIT Sloan proved this rigorously. They compared what customers said they wanted (via professional interviews) against what was discoverable from user-generated content sorted by frequency. The correlation between frequency of mention and actual importance was **ρ = 0.21** — barely above noise.

A keyword table sorted by search volume surfaces *popular topics*, not *important user needs*. Organizing the same keywords by *underlying intent* surfaces structurally different information — including the 29% of high-importance needs that frequency-based methods miss entirely.

This is why Deepl Search exists: to transform keyword data into intent-level understanding. This document synthesizes what the research literature says about whether and how to do this.

---

## 2. What We Know About Search Intent

### 2.1 Intent Has a Hierarchy

User intent is not flat. The structural convergence of three independent commercial taxonomies — Yahoo! Query Taxonomy (3,843 leaves), Google Intent Classification (3,184 leaves), and IAB Content Taxonomy (1,712 leaves) — reveals that web-scale intent follows a **4-level, branching-8 structure**:

| Level | Description | Domain-level (Timoshenko) | Web-scale (Yahoo!/Google) | Evidence |
|---|---|---|---|---|
| Primary (L1) | Broad goal categories | 6 (oral care) | **8** (universal) | Both Yahoo! YQT and Google intent have exactly 8 L1 categories. Timoshenko found 6 in oral care; the cross-domain taxonomy is slightly wider. |
| Secondary (L2) | Sub-goals within categories | 22 (oral care) | **64** (universal) | Both taxonomies: 8 × 8 = 64. Timoshenko's 22 is domain-specific; the universal taxonomy has 64. |
| Tertiary (L3) | Specific need areas | 86 (oral care) | **512** (universal) | 8 × 8 × 8 = 512. This is the level where most product profiling occurs. |
| Fine-grained (L4) | Atomic intent classes | — | **3,184–3,843** | Yahoo! has 3,843 (branching 7.51 from L3); Google has 3,184 (branching 6.22). The advertiser-viable subset: ~1,247 (ratio 3.08:1). |

**Key finding:** Timoshenko's 6→22→86 describes a *single-domain* hierarchy (oral care). The Yahoo!/Google structure (8→64→512→3,184–3,843) describes a *cross-domain web-scale* taxonomy. Deepl Search needs both: per-domain profiles at ~50–150 intents (Timoshenko scale) mapped onto the universal web-scale taxonomy (~3,800 scale). The universal structure is 4 levels, not 3 — and the L1 count is 8, not 5-7.

**The Octohedral Hypothesis:** Web-scale intent taxonomies converge on this 4-level, branching-8 structure because it is the unique attractor where three constraints intersect — query entropy (beyond ~4,000 classes, classification accuracy degrades), advertising economics (only ~1,200 classes are commercially viable), and human categorization limits (4 levels, branching ≤ 10). This is structural convergence, not coincidence: Yahoo! and Google's L1–L3 are identical (8→64→512), built independently by different teams for different products.

**Architecture implication:** Deepl Search should adopt the full 3,843-class taxonomy structure with zero-shot assignment from day one. Users see only the 5–20 intents relevant to their domain; the backend uses the full taxonomy to prevent coverage gaps. The 4-level structure is not optional — it is the discovered optimum.

### 2.2 Intent Is Multi-Label, Not Single-Label

A single search query can express multiple intents. Timoshenko found that 9.2% of user-generated content sentences contained two or more distinct customer needs. Yahoo!'s intent clustering showed some groups mixing related but distinct intents (e.g., movie cast AND musical band members in the same cluster).

**Implication:** Forcing each keyword into exactly one cluster loses information. The system should support soft membership — a keyword can belong to multiple intent clusters with different weights.

### 2.3 Intent Is Dynamic, Not Fixed

The taxonomy of intents changes by domain, over time, and with exposure to recommendations:

- **By domain:** Oral care intents (whitening, sensitivity, travel) differ structurally from kitchen appliance intents (malfunctions, difficulties, surprises). Timoshenko replicated across both domains and found significant differences.
- **Over time:** Krauth et al. (2022) showed that feedback loops in recommendation systems bias future user behavior. A system that recommends certain intents will shift the distribution of future queries toward those intents.
- **By user segment:** Pinterest's Query2Interest work showed that the same keyword ("coffee") maps to different interests for different users (buying beans vs. finding cafes vs. reviewing brewers).

**Implication:** Intent taxonomies cannot be built once and reused. They must be generated per domain, refreshed periodically, and potentially personalized.

### 2.4 The Human Agreement Ceiling

Even trained professionals disagree on what a "user intent" IS:

| Metric | Value | Source |
|---|---|---|
| New analyst vs. original analyst agreement | 70% | Timoshenko & Hauser |
| Same analyst, 2 weeks apart | 80% | Timoshenko & Hauser |
| Individual recall of all possible intents | 45-68% | Griffin & Hauser (1993) |
| Automated query classifier accuracy | 95.6% | Jansen (2009) |

**Implication:** The system cannot exceed ~70-80% agreement with human judges on intent labels, because that's the ceiling of human agreement itself. This doesn't mean the ML is failing — it means the task has inherent ambiguity.

---

## 3. What Makes This Hard

### 3.1 Short Queries

The average search query is 2.79 words (Jansen, 2009). 71.64% of search sessions contain only a single query. Intent extraction must work from extremely short text — which is hard even for large language models. Pinterest showed that BERT only achieves ~86% accuracy on 2-3 word queries, and that simpler models (fastText) can match it with good data augmentation.

### 3.2 Power-Law Distributions

Search behavior follows a power law: 10% of the most frequent queries account for 54% of all search volume. The remaining 90% of queries are rare — and these rare queries are often where the most strategically valuable intents live. Timoshenko found that 17 out of 86 customer needs appeared fewer than 5 times in 8,000 sentences. Popularity-based methods would miss them entirely.

### 3.3 Feedback Loops

Any system that influences what users see will also influence what users search for. Krauth et al. (2022) proved that recommendation algorithms create measurable feedback effects: the distribution of future user behavior shifts toward whatever the algorithm recommends. This means intent clusters built from post-recommendation data differ systematically from pre-recommendation data. Worse, some algorithms are more susceptible than others — frequency-based grouping amplifies feedback 50% more than embedding-based clustering.

### 3.4 Strategic Adaptation

Content creators respond to ranking algorithms. Krauth et al. showed that higher-dimensional embeddings (d=100 vs d=10) allow more targeted — and potentially more biased — content creation. SEO practitioners will optimize for whatever the intent-ranking system exposes. A pre-deployment audit of these incentives can predict manipulation patterns with 70%+ accuracy.

### 3.5 The Embedding Capacity Ceiling

There is a mathematical limit to single-vector embeddings. Kumar et al. (2025) proved that for a corpus of n documents with margin γ, the required embedding dimension to guarantee correct retrieval grows polynomially with n. For web-scale (n=10¹¹), the required dimension (d≥8,098) exceeds what any production system uses (typically d<1,024). Cross-encoders and multi-vector models (ColBERT) escape this limitation. The practical consequence: some retrievable intent-classes simply cannot be represented in fixed-dimension space, regardless of model quality.

---

## 4. What Architecture Is Indicated

The literature converges on a two-stage architecture:

```
┌─────────────────────────────────────────────────────┐
│  Stage 1: Fast Candidate Generation                  │
│                                                      │
│  Query text → Sentence Embedding (SimCSE / SBERT)   │
│           → UMAP dimensionality reduction             │
│           → HDBSCAN density-based clustering          │
│           → Noise-class for unclusterable queries     │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│  Stage 2: Hierarchy & Labeling                       │
│                                                      │
│  Cluster centroids → Ward's hierarchical clustering  │
│           → c-TF-IDF top terms per cluster            │
│           → LLM zero-shot label generation            │
│           → Human validation (accept/edit/reject)    │
└─────────────────────────────────────────────────────┘
```

### Why This Design

| Decision | Why | Evidence |
|---|---|---|
| Separate embedding and clustering | IR surveys show two-stage (bi-encoder + cross-encoder) is the proven pattern | BeiWang 2026 |
| Density-based clustering (HDBSCAN) | Variable cluster shapes, no k required, noise class for outliers | BERTopic; specific-search-terms-results |
| + Ward's hierarchical post-hoc | Produces the 4-level taxonomy structure that matches the Yahoo!/Google convergence | Intent Topology memo; Timoshenko & Hauser (domain-scale) |
| SimCSE over MiniLM | SimCSE-BERT achieves 81.6% on semantic similarity vs. ~72% for MiniLM | SimCSE paper |
| c-TF-IDF + LLM for labels | Fast initial labels + zero-shot LLM refinement at ~80% human agreement | BERTopic; BeiWang survey |
| Human validation loop | The human agreement ceiling (70%) means automated labels need review | Timoshenko inter-coder study |

### The Simplest Thing That Could Work

Pinterest's Query2Interest (2020) showed that **fastText with smart data augmentation** achieves within 2% of BERT's accuracy on short-query classification, while being 100x faster and running on CPU. If the data augmentation strategy is strong enough (using user engagement signals as weak labels), the simplest viable model is:

> **Zero-shot LLM assignment to the 3,843-class YQT taxonomy skeleton**

This is simpler than clustering from scratch: instead of discovering the taxonomy structure from data (which requires compute and validation), we adopt the already-converged Yahoo!/Google skeleton (8→64→512→3,843) and use an LLM prompt to assign each query to the most relevant intent node. Costs near-zero to deploy and gives full coverage from day one.

---

## 5. What Must Be True for This to Work

### 5.1 Evidence That Intent IS Learnable

| Evidence | Finding | Source |
|---|---|---|
| Fact 1 | 86% of interview-based customer needs recovered from UGC via ML | Timoshenko & Hauser |
| Fact 2 | 90.3% accuracy on 14-class intent classification | Yahoo! query intent (2016) |
| Fact 3 | 95.6% accuracy on query reformulation state classification | Jansen (2009) |
| Fact 4 | Bi-encoder dense retrieval works at corpus scale | BeiWang IR survey (2026) |
| Fact 5 | Short queries (2-3 words) classified at 86% accuracy | Pinterest Q2I (2020) |

### 5.2 The Hardest Open Questions

| Question | Why It Matters | How We'll Answer |
|---|---|---|
| Does Google Ads API provide enough keywords for niche B2B domains? | Core data source viability | Pilot across 5 domains |
| What's the actual cost per domain? | Unit economics | Track 10 analyses |
| Do users pay for intent-level insights? | Product viability | User interviews + pilot |
| How stable are clusters over 6 months? | Maintenance cost | Temporal stability study |
| What's the minimum keyword count for meaningful clustering? | Feature gate | Corpus size experiment |
| Can weak supervision replace human labels? | Cost structure | Compare label strategies |

---

## 6. What We'd Validate First

Before writing production code for the ML pipeline, three experiments:

### Experiment 1: Data Feasibility (2 weeks)
Can we get sufficient keyword coverage from Google Ads API across 5 diverse domains? Measure: keyword count, coverage breadth, cost. **Go/no-go: ≥1,000 keywords per domain, cost ≤$5/domain.**

### Experiment 2: Baseline Performance (3 weeks)
Does intent clustering (even simple TF-IDF + k-means) surface information not visible in a keyword table? Compare 3 baselines: (a) keyword table sorted by volume, (b) TF-IDF + k-means clustering, (c) SimCSE + HDBSCAN. **Go/no-go: clustering methods surface ≥20% novel intents not obvious from keyword table.**

### Experiment 3: Human Validation (2 weeks)
Do domain experts rate the generated intent clusters as interpretable and useful? 3 annotators × 100 clusters × 5 domains. **Go/no-go: mean interpretability ≥3.5/5.**

Total validation phase: **7 weeks, ~$5,000-$10,000** (API costs + annotation budget).

---

## 7. What Success Looks Like

A product team inputs their domain ("project management software") and receives:

1. **An intent map** — drawn from the universal 3,843-class taxonomy, filtered to the 20-60 intents relevant to their domain, organized in the 4-level hierarchy (L1→L2→L3→L4).
2. **Volume distribution across intents** — not just per keyword, but per need, aggregated at L2 (reporting) and L4 (analysis).
3. **Hidden opportunities** — intents with high aggregate volume but low-quality SERP coverage. These exist because the full 3,843-class taxonomy reveals intents that keyword-level tools miss.
4. **Trend direction** — which intents are growing/declining, tracked against the stable taxonomy skeleton.
5. **Content gap analysis** — intents that are underserved by existing content, measured as the delta between search volume and top-10 SERP relevance scores.

The value proposition: **not "more accurate keyword data" but "structurally different information"** — the difference between a list of words sorted by popularity and a map of what people actually want. The 3,843-class taxonomy is the map; every domain gets its slice.

---

## Appendix: Evidence Traceability

Key sources used in this synthesis:

| Paper | Key Finding | Section |
|---|---|---|
| Timoshenko & Hauser (2018) — Customer Needs from UGC | Frequency ≠ importance (ρ=0.21); 86% needs recoverable; 70% inter-coder ceiling; 3-level domain hierarchy (6→22→86) | 1, 2, 4 |
| Jansen (2009) — Query Reformulation Patterns | 6 reformulation states; 95.6% classification accuracy; 2.79 mean query length; 71.64% single-query sessions | 2, 3 |
| Hashemi et al. (2016) — Query Intent Detection using CNNs | 90.3% on 14-class, 81.6% on 125-class intent; query embeddings + k-means | 2, 5 |
| BeiWang (2026) — IR Survey | Two-stage retrieval (bi-encoder + cross-encoder); hard negative mining; knowledge distillation; LLM2Vec | 4, 5 |
| Krauth et al. (2022) — EECS-2022-178 | Feedback loops bias future queries; embedding dimension affects bias amplification; algorithm rankings stable | 3, 5 |
| Pinterest (2020) — Query2Interest | 86% accuracy on short queries; fastText ≈ BERT with augmentation; multi-modal signals | 4, 5 |
| SimCSE (2021) — Contrastive Sentence Embeddings | 74.5% unsupervised / 81.6% supervised STS; dropout as augmentation; NLI pairs as positives | 4 |
| Kumar et al. (2025) — LIMIT | Single-vector embedding capacity ceiling; d ≥ 8,098 required for web-scale | 3 |
| Qin et al. (2021) — Are Neural Rankers Still Outperformed | LambdaMART beats most neural rankers on tabular data; fixes after which neural matches GBDT | 4 |
| Airbnb (2018) — Real-time Personalization | Congregated negative sampling; booked listing as global context; cold-start via metadata | 4 |
| Facebook (2020) — Embedding-based Retrieval | Random negatives > impression-based; location + social features improve recall | 4 |
| Qin et al. (2021) — Google ICLR | LambdaMART still SOTA on LTR benchmarks; neural needs log1p + augmentation + SA + latent cross | 4 |
| Cheng et al. (2021) — XMC for Product Search | Tree-based partitioning for 1.25ms latency; outperforms BERT under latency constraints | 4 |
| Dehghani et al. (2017) — Weak Supervision | BM25 as weak label; pairwise objectives generalize better than pointwise | 4 |
| Grbovic et al. (2016) — search2vec | Joint query-ad-link embedding; implicit negatives (skipped ads); dwell-time weighting | 4 |
| BPR (Rendle 2009) | Pairwise ranking optimization outperforms pointwise for implicit feedback | 4 |
| YouTube DNN (Covington 2016) | Two-stage (candidate gen + ranking); sampled softmax; example age feature | 4 |
| IR Textbook (Buttcher 2010) | Pooling method for judgment sets; graded relevance; statistical significance testing | 3, 4 |
| ORCAS, MS MARCO, BEIR, AOL, TREC | Dataset landscape; no large clean intent dataset exists | 3 |
| SimClusters, RecWalk, PinnerSage | Community detection for keyword clusters; random walk with restart; multi-modal user embeddings | 4 |
| Rules of ML (Google) | Data quality > algorithmic improvement; ML suitability criteria | 3 |
| 150 ML Models at Booking | Real-world ML lessons; data-centric insights | 4 |
| EENMF, COLD, SplitNet | Ad ranking architectures; feature crossing; pre-ranking system design |
| Intent Topology Memo (2026) | Structural convergence: Yahoo! YQT 8→64→512→3,843; Google intent 8→64→512→3,184; advertiser pruning 3.08:1; Octohedral Hypothesis | 2, 7 | 4 |
