# Next Steps Analysis

Answers to the 5 open items from the project roadmap, grounded in experimental data.

---

## 1. Get LLM API Key → Run B8 Baseline & Annotation Pipeline

**What's needed:** A free LLM API key with a decent model (Groq is the primary target — free tier gives 30 req/min on llama3-70b).

**Why it's blocked:** No API key has been configured. The scripts (`run_b8_baseline.py`, `llm_annotation_pipeline.py`) wait for environment variables `LLM_API_BASE`, `LLM_API_KEY`, `LLM_MODEL`.

**What B8 would tell us:**
- Sets the "worth training" threshold — if an LLM can't beat 74.8% L2 accuracy with full context + reasoning, then the supervised bi-encoder is already at the ceiling.
- Cross-model agreement (run B8 on two different LLMs) → lower bound on label reliability. If LLMs agree at 85% and humans agree at 80%, then 74.8% bi-encoder accuracy may already be at the irreducible noise floor.
- Cost estimate: 2,000 queries × 1 prompt each × ~500 tokens/response. At Groq's free tier, ~$0.00. At paid API rates, ~$1-2.

**Expected B8 L2 accuracy (guess):** 60-70%. LLMs are good at short-text classification but the 64-way L2 is genuinely hard. The prompt has full category descriptions as few-shot context, so it should outperform zero-shot embedding retrieval (24% vanilla) but likely underperform the fine-tuned bi-encoder (75%).

**Recommendation:** Sign up for a free Groq account (groq.com, needs phone verification), set the three env vars, and run `python scripts/run_b8_baseline.py`. Total time: ~20 minutes for API setup + ~2 hours for the script to run (2K queries at 30 req/min).

---

## 2. Extend Bi-Encoder to L3/L4

**What it means:** Currently the bi-encoder trains on (query, L2_description) pairs — 64-way classification. Extending to L3 means 512 classes, L4 means 3,843.

**The sparsity problem:**

| Level | Classes | Labeled examples per class (avg) | Labeled examples with <5 samples |
|-------|---------|----------------------------------|----------------------------------|
| L2    | 64      | 7.8 (500/64)                    | 16 classes                        |
| L3    | 512     | 0.98 (500/512)                  | ~400+ classes                     |
| L4    | 3,843   | 0.13 (500/3,843)                | ~3,600+ classes                   |

With only 500 labels, L3/L4 training is **not viable**. The MNR loss needs positive pairs per class. 47 of 64 L2 classes have at least one labeled example; only ~50-100 of 512 L3 classes would have even a single example.

**The description quality problem:** 60% of L3/L4 names in `l3l4_mapping.json` are generated boilerplate ("Board Games and Puzzles - Detail 1"). Using them as training targets would teach the model to match noise.

**What you can do right now (without more data):**
- Evaluate the current bi-encoder on L3/L4 zero-shot: use the trained bi-encoder (tuned on L2) and compute cosine similarity to L3/L4 descriptions. This tests whether the L2 training transfers to finer granularity.
- If L3/L4 zero-shot accuracy is >40%, the model is learning a generalizable hierarchy. If <20%, L3/L4 is too fine for the current embedding space.

**Path forward:**
1. Get more labeled data (target 5K-10K for viable L3, 50K+ for L4)
2. Replace generated L3/L4 names with real descriptions (LLM-generated or IAB-sourced)
3. Add hierarchical loss (train on L2 but evaluate on L3/L4 through parent propagation)

**Recommendation:** Don't attempt L3/L4 training now. The 500 labels are barely sufficient for L2. Instead, write an evaluation script to measure what the current model can do zero-shot at L3/L4. That costs nothing and tells you the headroom.

---

## 3. Investigate SimCSE Effective K Drop

**The observation:**

| Model | Effective K | L2 Accuracy | Mean Confidence |
|-------|------------|-------------|-----------------|
| Vanilla all-MiniLM | 39 | 24.4% | 0.191 |
| SimCSE-pretrained | 38 | 28.2% | 0.294 |
| Bi-encoder (SimCSE + 500 labels) | 25 | 74.8% | 0.428 |

The effective K dropped from 39 → 38 → 25 across the three models. The question: is this **concentration** (model correctly learns that most queries belong to a smaller set of classes) or **collapse** (model stops distinguishing between classes)?

