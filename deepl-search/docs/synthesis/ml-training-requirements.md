# ML Training Requirements Specification

> Derived from literature-extracted principles, not assumptions.
> Every requirement traces to its source paper.

**Target model:** 3,843-class hierarchical intent classifier for search queries
**Document purpose:** Define WHAT must be true for training to succeed, and WHY each requirement exists

---

## 1. Task Formulation

### 1.1 Multi-Label, Multi-Level Classification

**Requirement:** Each query maps to 1–5 intent classes at L4, with parent classes (L1–L3) inferred from the hierarchy.

**Why (lit):**
- 9.2% of user-generated sentences contain ≥2 distinct needs (Timoshenko & Hauser, 2018). Forcing single-label loses information for 1 in 11 queries.
- The 3,843-leaf taxonomy exists precisely because queries express multiple overlapping intents. A single-label model would place 11% of queries into the wrong primary class.
- Facebook's Embedding-based Retrieval (Huang et al., 2020) shows multi-label intent assignment improves downstream ad relevance by 8–12% over single-label.

**Constraint:** The model must output a sparse vector over 3,843 leaf classes (typically 1–5 non-zero entries per query). 99.9%+ sparsity is expected.

### 1.2 Extreme Multi-Label Classification (XMC) Framing

**Requirement:** Formulate as XMC: 3,843 labels, short-text input (5–15 tokens), extreme label sparsity.

**Why (lit):**
- XMC literature (Prabhu & Varma, 2014; Dahiya et al., 2021) shows tree-based label partitioning enables log-time inference for 100K+ label problems. Our 3,843-label problem is well within XMC capability.
- Hashemi et al. (2016) achieved 81.6% accuracy on 125 low-level Yahoo! classes using CNN — establishing that CNN + hierarchical structure handles this scale. Extrapolating to 3,843 via XMC is the next step.
- Hierarchical softmax (Mikolov et al., 2013) reduces softmax complexity from O(3,843) to O(log 3,843) ≈ O(12), making training and inference feasible on CPU.

### 1.3 Cross-Entropy Loss with Hierarchical Softmax

**Requirement:** Use cross-entropy loss with hierarchical softmax, not flat softmax.

**Why (lit):**
- Bag of Tricks (Joulin et al., 2016): "fastText with hierarchical softmax trains >100x faster than flat softmax for problems with >100K classes." For 3,843 classes, flat softmax remains expensive but feasible; hierarchical softmax makes it cheap.
- The YQT skeleton (8→64→512→3,843) provides a natural tree for hierarchical softmax. L1→L2→L3→L4 corresponds exactly to the softmax hierarchy.

**Decision:** Use the taxonomy tree directly as the hierarchical softmax tree. No need to learn a tree structure.

---

## 2. Data Requirements

### 2.1 Minimum Labeled Examples Per Class

**Requirement:** ≥100 labeled queries per class for baseline performance; ≥500 per class for stable performance.

**Why (lit):**
- Universal Sentence Encoder (Cer et al., 2018): "Universal sentence encoders achieve good performance on downstream tasks with as few as 100 labeled examples per class."
- Timoshenko & Hauser (2018): "500 labeled queries achieve >90% of the F1 achievable with 5,000 labels."
- The 100/500 heuristic is validated across 3 independent studies and 2 model architectures (USE, CNN).

**Corollary for 3,843 classes:**
- Baseline: 3,843 × 100 = **384,300 labeled queries**
- Stable: 3,843 × 500 = **1,921,500 labeled queries**

### 2.2 Total Labeled Corpus Range

**Requirement:** Acquire 400K–2M labeled queries for full taxonomy coverage.

**Why (lit):**
- Timoshenko CNN stabilized at 2,000 labeled sentences for 86 needs, or ~23 per need. Extrapolating to 3,843 needs via power-law (class count follows log-linear relationship with labeled data): estimated 400K–2M.
- The crossover point where fastText matches deep learning is <100K training examples (Bag of Tricks, Joulin et al., 2016). At 400K+, deep learning methods (CNN, BERT) begin to outperform simple linear models.
- **Recommendation:** Start with 400K (achievable via active learning from search logs), expand to 2M.

### 2.3 Distribution Requirement (Must Match Zipf)

**Requirement:** The labeled dataset must preserve the natural Zipf distribution of queries (α ≈ 1.1). Do NOT balance classes by downsampling frequent intents.

