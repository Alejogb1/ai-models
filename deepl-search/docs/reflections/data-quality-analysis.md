# Data Quality Analysis

Every data-quality issue in the system, ranked by severity and assessed for impact.

---

## Executive Summary

The system has **three active data-quality problems** that degrade current results, **two latent problems** that will activate at deployment, and **one healthy property** that looks like a problem but isn't. The rest of the checklist items are not present or are already resolved.

**Active (degrading current results):**
1. Ambiguity ceiling (42.6% of queries are inherently ambiguous)
2. Single-annotator labels (no inter-annotator agreement)
3. Label distribution skew (first-2K sample bias)

**Latent (will activate at deployment):**
4. Temporal distribution shift (MS MARCO c. 2016-2018 → deployment c. 2026)
5. Generated L3/L4 names (harmless now, harmful if used as training targets)

**Not problems (or already handled):**
- Malformed records → zero found
- Taxonomy mismatch → resolved by re-running baselines
- Missing provenance → documented in build script

---

## 1. Ambiguous Queries (Active — High Severity)

**What it is:** 213 of 500 labeled queries (42.6%) are flagged `ambiguous: true`. These are queries where the annotator identified at least one plausible alternative intent.

**Examples from the data:**
- Query about "marking a collection posted on eBay" → labeled Shopping & Commerce / Toys & Hobbies, competing with Books & Media. Two valid interpretations.
- "What is a public nfp entity" → definition question, but straddles Business & Finance (accounting) and Education & Reference (research). The annotator chose Education & Reference with confidence 0.9, but a business-domain user might disagree.

**Why it's fundamental:** Search queries average 2-4 words. At that length, homonymy is irreducible. "Java" (coffee / programming / island), "windows" (OS / home improvement), "apple" (fruit / company). A system that forces every query into one category is wrong 42.6% of the time by construction.

**Impact on metrics:**
- Single-label L2 accuracy ceiling: ~57% (100% - 42.6% ambiguous). The current bi-encoder achieves 74.8%, which suggests it exceeds the theoretical ceiling. This means either: (a) the ambiguous flag is conservative (many "ambiguous" queries have a clearly dominant intent), or (b) the model's L2 predictions happen to match the annotator's primary choice even when alternative intents exist.
- Multi-label evaluation would show different results — the competing labels probably have meaningful similarity scores.

**What to do about it:**
- Evaluate with multi-label metrics (compute recall@K on `competing_labels`)
- Report accuracy stratified by ambiguous/non-ambiguous to see the actual gap
- Consider multi-label training: for ambiguous queries, treat all `competing_labels` as positive

**Stratification (from the labels):**

```
Total:         500
Non-ambiguous: 287 (57.4%)
Ambiguous:     213 (42.6%)
Needs review:    0 (0.0%)
```

The 0% needs-review rate is notable — the annotator never felt unable to classify. This suggests ambiguity is "there are multiple valid answers, but this one is best," not "I have no idea what this query means."

---

## 2. Single-Annotator Labels (Active — Medium-High Severity)

**What it is:** All 500 labels were written by one person. There is no inter-annotator agreement check. The `competing_labels` field captures some self-reported alternatives, but it's not a second opinion.

**Why it matters:**
- Without a second annotator, we don't know the label noise rate. The 74.8% bi-encoder accuracy might be partially overfitting to one person's labeling idiosyncrasies.
- Example: one annotator might systematically classify "how to X" queries as How-To Guides while another might put them under their topical L2 (e.g., "how to fix a leaky faucet" → Home & Garden for one annotator, How-To Guides for another).
- The 42.6% ambiguity rate is self-reported by the same annotator. A second annotator might flag different queries as ambiguous, or disagree on the primary label entirely.

