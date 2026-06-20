# Deepl Search — Validation Experiment Plan

> **Objective:** Answer "should we build this ML model?" before writing production code
> **Status:** Zero-budget protocol
> **Date:** 2026-06-08
> **Budget:** $0 (free tiers, CPU-only, public data, LLM-as-judge)
> **Timeline:** 1–2 weeks

---

## 1. Overview

### 1.1 The Problem

No budget for Google Ads API, human annotators, or GPU compute. The validation strategy must adapt: we use what we already have.

### 1.2 What We Already Have

| Asset | Source | How It Replaces Budget |
|---|---|---|
| 3,391 extracted concepts from ~85 papers | Multi-agent extraction | Ground-truth ontology for evaluation |
| Verified intent taxonomy structure (8→64→512→3,843) | Intent Topology memo: Yahoo! YQT + Google patent | Pre-built taxonomy skeleton, validated by structural convergence |
| Public search datasets (MS MARCO, TREC, ORCAS) | search-datasets.md | Free query corpora |
| CPU-only ML (fastText, TF-IDF, sklearn) | Open-source libraries | No GPU needed |
| LLM-as-judge (GPT-4 or local model) | Free tier or API | Replaces human annotators |
| Analytic entropy predictions for K=500..10,000 | Intent Topology memo §4 | Expected silhouette/median-size per K, used as priors |

### 1.3 Three Zero-Budget Experiments

| # | Experiment | Replaces Budget Item With | Duration | Topology Link |
|---|---|---|---|---|
| E1 | Literature Grounding | Paid data → extracted concept ontology | 2 days | Structured using YQT skeleton (8→64→512→3,843) |
| E2 | Baseline Benchmarks | GPU compute → CPU-only methods on public data | 1 week | Tests 7 K values around predicted optimum (500–8,000) |
| E3 | LLM Validation | Human annotators → GPT-4 judge with calibration | 3 days | Calibrated to Timoshenko 70% ceiling; validates taxonomy structure |

---

## 2. Experiment 1: Literature Grounding

### 2.1 Objective

Extract keyword→intent ground-truth pairs from the extraction corpus to use as an evaluation dataset.

### 2.2 Method

Mine the 325 extraction JSONs for explicit keyword-intent mappings:

| Source | What It Contains | Use |
|---|---|---|
| Timoshenko oral care | 86 tertiary needs + example phrases per need | Primary evaluation ontology |
| Yahoo! query intent | 14 high-level + 125 low-level intent classes | Hierarchy structure validation |
| Jansen reformulation | 6 reformulation states + example queries | Session-level intent validation |
| Pinterest Q2I interests | Query→interest category mappings | Short-text classification baseline |
| Intent Browse Segmentation | URL+time→intent boundaries | Behavioral signal validation |

### 2.3 Output

A file `experiments/evaluation_ontology.json` containing:

```json
{
  "domains": [
    {
      "domain": "oral_care",
      "source": "Timoshenko 2018",
      "hierarchy": {
        "primary": 6,
        "secondary": 22,
        "tertiary": 86
      },
      "keyword_intent_pairs": [
        {"keyword": "teeth whitening toothpaste", "intent": "whitening", "primary": "product_efficacy"},
        {"keyword": "sensitive teeth gum pain", "intent": "sensitivity_relief", "primary": "product_efficacy"}
      ]
    }
  ]
}
```

Target: at least 500 keyword→intent pairs across 3+ domains.

---

## 3. Experiment 2: Baseline Benchmarks

### 3.1 Objective

Run CPU-only baselines on public query data, evaluated against the literature-derived ontology.

### 3.2 Data Sources

| Dataset | Size | How to Get | Use |
|---|---|---|---|
| MS MARCO queries | 1M queries | HuggingFace datasets | Large-scale test |
| ORCAS click logs | 10M query-doc pairs | ir_datasets library | Click-signal test |
| TREC Web Track | ~400 queries with intent judgments | TREC website | Intent-specific test |
| AOL query log (sample) | ~10K sessions | ir_datasets | Session-intent test |