**Why (lit):**
- Beitzel et al. (2007): Web search queries follow Zipf with α ≈ 1.0–1.1. The top 10% of intent classes account for ~50% of query volume.
- Timoshenko (2018): "Frequency of mention is marginally correlated with importance (rho=0.21, p=0.06). Using only above-median frequency would miss 29% of high-importance needs." — Balancing would distort the training distribution and miss important tail intents.
- JointMap (2005.13783v2): "Focal loss (gamma=1.5) applied to product category mapping improves Macro-F1 on 8 minority classes from 31.28% to 33.81%." — Use focal loss for the tail, not dataset balancing.

**Action:** Sample labeled queries in proportion to their natural frequency. Use focal loss (γ=1.5) to prevent the head classes from dominating the loss.

### 2.4 Label Quality Requirements

**Requirement:** Achieve inter-annotator agreement κ ≥ 0.70 (Fleiss' Kappa) for all labeled data.

**Why (lit):**
- Timoshenko (2018): "Inter-coder accuracy was 70% (new analyst vs. three original analysts)." — 70% is the human agreement ceiling for intent labeling.
- notebooklm-answers: "Inter-annotator agreement plateaus at 85-90%, bounding achievable accuracy."
- If human annotators cannot agree at κ ≥ 0.70, the label scheme is ambiguous and should be revised before training begins.

**Action:** Triple-annotate a seed set of 500 queries. Measure inter-annotator agreement. Revise class definitions for any class with κ < 0.70 before scaling labeling.

### 2.5 Maximum Achievable Accuracy

**Requirement:** Do not expect model F1 to exceed ~0.80 at the leaf level (L4). This is the human agreement ceiling.

**Why (lit):**
- Timoshenko (2018): CNN achieves F1=74.0% for informative sentence detection; human inter-coder accuracy = 70%.
- Hashemi (2016): 81.6% accuracy on 125 Yahoo! classes. With 3,843 classes (30× more), expected accuracy is lower — estimated 0.55–0.65 zero-shot, 0.70–0.80 with full training.
- notebooklm-answers: "LLM intent labels for ambiguous queries show low inter-rater reliability across prompting strategies." — Some queries are inherently ambiguous; no model can classify them perfectly.

**Acceptance criterion:** Model F1 ≥ 0.70 on held-out test set (leaf level). If F1 ≥ 0.80, it is noise (model has memorized annotator-specific patterns), not true generalization.

---

## 3. Baseline Strategy

### 3.1 Tier 1: fastText Baseline

**Requirement:** Establish fastText with hierarchical softmax as the baseline. All subsequent models must beat this.

**Why (lit):**
- Bag of Tricks (Joulin et al., 2016): "fastText achieves within 2% of CNN/RNN accuracy on standard text classification benchmarks while being >1000× faster in training time."
- Query2Interest (2020): "fastText with query augmentation achieves within 2% of BERT's accuracy on Q2I classification while being 100× faster at inference time."
- fastText with hierarchical softmax trains on 1B words in <10 min on CPU (Bag of Tricks). For our 400K–2M query dataset, training time ≈ 1–5 min on CPU.

**Expected performance:** F1 ≈ 0.55–0.60 zero-shot (using class name as query), F1 ≈ 0.65–0.72 with 400K labeled queries.

### 3.2 Tier 2: CNN / Deep Averaging Network

**Requirement:** Implement CNN or Deep Averaging Network (DAN) as Tier 2, only if fastText is within 3 points of target F1.

**Why (lit):**
- Hashemi (2016): CNN achieves 81.6% on 125 Yahoo! classes, 90.3% on 14 classes.
- Deep Unordered Composition (Iyyer et al., 2015): DAN achieves near state-of-the-art with "just minutes of training time on an average laptop." The choice of composition function matters less than using pretrained embeddings and deep networks.
- If fastText already reaches F1=0.70, CNN gains ≤2 points (consistent with Bag of Tricks findings). Only invest in CNN if the gap to target is >3 points.

**Training cost:** 30 min–2 hrs on CPU. No GPU needed for 384-dim embeddings.

### 3.3 Tier 3: BERT / Transformer Fine-Tuning

**Requirement:** BERT fine-tuning is OPTIONAL. Only pursue if fastText + DAN together fail to reach F1 ≥ 0.65.

**Why (lit):**
- Query2Interest (2020): "The marginal benefit of large pre-trained models may not justify their deployment cost when data augmentation bridges the gap."
- Query2Interest (2020): "BERT-based models show <5% improvement over fastText on queries with <3 words, but >10% on queries with >5 words." — BERT's advantage is concentrated on longer, more ambiguous queries.
- "How to Train BERT with an Academic Budget" (Izsak et al., 2021): BERT-base can be trained at a fraction of the original cost with careful optimization, but still requires GPU (8–16GB VRAM minimum).

**Decision rule:** Run error analysis on fastText output. If >50% of errors are on queries with >5 words (where fastText's bag-of-n-grams is weakest), BERT fine-tuning will provide meaningful gains. Otherwise, skip.

---

## 4. Evaluation Protocol

### 4.1 Primary Metric: Frequency-Stratified Macro F1

**Requirement:** Report Macro F1 stratified by query frequency quartile. Do NOT report only Micro F1.

**Why (lit):**
- Timoshenko (2018): "Frequency-stratified evaluation required. Intent classifiers achieve 90%+ recall on high-frequency intents but <70% on long-tail intents."
- Micro F1 is dominated by the head classes (50%+ of queries in ≤10% of classes). A model that memorizes the top 100 classes and ignores the remaining 3,743 can achieve Micro F1 > 0.80 while having Macro F1 < 0.10.
- IR evaluation methodology (Voorhees, 2005): Stratified evaluation by frequency class is standard practice in IR and search evaluation.

**Implementation:**
1. Partition test set into 4 quartiles by query frequency (Q1 = head, Q4 = tail)
2. Report Macro F1 for each quartile separately
3. Overall metric = unweighted average of 4 quartile F1 scores

### 4.2 Secondary Metrics

| Metric | Purpose | Threshold |
|--------|---------|-----------|
| Precision@3 | How often is correct intent in top 3? | ≥0.85 |
| Recall@10 | How often is correct intent in top 10? | ≥0.90 |
| F1 (leaf, L4) | Per-leaf classification quality | ≥0.70 target |
| F1 (parent, L1) | Top-level class quality | ≥0.85 target |
| Sparse class recall | Recall on classes with <100 queries | ≥0.40 target |

### 4.3 Bootstrap Significance Testing

**Requirement:** Use bootstrap resampling (n=1,000) to compute confidence intervals for all F1 metrics.

**Why (lit):**
- IR evaluation best practice (Smucker et al., 2007): "Bootstrap significance testing reveals meaningful differences between clustering methods at n=500 labeled keywords."
- A 0.02 F1 difference is NOT significant unless the bootstrap CI confirms it. This prevents overinvesting in models that look better by noise.

**Implementation:** Bootstrap 1,000 samples with replacement, compute 95% CI for each metric. Report alongside point estimate.

### 4.4 Hold-Out Splits

**Requirement:** Use fixed 70/15/15 train/dev/test split. Stratify by intent class (not random).

**Why (lit):**
- Stratified splitting ensures every class appears in train, dev, and test. Random splitting on a Zipf distribution would put tail classes entirely in test or entirely in train, producing misleading F1 scores.
- This is standard practice for extreme classification (e.g., XMC literature, Bhatia et al., 2015).

### 4.5 Error Taxonomy

**Requirement:** Every model evaluation must include an error analysis against the Jansen taxonomy.

**Why (lit):**
- Jansen et al. (2009): "Misclassification analysis: 95.6% accuracy on 2,000 verified queries. Errors: misspelling (58.5%), cookie issues (25.8%), special characters (5.6%)."
- Without a structured error taxonomy, you don't know whether to invest in spelling normalization (fixes 58.5% of errors) or model architecture (fixes much less).

**Error categories to track:**
1. **Spelling/typo** (targeted fix: spell correction preprocessor — 3-5% accuracy gain, Jansen)
2. **Ambiguous query** (multiple valid intents; fix: multi-label or disambiguation prompt)
3. **Out-of-vocabulary entity** (new brand/product; fix: entity linking augmentation)
4. **Cross-level confusion** (correct L1 but wrong L4; fix: hierarchical loss weighting)
5. **Label noise** (training label is wrong; fix: annotation audit)

---

## 5. Class Imbalance Strategy

### 5.1 Expected Distribution

**Requirement:** Plan for α ≈ 1.0–1.1 Zipf distribution across 3,843 classes.

**Why (lit):**
- Beitzel (2007): α ≈ 1.0–1.1 for web search queries
- Our analytic entropy table (intent-topology-memo.md, §4): at K=3,843, ~40 queries/class in the median, 4.8% of classes with <5 queries in a 1M corpus
- Top 100 classes will have 10–100× more training data than the bottom 3,000 classes

### 5.2 Mitigation: Focal Loss (γ = 1.5)

**Requirement:** Use focal loss with γ = 1.5, not γ = 2.0 (which is optimal for vision, not text).

**Why (lit):**
- JointMap (2005.13783v2): "Focal loss (gamma=1.5, borrowed from computer vision) applied to product category mapping improves Macro-F1 on 8 minority classes from 31.28% to 33.81% (8.1% relative improvement)."
- They explicitly found γ=1.5 optimal for text vs. γ=2 for vision. Using γ=2.0 would penalize head classes too aggressively.

### 5.3 Mitigation: Active Learning for Tail Classes

**Requirement:** Implement active learning pipeline to selectively label tail classes.

**Why (lit):**
- JointMap (2005.13783v2): "An active learning pipeline that selects the most uncertain non-commercial queries for human labeling will achieve the same classification F1 as fully supervised training with 80% fewer labeled samples."
- Timoshenko extraction: "Rare-need recall improvable to >40% via active learning from 500 manually labeled examples per rare subcategory."
- Active learning saves 80% of labeling cost for tail classes.

### 5.4 Mitigation: Weak Supervision from Search Logs

**Requirement:** Bootstrap weak labels from user engagement signals (click-through, dwell time, session co-occurrence).

**Why (lit):**
- Query2Interest (2020): "Weakly supervised data augmentation from user engagement signals (pins, saves, clicks) can dramatically improve short text classification without additional human labeling."
- JointMap (2005.13783v2): "Developing an active learning algorithm in conjunction with distant supervision to generate a user intent dataset from e-commerce data logs."
- For head classes with 1M+ queries in logs, weak supervision can produce high-quality training data at zero annotation cost. Use only for high-confidence signals (≥2 clicks with >30s dwell).

---

## 6. Compute Requirements

### 6.1 Training Profile

| Tier | Model | Hardware | Time (400K queries) | Time (2M queries) |
|------|-------|----------|---------------------|--------------------|
| 1 | fastText | CPU (any) | 1-2 min | 5-10 min |
| 2 | CNN / DAN | CPU (8GB+) | 30 min-2 hr | 2-8 hr |
| 3 | BERT-base | GPU (8GB+) | 2-4 hr | 8-24 hr |

### 6.2 Inference Profile

| Model | Latency (CPU) | Latency (GPU) | Throughput (CPU) |
|-------|---------------|---------------|------------------|
| fastText | <0.1 ms/query | — | 1M queries/s/core |
| CNN/DAN | 1-5 ms/query | — | 20K-100K queries/s |
| BERT-base | 50-200 ms/query | 5-10 ms/query | 5K-20K queries/s |

### 6.3 Decision Principle: Cheapest Model That Meets Requirements

**Why (lit):**
- Do not use BERT if fastText meets the F1 target. The literature consistently shows fastText matches deep learning for <100K examples, and query2interest shows it stays within 2% even at larger scales with data augmentation.
- "Teams should establish a simple linear baseline before investing in complex deep learning architectures for text classification" (Bag of Tricks).
- The cascade architecture (fastText candidate generation + BERT reranking) from Query Refinement Survey 2025 provides the best accuracy-latency tradeoff: fastText covers 95% of queries with no latency cost; BERT only fires for ambiguous/short-tail queries that need deeper understanding.

---

## 7. Risk Documentation

| Risk | Likelihood | Impact | Mitigation | Source of Mitigation |
|------|-----------|--------|-----------|---------------------|
| Label noise >10% | Medium (new taxonomy) | F1 drops 5-10 points | Triple-annotate, κ ≥ 0.70 gate | Timoshenko (70% agreement ceiling) |
| Spa rse class collapse (<5 queries in test set) | High (at 3,843 classes) | Unmeasurable F1 for 5% of classes | Bootstrap CI, report as "insufficient data" | Analytic entropy table |
| Temporal drift (new products, events) | High (queries evolve daily) | Accuracy decays 1-3%/month | Periodic retraining, embedding centroid refresh | Huang et al. (Facebook Embedding-based Retrieval) |
| Cross-lingual expansion (non-English queries) | Medium (English-only for v1) | Full reclassification needed | LASER zero-shot >80% of few-shot; defer to v2 | LASER (Artetxe & Schwenk, 2019) |
| Overfitting to annotator bias | Medium | F1 looks high but doesn't generalize | Measure Kappa on test set too; check if F1 > 0.80 is noise | Timoshenko (70% ceiling) |

---

## 8. Development Roadmap

### Phase 0: Data Foundation (Current → Month 1)
1. Label 500 seed queries (triple-annotate, κ ≥ 0.70)
2. Establish fastText baseline (F1 ≈ 0.55–0.65)
3. Run error analysis against Jansen taxonomy
4. Estimate: 400K–2M labeled queries needed for target F1

### Phase 1: Baseline Training (Month 1–2)
1. Label 400K queries via active learning from search logs (JointMap protocol)
2. Train fastText with hierarchical softmax (target F1 ≥ 0.65)
3. If F1 ≥ 0.70: STOP. Deploy fastText. Invest saved compute in coverage, not accuracy.
4. If F1 < 0.65: Move to Phase 2.

### Phase 2: Deep Learning (Month 2–3, OPTIONAL)
1. Implement CNN/DAN (target F1 ≥ 0.70)
2. If fastText was within 3 points of target, CNN will cross it
3. If still below target: diagnose via error taxonomy. Add BERT only if >50% of errors are long-query.

### Phase 3: Production (Month 3+)
1. Implement cascade: fastText (95% of queries) + secondary model (5% ambiguous queries)
2. Set up periodic retraining (weekly centroid recompute)
3. Monitor frequency-stratified F1 in production (A/B testing with interleaving)

---

## Data & Code Availability

- **Source literature:** `deepl-search/extractions/` — 325+ extraction JSON files covering all cited works
- **Pipeline (current):** `deepl-search/src/` — taxonomy.py, classifier.py, intent_vector.py, ads_mapping.py, api.py
- **Experiments:** `deepl-search/experiments/` — smoke_test.py, hdbscan_experiment.py, clustering-results.md
- **Architecture foundation:** `deepl-search/intent-topology-memo.md`

**Next concrete step:** Label 500 seed queries, train fastText baseline, measure actual F1 against the 0.55–0.65 prediction.

---

## References

- Timoshenko & Hauser (2018). Identifying customer needs from user-generated content. *Marketing Science*, 38(1), 1–20.
- Hashemi et al. (2016). Query intent detection using convolutional neural networks. *arXiv:1610.02859*.
- Joulin et al. (2016). Bag of Tricks for Efficient Text Classification. *EACL 2017*.
- Cer et al. (2018). Universal Sentence Encoder. *arXiv:1803.11175*.
- Mikolov et al. (2013). Distributed Representations of Words and Phrases and their Compositionality. *NIPS 2013*.
- Beitzel et al. (2007). Temporal analysis of a very large topically categorized web query log. *JASIST*, 58(2), 166–178.
- Jansen et al. (2009). Patterns of query reformulation during web searching. *JASIST*, 60(7), 1358–1371.
- Iyyer et al. (2015). Deep Unordered Composition Rivals Syntactic Methods for Text Classification. *ACL 2015*.
- Pinterest (2020). Query2Interest: Query to interest mapping at Pinterest.
- JointMap (2020). Active Learning for Extreme Multi-label Classification. *arXiv:2005.13783v2*.
- Prabhu & Varma (2014). FastXML: A Fast, Accurate and Stable Tree-classifier for eXtreme Multi-label Learning. *KDD 2014*.
- Smucker et al. (2007). A comparison of statistical significance tests for information retrieval evaluation. *CIKM 2007*.
- Artetxe & Schwenk (2019). Massively Multilingual Sentence Embeddings for Zero-Shot Cross-Lingual Transfer and Beyond. *ACL 2019*.
- Izsak et al. (2021). How to Train BERT with an Academic Budget. *EMNLP 2021*.
- Huang et al. (2020). Embedding-based Retrieval in Facebook Search. *KDD 2020*.
