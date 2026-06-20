## Executive Summary

The ecosystem for search-query analysis and semantic search is fragmented across **information retrieval (IR), recommender systems, and web mining**. No single dataset covers the full pipeline (intent → reformulation → retrieval → SERP → clicks → content gaps). Instead, practitioners must **compose multiple datasets**:

* **MS MARCO / BEIR** → core retrieval and ranking
* **AOL / ORCAS / Yandex logs** → behavioral signals (clicks, sessions)
* **TREC / MSLR-WEB** → evaluation-grade relevance judgments
* **ClueWeb / Common Crawl** → raw web corpus for content modeling
* **Intent datasets (e.g., ORCAS-Intent, TREC Session Track)** → partial labeling

Critical gaps remain in **SERP structure, cannibalization detection, and content gap labeling**, which are rarely directly annotated and must be inferred.

---

# 1. Ranked Dataset & Benchmark Inventory

### Top-Tier (High Utility, Widely Used, Reproducible)

| Dataset                      | Task                         | Size            | Schema                                  | Strengths                                   | Limitations                                 |
| ---------------------------- | ---------------------------- | --------------- | --------------------------------------- | ------------------------------------------- | ------------------------------------------- |
| **MS MARCO** (Microsoft)     | Query-document ranking, QA   | ~1M queries     | Query, passage/doc, relevance labels    | Industry standard, dense + sparse retrieval | Weak labels (derived from Bing clicks)      |
| **BEIR Benchmark**           | Zero-shot IR evaluation      | 18 datasets     | Query, corpus, relevance                | Cross-domain evaluation                     | Not a single dataset; heterogeneous schemas |
| **TREC Deep Learning Track** | Ranking                      | ~400k queries   | Query, doc, graded relevance            | High-quality annotations                    | Limited query diversity                     |
| **MSLR-WEB10K / 30K**        | Learning-to-rank             | 10k–30k queries | Query features, doc features, relevance | Feature-rich                                | No raw text                                 |
| **ORCAS**                    | Query-document click mapping | 10M queries     | Query, clicked doc IDs                  | Large-scale click signals                   | No full session context                     |

---

### Click Logs & Session Data (Behavioral Modeling)

| Dataset                                    | Task                            | Schema                                  | Notes                                                 |
| ------------------------------------------ | ------------------------------- | --------------------------------------- | ----------------------------------------------------- |
| **AOL Query Log (2006)**                   | Session modeling, reformulation | User ID, query, timestamp, clicked URLs | Only public session dataset; privacy issues; outdated |
| **Yandex Personalized Web Search Dataset** | Click modeling                  | Query, session, clicks, dwell time      | Richer than AOL; harder access                        |
| **TREC Session Track**                     | Interactive search              | Query sequences, judgments              | Small but high-quality                                |

**Key Insight:**
Click datasets are essential for:

* Intent inference
* Query reformulation modeling
* Ranking via implicit feedback

But they suffer from:

* Bias (position bias, trust bias)
* Privacy filtering
* Missing negative signals

---

### Query–Document Relevance / Retrieval

| Dataset                        | Task                     | Notes                            |
| ------------------------------ | ------------------------ | -------------------------------- |
| **ClueWeb12 / ClueWeb22**      | Web-scale retrieval      | Paired with TREC judgments       |
| **Robust04 (TREC)**            | Ad hoc retrieval         | Classic IR benchmark             |
| **Natural Questions (Google)** | QA / retrieval           | Real queries + Wikipedia answers |
| **NQ + DPR format**            | Dense retrieval training | Widely used in embedding systems |

---

### Query Intent & Classification

| Dataset                           | Task                          | Notes                        |
| --------------------------------- | ----------------------------- | ---------------------------- |
| **TREC Web Track Intent Data**    | Navigational vs informational | Limited scale                |
| **ORCAS-derived intent datasets** | Weak intent signals           | Derived from click diversity |
| **DBPedia / Wikidata mappings**   | Entity-based intent           | Indirect labeling            |

**Observation:**
There is **no large, clean, multi-class intent dataset** comparable to MS MARCO. Intent is usually:

* Binary (nav vs non-nav)
* Weakly inferred from clicks

---

### Query Clustering & Semantic Similarity

| Dataset                       | Task                 | Notes                        |
| ----------------------------- | -------------------- | ---------------------------- |
| **Quora Question Pairs**      | Semantic similarity  | Useful proxy for clustering  |
| **WikiTitles / WikiSections** | Topic clustering     | Structured semantic grouping |
| **StackOverflow datasets**    | Technical clustering | Domain-specific              |

These are **proxies**, not true search query clusters.

---

### SERP & Snippet-Level Data

| Dataset                                 | Task              | Notes                       |
| --------------------------------------- | ----------------- | --------------------------- |
| **TREC CAR (Complex Answer Retrieval)** | Passage retrieval | Approximates SERP structure |
| **OpenSERP (limited)**                  | SERP snapshots    | Sparse availability         |
| **Commercial APIs (Google, Bing)**      | Real SERP         | Not reproducible or free    |

**Major Gap:**
No large-scale, open dataset with:

* Full SERP layout
* Ranking positions
* Rich features (snippets, features, ads)

---

### Web Crawl & Content Corpora

| Dataset                                | Task                 | Notes            |
| -------------------------------------- | -------------------- | ---------------- |
| **Common Crawl**                       | Raw web text         | Massive, noisy   |
| **C4 (Colossal Clean Crawled Corpus)** | Cleaned crawl        | Used in LLMs     |
| **ClueWeb22**                          | Research-grade crawl | Better structure |

