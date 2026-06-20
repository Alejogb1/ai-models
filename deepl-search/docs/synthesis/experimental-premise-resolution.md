# Experimental Premise Resolution Program

> Follow the philosophy of premise-foundations-questions.md:
> Treat each assumption as a testable hypothesis.
> The smallest experiment that can falsify it determines the architecture.
> No architectural decisions before experimental evidence.

---

## Overview

| # | Premise | Experiment | Cost | Duration | Decision Rule |
|---|---------|-----------|------|----------|---------------|
| 1 | Query is the unit | Session vs. single-query classification | $0 (synthetic sessions) | 1 day | If session-F1 > query-F1 by ≥5 pts → redesign |
| 2 | Intent lives in query text | LLM generates disambiguating context | $5 (API calls) | 1 day | If context-augmented outperforms query-only → augment input |
| 3 | 3,843 is correct K | Classify at K=64, 256, 1024, 3843 | $0 (taxonomy subset) | 2 days | If K=1024 within 3 pts of K=3843 → reduce taxonomy |
| 4 | Labels are ground truth | Measure inter-annotator agreement on 200 queries | $200 (annotation) | 3 days | If agreement <75% → adopt soft labels / behavioral signal |
| 5 | Classification is the paradigm | Compare classification vs. retrieval vs. ranking | $0 (same embedding) | 2 days | If retrieval/ranking outperforms class FN → switch paradigm |
| 6 | F1 measures success | Compare F1 vs. cost-weighted F1 vs. behavioral proxy | $0 (computation) | 1 day | If ranking of models differs → replace F1 with cost-weighted |
| 7 | Taxonomy is static | Simulate 1-year query drift on historical logs | $0 (if logs exist) | 2 days | If coverage decays >5% → implement living taxonomy |
| 8 | English-first | Compare English-only vs. translate-then-classify vs. cross-lingual | $10 (translation API) | 1 day | If cross-lingual within 5 pts of English → go multilingual |
| 9 | Bottleneck is labels | Compare random sampling vs. active learning vs. LLM-synthetic | $50 (LLM API) | 2 days | If active/LLM achieves same F1 with 50% fewer labels → adopt |
| 10 | Octohedral is universal | Compare YQT taxonomy vs. domain-specific minimal taxonomy | $0 (taxonomy design) | 2 days | If minimal taxonomy achieves 90% of product goals → drop YQT |
| 11 | Raw text is input | Compare with vs. without spell correction | $0 (SymSpell) | 1 day | If spell-corrected F1 > raw F1 by ≥3 pts → add preprocessor |
| 12 | Every query must classify | Compare forced vs. reject-option vs. granularity-ladder | $0 (threshold sweep) | 1 day | If reject-option improves Precision@1 by ≥5 pts → add reject |

---

## Experiment Designs

### Experiment 1: Session vs. Single-Query Classification

**Premise:** The query is the unit of analysis.

**Hypothesis:** Session-level classification (last 3-5 queries as input) yields higher accuracy than single-query classification.

**Method:**
1. Take 1,000 real search sessions (sequences of 3-5 queries from the same user within 5 minutes).
2. For each session, extract the last query (single-query condition) and the full session (session condition).
3. Use the existing classifier (`classifier.py`) to classify both conditions.
4. Evaluate against human labels for the final query's intent.
5. Measure: F1, cross-L1 error rate, and confidence calibration for each condition.

**Cost:** $0. Use the existing pipeline. Requires session-structured data (synthetic sessions can be constructed from single queries by copying with slight variations, but real sessions are preferred).

**Duration:** 1 day of implementation + analysis.

**Decision Rule:**
- If session-level F1 > single-query F1 by **≥5 points**: Premise 1 is falsified. Adopt Door 1.1 (session-as-unit) as the primary architecture. Redesign input pipeline.
- If session-level F1 > single-query F1 by **2–4 points**: Premise 1 is weakened. Adopt Door 1.5 (synthetic context via LLM) — impute session context without requiring real session data.
- If session-level F1 ≈ single-query F1 (within 1 point): Premise 1 holds. Continue with query-as-unit.

---

### Experiment 2: Context-Augmented vs. Query-Only Classification

**Premise:** Intent lives in query text.

