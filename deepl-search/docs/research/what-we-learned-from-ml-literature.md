# What We Learned from the ML Literature

> Synthesis of ML/AI principles from 325 extracted sources.
> Purpose: Fulfill the original goal of learning properly about AI models and ML.

---

## 1. The First Principle: Baselines Before Breakthroughs

The single most consistent lesson across the literature:

> "Establish a simple linear baseline before investing in complex deep learning architectures." — Bag of Tricks (Joulin et al., 2016)

fastText — a linear classifier with n-gram features and hierarchical softmax — **matches or exceeds deep learning on datasets with <100K examples**, trains in minutes on CPU, and runs at 1M queries/second/core. It achieves within 2% of CNN accuracy and within 3% of BERT on short-text classification.

Pinterest's Query2Interest team confirmed this: "fastText with query augmentation achieves within 2% of BERT's accuracy while being 100× faster." Their conclusion: "The marginal benefit of large pre-trained models may not justify their deployment cost when data augmentation bridges the gap."

**What this means for us:** Our first model should be fastText, not BERT. We only move to deep learning if fastText fails to reach the target F1. The literature gives us a clear decision rule for when to escalate.

---

## 2. Data Is the Constraint, Not Architecture

Every major ML success story in our extraction corpus shares a pattern: they invested more in data than in model architecture.

**Timoshenko & Hauser (2018):** The difference between F1=0.66 (SVM) and F1=0.74 (CNN) was 8 points. But the difference between 500 labeled examples and 5,000 was also 8 points. Data quality matters as much as model choice.

**Active learning savings:** JointMap (2005.13783v2) showed that active learning achieves the same F1 as fully supervised training with **80% fewer labels**. The protocol: train a classifier, find the queries it's most uncertain about, label only those, retrain. Repeat. This is not an optimization trick — it's a fundamentally different approach to data acquisition.

**Weak supervision:** Query2Interest and JointMap both show that engagement signals (clicks, dwell time, saves) produce labels at zero cost that are competitive with human annotations for head classes. The trick is knowing when to trust them (high confidence signals) and when to use active learning instead (tail classes, ambiguous queries).

**What this means for us:** Our first 400K labels should come from active learning + weak supervision, not bulk annotation. The data acquisition strategy matters more than whether we use CNN or BERT.

---

## 3. The Human Agreement Ceiling Bounds Everything

The literature converges on a frustrating but important number: **humans agree on intent labels only 70–85% of the time.**

- Timoshenko: "Inter-coder accuracy was 70% (new analyst vs. three original analysts). Individual analysts identified 45-68% of universe needs."
- NotebookLM answers: "Inter-annotator agreement plateaus at 85-90%, bounding achievable accuracy."
- Hashemi: 81.6% accuracy on 125 Yahoo! classes (with supervised CNN).

If humans can't agree on the correct label for a query, no model can "correctly" classify it either. **The maximum achievable F1 is bounded by the annotation ceiling**, not by model capacity.

**Implications:**
- Do not chase F1 > 0.80 on leaf-level intent classification. It's a fool's errand.
- If your model achieves F1 = 0.78, it's operating at the human ceiling. Further investment should go to coverage (handling more query types, more languages) rather than accuracy.
- When evaluating, check whether model disagreements are also human disagreements. If so, they don't count as errors.

---

## 4. The Zipf Distribution Is the Central Design Constraint

Search queries follow Zipf with α ≈ 1.0–1.1 (Beitzel et al., 2007). This single fact drives almost every design decision:

- **Class imbalance:** The top 100 intent classes have 100× more queries than the bottom 3,000. Micro F1 is meaningless — a model that only learns the top 100 classes can score 0.80+ Micro F1 while being useless for the tail.
- **Frequency-stratified evaluation is mandatory.** Timoshenko: "Intent classifiers achieve 90%+ recall on high-frequency intents but <70% on long-tail intents." You must report performance by frequency quartile.
- **Focal loss for text uses γ=1.5**, not γ=2.0 (the vision value). This was explicitly measured by JointMap (2005.13783v2).
- **Active learning for the tail makes economic sense** because the head classes already have enough data from weak supervision.

**What this means for us:** The evaluation protocol must be frequency-stratified. The loss function must handle imbalance. The labeling strategy must prioritize the tail. All of these flow from Zipf, not from any design preference.

---

## 5. The XMC Literature Is Our Best Technical Reference