All available via `pip install ir_datasets` — zero cost.

### 3.3 CPU-Only Baselines

| Baseline | Implementation | Expected Runtime (100K queries) |
|---|---|---|
| TF-IDF + k-means | sklearn TfidfVectorizer + KMeans | ~30 seconds |
| fastText + k-means | gensim fastText + sklearn KMeans | ~2 minutes |
| SimCSE CPU | sentence-transformers on CPU | ~30 minutes (slow but free) |
| BM25 similarity | rank_bm25 library | ~1 minute |

### 3.4 Evaluation Protocol

1. Sample 10,000 queries from MS MARCO
2. Map each query to an intent label from the ontology (via keyword matching + LLM disambiguation)
3. Run each baseline, produce cluster assignments
4. Compute: NMI, ARI, adjusted cluster purity, noise ratio
5. **Critical: Test multiple K values informed by the topology findings:**
   - K = **500** (coarse; predicted silhouette ~0.72, excellent)
   - K = **1,000** (medium; predicted silhouette ~0.68, very good)
   - K = **2,000** (predicted silhouette ~0.63, good)
   - K = **3,184** (Google intent taxonomy size; predicted silhouette ~0.60)
   - K = **3,843** (Yahoo! YQT size; predicted silhouette ~0.58)
   - K = **5,000** (above convergence range; predicted silhouette ~0.52, marginal)
   - K = **8,000** (predicted silhouette ~0.44, poor)
6. Compare empirical silhouette against the analytic predictions from the Intent Topology memo
7. Stratify results by:
   - Query length (1-2 words vs 3-4 vs 5+)
   - Frequency quartile (simulated by inverse sampling)
   - Domain (for MS MARCO queries that match ontology domains)

### 3.5 Expected Outcome

| K | Predicted Silhouette | Predicted Median/Class | Predicted % Sparse | Verdict if Confirmed |
|---|---|---|---|---|
| 500 | 0.72 | 1,200 | 0.0% | Classification viable but too coarse |
| 1,000 | 0.68 | 450 | 0.2% | Viable; good starting point |
| 2,000 | 0.63 | 145 | 1.1% | Viable; approaching optimum |
| 3,184 | 0.60 | 52 | 3.4% | **Optimum (Google threshold)** |
| 3,843 | 0.58 | 40 | 4.8% | **Optimum (Yahoo! threshold)** |
| 5,000 | 0.52 | 19 | 12.3% | Marginal; sparse classes emerging |
| 8,000 | 0.44 | 5.2 | 38.7% | Too fine-grained; classification degradation |

If K=3,184 or K=3,843 yields the highest empirical silhouette AND keeps sparse clusters below 10%, the Octohedral Hypothesis is confirmed. If K=500 or K=1,000 wins, the taxonomy is too fine-grained for the current query distribution. If K=8,000 wins, the taxonomy is too coarse — but this is unlikely given the structural convergence evidence.

---

## 4. Experiment 3: LLM Validation

### 4.1 Objective

Use an LLM as a proxy for human annotators to rate cluster quality, calibrated against the known human agreement ceiling (70%).

### 4.2 Protocol

1. Take the best clusters from Experiment 2 (one method, one domain, ~20 clusters)
2. For each cluster, prompt GPT-4 with:
   - The cluster's member keywords + c-TF-IDF label
   - The 5-point interpretability rubric from the original plan
3. Ask for both a score AND a justification
4. Run 3 independent evaluations per cluster (different random seeds, different prompt phrasings)
5. Compute LLM "self-agreement" — how often does the same model give the same score for the same cluster?
6. Calibrate: adjust thresholds so that LLM agreement matches the known 70% human ceiling

### 4.3 Calibration Prompt