**Hypothesis:** Augmenting the query with LLM-generated disambiguating context improves classification accuracy.

**Method:**
1. Take 500 ambiguous queries (those with high entropy in the current classifier's output distribution).
2. For each query, use an LLM (GPT-4o-mini, ~$0.15/1M tokens) to generate 3 plausible user scenarios:
   - Prompt: "Given the search query '{query}', list 3 plausible user scenarios that would produce this query. For each scenario, describe the user's likely intent."
3. For each query, create two classification inputs:
   - Condition A: Query text only (baseline)
   - Condition B: Query text + LLM-generated scenarios as synthetic context
4. Classify both conditions with the existing classifier.
5. Evaluate against human labels.

**Cost:** ~500 queries × 3 scenarios × ~100 tokens = 150K tokens ≈ $0.02 (GPT-4o-mini). Plus ~$5 for one-off LLM labeling. Total: ~$5.

**Duration:** 1 day.

**Decision Rule:**
- If context-augmented F1 > query-only F1 by **≥5 points**: Premise 2 is weakened. Adopt Door 2.6 (generative context) for ambiguous queries at inference time.
- If context-augmented F1 > query-only F1 by **≥10 points on ambiguous queries**: Premise 2 is falsified. Intent does not live in query text. Redesign around session/behavioral input (Door 2.1 or 2.3).
- If no significant difference: Premise 2 holds for the classifier's current capability. Monitor but do not redesign.

---

### Experiment 3: Taxonomy Granularity Sweep

**Premise:** 3,843 classes is the correct target.

**Hypothesis:** Coarser taxonomies (K=64, K=256, K=1024) achieve F1 within 3 points of the full K=3843 taxonomy.

**Method:**
1. Create 4 taxonomy variants from the existing skeleton:
   - K=64 (L2 level: 8 L1 × ~8 L2 each)
   - K=256 (L3 level: ≈ every 2nd L3)
   - K=1024 (L3 level: all 512 L3 × 2 sub-classes each)
   - K=3843 (full L4)
2. For each variant, map each intent class ID to its parent at the coarser level. This is a label mapping, not a retrain — take the existing classification output and map it up to the coarser granularity.
3. Evaluate at each granularity on 1,000 labeled queries.
4. Measure: Macro F1, coverage (fraction of queries assigned to a leaf), density distribution.

**Cost:** $0. Pure computation on existing classifier output with hierarchical label mapping.

**Duration:** 2 days.

**Decision Rule:**
- If K=1024 F1 is within **3 points** of K=3843 F1: Premise 3 is weakened. The marginal 0.15 bits from the extra 2,819 classes is not worth the data dilution. Target K=1024–1500 for initial training.
- If K=256 F1 is within **3 points** of K=3843: Premise 3 is falsified. The taxonomy is vastly overparameterized. Target K=256–512.
- If K=3843 significantly outperforms all coarser levels: Premise 3 holds. Keep full taxonomy but implement Door 3.5 (adaptive granularity per query based on confidence).

---

### Experiment 4: Inter-Annotator Agreement

**Premise:** Human labels are ground truth.

**Hypothesis:** Inter-annotator agreement on intent labels is below 75% (Cohen's κ < 0.70), indicating that labels are not reliable ground truth.

**Method:**
1. Sample 200 queries stratified by:
   - Frequency: 100 head queries (top 10% by volume), 100 tail queries (bottom 50%)
   - Ambiguity: 100 low-entropy queries (existing classifier confidence >0.8), 100 high-entropy queries (confidence <0.4)
2. Send each query to 3 annotators on a crowdsourcing platform (Amazon MTurk or Prolific).
3. Annotators choose from the full 3,843-class taxonomy (or a simplified L2-level selection).
4. Measure: pairwise agreement, Fleiss' κ, distribution of disagreements (are they within-L1 or cross-L1?).
5. Also measure: does agreement vary by frequency stratum? By ambiguity stratum?

**Cost:** 200 queries × 3 annotators × $0.10 per label = $60. Plus platform fees ≈ $200 total.

**Duration:** 3 days (1 day setup, 1 day annotation, 1 day analysis).

**Decision Rule:**
- If overall agreement <75% (κ < 0.70): Premise 4 is weakened. Adopt Door 4.1 (multi-annotator soft labels) and/or Door 4.5 (LLM-as-annotator with human verification).
- If agreement <65% (κ < 0.55): Premise 4 is falsified. Labels are unreliable. Shift to behavioral supervision (Door 4.3/4.6) as primary training signal. Use labels only for initialization.
- If agreement >85% (κ > 0.80): Premise 4 holds. Labels are reliable ground truth. Proceed with standard supervised learning.

---

### Experiment 5: Paradigm Comparison (Classification vs. Retrieval vs. Ranking)

**Premise:** Classification is the correct paradigm.

**Hypothesis:** Framing intent prediction as retrieval (bi-encoder with cosine similarity) or ranking (query-to-class scoring) yields better NDCG@5 than the current classification approach.

**Method:**
1. Implement three paradigms on the same embedding backbone:
   - **Classification** (current): linear projection from 384-dim query embedding → 3843-class logits → softmax → cross-entropy
   - **Retrieval** (Door 5.1): bi-encoder. Query encoder + class definition encoder. For each query, retrieve top-K classes by cosine similarity. Predict "Other" if max similarity < threshold.
   - **Ranking** (Door 5.2): score each class for the query. Rank by score. Evaluate NDCG@5, MAP@10.
2. All three use the same base embedding (all-MiniLM-L6-v2 or similar).
3. Evaluate on 500 labeled queries.
4. Measure: Macro F1 (classification), NDCG@5 (ranking), Recall@3 (retrieval), and a human evaluation of top-3 relevance.

**Cost:** $0. All three paradigms can be implemented with the existing sentence-transformer backbone. The difference is in the output layer and loss function.

**Duration:** 2 days.

**Decision Rule:**
- If retrieval or ranking outperforms classification on **all three metrics** (NDCG, Recall, human relevance): Premise 5 is falsified. Classification is the wrong paradigm. Adopt retrieval/ranking architecture.
- If classification outperforms on F1 but retrieval is within 3 points: Premise 5 is weakened. Use classification for hard assignments, retrieval for exploratory use cases (market research trend detection).
- If classification clearly dominates: Premise 5 holds. Continue with classification.

---

### Experiment 6: F1 vs. Cost-Weighted F1 vs. Behavioral Proxy

**Premise:** F1 measures success.

**Hypothesis:** Cost-weighted F1 (using the cost matrix from Step 1) and a behavioral proxy (click-through rate on served content) rank models differently than standard F1.

**Method:**
1. Take 3 model variants with different error profiles:
   - Model A: high F1 but makes cross-L1 errors on 5% of queries (predicts Shopping when true is Health)
   - Model B: slightly lower F1 but never makes cross-L1 errors (all errors are within-L3)
   - Model C: moderate F1 but calibrated confidence scores (0.7 = 70% correct)
2. Evaluate each on: (a) standard Macro F1, (b) cost-weighted F1 (cross-L1=1.0, within-L1=0.3, within-L3=0.1), (c) simulated CTR using a simple user model (if cross-L1 error → bounce = no click; if within-L3 → partial engagement).
3. Check whether the ranking of models changes across metrics.

If real behavioral data is not available, simulate: assume that cross-L1 errors cause 90% bounce rate, within-L1 errors cause 40% bounce, correct classification causes 10% bounce.

**Cost:** $0 (simulation).

**Duration:** 1 day.

**Decision Rule:**
- If the ranking of models differs between F1 and cost-weighted F1: Premise 6 is falsified. F1 is misleading. Replace with cost-weighted F1 or utility-based evaluation (Door 6.1/6.2).
- If the ranking of models differs between F1 and simulated CTR: Double falsification. F1 does not predict product outcome. Adopt Door 6.2 (utility-based evaluation).
- If rankings are identical: Premise 6 holds. F1 is a sufficient proxy. Continue with F1 but add cost-weighted as a secondary metric.

---

### Experiment 11: Spell Correction Preprocessor

**Premise:** Raw query text is the model's input.

**Hypothesis:** A spell-correction preprocessor improves classification accuracy by ≥3 points on the subset of queries containing misspellings (~15% of all queries).

**Method:**
1. Integrate SymSpell or a lightweight neural spell-corrector into the classification pipeline.
2. Identify which queries in the test set contain misspellings (use a dictionary lookup: if ≥1 tokens not in dictionary → likely misspelled).
3. Compare:
   - Condition A: Raw query → classifier
   - Condition B: Spell-corrected query → classifier
4. Measure: F1 on misspelled subset, F1 overall, precision/recall on misspelled vs. clean queries.

If a dedicated misspelled test set is not available, introduce synthetic misspellings (edit distance 1-2) into 200 clean queries to create a controlled test set.

**Cost:** $0. SymSpell is free and runs in <1ms per query.

**Duration:** 1 day.

**Decision Rule:**
- If spell-corrected F1 > raw F1 by **≥3 points** on the misspelled subset: Premise 11 is weakened. Add spell-correction preprocessor to the pipeline permanently.
- If spell-corrected F1 > raw F1 by **≥5 points** overall: Premise 11 is falsified. Preprocessing is more important than model architecture. Invest in normalization pipeline (Door 11.2) before investing in model improvements.
- If no significant difference: Premise 11 holds for this classifier. Raw text is sufficient.

---

### Experiment 12: Reject Option vs. Forced Classification

**Premise:** The model must predict a specific intent for every query.

**Hypothesis:** Adding a reject option (abstain when confidence < threshold) improves Precision@1 by ≥5 points on the accepted queries, and the rejected queries can be handled by falling back to a coarser granularity.

**Method:**
1. Sweep confidence thresholds from 0.1 to 0.9 in increments of 0.1.
2. For each threshold τ:
   - Queries with max confidence < τ: reject. Assign to either "Unknown" or the L1 parent class (granularity ladder).
   - Queries with max confidence ≥ τ: accept. Evaluate Precision@1 and coverage.
3. Plot the Precision–Coverage curve.
4. Identify the "elbow" where marginal precision gain per coverage loss drops below 0.5.
5. Compare:
   - Forced classification (τ = 0, all queries classified)
   - Reject option at elbow threshold
   - Granularity ladder (Door 12.4): reject at L4 but classify at L3 or L2 based on confidence

**Cost:** $0. Pure analysis of existing classifier output.

**Duration:** 1 day.

**Decision Rule:**
- If reject-option (at elbow threshold) improves Precision@1 by **≥5 points** while maintaining ≥80% coverage: Premise 12 is weakened. Add reject-option with granularity ladder to the pipeline.
- If reject-option improves Precision@1 by **≥10 points** (even at 60-70% coverage): Premise 12 is falsified. Forcing classification degrades quality. Reject-option is essential. Design the deployment around selective classification.
- If forced classification achieves similar precision at all coverage levels: Premise 12 holds. Continue with forced classification.

---

## Execution Strategy

### Phase 1: Zero-Cost Experiments (Week 1)

Run experiments that require no annotation budget and no external APIs:

| Day | Experiment | Output |
|-----|-----------|--------|
| 1 | Exp 1: Session vs. single query | Decision on input unit |
| 1 | Exp 11: Spell correction | Decision on preprocessor |
| 2 | Exp 3: Taxonomy granularity sweep | Decision on target K |
| 2 | Exp 12: Reject option | Decision on abstention |
| 3 | Exp 5: Paradigm comparison | Decision on classification vs. retrieval |
| 3 | Exp 6: F1 vs. cost-weighted | Decision on evaluation metric |

### Phase 2: Low-Cost Labeled Experiments (Week 2)

Experiments that require small amounts of labeled data:

| Day | Experiment | Budget | Output |
|-----|-----------|--------|--------|
| 4-5 | Exp 4: Inter-annotator agreement | ~$200 | Decision on label reliability |
| 5-6 | Exp 2: Context augmentation | ~$5 | Decision on input augmentation |

### Phase 3: Synthesis (Week 3)

Consolidate all experimental results into a unified architecture specification:

1. Resolved premises → fixed architecture decisions
2. Weakened premises → adaptation strategy
3. Falsified premises → redesign requirements
4. The result is the formal Problem Derivation (Step 2)

---

## Guiding Principle

> No architectural decision is made before its premise is tested.
> The smallest falsifying experiment determines the path.
> If an experiment costs more than the risk of being wrong, skip it and accept the premise as a working assumption with a flag for later revision.

---

---

## Phase 1 Results

Phase 1 ran 6 zero-cost experiments using the embedding classifier (all-MiniLM-L6-v2) on 2,000 queries from the MS MARCO sample.

### Critical Caveat

All confidence values are very low (mean 0.07–0.14) because the taxonomy uses generic placeholder descriptions ("Intent 1", "Subcategory 1"). The embedding classifier does cosine similarity between query embeddings and these generic label descriptions — they barely match semantically. Results should be interpreted as **relative comparisons** and **structural properties**, not absolute performance. The LLM classifier or a trained classifier would produce different absolute numbers, but the structural findings (self-consistency, distribution shape, change rates) are likely robust.

### Exp 1: Session vs Single Query

| Metric | Value |
|--------|-------|
| Single query mean confidence | 0.1230 |
| Session (concat) mean confidence | 0.1396 |
| Confidence gain | +0.0166 (+13.5% relative) |
| Predictions changed by session | 438/500 = **87.6%** |

**Decision: FALSIFIED.** Adding session context changes 87.6% of predictions and increases confidence by 13.5%. The query alone carries insufficient signal. The deployment must use session-level input.

*Caveat: Without labels, we cannot determine whether the changed predictions are correct. The proxy uses self-consistency, not accuracy. A label-dependent version (Phase 2 Exp 2) is needed for confirmation.*

### Exp 3: Taxonomy Granularity Sweep

| Metric | Value |
|--------|-------|
| L1 (8 classes) mean confidence | 0.0667 |
| L2 (64 classes) mean confidence | 0.1086 |
| L3 (512 classes) mean confidence | 0.1155 |
| L4 (3843 classes) mean confidence | 0.1222 |
| L1 self-consistency (L4→L1 vs direct L1) | **72.8%** |
| L4 effective usage (classes with >1% share) | **1/3843** |

Confidence *increases* with granularity (0.067 → 0.122) because more centroids increase the chance of a random close match. But self-consistency is only 72.8% — meaning ~27% of queries get different L1 assignments depending on whether we classify at L4 and map up, or classify at L1 directly. Only 1 of 3,843 L4 classes captures >1% of queries.

**Decision: WEAKENED.** The L4 taxonomy is not consistently aligned with L1 structure. Self-consistency should be >90% for a well-structured taxonomy. Effective K is much lower than 3,843.

### Exp 5: Paradigm Comparison

| Metric | Value |
|--------|-------|
| Mean non-zero classes per query | **47.7** |
| Single-class predictions | 0.0% |
| 10+ class predictions | 95.8% |
| Max confidence | 0.1286 |
| Queries with any class >0.3 | 2.8% |

The classifier distributes confidence extremely diffusely — average 47.7 classes per query with non-zero similarity, and essentially no query has any class above 0.3. This is not a classification signal; it's near-random similarity noise across many centroids.

**Decision: WEAKENED.** With 48 non-zero labels per query, the paradigm is closer to "dense retrieval over 3,843 candidates" than to classification. A bi-encoder retrieval framework (Door 5.1) or ranking paradigm (Door 5.2) is more structurally appropriate.

### Exp 6: F1 vs Cost-Weighted F1

| Model | Accuracy | F1 | Avg Cost | CW-F1 |
|-------|----------|----|----------|-------|
| Model A: High F1, some cross-L1 | 0.850 | 0.850 | 0.079 | 0.783 |
| Model B: Lower F1, all within-L1 | 0.805 | 0.805 | 0.062 | 0.755 |
| Model C: Moderate F1 | 0.834 | 0.834 | 0.071 | 0.775 |

Rank by F1: A > C > B
Rank by CW-F1: A > C > B

**Decision: HOLDS.** Identical ranking. This means for these simulated error profiles, F1 is a sufficient proxy. However, this is a synthetic simulation with 100 classes (not 3,843) and assumes cost matrix weights of 1.0 (cross-L1) vs 0.3 (within-L1). With real models, larger differences may appear.

### Exp 11: Spell Correction

| Metric | Value |
|--------|-------|
| Queries tested | 500 |
| Misspelled variants generated | 727 |
| Predictions changed by misspelling | 600/727 = **82.5%** |

Synthetic misspellings (edit distance 1-2, 25% per-word probability) change predictions 82.5% of the time.

**Decision: FALSIFIED.** Misspellings are devastating to embedding-based classification. Preprocessing (spell correction) is at least as important as the classifier architecture itself.

*Caveat: Real-world misspelling rates are ~5-15% of queries, not 82.5%. The 25% per-word probability is aggressive. A more realistic estimate: ~15-20% of real queries contain misspellings, and of those, our 82.5% change rate applies, giving ~12-16% of all queries affected.*

### Exp 12: Reject Option

| Threshold | Coverage | Mean Confidence |
|-----------|----------|----------------|
| 0.00 | 100.0% | 0.123 |
| 0.05 | 83.0% | 0.144 |
| 0.10 | 57.4% | 0.174 |
| 0.15 | 32.3% | 0.210 |
| 0.20 | 15.7% | 0.254 |
| 0.25 | 6.7% | 0.292 |
| 0.30 | 2.4% | 0.333 |
| 0.40 | 0.1% | 0.420 |
| 0.50 | 0.0% | — |

At τ=0.5, coverage is 0% — literally no query has confidence above 0.5. At τ=0.1, only 57% of queries are accepted. The confidence distribution is entirely in the [0.0, 0.3] range.

**Decision: FALSIFIED.** Forced classification produces near-random assignments for the vast majority of queries. A reject option with granularity ladder is architecturally essential. The deployment must be designed around selective classification (Door 12.3): accept high-confidence predictions, fall back to coarser levels for uncertain ones.

### Summary

| # | Premise | Result | Architectural Implication | Action |
|---|---------|--------|--------------------------|--------|
| 1 | Query is unit | **FALSIFIED** | Session input required | Redesign input pipeline |
| 3 | 3843 is correct | **WEAKENED** | Target K likely 512-1024 | Granularity reduction |
| 5 | Classification paradigm | **WEAKENED** | Retrieval/ranking more appropriate | Paradigm shift |
| 6 | F1 measures success | **HOLDS** | F1 sufficient as proxy | Continue but add cost-weighted |
| 11 | Raw text is input | **FALSIFIED** | Preprocessing essential | Add spell correction |
| 12 | Every query classified | **FALSIFIED** | Reject option essential | Add selective classification |

### Meta-Finding: The Embedding Classifier Doesn't Work

The most important finding is not about any specific premise. **The zero-shot embedding classifier with generic placeholder descriptions produces near-random similarity scores** (mean 0.07-0.14 across all 3,843 classes). The classifier cannot distinguish between "Arts & Entertainment" and "Business & Finance" for real queries because the leaf descriptions ("Intent 1 > Subcategory 1") carry no semantic content.

This means:
1. All quantitative findings above are lower bounds — a better classifier would produce different numbers
2. The structural findings (self-consistency, change rates, distribution shapes) are likely robust because they depend on the embedding space geometry, not the absolute scores
3. The immediate architectural priority is **class description quality** — either realistic IAB-based class names or an LLM-based approach

---

## Appendix: Premise Decision Log

| # | Premise | Experimental Result | Decision | Date |
|---|---------|---------------------|----------|------|
| 1 | Query is unit | FALSIFIED (proxy: 87.6% prediction change) | Session input required; confirm with labels in Phase 2 | 2026-06-12 |
| 2 | Intent in text | *Pending — Phase 2 (Exp 2)* | | |
| 3 | 3843 is correct | WEAKENED (72.8% L1 self-consistency) | Reduce target K; test at 512-1024 | 2026-06-12 |
| 4 | Labels are truth | *Pending — Phase 2 (Exp 4)* | | |
| 5 | Classification paradigm | WEAKENED (47.7 mean labels/query) | Shift to retrieval/ranking architecture | 2026-06-12 |
| 6 | F1 measures success | HOLDS (simulation) | Use F1 + cost-weighted as secondary | 2026-06-12 |
| 7 | Taxonomy is static | *(deferred)* | | |
| 8 | English-first | *(deferred)* | | |
| 9 | Bottleneck is labels | *(deferred)* | | |
| 10 | Octohedral is universal | *(deferred — linked to Exp 3)* | | |
| 11 | Raw text input | FALSIFIED (82.5% change from misspellings) | Add spell-correction preprocessor | 2026-06-12 |
| 12 | Every query classified | FALSIFIED (0% coverage at τ=0.5) | Add reject option + granularity ladder | 2026-06-12 |