Extreme Multi-label Classification (XMC) addresses exactly our problem: thousands of labels, sparse labels per instance, severe class imbalance.

Key findings from XMC research:
- **Tree-based label partitioning** (FastXML, XR-Linear, Parabel) enables log-time inference, which is critical for 3,843 classes at web scale.
- **Hierarchical softmax** reduces softmax complexity from O(K) to O(log K). For 3,843 classes, that's the difference between a 3,843-way softmax and 12-way × 4 levels.
- **Correlation networks** (explicitly modeling label-label co-occurrence) improve XMC accuracy by 3-5% over treating labels independently.

**What this means for us:** Frame the problem as XMC and use the taxonomy tree as the hierarchical softmax tree. This gives us both training efficiency inference speed.

---

## 6. Transfer Learning Works, But Marginal Gains Are Modest

The excitement about transfer learning is justified, but the effect sizes for short-text classification are smaller than expected:

- Query2Interest: "BERT achieves ~86% accuracy" on Q2I. But fastText with augmentation achieves ~84%. **The gap is 2 points**, not 10+.
- "A Survey on Transfer Learning": Parameter-sharing transfer generally outperforms instance weighting or feature mapping — but for search query text, the gains are 3-5%, not 20%.
- Timoshenko: Deep learning classifiers outperform SVM by ~8-10 F1 points. Most of this gain comes from representation learning, not architecture.

The big surprise: **Knowledge distillation sometimes helps the student surpass the teacher.** ARALLM (2401.04319v3) showed that smaller models trained on synthetic data from GPT-3.5 actually outperformed GPT-3.5 on the target task. This contradicts the intuition that larger models are always better.

**What this means for us:** Transfer learning helps, but don't expect BERT to magically solve classification. The biggest gains come from having enough training data and using the right loss function, not from the fanciest pretrained model.

---

## 7. Error Taxonomy Is More Important Than Architecture

Jansen et al. (2009) analyzed 2,000 misclassified queries and found:
- 58.5% = misspelling
- 25.8% = cookie/session issues
- 5.6% = special characters

**A spell-correction preprocessor fixes 58.5% of errors.** No architecture change — not switching from fastText to BERT, not adding more training data — would have that impact. The most cost-effective improvement is not a better model; it's a better preprocessor.

And yet, most ML projects optimize architecture first and analyze errors later. The literature reverses this order: **analyze errors → identify bottleneck → fix bottleneck → measure improvement.**

**Common failure modes from our extraction corpus:**
-- False positives on broad categories (specific product classified as general category one level up)
-- False negatives when long descriptive text overwhelms the intent signal
-- Brand+product combinations that trigger the wrong class (new product in well-known brand)
-- Spelling errors (the most common error, the cheapest to fix)

**What this means for us:** The first thing after baseline training should be an error analysis against the Jansen taxonomy, not a model upgrade.

---

## 8. Compute Is Not the Barrier

A consistent theme across papers from 2016-2025: training text classification models is cheaper than most practitioners assume.

| Model | Training Cost | Source |
|-------|--------------|--------|
| fastText (1B words) | <10 min on CPU | Bag of Tricks |
| DAN (sota text classification) | "Minutes on an average laptop" | Deep Unordered Composition |
| BERT-base (academic budget) | ~$100-500 in compute | "How to Train BERT with an Academic Budget" |
| XMC tree (100K labels) | <1 hr on CPU | FastXML, Parabel |

The barrier is not compute — it's data. **Labeled data acquisition costs 10-100× more than model training** in any realistic ML project. This is especially true for our problem: training fastText on 2M queries costs pennies; labeling 2M queries costs thousands.

**What this means for us:** Spend the budget on data, not on GPU hours. The most compute-efficient approach is the simplest model that meets the accuracy requirement.

---

## 9. Evaluation Must Match the Use Case

The literature documents several evaluation mistakes that lead to deploying bad models:

**Mistake 1: Only reporting Micro F1.** Micro F1 is dominated by the head classes (50%+ of queries are in ≤10% of classes). A model that memorizes the top 100 classes and ignores the rest can achieve Micro F1 > 0.80.

**Mistake 2: Random splitting on Zipf data.** Random splits on a power-law distribution put tail classes entirely in train or entirely in test, producing misleading accuracy numbers. Use stratified splitting.

**Mistake 3: Ignoring human agreement bounds.** If annotators agree at 70%, a model achieving 80% F1 is either noisy or overfit to annotator-specific patterns. The 70% ceiling is the signal; above that is noise.