**Quantifying the risk:**
- Typical inter-annotator agreement for intent classification on short text: 70-85% (Cohen's κ = 0.6-0.75 for 8-way L1; lower for 64-way L2).
- If true agreement is 75% at L2, then ~25% of labels have annotator-specific bias. The model's 74.8% accuracy would partially reflect memorizing the primary annotator's preferences, not learning generalizable intent patterns.
- The 100-query validation set was labeled by the same annotator, so validation accuracy measures agreement with that annotator, not ground truth.

**What to do about it:**
- Have a second annotator label a random 50-100 query subset (ideally from the existing 500, to measure agreement)
- Report Cohen's κ for L1 and L2
- If κ < 0.7, the label budget should prioritize double-labeling over new single-labeled data

---

## 3. Label Distribution Skew (Active — Medium Severity)

**What it is:** The 500 labeled queries are the first 500 from `msmarco_sample.txt`, which itself is the first 2,000 lines of the MS MARCO TSV. MS MARCO's ordering is by doc ID (alphanumeric sort of passage IDs), not random. This creates an ordering bias.

**Measured L2 distribution from the 500 labels:**

```
L2 classes used: 48 of 64 (75% coverage)
Most common L2:  Dictionaries & Thesauri (~30+ occurrences)
Least common L2: Comics & Animation, Cloud & DevOps, Senior Health, Food Science (~1-2 each)
```

**Implications:**
- Some L2 classes have very few training examples (1-2 for the tail). The bi-encoder's MNR loss doesn't see them as positives very often.
- If the first 2K MS MARCO queries happen to be predominantly about definitions (dictionary queries), the model will be biased toward Education & Reference.
- The effective K of 25 (bi-encoder) reflects this — it may indicate the model is only learning the well-represented classes.

**Comparison with expected natural distribution:**
MS MARCO is a passage-retrieval dataset, not an intent dataset. Its query distribution reflects what people search when they need a specific fact from a document — which skews toward definitional and informational queries (Education & Reference, Dictionaries & Thesauri, Academic Subjects). Transactional and commercial queries (Shopping & Commerce, Travel & Local) are underrepresented.

**What to do about it:**
- Stratify future labeling: explicitly sample queries with rare L1/L2 keywords
- Report per-class accuracy to identify which classes the model is missing
- Consider class-weighted training or oversampling for tail classes
- Compare label L2 distribution against the full MS MARCO B9 prediction distribution (47 classes with >1% share) to detect skew

---

## 4. Temporal Distribution Shift (Latent — Will Activate at Deployment)

**What it is:** MS MARCO was collected in 2016-2018. The model would deploy on 2026 queries. Eight years of linguistic and cultural change create systematic prediction errors for anything new.

**Examples of post-2018 terms not in MS MARCO:**

| Term | Emerged | Correct L2 | Risk |
|------|---------|-----------|------|
| "NFT" | 2021 | Investing (or Digital Art) | Would map to nearest embedding neighbor, likely wrong |
| "semaglutide" / "Ozempic" | 2021 | Medications | No occurrences in training data |
| "AI assistant" (as distinct from "AI") | 2023 | AI & Data | Synonyms may not embed near training queries |
| "remote work" (surge in 2020) | 2020 | Careers & Jobs | Few if any MS MARCO examples |
| "TikTok" | 2018+ | Celebrities (or Social Media) | Brand new since MS MARCO |

**Why it matters now:**
- The bi-encoder was trained only on 2016-2018 queries. It has never seen embeddings for post-2018 vocabulary.
- The SimCSE pre-training was also on MS MARCO, so it doesn't help with temporal shift.
- When deployed, queries containing novel terms will have nearest-neighbor matches based on unrelated semantic dimensions.

**Quantifying (theoretical):**
- Word embedding drift for consumer vocabulary: ~5-10% of the vocabulary changes meaning or importance per year (measured by embedding stability studies).
- Over 8 years: ~40-80% of the semantic space could have shifted.
- Not all shifts matter (most words are stable), but high-frequency search terms are precisely the ones that shift most (technology, culture, brands).

**What to do about it:**
- Before deployment: collect a sample of 2026 queries and measure the accuracy gap vs 2016 MS MARCO
- If the gap is >10%: fine-tune on a mix of old + new queries
- Long-term: set up a continuous labeling pipeline to catch drift early
- The B8 LLM baseline (when run) will be immune to temporal shift (LLMs are trained on recent data) — use it as a "no-drift" comparison point

---

## 5. Generated L3/L4 Names (Latent — Low Severity for Now)

**What it is:** The `l3l4_mapping.json` has ~60% of L3/L4 names generated from L1/L2 context, not sourced from IAB. From `build_real_taxonomy.py`:

```python
# generate_l3_name: prefers IAB name, falls back to template
if iab_names and l3_idx < len(iab_names):
    return iab_names[l3_idx]
return l3_ideas.get(l2_name, [f"{l2_name} - Topic {l3_idx+1}"])[l3_idx % 8]
```

**Why it's not a problem yet:** The bi-encoder trains only on L2 descriptions. L3/L4 names are unused for training. They only appear in the label record (for provenance) and in potential future extensions.

**When it would become a problem:**
- If training extends to L3/L4: generated names like "Board Games and Puzzles - Detail 1" carry no semantic signal. Using them as positive pairs would teach the model to associate queries with boilerplate text.
- If evaluating L3/L4 accuracy: generated names make the evaluation meaningless (the labels use these names, so the model would appear to match them, but it's matching noise).
- If the L3 name conflicts with a real L2 name (e.g., "Academic Papers" appears as both an L2 under Education & Reference — Research, and as an L3 name under Research). This creates embedding collisions.

**What to track:**
- The ratio of IAB-sourced vs generated names per L1 (some L1s like Arts & Entertainment have richer IAB coverage than others)
- Any L3/L4 evaluation should use only IAB-sourced names and flag generated-name evaluations as unreliable
- If L3/L4 training is planned, the taxonomy needs a second pass with real names (another IAB parsing pass, or LLM-based name generation)

---

## 6. Synthetic Session Data (Latent — Active if Sessions Used for Training)

**What it is:** The session dataset (`data/session_dataset.jsonl`, 1,000 sessions of 3 queries) is constructed by `build_session_dataset.py` using a heuristic grouping strategy, not from real user sessions. The heuristic — grouping queries by similarity or random adjacency — creates sessions that may not reflect real search behavior.

**Current usage:** Sessions are used only for SimCSE evaluation (measuring query-to-query similarity before/after pre-training). They are not used for training.

**Impact on evaluation:**
- The SimCSE "improvement" (+13.3% session pair similarity) was measured on synthetic sessions. Real user sessions have:
  - Topic drift (user switches from "buy running shoes" to "weather forecast")
  - Reformulation (user repeats same query with different wording)
  - Abandonment (session ends without resolution)
- Synthetic sessions lack all three behaviors. The +13.3% might not transfer to real session patterns.
- The downstream eval (L1/L2 confidence improvement) is independent of sessions and unaffected.

**What to do:**
- Before deploying session-based features (ADR-1): validate on real session data if available, or simulate more realistic session trajectories
- For now: continue using sessions only for evaluation, not training

---

## 7. Missing Provenance Tracking (Minor — Easy to Fix)

**What it is:** Several artifacts lack provenance metadata:

| Artifact | Missing | Current |
|----------|---------|---------|
| L3/L4 names | Per-name source tag (IAB vs generated) | Only aggregate count (`iab_sourced_l3`) printed during build |
| Labeled records | Annotator identity, labeling session ID | No field in schema |
| Training data | Which label records vs which raw queries | Implicit via `record_index` |
| Experiment results | Git commit hash of running script | Not recorded in result JSON |
| Random seeds | Seed value used for each random operation | Inconsistent across scripts |
| Python environment | Pinned dependency versions | No `requirements.txt` |

**Why it matters:** Without provenance, you can't answer "did changing X affect Y?" — the core question of experiment-driven development. If someone re-runs `train_bi_encoder.py` with a different batch ordering (different seed), the 74.8% accuracy might become 72% or 77%.

**Easy fixes:**
- Add `seed` to every script that uses randomness (make it configurable, default=42)
- Add `_provenance: {commit_hash, script_name, timestamp, seed}` to every experiment JSON output
- Add `annotator_id` to future labeled records
- Create `requirements.txt` with pinned versions

---

## 8. No Malformed Records (Not a Problem)

**What it is:** All 500 labeled records have `malformed_record: false` and `needs_human_review: false`. The raw MS MARCO TSV is clean (tab-separated, well-formed). The IAB taxonomy TSV has two header rows and a consistent schema.

**Why it's clean:** The data sources are professional datasets (MS MARCO, IAB Content Taxonomy). They have undergone their own quality control. The labeling process was manual (batch scripts), not automated, so no malformed output from a brittle pipeline.

**Not a problem now, but:** If the LLM annotation pipeline runs (B8), malformed records will appear:
- JSON parse failures in LLM output (trailing commas, unescaped quotes)
- Out-of-taxonomy categories hallucinated by the LLM
- Empty responses (rate limiting, API errors)

The schema already has `contains_prompt_injection` and `malformed_record` fields for this. The B8 script's `parse_response()` handles the common failure modes. This is **well-scoped risk**.

---

## 9. Taxonomy Mismatch (Resolved)

**What it was:** All Phase 1 and early Phase 2 experiments (B9, reject calibration) used the old YQT taxonomy (Autos & Vehicles, Health & Medical, Home & Garden, Shopping & E-commerce, Sports & Recreation). The labels, SimCSE eval, and training use the new IAB-based taxonomy (Computers & Technology, Food & Dining, Health & Fitness, Shopping & Commerce, Travel & Local).

**Resolution:**
- B9 baseline re-run with new taxonomy ✓
- Reject calibration re-run with new B9 ✓
- SimCSE downstream eval re-run with new taxonomy ✓
- Old results marked as stale in AGENTS.md ✓
- All three scripts updated with new L1/L2 descriptions ✓

**Remaining gap:** The old experiment result files (`experiments/b9_baseline_results.json`, `experiments/reject_calibration_results.json`) have been overwritten with new results. The old numbers are only recoverable from git history.

---

## Summary: Quality Scorecard

| Issue | Severity | Status | Mitigation |
|-------|----------|--------|------------|
| Ambiguous queries | High | Active | Multi-label eval, stratified reporting |
| Single annotator | Medium-High | Active | Second annotator, Cohen's κ |
| Label distribution skew | Medium | Active | Stratified sampling for next batch |
| Temporal shift | Medium | Latent | Pre-deployment gap measurement |
| Generated L3/L4 names | Low | Latent | Don't train on L3/L4 without fixing |
| Synthetic sessions | Low | Latent | Validate on real sessions before using for training |
| Missing provenance | Low | Active | Add to experiment JSON schema |
| Malformed records | None | Not present | Schema already handles LLM failure modes |
| Taxonomy mismatch | None | Resolved | Baselines re-run with new taxonomy |

**The one quality issue that matters most right now:** **Single-annotator labels.** All 500 records, the 74.8% accuracy figure, the 84.8% L1 accuracy, every training and evaluation decision — everything rests on one person's judgment. A second annotator on 50-100 queries would tell us whether the model is learning real patterns or one person's preferences.