These are required for:

* Content gap analysis
* Topic modeling
* Index construction

---

### Query Reformulation / Session Evolution

| Dataset                | Task                   | Notes                         |
| ---------------------- | ---------------------- | ----------------------------- |
| **AOL Logs**           | Reformulation          | Only open dataset             |
| **TREC Session Track** | Query evolution        | High quality but small        |
| **Yandex Logs**        | Reformulation + clicks | Best available but restricted |

---

# 2. Key Papers & Technical Sources

| Paper                                                                                 | Contribution                            | Dataset    |
| ------------------------------------------------------------------------------------- | --------------------------------------- | ---------- |
| **MS MARCO: A Human Generated MAchine Reading COmprehension Dataset (Nguyen et al.)** | Defines large-scale retrieval benchmark | MS MARCO   |
| **BEIR Benchmark (Thakur et al.)**                                                    | Zero-shot retrieval evaluation          | BEIR       |
| **Deep Learning for IR (Mitra & Craswell)**                                           | Ranking models overview                 | General    |
| **LambdaMART (Burges)**                                                               | Learning-to-rank baseline               | MSLR-WEB   |
| **DPR (Karpukhin et al.)**                                                            | Dense retrieval                         | NQ         |
| **ColBERT (Khattab & Zaharia)**                                                       | Late interaction retrieval              | MS MARCO   |
| **Query Reformulation Study (Huang et al.)**                                          | Session modeling                        | AOL        |
| **Click Models (Joachims, DBN, UBM)**                                                 | Bias correction                         | Click logs |

---

# 3. Dataset Requirements & Practical Constraints

### Data Engineering Requirements

To make datasets usable in a unified pipeline:

1. **Normalization**

   * Lowercasing, tokenization
   * Deduplication of queries
   * URL canonicalization

2. **Entity Extraction**

   * Required for intent modeling
   * Use: spaCy, Wikidata linking

3. **Session Reconstruction**

   * Group queries by user/time window
   * Required for reformulation tasks

4. **Embedding Generation**

   * Dense vectors (e.g., BERT, E5, OpenAI embeddings)
   * Needed for clustering and retrieval

5. **Document Processing**

   * HTML stripping
   * Passage segmentation

---

### Legal & Licensing Constraints

| Dataset      | Constraint                       |
| ------------ | -------------------------------- |
| AOL Logs     | Privacy concerns; restricted use |
| MS MARCO     | Research-friendly                |
| ClueWeb      | Requires license                 |
| Common Crawl | Open but noisy                   |
| Yandex       | Limited access                   |

---

# 4. Evaluation Metrics & Modeling Implications

### Retrieval Metrics

* **NDCG@k** (ranking quality)
* **MRR** (first relevant hit)
* **Recall@k** (coverage)

### Clustering / Semantic Tasks

* **Silhouette score**
* **Adjusted Rand Index (ARI)**

### Intent Classification

* Accuracy / F1
* Macro-F1 (imbalanced classes)

### Click Modeling

* Log-likelihood
* Perplexity

---

### Modeling Stack Implications

| Task          | Model Type                     |
| ------------- | ------------------------------ |
| Retrieval     | BM25, Dense (DPR), Hybrid      |
| Ranking       | LambdaMART, BERT re-rankers    |
| Clustering    | Embeddings + k-means / HDBSCAN |
| Intent        | Classification (BERT)          |
| Reformulation | Sequence models / transformers |

---

# 5. Critical Gaps in the Ecosystem

### 1. No Unified Search Intelligence Dataset

There is no dataset that combines:

* Queries
* SERPs
* Clicks
* Content

This forces synthetic pipelines.

---

### 2. Missing Labels for:

* Content gaps
* Cannibalization
* Query-to-page mapping (explicit)

These must be **inferred**, not learned directly.

---

### 3. SERP Structure Absence

No open dataset includes:

* Featured snippets
* Ranking layout
* SERP features

---

### 4. Weak Intent Labeling

Intent is:

* Under-defined
* Often binary
* Not standardized

---

### 5. Temporal Dynamics Missing

Most datasets ignore:

* Query trends
* Seasonality
* Ranking changes

---

# 6. Prioritized Starter Stack (For Prototype)

### Core Retrieval

1. **MS MARCO (passage + document)**
2. **BEIR (for evaluation)**

### Behavioral Signals

3. **ORCAS (query-click mapping)**
4. **AOL logs (for sessions)**

### Content Layer

5. **Common Crawl or ClueWeb22**

### Semantic Layer

6. **Quora Question Pairs (for clustering pretraining)**

---

### Minimal Viable Pipeline

1. Train embeddings on MS MARCO
2. Build retrieval system (BM25 + dense hybrid)
3. Use ORCAS for weak supervision
4. Cluster queries using embeddings
5. Map queries → documents
6. Detect gaps via coverage mismatch

---

# Final Assessment

* **Best immediate datasets:** MS MARCO, BEIR, ORCAS
* **Best for behavioral modeling:** AOL, Yandex
* **Best for content modeling:** ClueWeb, Common Crawl
* **Biggest missing piece:** SERP-level structured data and explicit SEO-oriented labels

A complete search intelligence system is not trained from a single dataset but **assembled from heterogeneous sources with heavy preprocessing and inferred supervision**.