**Mistake 4: No bootstrap CIs.** A 0.02 F1 difference is not significant. Bootstrap confidence intervals (n=1,000) prevent overinvesting in models that look better by chance.

**Correct protocol from the literature:**
1. Stratified 70/15/15 split (stratified by class)
2. Report stratified Macro F1 by frequency quartile
3. Bootstrap 95% CIs on all metrics
4. Compare model disagreement against human disagreement
5. Error taxonomy analysis as a prerequisite to any model change

---

## 10. The Training Data Quantity Heuristics

From the literature, we can derive concrete numbers:

| What you need | How much | Source |
|--------------|----------|--------|
| Minimum labeled examples per class | ~100 | Universal Sentence Encoder |
| Stable performance per class | ~500 | Timoshenko |
| Total labeled corpus for 3,843 classes (baseline) | ~400K | Extrapolated from Timoshenko |
| Total labeled corpus (stable) | ~2M | Extrapolated |
| Active learning savings vs. passive labeling | 80% fewer labels | JointMap |
| Weak supervision quality threshold | >2 clicks, >30s dwell | Query2Interest |
| Human agreement ceiling (intent labeling) | 70-85% | Timoshenko, NotebookLM |
| Annotation cost per 1,000 queries (expert) | ~$50-200 (est.) | Industry benchmarks |
| Training data for fastText to match DNN | <100K examples | Bag of Tricks |
| Few-shot with meta-learning | 85%+ accuracy at 5 examples/class | MAML survey |

---

## 11. Cascading Architectures Beat Single Models

The recurring architectural pattern for production systems at scale is not a single model — it's a cascade:

1. **Fast/cheap filter** (fastText/embedding similarity) handles 90-95% of traffic
2. **Slow/expensive reranker** (BERT/cross-encoder) only fires for the 5-10% of ambiguous cases
3. **Fallback** (LLM zero-shot with higher latency) handles novel cases

This pattern appears in Facebook Search (Huang et al., 2020), Pinterest Q2I (2020), LinkedIn's query understanding system, and Google's query classification architecture.

**Why cascades work:** 95% of search queries are unambiguous — "nike air max size 10" has a clear intent. The cascade lets the cheap model handle the easy cases and allocates compute budget to the hard cases where it matters. The overall system is 20-50× cheaper than running a single heavy model on every query.

---

## 12. Iterative Development Is the Dominant Pattern

The most successful ML projects in our extraction corpus ("150 Successful Machine Learning Models: 6 Lessons Learned at Booking.com", rules_of_ml, Timoshenko's multi-wave process) follow the same pattern:

1. **Ship a bad model fast** — get something working in production within weeks
2. **Measure the gap** — compare actual performance to requirements
3. **Fix the biggest bottleneck** — which is usually data, not architecture
4. **Repeat** — each iteration fixes the most impactful next problem

Booking.com's key finding: "Teams that spent 6 months building the perfect model failed more often than teams that shipped a 70%-accurate model in 2 weeks and iterated." The reason: the 70% model in production generates real feedback that shapes the next iteration. The perfect model on a laptop generates no feedback.

**What this means for us:** Ship fastText in 2 weeks, measure the actual F1, run error analysis, then decide whether to invest in CNN, BERT, or more data.

---

## Source Coverage

This memo synthesizes findings from the following extraction files (all at `deepl-search/extractions/`):

**Core methodology:** Timoshenko & Hauser (agent01), Jansen et al. (agent01), Bag of Tricks (agent02), fastText (agent02), Query2Interest (agent02), IR evaluation (agent03), XMC (agent03)

**Data & active learning:** JointMap (2005.13783v2), Universal Sentence Encoder (agent02), Timoshenko weak supervision (agent01)

**Transfer learning:** Survey on Transfer Learning, ARALLM (2401.04319v3), LASER (4. Zero-shot transfer), Knowledge Distillation (agent03)

**Architecture:** Deep Unordered Composition, Hashemi CNN, BERT Academic Budget, RNE (agent03), Facebook Embedding Retrieval (agent03)

**Error analysis:** Jansen (agent01), TRENC (2023.findings-acl.474), extraction_index

**ML lifecycle:** Booking.com (150 Successful Models), rules_of_ml, Auto-Sklearn 2.0

**Compute:** How to Train BERT with an Academic Budget, Distributed Deep Learning, Attention Is All You Need