```
You are evaluating an intent cluster generated by an unsupervised ML system.
The system grouped these search keywords together because it believes they
share a common user intent.

Cluster label: "{label}"
Keywords: {keyword_list}

Rate this cluster on interpretability (1-5):
1 = Incoherent — keywords appear randomly grouped
2 = Weak — vague commonality but includes unrelated keywords
3 = Acceptable — most keywords share a theme, a few outliers
4 = Coherent — keywords clearly share a specific user goal
5 = Crystal clear — all keywords express the same intent

First explain your reasoning in 1-2 sentences, then output your score as
a single number on the last line.
```

### 4.4 Success Criteria

| Criterion | Target |
|---|---|
| LLM self-agreement (same cluster, 3 runs) | ≥70% (matches human ceiling) |
| Mean interpretability score | ≥3.0/5 (adjusted for LLM bias) |
| Distribution of scores | Spans full 1-5 range (no collapse to middle) |

### 4.5 Validation Against Known Ceiling

The Timoshenko study found human inter-coder agreement of 70%. If the LLM achieves ≥70% self-agreement (same cluster, repeated prompt), it is operating at the same reliability level as a human annotator. Below 60%, LLM judgments are too noisy to use.

---

## 5. Consolidated Timeline

| Day | Experiment | Activities |
|---|---|---|
| 1 | E1 | Mine extraction JSONs for keyword→intent pairs; build evaluation ontology |
| 2 | E1+E2 | Finalize ontology; install dependencies; download public datasets |
| 3 | E2 | Run TF-IDF + k-means on all datasets |
| 4 | E2 | Run fastText + k-means; begin SimCSE CPU run |
| 5 | E2+E3 | Complete all baselines; compile metrics; select best clusters |
| 6 | E3 | Run LLM validation (GPT-4 or local model); compute self-agreement |
| 7 | E3 | Calibrate LLM against known ceiling; synthesize all results; go/no-go |

---

## 6. Success Criteria & Go/No-Go

| Layer | Criterion | Gate |
|---|---|---|
| E1 | ≥500 keyword→intent pairs across ≥3 domains | Prerequisite for E2 |
| E2 | Best baseline NMI ≥0.3 against ontology | HARD — phenomenon learnable |
| E2 | At least one ML method surfaces ≥20% intents not obvious from keyword table alone | HARD — ML adds value |
| E3 | LLM self-agreement ≥70% AND mean interpretability ≥3.0/5 | HARD — clusters are coherent |

If E2 fails (NMI < 0.3): the phenomenon (search intent) cannot be reliably recovered from query text alone with the methods tested. Pivot: explore richer features (session context, SERP data) or different task formulation.

---

## 7. What Zero Budget Means

| Eliminated | Replaced With |
|---|---|
| Google Ads API ($500-1,000) | Public datasets (MS MARCO, TREC, ORCAS) |
| GPU compute ($500-1,500) | CPU-only methods (fastText, TF-IDF) |
| Human annotators ($900-3,000) | LLM-as-judge with calibration |
| Domain experts ($500-1,000) | Literature-derived ontology from extractions |
| Annotation platform ($0-500) | CLI scripts + JSON files |

**What we lose:** ecological validity (public queries ≠ API queries), real cost data, and human validity signals. The conclusions will be indicative, not definitive.

**What we keep:** the ability to answer the core question — "is there a principled, simple, useful reason to build this ML model?" — before writing production code.

---

## 8. Pre-Requisites

| Dependency | Status | Action |
|---|---|---|
| Python + sklearn + sentence-transformers | Available | `pip install ir_datasets gensim fasttext rank_bm25` |
| Public dataset access | Available | `python -m ir_datasets` downloads on demand |
| LLM API key (GPT-4 or open-source) | GPT-4 free tier (OpenAI) or local via ollama (Llama 3 8B) | Free tier covers calibration runs; local model for production |
| Extraction ontology | **Ready** | 3,391 concepts exist; needs mining into keyword→intent pairs |

---

> **End of Validation Experiment Plan — Version 2.0 (Zero-Budget)**
>
> Replaces v1.0's $5k–$12k budget with a $0, 1-week protocol using literature-derived ground truth, CPU-only computation, and LLM-as-judge. The tradeoff is ecological validity for cost. If results are positive, budget for a production-quality run can be justified.