**Evidence for concentration (good):**
- Accuracy jumped from 24% → 75% simultaneously with K dropping 39 → 25. If the model were collapsing, accuracy would drop.
- Mean confidence increased from 0.19 → 0.43. Collapsing models tend to have high-but-even confidence across all classes; here confidence is both higher and more peaked (std 0.12 vs 0.09).
- Confidence distribution shifts right dramatically: vanilla has 194/500 samples in 0-0.15 range; bi-encoder has only 10/500 in that range.

**Evidence for collapse (bad):**
- Training data is 500 labels, 48 of 64 L2 classes covered, with heavy skew (Dictionaries & Thesauri has ~30+ examples, some classes have 1-2). The bi-encoder may simply not learn the tail classes.
- Per-L1 accuracy reveals the weak spots: Food & Dining (48% — only 25 samples), Computers & Technology (61% — 31 samples). Low-sample L1s have the worst accuracy.
- The effective K of 25 is far below ADR-6's target of 200-300 (which was about L3/L4, not L2). At L2, 25/64 means the model is functionally 39-class — 25 classes get >1% prediction share, the other 39 get <1%.

**How to distinguish (surgical experiment):**
1. Per-class recall: compute the recall for each of the 64 L2 classes. If tail classes (1-2 examples) have 0% recall, it's concentration-by-data-sparsity. If well-represented classes also have low recall, it's collapse.
2. Confidence by class: plot mean confidence for each L2 class. If some classes consistently get 0.15-0.20 confidence (near the decision boundary), the model is uncertain about them, not collapsing them.
3. Simulate with synthetic data: add 5-10 labeled examples for each of the 16 missing L2 classes, retrain, and check if effective K increases. If it does, the problem is data coverage, not model collapse.

**Recommendation:** The current evidence points to **healthy concentration**, not collapse. The bi-encoder is correctly learning that most of the 500 queries belong to ~25 frequent classes. The 16 L2 classes with 0 examples in training will never get meaningful weight. The fix is more training data with better coverage, not architectural changes. Run per-class recall analysis to confirm.

---

## 4. Design Production Reject Threshold

**Data from reject calibration (B9, 2,000 queries, new IAB taxonomy):**

| τ (threshold) | L2 Coverage | L1 Fallback Added | Total Accepted |
|---------------|-------------|-------------------|----------------|
| 0.05          | 99.0%       | 0.0%              | 99.0%          |
| 0.10          | 86.9%       | +0.1%             | 87.0%          |
| 0.15          | 60.2%       | +0.2%             | 60.4%          |
| 0.20          | 37.8%       | +0.2%             | 38.0%          |
| 0.30          | 10.8%       | +0.3%             | 11.1%          |

**Critical pattern:** L1 fallback adds **at most 0.3%** coverage at any threshold. The granularity ladder is effectively useless — if L2 confidence is below τ, L1 confidence is also below τ (L1 descriptions are vaguer, producing lower similarities). This confirms the finding from both old and new taxonomy: **drop the granularity ladder from the design.**

**However:** These numbers are from the **B9 zero-shot model** (mean L2 conf 0.187). The **bi-encoder** (mean L2 conf 0.428) would have a completely different reject curve. We haven't run reject calibration on the bi-encoder's predictions.

**Recommendation for production τ:**
1. **Don't use the B9 reject curve.** It's for the wrong model. B9 has 60% coverage at τ=0.15; the bi-encoder would have much higher coverage at the same τ because its confidence distribution is shifted right (0.428 mean vs 0.187).
2. **Estimate bi-encoder reject curve:** Bi-encoder mean conf is 0.428, std 0.120. Assuming roughly normal distribution, at τ=0.15, ~99% of predictions would be accepted. At τ=0.30, ~86% would be accepted. At τ=0.50, ~27% accepted.
3. **Run actual reject calibration on bi-encoder predictions** — this is a one-line change in `run_reject_calibration.py` (swap the model). Do this after confirming the 74.8% accuracy figure is robust.
4. **Choose τ by desired coverage**, not the other way around:
   - "Accept everything except the most uncertain" → τ=0.15 (est. 99% coverage, ~72% accuracy on accepted)
   - "Accept only confident predictions" → τ=0.30 (est. 86% coverage, ~80% accuracy on accepted)
   - "Only accept very confident predictions" → τ=0.40 (est. 60% coverage, ~85% accuracy on accepted)

