# Deepl Search — AI/ML Model Requirements Package

> **Status:** Living requirements document (AI-native restructuring)
> **Version:** 2.0
> **Methodology:** Evidence-grounded, literature-integrated requirements engineering
> **Date:** 2026-06-07
> **Sources:** ~85 documents across IR, NLP, RecSys, customer-needs mining, knowledge graphs, and representation learning — 300+ extracted concepts integrated

---

## Table of Contents

1. [Fundamental Usefulness Claim](#1-fundamental-usefulness-claim)
2. [Target Construct](#2-target-construct)
3. [Data Contract](#3-data-contract)
4. [Label/Validation Contract](#4-labelvalidation-contract)
5. [Baseline Contract](#5-baseline-contract)
6. [Experiment Contract](#6-experiment-contract)
7. [Evaluation Contract](#7-evaluation-contract)
8. [Behavioral Tests](#8-behavioral-tests)
9. [Error Taxonomy](#9-error-taxonomy)
10. [Kill Criteria](#10-kill-criteria)
11. [Robustness](#11-robustness)
12. [Model Candidate Space](#12-model-candidate-space)
13. [Ablation Plan](#13-ablation-plan)
14. [Monitoring and Drift](#14-monitoring-and-drift)
15. [Human Oversight](#15-human-oversight)
16. [Software Wrapper Requirements](#16-software-wrapper-requirements)

---

## 1. Fundamental Usefulness Claim

### 1.1 Core Question

**Is there a principled, simple, useful reason to build and train this ML model, beyond producing a technically impressive pipeline?**

### 1.2 Claim

Search queries encode latent user intents and jobs-to-be-done that are not directly visible from keyword-level metrics (volume, CPC, competition). A system that maps keywords → intent clusters → market demand patterns provides decision-making value that keyword tables alone cannot. The claim is testable: intent clusters should surface demand categories that product teams recognize as real and actionable, and that are NOT obvious from a flat keyword table.

### 1.3 Evidence That the Phenomenon Is Learnable

| Evidence Source | Finding | Implication for Learnability |
|---|---|---|
| Timoshenko & Hauser (2018) | 86% of interview-based customer needs recovered from UGC via CNN + clustering | Query text contains systematic intent signals extractable by ML |
| Hashemi et al. (2016, Yahoo!) | 90.3% accuracy on 14 high-level intent classes, 81.6% on 125 low-level classes using CNN query vectors | Query intent is predictable at scale with supervised methods |
| IR Survey BeiWang (2026) | Bi-encoder dense retrieval captures query-document relevance at corpus scale | Intent representation in dense space is a solved sub-problem |
| Jansen et al. (2009) | 6-state query reformulation model with 95.6% classifier accuracy | Search session structure follows predictable intent-transition patterns |
| Pinterest Q2I (2020) | 86% accuracy on short-query interest classification with augmented fastText | Even simple models capture intent from short queries with good data |

### 1.4 Why Not Just a Keyword Table?

The Timoshenko & Hauser finding (frequency of mention vs. importance, ρ=0.21, p=0.06) demonstrates that frequency-based signals miss 29% of high-importance, 44% of high-performance, and 72% of hidden-opportunity needs. A keyword table sorted by volume surfaces popular queries, not important intents. Intent clustering surfaces structurally different information.

### 1.5 Risk of Non-Usefulness

| Risk | Mitigation |
|---|---|
| Clusters do not correspond to real user intents | Human evaluation study (3 raters, 100 clusters, 5 domains); compare against interview-based needs per Timoshenko methodology |
| Users prefer keyword tables over clusters | MVS-first approach: ship keyword tables first, add clustering only if users engage with it |
| Intent value insufficient to justify cost | Measure cost per unique intent discovered vs. manual taxonomy building (target: 40-50% cost reduction per Timoshenko) |

---

## 2. Target Construct

### 2.1 Operational Definition

**Intent** for this system: a multi-label soft assignment of a search query to one or more user-goal categories derived from the query text and its behavioral context. Each intent cluster represents a set of queries sharing a common user goal, as validated by human judges with ≥70% inter-annotator agreement (matching the Timoshenko inter-coder accuracy ceiling of 70%).

### 2.2 Construct Hierarchy (from Evidence)

**Important distinction:** There are two hierarchy scales — the *per-domain scale* (what Timoshenko measured for oral care) and the *web-universal scale* (what Yahoo!/Google built for all search). Both are needed.

| Level | Domain-scale (Timoshenko) | Web-scale (Yahoo!/Google) | Branching | Evidence |
|---|---|---|---|---|
| L1 — Primary | 6 (oral care: Product Efficacy, Convenience, etc.) | **8** (universal macro-categories) | 8× expansion | Yahoo! YQT: 8 L1; Google intent: 8 L1; Timoshenko domain = constrained subset |
| L2 — Secondary | 22 (oral care sub-goals) | **64** | 8× from L1 | Both Yahoo! and Google: 8×8 = 64; Timoshenko has 22 in a single domain |
| L3 — Tertiary | 86 (oral care JTBD statements) | **512** | 8× from L2 | Yahoo! and Google: 8×8×8 = 512; Timoshenko's 86 is domain-specific |
| L4 — Fine-grained | — | **3,184–3,843** | 6.2–7.5× from L3 | Yahoo! YQT: 3,843 (L3→L4 branching 7.51); Google patent: 3,184 (L3→L4 branching 6.22); IAB (3-level): 1,712 |

**Key implication:** Deepl Search should use the full 4-level, 3,843-class web-scale taxonomy as the universal skeleton, and populate per-domain subsets at L3–L4 (~50–150 intents per domain) using the Timoshenko methodology. The two scales are not contradictory — they are nested.

### 2.3 Properties

| Property | Requirement | Evidence |
|---|---|---|
| Multi-label | A keyword may belong to multiple intents | Timoshenko: 9.2% of sentences contained ≥2 needs; Yahoo! clustering showed some clusters mixed related intents |
| Soft membership | Membership weights, not binary assignment | VAE-CF (Liang 2018): multinomial VAE captures uncertainty in assignments |
| Dynamic taxonomy | Taxonomy is per-domain, not universal | Timoshenko: oral care hierarchy differs; Intent taxonomy should be generated per vertical |
| Hierarchical | 4-level structure (8→64→512→3,843) | Intent Topology memo: Yahoo! YQT & Google intent converge on 4 levels, branching 8; Timoshenko domain-scale is 3-level subset |
| Universal skeleton + per-domain profile | Taxonomy structure is universal at L1-L3; domain-specific at L4 | Yahoo! YQT: 8×8×8 structure is identical across domains; Timoshenko: per-domain hierarchies differ at L3-L4 |
| Long-tail aware | Rare intents preserved, not force-assigned | Timoshenko: 17 needs appeared ≤5 times in 8,000 sentences; HDBSCAN noise class retains unclusterable queries |

### 2.4 What Intent Is NOT

- **Not a URL category** (URL structure is a feature, not the target — Intent Segmentation paper: URL features ranked #1 for segmentation but not the definition of intent)
- **Not a single-label class** (queries may have multiple intents — Yahoo! found mixed-intent clusters)
- **Not a single flat taxonomy** (the universal L1-L3 skeleton is predefined; domain-specific L4 profiles emerge from data per domain)
- **Not search satisfaction** (query intent ≠ result relevance — satisfaction is downstream)

### 2.5 Adjacent Constructs

| Construct | Relationship | Key Paper |
|---|---|---|
| Query Reformulation State | Temporal refinement of intent within session | Jansen: 6 states (New → Specialization, Generalization, etc.) |
| Customer Need | Abstract benefit statement (richer than query intent) | Timoshenko & Hauser |
| JTBD | Why a user "hires" a product (funnels into intent) | Christensen; operationalized via Timoshenko hierarchy |
| Browse Segment | Intent coherent from URL+time features | Intent-Based Browse Activity Segmentation |
| Interest (Q2I) | Long-term user affinity vs. short-term search intent | Pinterest Q2I |

---

## 3. Data Contract

### 3.1 Primary Data Source

Google Ads API (KeywordPlanIdeaService). This is the core innovation claim — replacing web crawling with API access.

### 3.2 Data Properties (from Evidence)

| Property | Expected Value | Evidence |
|---|---|---|
| Query length | Mean 2.79 terms (SD=1.54) | Jansen: 964,780 sessions analysis |
| Session structure | 71.64% single-query, 15.85% 2-query, 12.51% 3+ | Jansen |
| Query distribution | Power-law: few dominant, many rare | Timoshenko: 10% most frequent needs → 54% of informative sentences |
| Topical breadth | ~100 intents per domain at tertiary level | Timoshenko: 86-94 needs per domain |
| Data volume | 1,000-200K+ keywords per domain | Constraint from API quotas |

### 3.3 Available Features (Ranked by Predictive Power)

| Rank | Feature Type | Evidence |
|---|---|---|
| 1 | URL/temporal features | Intent Segmentation paper: URL domain shift best single feature for intent boundary detection |
| 2 | Query text (content) | Timoshenko: CNN on query text achieves F1=74% for informative sentence detection |
| 3 | Co-occurrence signals | Airbnb: skip-gram on click sessions for listing embeddings |
| 4 | Volume/competition | Google Ads API native metadata |
| 5 | GEO/language | Facebook Search: +2.20% recall from location features |
| 6 | Session context | Jansen: ~28% of sessions have multi-query structure with reformulation patterns |

### 3.4 Data Challenges

| Challenge | Severity | Evidence/Mitigation |
|---|---|---|
| Short query length | High | SimCSE: dropout-based contrastive learning works even with short text; Q2I: pin annotation augmentation compensates |
| No labeled intents | High | Weak supervision (Dehghani 2017): BM25 as weak label, paired objectives generalize; Query2Interest: user engagement as weak signal |
| API rate limits | High | Use token-bucket rate limiting, MCC sub-account pool, exponential backoff |
| PII in queries | Must-solve | Pattern-based PII detection (phone, email, name); k-anonymity (k<5 queries excluded) |
| Temporal coverage | Medium | Periodic refresh; freshness feature per YouTube DNN paper ("Example Age") |
| Feedback loops | Medium | Krauth/EECS: past recommendations bias future queries; CAFL-style correction may be needed |
| Strategic adaptation (SEO) | Medium | EECS: content creators respond to ranking algorithms; pre-deployment audit recommended |

### 3.5 Dataset Landscape

| Dataset | Relevance | Limitation |
|---|---|---|
| MS MARCO | Retrieval backbone, 1M queries | Weak click-based labels |
| BEIR | Zero-shot IR evaluation, 18 datasets | Not intent-focused |
| TREC Deep Learning Track | High-quality graded relevance | Limited query diversity |
| ORCAS | Click signals, 10M queries | No full session context |
| AOL Query Log | Session modeling | Privacy concerns, outdated (2006) |
| Yahoo! Query Intent | 14-class / 125-class taxonomy | Not publicly available |

**Key gap:** No large, clean, multi-class intent dataset exists. Intent datasets are binary or weakly inferred. This reinforces the unsupervised + human-in-the-loop approach.

### 3.6 Schema Requirements

```json
{
  "keyword": {
    "text": "string",
    "search_volume": "integer >= 0",
    "competition_index": "float [0.0, 1.0]",
    "average_cpc": "float >= 0 | null",
    "language": "ISO 639-1",
    "geo_target": "ISO 3166-1 alpha-2",
    "retrieval_timestamp": "ISO 8601 UTC"
  },
  "intent_cluster": {
    "cluster_id": "uuid",
    "level": "primary | secondary | tertiary",
    "parent_id": "uuid | null",
    "label": "string",
    "top_terms": ["string"],
    "representative_queries": ["string"],
    "member_count": "integer",
    "confidence": "float [0, 1]",
    "human_validated": "boolean",
    "validation_history": [{"user_id", "timestamp", "action"}]
  },
  "assignment": {
    "keyword_text": "string",
    "cluster_id": "uuid",
    "membership_weight": "float [0, 1]"
  }
}
```

---

## 4. Label/Validation Contract

### 4.1 The Annotation Ceiling

| Finding | Value | Source |
|---|---|---|
| Inter-coder agreement (new analyst vs original) | 70% | Timoshenko & Hauser |
| Inter-task agreement (same analyst, 2 weeks apart) | 80% | Timoshenko & Hauser |
| Individual analyst recall of universe needs | 45-68% | Griffin & Hauser (1993) |
| Automated query classifier accuracy | 95.6% | Jansen |
| LLM zero-shot taxonomy labeling (GPT-4) | ~80% estimated | BeiWang 2026 survey |

**Target:** Multi-annotator majority vote (3 annotators per sample) with ≥70% agreement acceptance threshold.

### 4.2 Labeling Strategy

| Method | Cost | Quality | When Used |
|---|---|---|---|
| Unsupervised clustering (no labels) | $0 | Baseline | First pass, all domains |
| Weak supervision (BM25, rules, heuristics) | Low | Moderate | Bootstrapping, tail queries |
| Expert annotation (3 per cluster, 100 clusters) | Medium | High | Evaluation set creation |
| Human-in-the-loop validation | Low per sample | High | Production cluster labeling |
| LLM zero-shot labeling | Very low | ~80% | Seed taxonomy creation, rapid iteration |

### 4.3 Minimal Labeled Data Requirements

| Task | Minimum Labeled | Evidence |
|---|---|---|
| Informative query classifier | 500-2,000 labeled queries | Timoshenko: CNN stabilizes after ~500 sentences |
| Intent classification (flat) | 8,000-12,000 labeled queries | Timoshenko: 8K sentences covered 86% of needs; 12K covered 97% |
| Intent classification (hierarchical) | 15,000-25,000 labeled queries | Extrapolation from Timoshenko + Yahoo! hierarchy |
| Cluster quality evaluation | 100 clusters × 3 raters | Standard HCI evaluation methodology |

### 4.4 Validation Methodology (per Timoshenko)

Compare system-discovered intent clusters against professionally curated needs:
1. Build ground-truth need set via expert interview protocol (20-30 interviews per domain)
2. Extract needs via the ML pipeline
3. Compute recall: what fraction of ground-truth needs are surfaced by the system
4. Compute uniqueness: what fraction of system-discovered needs are NOT in the ground-truth set (novel discoveries)
5. Cost: compare total project cost vs. traditional methods (target: 40-50% cost reduction per Timoshenko's efficiency findings)

### 4.5 Label Quality Gates

| Gate | Criteria | Action if Failed |
|---|---|---|
| Inter-annotator agreement | ≥70% on evaluation set | Retrain annotators, refine taxonomy, adjust labels |
| Label consistency over time | Same keyword → same label within 30 days | Review drift, check for taxonomy changes |
| Label coverage | ≥80% of keywords assigned to a non-noise cluster | Adjust clustering parameters, consider more clusters |
| LLM label sanity | LLM-assigned labels match expert labels ≥70% | Review LLM prompting, fall back to expert labels |

---

## 5. Baseline Contract

### 5.1 Mandatory Baselines

| Baseline | Description | Evidence | Minimum Improvement |
|---|---|---|---|
| BM25 query similarity | Traditional lexical matching for query grouping | IR textbook: BM25 is mandatory non-neural baseline | Must beat; else ML is not justified |
| TF-IDF + k-means | Sparse feature clustering | fastText/Q2I: simple models can approach complex ones with good data | ≥10% NMI improvement |
| Word2Vec avg + k-means | Averaged word embeddings + flat clustering | Timoshenko: 20-dim avg embeddings with Ward's clustering separate primary needs | ≥15% NMI improvement |
| Keyword table (no ML) | Just show the keyword table sorted by volume | This is the simplest "model" — what the user sees without ML | Clusters must provide info NOT visible in sorted table |
| LambdaMART on keyword features | GBDT on engineered features (counts, tf-idf) | Qin (ICLR 2021): LambdaMART beats most neural rankers on tabular data | Relevant if using numerical features |
| MiniLM + HDBSCAN (current plan) | The proposed architecture | specific-search-terms-results.md | Any improvement over this is the ablation target |

### 5.2 Baseline Testing Protocol

1. Run all baselines on the same corpus (same domain, same keyword set)
2. Evaluate using all metrics from Section 7
3. Report mean and 95% CI across 5 domains (3 consumer, 2 B2B)
4. **Pre-register** which baseline is the primary comparison before running experiments
5. If no baseline outperforms BM25 + keyword table (no ML), the ML component is not justified

### 5.3 Evidence That Simple Baselines Are Strong

| Evidence | Implication |
|---|---|
| Qin (2021): LambdaMART beats neural rankers on LTR benchmarks | Simple tree-based models on tabular features are strong |
| Pinterest Q2I: fastText with augmentation matches BERT at 100x lower cost | Data quality can close the architecture gap |
| Timoshenko: CNN (F1=74%) only +8 points above SVM (65.7%) | Complex models show diminishing returns on this task |
| Jansen: 2nd-order Markov model (40% precision) best tradeoff | Simple n-gram models exploit session structure effectively |

---

## 6. Experiment Contract

### 6.1 Experimental Design Principles

| Principle | Requirement | Source |
|---|---|---|
| Pre-registered | All experiment designs and baselines registered before execution | IR evaluation standards |
| Multi-domain | Test on ≥5 domains (3 consumer, 2 B2B) | Timoshenko: oral care + kitchen appliances showed different patterns |
| Frequency-stratified | Report metrics separately for head (top 20%), torso (40%), tail (40%) by volume | Timoshenko: CNN recall varied by frequency class; EECS: bias by frequency |
| Reproducible | All dependencies versioned; random seeds fixed; pipeline logs stored | NFR-18, NFR-19 |
| Statistical significance | Bootstrap or paired tests for all comparisons | IR textbook: t-test, Wilcoxon for metric comparisons |
| Ablation-friendly | Every component can be disabled/swapped independently | See Section 13 |

### 6.2 Experiment Types

| Type | Purpose | Method | Sample Size |
|---|---|---|---|
| A. Embedding quality | Compare embedding models for intent separation | NMI on known intent categories, STS correlation | 5 domains, 100K+ queries |
| B. Clustering quality | Compare clustering algorithms | NMI, ARI, noise ratio, cluster count stability | 5 domains, same embeddings |
| C. Taxonomy structure | Evaluate hierarchical vs flat taxonomy | Task completion rate, interpretability score | 3 domains, 3 raters |
| D. Human evaluation | Measure real-world usefulness | Cluster interpretability (1-5), uniqueness, actionability | 100 clusters, 3 raters |
| E. Cost benchmark | Measure total cost per domain | API cost + compute cost (GPU hours + storage) | 10 domains |
| F. Temporal stability | Measure cluster drift over time | Cluster purity month-over-month | 3 domains, 6 months |

### 6.3 Training Protocol

| Step | Detail |
|---|---|
| Hardware | CPU baseline (fastText, TF-IDF); GPU for transformers (T4 minimum, A100 recommended) |
| Batch size | 256-1024 depending on GPU memory |
| Sequence length | 256 tokens for MiniLM (longer provides no benefit per specific-search-terms-results) |
| Early stopping | Validation loss plateau for 3 epochs |
| Data splits | 70/15/15 train/val/test stratified by query length |
| Contrastive training | InfoNCE loss with in-batch negatives + BM25 lexical negatives (BeiWang 2026) |
| Optimization | AdamW, linear warmup (10% of steps), cosine decay |

### 6.4 Negative Sampling Strategy

| Strategy | Use Case | Evidence |
|---|---|---|
| Random negatives | General pre-training | Facebook Search: random negatives outperform impression-based |
| In-batch negatives | Efficient training at scale | BeiWang 2026: standard in bi-encoder training |
| BM25 lexical negatives | Hard negatives for fine-grained separation | BeiWang 2026: lexical near-misses improve separation |
| Congregated negatives | Domain-specific separation | Airbnb: same-market negatives prevent trivial separation by domain |
| Implicit negatives (skipped) | Behavioral signal | search2vec: skipped ads above clicked ad as negatives; dwell-time weighting |

---

## 7. Evaluation Contract

### 7.1 Primary Metrics

| Metric | What It Measures | Target | Evidence |
|---|---|---|---|
| NMI (Normalized Mutual Information) | Cluster coherence vs. ground truth | ≥0.5 | Standard in clustering evaluation |
| Noise ratio | Fraction of queries assigned to noise | ≤30% | HDBSCAN default can reach 30% in diverse corpora |
| Human interpretability score | Cluster makes sense to domain experts | ≥3.5/5 | Timoshenko: 70% inter-coder baseline |
| Unique intent recall | Fraction of known intents discovered | ≥80% | Timoshenko: 86% of interview needs recovered |
| Cost per unique intent | $ per novel intent discovered | **$0 for bootstrap** (zero-shot LLM); **monitor for cost at scale** | Timoshenko: 40-50% cost reduction target; zero-shot eliminates annotation cost for v1 |
| Topic coherence (c_v) | Topic internal consistency | **≥0.55** | Standard topic model metric; informed by BERTopic benchmarks on similar-scale corpora |

### 7.2 Secondary Metrics

| Metric | What It Measures | Evidence |
|---|---|---|
| Silhouette score | Cluster separation | Standard unsupervised metric |
| nDCG@k | Ranked cluster relevance | IR textbook: graded relevance standard |
| Cluster count stability | Run-to-run variance | EECS: relative algorithm rankings stable |
| Spearman correlation | Volume accuracy vs. GSC ground truth | EV-06, EV-07 |
| Inter-annotator agreement (Kappa) | Label reliability | Timoshenko: 70% baseline; IR textbook: pooling method |
| Rank-biased overlap (RBO) | Top-k stability over time | Information retrieval evaluation |

### 7.3 Evaluation Framework

Following the EECS-2022-178 pipeline:
1. **Offline-first**: Dataset creation from logged interactions → offline metrics (NMI, coherence, noise ratio) → baseline comparison → human evaluation
2. **Online validation**: A/B test or user satisfaction survey
3. **Diminishing returns check**: Beyond NMI=0.75, further improvements may not yield online gains (EECS finding)

### 7.4 Relative vs. Absolute Metrics

EECS finding: absolute metric values are biased by sampling distribution, but **relative algorithm rankings are stable**. Therefore:
- Report absolute metrics for interpretability
- Make decisions based on relative comparisons between methods
- Compare on the same held-out evaluation set

### 7.5 Frequency-Stratified Reporting

| Quartile | Definition | Expected Performance | Risk |
|---|---|---|---|
| Head | Top 20% by volume | High NMI, low noise ratio | Overfitting to popular queries |
| Torso | 20-60% | Moderate | Most representative of "typical" performance |
| Tail | Bottom 40% | Lower NMI, higher noise ratio | Rare intents may be missed entirely |

**Requirement:** Every evaluation must include stratified results. Aggregate metrics alone are insufficient.

---

## 8. Behavioral Tests

### 8.1 Pre-Deployment Behavioral Tests

| Test ID | Test Description | Pass Criteria | Source |
|---|---|---|---|
| BT-01 | **Synonym robustness**: Queries with different wording for same intent should cluster together | ≥70% of synonym pairs in same cluster | Timoshenko: spelling variants cluster; SimCSE: semantic equivalence |
| BT-02 | **Polysemy handling**: "apple" (fruit) and "apple" (tech) should separate if domain includes both | Distinct clusters with ≤20% overlap | PinText multitask: different facets |
| BT-03 | **Long-tail preservation**: Rare but valid intents are not discarded as noise | ≥50% of queries from tail quartile assigned to non-noise clusters | Timoshenko: 17 rare needs missed by frequency filter |
| BT-04 | **Cross-domain transfer**: Taxonomy from domain A should partially match domain B at primary level | ≥30% overlap at primary level | Timoshenko: 6-primary structure generalizes |
| BT-05 | **Reformulation tracking**: "cheap flights" → "budget airlines" → "low cost carriers" assigned to same intent | ≥80% same cluster | Jansen: reformulation states show intent preservation |
| BT-06 | **Freshness awareness**: Temporal trends in query volume produce cluster shifts over time | Cluster membership shifts <20% over 30 days | YouTube Example Age feature; EECS: drift over time |
| BT-07 | **SEO resistance**: Repeated queries from same source do not dominate cluster membership | No single client accounts for >5% of any cluster | EECS: strategic adaptation; exposure games |

### 8.2 Behavioral Test Protocol

For each behavioral test:
1. Define the test scenario (input queries + expected cluster assignments)
2. Generate synthetic or curated test data
3. Run pipeline with current model version
4. Compare output against expected behavior
5. Report pass/fail + deviation magnitude

### 8.3 Adversarial Test Cases

| Case | Design | Expected Vulnerability |
|---|---|---|
| Typos and misspellings | "restaraunt menu" for "restaurant menu" | Low if char n-gram features used; high if word-only |
| Multi-intent queries | "buy iphone case and compare plans" | Low if soft clustering; high if hard assignment |
| Domain-specific jargon | "SEM" = "Search Engine Marketing" vs "Scanning Electron Microscope" | High without domain context |
| Very short queries | "coffee" — hundreds of possible intents | High (fundamental limitation per Jansen: 2.79 mean length) |
| Query injection | SEO keyword stuffing — "buy cheap nike air jordan shoes online free shipping" | Cluster may be anomalous; flag for review |

---

## 9. Error Taxonomy

### 9.1 Error Types

| Error Class | Type | Severity | Example | Detection |
|---|---|---|---|---|
| False positive cluster | A cluster that does not correspond to any real user intent | High | Queries about "pizza" and "software" clustered due to embedding artifact | Human evaluation; topic coherence < threshold |
| False negative (missed intent) | A real user intent not captured by any cluster | High | "electric toothbrush travel case" not grouped with travel-related queries | Recall vs. ground-truth needs; human review |
| Over-splitting | A single intent split across multiple clusters | Medium | "white teeth", "teeth whitening", "whiten smile" in 3 separate clusters | High cluster similarity (low silhouette); merge recommendations |
| Under-splitting | Multiple intents collapsed into one cluster | Medium | "buy toothbrush" and "repair toothbrush" in same cluster | Low topic coherence; high within-cluster variance |
| Noise misclassification | Valid query marked as noise | Low-Medium | High-volume queries that are hard to group | High noise ratio; review noise samples |
| Contamination | PII or sensitive data in cluster | Critical | Phone number in cluster top terms | PII detection pre-filter; k-anonymity |
| Drift error | Model behavior changes over time | Medium | Seasonal queries change cluster membership | Monitoring alert; Wasserstein distance |
| Ambiguity error | Correct assignment but label is misleading | Low | Cluster label "Oral Care" when queries are about "Travel size" | Human label review; suggest alternative labels |

### 9.2 Error Budget

| Error Type | Maximum Acceptable Rate | Measurement |
|---|---|---|
| False positive clusters | ≤20% of all clusters | Human evaluation of cluster quality |
| Missed intents (recall) | ≤20% of ground-truth needs | Comparison with interview-based needs |
| Noise misclassification | ≤30% of tail-quartile queries | Noise ratio analysis |
| PII contamination | 0% | Automated scan + manual audit |
| Label drift | ≤15% membership change per 30 days | Successive pipeline comparison |

### 9.3 Error Recovery

| Error | Recovery Action |
|---|---|
| False positive cluster | Mark cluster, exclude from default view, trigger re-clustering |
| Missed intent | Add intent as "uncategorized" cluster, flag for expansion |
| Contamination | Redact PII, regenerate cluster, audit source data |
| Drift error | Re-cluster affected domain, compare with previous taxonomy |
| Label misleading | Queue for human re-labeling, suggest alternatives |

---

## 10. Kill Criteria

### 10.1 Hard Kill Criteria (Stop immediately)

| ID | Criterion | How Measured | Trigger |
|---|---|---|---|
| KC-01 | Google Ads API access denied or ToS prohibits use | Legal review | API access not granted |
| KC-02 | Mean cost per analysis > $5.00 target | Cost tracking over 10 domains | 10 consecutive over-budget |
| KC-03 | Human interpretability score < 2.5/5 | Human evaluation (3 raters, 100 clusters) | Mean score below threshold |
| KC-04 | Noise ratio > 50% with no path to improvement | Pipeline metrics | Baseline experiments show no progress |
| KC-05 | Unique intent recall < 50% vs. interview baseline | Validation experiment (1 domain) | Expert needs not recovered |

### 10.2 Soft Kill Criteria (Reassess scope)

| ID | Criterion | Assessment |
|---|---|---|
| KC-06 | Users prefer keyword tables over clusters | Ship MVS without ML; reassess if users request clusters |
| KC-07 | Competitor replicates ML approach within 6 months | Shift differentiation to data moat, UX, or integrations |
| KC-08 | Cost of human labeling exceeds engineering cost for automated labeling | Re-assess label strategy; lean toward weak supervision |
| KC-09 | Embedding model choice locked too early (MiniLM insufficient) | Benchmark alternatives (SBERT, SimCSE, LLM2Vec); budget for upgrade |
| KC-10 | Clustering parameters require per-domain tuning with no generalization | Fix parameters or accept domain-specific configs |

### 10.3 Review Cadence

| Milestone | Kill Criteria Check |
|---|---|
| After API feasibility (10 domains) | KC-01, KC-02 |
| After baseline experiment | KC-04 |
| After first human evaluation | KC-03, KC-05 |
| After MVP with 5 pilot users | KC-06, KC-07 |
| After 6 months production | KC-08, KC-09, KC-10 |

---

## 11. Robustness

### 11.1 Distribution Shift

| Shift Type | Risk | Detection | Mitigation |
|---|---|---|---|
| Seasonal | Christmas queries in December vs. July | Wasserstein distance on weekly embedding distributions | Periodic re-clustering; freshness feature |
| Domain drift | New products/categories emerge | Cluster count stability monitor | Add new queries incrementally, expand taxonomy |
| Query language shift | Slang, new terms enter vocabulary | OOV rate monitor | Domain-adaptive pre-training (Inverse-Cloze Task per BeiWang) |
| User behavior shift | COVID-like changes in search patterns | Embedding drift alert | Trigger full re-clustering |
| SEO adaptation | Content creators game the system | Cluster composition analysis per EECS | Pre-deployment audit; exposure-aware tuning |

### 11.2 Edge Cases

| Edge Case | Detection | Handling |
|---|---|---|
| Empty API response | Response length = 0 | Show "No keywords found" with domain suggestions |
| Single-query domain | < 50 unique queries | Explain clustering requires more data; show keyword table only |
| All noise cluster | > 90% noise ratio | Notify user; suggest broader domain or different parameters |
| Duplicate domains | Same domain analyzed twice | Update existing analysis, increment version |
| Restricted category | Google Ads API blocks category | Return informative error; suggest different domain |
| Multi-language mix | Queries in multiple languages | Detect language distribution; cluster per language or use multilingual encoder |

### 11.3 Safety Requirements

| Requirement | Implementation | Source |
|---|---|---|
| No PII storage | Pattern-based + NER detection + k-anonymity | FR-18, NFR-14 |
| No sensitive category inference | Blocked category list per Google policy | MR-05, MR-06 |
| No individual-level data | Google Ads API provides only aggregated data | TA-06 |
| Audit logging | Every cluster assignment versioned | TA-04 |
| Human override capability | All automated decisions can be overridden | TA-07 |
| Fairness monitoring | Report bias by language, geo, query length | TA-03 |

---

## 12. Model Candidate Space

### 12.1 Embedding Models

| Model | Dim | Params | Speed | Quality (STS) | Source | Best For |
|---|---|---|---|---|---|---|
| MiniLM-L6-v2 | 384 | 22M | Very fast | ~72% | specific-search-terms-results | Production baseline |
| SimCSE-BERT (unsup) | 768 | 110M | Fast | 74.5% | SimCSE paper | Unsupervised embedding |
| SimCSE-BERT (sup) | 768 | 110M | Fast | 81.6% | SimCSE paper | Best quality with NLI data |
| Sentence-BERT | 768 | 110M | Moderate | ~80% | Reimers 2019 | Semantic similarity |
| LLM2Vec (7B) | 4096 | 7B | Slow | ~85% | BeiWang survey | Best quality at high cost |
| USE (Universal Sentence Encoder) | 512 | Varies | Fast | ~77% | USE paper | Multi-language |
| fastText+average | 300 | Light | Very fast | ~70% | Pinterest Q2I; SimCSE baseline | Strong baseline, CPU inference |
| StarSpace | Varies | Light | Fast | ~72% | Facebook paper | Unified keyword+intent embedding |
| ColBERT (multi-vector) | Varies | 110M | Moderate | ~80% | ColBERT paper; multi-vector advantage | Multi-faceted intent capture |

### 12.2 Clustering Models

| Model | Type | Pros | Cons | Source |
|---|---|---|---|---|
| HDBSCAN | Density-based | No k needed, handles noise, variable density | Sensitive to min_cluster_size; can have high noise ratio | BERTopic; specific-search-terms-results |
| k-means | Flat | Simple, scalable, deterministic | k must be known; uniform cluster size assumed | Yahoo! CNN intent paper |
| Ward's hierarchical | Hierarchical | Natural hierarchy, fast for <500K | O(n³) worst case; memory intensive | Timoshenko & Hauser (primary method) |
| Agglomerative clustering | Hierarchical | Handles variable shapes | Doesn't scale to millions | sklearn standard |
| Community detection (Louvain/Leiden) | Graph-based | Natural for co-occurrence graphs | Requires graph construction | DeepWalk; SimClusters |
| BERTopic | Topic model | Built-in label generation, UMAP + HDBSCAN baked in | Less flexible for custom pipelines | HDBSCAN + c-TF-IDF |
| VAE-based clustering | Probabilistic | Soft assignments, uncertainty estimates | Harder to train, slower inference | VAE-CF (Liang 2018) |

### 12.3 Hybrid / Two-Stage Architectures

| Architecture | Stage 1 | Stage 2 | Evidence |
|---|---|---|---|
| Bi-encoder → Cross-encoder | Fast bi-encoder candidate selection | Cross-encoder refinement | BeiWang survey: standard IR pattern |
| Bi-encoder → Clustering | Embedding generation | HDBSCAN clustering | Current plan |
| Bi-encoder → GBDT ranker | Embedding candidates | LambdaMART ranking by relevance | Qin 2021: GBDT strong on tabular features |
| Bi-encoder → LLM labeler | Embedding + clustering | GPT-4/LLaMA cluster labeling | BeiWang: zero-shot taxonomy labeling ~80% agreement |
| Sparse (SPLADE) → Dense refinement | Sparse interpretable vectors | Dense similarity rescoring | SPLADE offers interpretable term weights |

### 12.4 Training Data Sources for Embedding

| Approach | Positive Pairs | Negative Pairs | Source |
|---|---|---|---|
| Session-based | Queries in same session | Random queries | search2vec; query2vec; Airbnb |
| Click-based | Query + clicked document | Query + skipped document | search2vec |
| Co-occurrence-based | Keywords appearing together | Random unigram^0.75 sampling | Item2Vec; GloVe |
| Contrastive dropout | Same query, different dropout mask | Different queries | SimCSE |
| NLI-based | Entailment pairs | Contradiction pairs | Supervised SimCSE |
| Side-information | Keywords with same category | Keywords with different category | Alibaba EGES; PinText multitask |

### 12.5 Recommendation (from Synthesis)

**Recommended architecture:**
1. **Embedding**: SimCSE-BERT (unsupervised) or domain-fine-tuned Sentence-BERT — balances quality and cost
2. **Dimensionality reduction**: UMAP (n_components=5, n_neighbors=15)
3. **Clustering**: HDBSCAN with min_cluster_size auto-tuned per domain
4. **Labeling**: c-TF-IDF for initial labels, LLM zero-shot for alternatives, human for final validation
5. **Taxonomy structuring**: Zero-shot assignment to the 4-level YQT skeleton (8→64→512→3,843), with per-domain L3/L4 profile generation

**Why not pure BERTopic:** Need custom embedding model (SimCSE may outperform MiniLM), and need control over hierarchy structure.

---

## 13. Ablation Plan

### 13.1 Component Ablation

| Component | Ablation | Expected Impact | Test |
|---|---|---|---|
| Embedding model | Replace MiniLM → SimCSE → LLM2Vec | NMI improvement 0.05-0.15 per step | Run 3 embeddings on 5 domains |
| Embedding source | Remove domain-specific training | NMI drop 0.05-0.10 | Compare domain-trained vs. general |
| Contrastive negatives | Remove hard negatives (BM25 lexical) | NMI drop 0.03-0.08 | Ablate negative types |
| Dimensionality reduction | Skip UMAP, cluster in full 384/768-d | Degradation with HDBSCAN (curse of dimensionality) | Compare with/without UMAP |
| Clustering algorithm | Replace HDBSCAN → k-means | Higher noise ratio for tail; different cluster shapes | Compare on 5 domains |
| Hierarchy construction | Replace Ward's → flat clustering | Loss of parent-child structure | User interpretability score |
| Labeling method | Replace c-TF-IDF → LLM zero-shot | Label quality improvement | Human evaluation |
| Soft clustering | Replace hard HDBSCAN → VAE (soft) | Better multi-label handling | Multi-intent query test |

### 13.2 Data Ablation

| Ablation | Manipulation | Expected Impact |
|---|---|---|
| Remove volume metadata | Text-only clustering | Drop in cluster coherence for ambiguous queries |
| Remove GEO data | Global clustering | Loss of regional intent variation |
| Remove tail queries (>90% quantile) | Only head queries | Better metrics but misses rare intents |
| Reduce domain size | 100 vs. 1000 vs. 10000 keywords | Cluster quality vs. corpus size curve |
| Remove PII filtering | Raw queries | Better cluster quality but compliance risk |

### 13.3 Ablation Protocol

1. Start with full pipeline (baseline configuration)
2. Disable/modify one component at a time
3. Measure change on all primary metrics
4. Report effect size and direction
5. If removing a component does not degrade metrics, it is candidate for removal

---

## 14. Monitoring and Drift

### 14.1 Production Metrics to Track

| Metric | Alert Threshold | Action | Granularity |
|---|---|---|---|
| Embedding distribution (Wasserstein) | >0.1 vs. reference | Investigate data or model shift | Weekly |
| Cluster count change | >20% from previous run | Review taxonomy; may need reclustering | Per analysis |
| Noise ratio | >40% | Adjust clustering parameters; check data quality | Per analysis |
| API quota remaining | <20% of daily limit | Scale back analyses; distribute across sub-accounts | Hourly |
| Pipeline runtime | >2x expected | Check for failures; review compute scaling | Per pipeline |
| Cost per analysis | >$5.00 | Review API usage; optimize batch sizes | Per domain |
| Human label agreement | <70% | Re-train annotators; review difficult cases | Per evaluation |
| PII detection hit rate | >1% of queries | Review PII patterns; update detection rules | Per pipeline |

### 14.2 Drift Detection

| Drift Type | Detection Method | Response |
|---|---|---|
| Embedding drift | Wasserstein distance between weekly/monthly distributions | Recompute embeddings; check for upstream data changes |
| Cluster drift | Cluster purity M/M comparison; cluster count change | Flag for human review; re-cluster if significant |
| Label drift | Label assignment change for same queries over time | Maintenance release; update taxonomy |
| Data drift | Query length distribution, volume distribution, OOV rate | Data quality report; update preprocessing |

### 14.3 Version Control

| Artifact | Versioned | Retention |
|---|---|---|
| Embedding model weights | Yes | Current + 2 previous |
| Clustering parameters | Yes (per domain) | All |
| Cluster assignments | Yes | Current + 1 previous |
| Human labels | Yes (with audit log) | Permanent |
| Experiment configurations | Yes (pipeline logs) | Permanent |

---

## 15. Human Oversight

### 15.1 Required Human Decisions

| Decision | Why Human Required | When | Automation Gate |
|---|---|---|---|
| Accept/reject cluster labels | LLM labels may be misleading | After initial clustering | Label confidence < threshold |
| Merge/split clusters | Algorithms can over/under-split | During taxonomy review | Cluster similarity > threshold |
| Define domain boundaries | Domain scope is subjective | At analysis creation | N/A (user provides input) |
| Validate novel intents | New intents may be noise or insight | During review | Cluster size < min threshold |
| Cost overrun approval | Budget requires judgment | When cost exceeds $5/analysis | Cost > $5 triggers approval |

### 15.2 Human-in-the-Loop Workflow

1. System generates clusters + labels (fully automated)
2. System flags low-confidence clusters for review (< threshold)
3. Human reviewer: accept, edit label, merge, split, or reject
4. System records decision in audit log
5. Validated clusters published to end users

### 15.3 Escalation Path

| Level | Who | When |
|---|---|---|
| Automated | System | Cluster confidence > threshold |
| Reviewer | Domain expert | Cluster flagged, confidence below threshold |
| Senior review | Product manager / founder | Reviewer disagrees with system; cross-cluster decisions |
| Externally referred | Domain expert panel | New primary intents discovered; taxonomy restructuring |

---

## 16. Software Wrapper Requirements

### 16.1 System Architecture

```
User Input (domain URL / category)
    │
    ▼
[API Ingestion Service] ← Google Ads API
    │
    ▼
[Data Processing Pipeline]
    ├── PII Scrubber (Presidio + regex)
    ├── Sparse feature extractor (TF-IDF char n-grams)
    └── Dense embedding generator (SimCSE / SBERT)
    │
    ▼
[Clustering Pipeline]
    ├── UMAP dimensionality reduction
    ├── HDBSCAN (first-pass clustering)
    ├── Ward's hierarchical (taxonomy structuring)
    └── c-TF-IDF + LLM (label generation)
    │
    ▼
[Storage Layer]
    ├── Relational DB (keyword corpus, users)
    └── Vector DB (pgvector / Pinecone)
    │
    ▼
[Web Application]
    ├── Keyword table (MVS)
    ├── Intent cluster map (ML feature)
    └── Human review dashboard
    │
    ▼
[Monitoring]
    ├── Prometheus metrics
    ├── Drift detection
    └── Cost tracking
```

### 16.2 Component Specifications

| Component | Technology | Justification | Alternative |
|---|---|---|---|
| API ingestion | Python + google-ads library | Native SDK | Custom HTTP |
| Message queue | Kafka / GCP PubSub | Decouple ingestion from processing | RabbitMQ |
| Embedding inference | ONNX Runtime / HuggingFace | Standard for transformer serving | Triton inference server |
| Vector store | pgvector + HNSW index | Sub-10ms for 50M+ vectors; simpler than dedicated vector DB | Pinecone, Qdrant, Weaviate |
| Relational store | PostgreSQL | Industry standard; pgvector integration | CockroachDB |
| Compute | GPU (T4/A100) | Required for transformer inference at scale | CPU for fastText baseline only |
| Frontend | React / Next.js | Standard for data-rich web apps | Vue, Svelte |
| Monitoring | Prometheus + Grafana | Industry standard observability stack | Datadog, CloudWatch |
| Containerization | Docker + Kubernetes | Scalability and reproducibility | Docker Compose (small scale) |

### 16.3 Development Phases

| Phase | Components | ML Included? | Validation |
|---|---|---|---|
| MVS (Phase 0) | API ingestion, keyword table, PII filter, export | No | Keyword coverage, volume accuracy, cost baseline |
| Phase 1 | All MVS + embedding + clustering pipeline | Yes | NMI, noise ratio, human evaluation |
| Phase 2 | All Phase 1 + hierarchy + LLM labeling + review UX | Yes | Taxonomy quality, user engagement |
| Phase 3 | Drift monitoring, incremental updates, multi-language | Yes | Production stability, time-to-detection |

### 16.4 Deployment Requirements

| Requirement | Specification | Priority |
|---|---|---|
| Uptime | 99.5% business hours | Should |
| RTO/RPO | 4h / 24h | Should |
| Concurrency | 10 simultaneous users | Should |
| Weekly ingestion | 5M keyword records | Could |
| Cost per analysis | ≤$5.00 | Must |
| Time-to-analysis | ≤30 min for 200K keywords | Should |
| Table load time | ≤3s for 500K rows (paginated) | Must |

### 16.5 Open Implementation Questions

| Question | Options | Recommended | Rationale |
|---|---|---|---|
| Embedding model | MiniLM / SimCSE / SBERT / LLM2Vec | SimCSE-BERT (unsup) | Best unsupervised quality-to-cost ratio |
| Clustering algorithm | HDBSCAN / k-means / Ward's | HDBSCAN + Ward's post-hoc | Density-based primary, hierarchical for taxonomy |
| Vector database | pgvector / Pinecone / Qdrant | pgvector | Simpler ops, familiar stack, sufficient scale |
| Cloud provider | GCP / AWS / Azure | GCP (if Google Ads API is the source) | Closer to data source; natural affinity |
| GPU type | T4 / A100 / RTX 4090 | T4 for development, A100 for production | T4 sufficient for batch inference; A100 for scale |
| Labeling approach | Human-only / Weak supervision / LLM | Weak supervision + LLM + human validation | Three-tier: cheap → moderate → high quality |
| Pipeline trigger | On-demand / Scheduled / Hybrid | Hybrid (on-demand for user request, scheduled for refresh) | Balance freshness with cost |
| Multi-language | Phased / Native support from start | Phased (English first) | MVP scope constraint |

---

## Appendix A: Evidence Traceability

### Key Claims and Their Sources

| Claim | Source | Section |
|---|---|---|
| Intent is learnable from query text | Timoshenko CNN (F1=74%), Hashemi CNN (90.3% accuracy) | 1.3 |
| Human agreement ceiling is ~70% | Timoshenko inter-coder accuracy 70% | 2.1, 4.1 |
| 3-level domain hierarchy (6→22→86) + 4-level universal taxonomy (8→64→512→3,843) | Timoshenko + Intent Topology memo | 2.2 |
| 71.64% of sessions are single-query | Jansen 964,780 session analysis | 3.2 |
| Query length mean 2.79 terms | Jansen | 3.2 |
| Frequency ≠ importance (ρ=0.21) | Timoshenko | 1.4 |
| URL features > temporal features for intent segmentation | Intent-Based Browse Activity Segmentation | 3.3 |
| Simple models + good data ≈ complex models | Pinterest Q2I: fastText ≈ BERT with augmentation | 5.3, 12.1 |
| LambdaMART beats most neural rankers | Qin et al. ICLR 2021 | 5.3, 12.3 |
| Two-stage (bi-encoder → cross-encoder) is standard IR pattern | BeiWang survey 2026 | 12.3 |
| Feedback loops bias future query distributions | Krauth EECS-2022-178 | 3.4, 11.1 |
| Random negatives outperform impression-based | Facebook Search embedding paper | 6.4 |
| Hard negatives (lexical) improve separation | BeiWang survey | 6.4 |
| Causal embeddings (directed) better predict intent | search2vec: directed ad-query2vec | 6.4 |
| Offline metrics predict online but with diminishing returns | EECS simulation experiments | 7.3 |
| Algorithm rankings stable across sampling distributions | EECS | 7.4 |
| 8,000 labels cover ~86% of needs; 12,000 cover 97% | Timoshenko | 4.3 |
| ML reduces manual effort by 15-22% | Timoshenko efficiency experiment | 4.3 |
| Embedding dimension choice affects bias amplification | EECS: d=50 vs d=10 on MovieLens | 11.1 |

### Documents Processed

| Source Group | Count | Agent |
|---|---|---|
| web-sources core papers (Timoshenko, Jansen, IR Survey, EECS, IJCA, PNAS) | 6 | Agent 1 |
| web-sources remaining (IR textbook, KG, QUIDS, BloomIntent, LIMIT, Li-Ma, Suh, Revealed Attention, behavioral economics, etc.) | ~17 | Agent 4 |
| Ranking/ papers | 10 | Agent 3 |
| Search/ papers (Query Intent CNN) | 1 | Agent 3 |
| Other/ papers (Intent Segmentation, Q2I, SimCSE, DeepCluster, SCAN, fastText, Rules of ML, Booking ML, etc.) | ~15 | Agent 2 |
| Embeddings/ papers (Facebook Search, Airbnb, PinText, PTE, StarSpace, Item2Vec, DeepWalk, node2vec, LINE, GloVe, etc.) | 15 | Agent 3 |
| Keywords Extraction/ papers | 3 | Agent 2 |
| Lookalike/ papers | 3 | Agent 2 |
| MF/ papers (BPR, VAE, NCF, YouTube Recs, SimClusters, Monolith, Debiasing) | 13 | Agent 3 |
| Deepl-search markdown files | 3 | Direct |
| **Total** | **~85** | |

---

## Appendix B: Open Questions (Unresolved)

| OQ | Question | Category | Must Answer Before | Evidence Needed |
|---|---|---|---|---|
| OQ-01 | What is the actual Google Ads API daily quota per customer ID? | Data | Phase 0 | API access experiment |
| OQ-02 | Does Google Ads API ToS permit aggregation and resale? | Legal | Public launch | Legal review |
| OQ-03 | What is the actual cost per domain analysis at scale? | Cost | Pricing decision | 10-domain cost pilot |
| OQ-04 | What is the minimum keyword count for meaningful clustering? | ML | Phase 1 | Systematic corpus size experiment |
| OQ-05 | What NMI threshold constitutes "good enough" intent clustering? | Evaluation | Phase 1 human eval | Human evaluation study |
| OQ-06 | Is SimCSE-BERT worth 5x cost over MiniLM for this task? | ML | Phase 1 | Ablation experiment (Section 13) |
| OQ-07 | How stable are intent clusters over 6 months? | Monitoring | Phase 3 | Temporal stability study |
| OQ-08 | Do users actually pay for intent-level insights? | Product | Pre-launch | User interviews / pilot |
| OQ-09 | What taxonomic level (primary/secondary/tertiary) provides most value? | ML | Phase 2 | A/B test of taxonomy granularity |
| OQ-10 | Can weak supervision replace human labels for bootstrapping? | Label | Phase 1 | Compare weak-sup vs. human-only labels |
| OQ-11 | What embedding dimension balances quality vs. bias amplification? | ML | Phase 1 | Dimension ablation + fairness audit |

---

> **End of Requirements Package — Version 2.0 (AI-Native Restructuring)**
>
> This document replaces version 1.0 with a restructured, evidence-grounded format integrating concepts from ~85 documents across IR, NLP, RecSys, customer-needs mining, and representation learning. All TBD values and open questions mark points requiring empirical measurement. The structure supports traceability from research evidence through behavioral test to production requirement.