**The granularity ladder should be redesigned or removed.** It adds 0.1-0.3% coverage at any τ. A simpler design: predict L2 directly; if confidence < τ, reject. No L1 fallback. The 8 L1 descriptions are too vague for cosine similarity to work as a fallback.

**Alternative design for the ladder:** Instead of similarity-based L1 fallback, use a **separate L1 classifier** (trained on the same 500 labels, 84.8% L1 accuracy). When L2 is rejected, run L1 classification. This would actually add coverage because L1 is easier (8 vs 64 classes) and the bi-encoder already achieves 84.8% L1 accuracy.

---

## 5. Create More Labeled Data

**Why more labels matter (from data):**

| Training size | L2 Accuracy | Mean Confidence | Effective K | Source |
|---------------|-------------|-----------------|-------------|--------|
| 0 (vanilla) | 24.4% | 0.191 | 39 | eval on 500 |
| 0 (SimCSE) | 28.2% | 0.294 | 38 | eval on 500 |
| 400 (bi-encoder) | 74.8% (on 500 total) | 0.428 | 25 | eval on 500 |

The jump from 24% → 75% with 400 training labels is the largest effect in the project. The marginal return of additional labels is **high and likely decreasing but still significant**.

**Diminishing returns estimate:**
- 0 → 400 labels: +50.4pp accuracy (12.6pp per 100 labels)
- 400 → 1,000 labels (estimated): +8-12pp (1.3-2.0pp per 100 labels)
- 1,000 → 5,000 labels (estimated): +5-8pp (0.1-0.2pp per 100 labels)
- Beyond 5K labels: accuracy gains < 0.1pp per 100 labels

Based on the learning curve: 500 labels got us to 75% L2 accuracy. 1,000 would likely push to 83-87%. 5,000 would push to 90-93%. Beyond that, the 42.6% ambiguity ceiling means single-label accuracy caps around 92-95%.

**The most impactful labeling target:** **Cover the 16 missing L2 classes** that have 0 examples in the current 500. Even 1-2 examples per missing class would expand effective K and prevent the model from being blind to entire intent categories.

**Labeling workflow options:**

| Method | Throughput | Quality | Cost | Time for 500 more |
|--------|-----------|---------|------|-------------------|
| Manual batch scripts (current) | ~50-100/hr | High | Free | 5-10 hours |
| Manual via UI tool | ~30-60/hr | High | Free + build time | 8-16 hours |
| LLM annotation (pipeline) | ~2,000/hr | Medium | ~$0.01 (Groq free) | 15 min |
| LLM + human calibration | ~2,000/hr LLM, ~100/hr human | High | ~$0.01 + human time | 15 min + 1 hr |

**Practical recommendation:**
1. **First, run the LLM annotation pipeline** (once the API key is available) to get 1K-5K LLM-labeled queries. Compare them against the 500 human labels. Compute agreement rate.
2. **Double-label 50-100 existing records** with a second human annotator. Measure Cohen's κ. This tells you the label noise floor — the highest accuracy your model can theoretically reach.
3. **If agreement > 80%**: trust LLM labels for training data expansion. Label 2K-5K more via LLM, spot-check 5%.
4. **If agreement < 70%**: the single-annotator problem is severe. Prioritize double-labeling, not expansion.

**Don't create more labels until you know your label noise rate.** The 74.8% bi-encoder accuracy might partially reflect overfitting to one annotator's preferences. Measuring this first prevents wasting effort labeling data that doesn't generalize.

---

## Summary Decision Matrix

| Step | Effort | Impact | Dependency | Do Now? |
|------|--------|--------|------------|---------|
| Run B8 baseline | 2 hrs script + 20 min API setup | Low-Med (sets threshold) | API key | **No, blocked by key** |
| Extend bi-encoder to L3/L4 | 1 day code + train | Low (500 labels too few) | More labels first | **No, wait for data** |
| Investigate effective K | 2 hrs analysis script | Medium (per-class recall) | None | **Yes, run now** |
| Design reject threshold | 1 day (re-run on bi-encoder) | Medium (product decision) | Robust accuracy figure | **Yes, swap model in script** |
| Create more labels (human) | 5-10 hrs | High (largest ROI) | Understanding noise rate | **Yes, start with double-labeling** |
| Create more labels (LLM) | 15 min script | High | API key | **No, blocked by key** |
