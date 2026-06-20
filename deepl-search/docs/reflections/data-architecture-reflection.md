# Data Architecture Reflection

Answers to 15 schema and data-model questions about the Deepl Search intent classifier.

---

## 1. What are the entities I created in this project?

| Entity | Files / Locations | Description |
|--------|------------------|-------------|
| **Taxonomy Node (L1–L4)** | `labels/taxonomy/l3l4_mapping.json`, `scripts/run_b9_baseline.py` (L1/L2_DESCRIPTIONS) | 8 L1 × 64 L2 × 512 L3 × 3,843 L4 hierarchy; each node has a name and belongs to a parent |
| **Labeled Record** | `labels/output/labeled_records.jsonl` | 500 MS MARCO queries classified into L1–L4 with confidence, ambiguity flag, rationale |
| **Query** | MS MARCO TSV (`queries.tsv`), `experiments/msmarco_sample.txt` | Raw search query text with optional ID |
| **Session** | `data/session_dataset.jsonl` | 1,000 sessions of 3 sequential queries |
| **Embedding Model** | `models/simcse_query_encoder/`, `models/bi_encoder_labeled/` | Trained all-MiniLM-L6-v2 checkpoints (HF format: config.json, pytorch_model.bin, tokenizer files) |
| **Experiment Result** | `experiments/*.json` (20 files) | Structured JSON with metrics, comparisons, and configuration snapshots |
| **Batch Label Script** | `memory-bank/label_batch1.py` through `label_batch9_10.py` | Python files containing hardcoded query→label mappings per batch |
| **Preprocessing Rule** | `scripts/preprocessor.py` | Spell correction + normalization pipeline (used at inference time, not stored) |

---

## 2. What did I decide deserves to be stored?

Persistent artifacts needed to reproduce or deploy:

- **Taxonomy structure** (`l3l4_mapping.json`, `L1_DESCRIPTIONS` in scripts) — the 4-level hierarchy with real IAB names. Without this, classification is impossible.
- **Human-labeled records** (`labeled_records.jsonl`) — ground truth for training and evaluation. Only 500 exist; they are the bottleneck asset.
- **Model checkpoints** (`models/simcse_query_encoder/`, `models/bi_encoder_labeled/`) — trained weights that encode the learned mapping from query text to intent space.
- **Experiment results** (`experiments/*.json`) — all numeric findings, because each experiment is a falsification test of a premise (per the methodology). Losing an experiment = losing the warrant for a design decision.
- **Session pairs** (`data/session_dataset.jsonl`) — SimCSE pre-training depends on these; they are expensive to regenerate (synthetic session construction from MS MARCO queries).
- **Batch label scripts** (`memory-bank/label_batch*.py`) — the original human classifications. The `.jsonl` is derived from these; the scripts are the audit trail source.
- **AGENTS.md** — session context for AI agents. Losing it means the next AI session starts with zero context.
- **Architecture docs** (`step-*.md`, `final-synthesis.md`, `key-decisions.md`) — the *reasoning* behind every decision, which is more valuable than the decision itself.

---

## 3. What did I treat as raw data?

Data that arrived from outside the project with no project-specific transformations:

| Data | Origin | Size | Usage |
|------|--------|------|-------|
| MS MARCO passage queries | `~\.ir_datasets\msmarco-passage\train\queries.tsv` | 808,731 queries | Input to B9, SimCSE, session construction; raw text never modified |
| IAB Content Taxonomy 3.0 TSV | External file on E: drive | ~5,000 entries (36 Tier-1, 322 Tier-2) | Parsed to build `l3l4_mapping.json` |
| Yahoo! YQT taxonomy structure | Literature (Webscope L18) | 3,843 leaves | Structural inspiration for 8→64→512→3,843 hierarchy (predecessor, now replaced by IAB) |
| The Octohedral Hypothesis | Literature (prior memo) | N/A | Theoretical justification for 8-branching structure |

**Key decision**: MS MARCO queries are treated as immutable. All experiment results are stable under re-runs because the query sample is fixed (`msmarco_sample.txt` has 2,000 deterministic lines from the first 2K rows of the TSV).

---

## 4. What did I treat as generated data?

Data produced by code, not by direct human annotation or external acquisition:

| Data | Generator | Status |
|------|-----------|--------|
| L3/L4 fallback names | `memory-bank/build_real_taxonomy.py` (generate_l3_name, generate_l4_name) | ~40% of names are IAB-sourced, ~60% are generated from L1/L2 context |
| Session dataset | `scripts/build_session_dataset.py` | Synthetic: constructs 3-query sessions from single-query MS MARCO data using heuristic grouping |
| SimCSE contrasts | `scripts/run_simcse_pretraining.py` | Contrastive pairs created by feeding the same query through different dropout masks |
| LLM labels (planned) | `scripts/llm_annotation_pipeline.py` | Not yet generated (blocked by API key). Would be generated data when run. |
| Experiment JSON outputs | Each `run_*.py` script | All files in `experiments/*.json` |

**Distinction from validated data**: Generated data is **not** ground truth. It is used for pre-training (SimCSE), structure (taxonomy), or evaluation (experiment results), but never as labels for the final model (except experiment results → meta-analysis).

---

## 5. What did I treat as validated data?

Data that has been verified against a human standard:

| Data | Validation Method | Status |
|------|------------------|--------|
| 500 labeled records | Human-written classifications in `label_batch*.py` with audit at `labels/audit/labeling_audit.md` | 100% validated. 213 ambiguous flagged explicitly, 0 needing review. |
| B9 baseline on old taxonomy | Cross-checked against Phase 1 generic-description results | Validated as consistent improvement |
| B9 baseline on new taxonomy | Just re-run (2026-06-19) | Numerically valid as self-contained baseline |
| SimCSE downstream eval | Re-ran on new taxonomy | Validated numbers in `experiments/simcse_downstream_eval.json` |
| Bi-encoder eval | 80/20 train/val split, trained on 400, tested on 100 | 53% val accuracy on held-out set |

**Validated = ground truth.** Only the 500 human labels qualify as validated data. Everything else is either raw (unverified) or generated (computed).

---

## 6. What did I treat as derived or computed data?

Data that is a mathematical or algorithmic transformation of other data, not independently collected or annotated:

| Data | Derived From | Computation |
|------|-------------|-------------|
| Query embeddings | Query text | `model.encode(text)` → 384-d vector |
| Class embeddings | Class descriptions | `model.encode(description)` → 384-d vector |
| Cosine similarities | Query + class embeddings | `q_embed @ d_embed.T` |
| Confidence scores | Cosine similarity max | `max(sim(q, all_classes))` |
| Confidence distributions | All 64/3843 cosine similarities | Softmax-normalized similarity vector |
| Effective K | Confidence distribution | Count of classes with >1% prediction share |
| Accuracy / Mean conf | Predictions vs labels | Aggregation statistics |
| MNR loss | (query, positive_desc, batch negatives) | `cross_entropy(sim(q, descs) / T, labels)` |
| Reject coverage curve | Confidence scores over thresholds | `sum(conf >= tau) / N` for each threshold |

**Derived data is ephemeral by design.** Embeddings, similarities, and metrics are recomputed on demand rather than stored. The experiment result files cache the *aggregates* but not the individual embeddings (which would be ~500 MB for all queries).

---

## 7. What relationships did I create between records?

| Relationship | Cardinality | How Expressed | Example |
|-------------|-------------|---------------|---------|
| Query → Label | N:1 (each query has 1 label) | `labeled_records.jsonl`: `record_index` → line in `msmarco_sample.txt` | Query line 42 → label `["Health & Fitness", "Exercise & Workouts", ...]` |
| Label hierarchy | 1:N (L1→L2→L3→L4) | `l3l4_mapping.json`: `A1.B1.C1` → name; label array `["L1", "L2", "L3", "L4"]` | `"Arts & Entertainment"` → `"Visual Arts"` → `"Drawing & Painting"` → `"Drawing & Painting - Detail 1"` |
| Session → Queries | 1:N (1 session = 3 queries) | `session_dataset.jsonl`: `{"queries": [q1, q2, q3]}` | Session with 3 sequential MS MARCO queries |
| Script → Experiment result | 1:1 | Script name + output path convention | `run_b9_baseline.py` → `experiments/b9_baseline_results.json` |
| Model → Eval result | 1:N | Script loads model, writes results JSON | `models/bi_encoder_labeled/` → `experiments/bi_encoder_eval_results.json` |
| Batch script → Labels | N:1 (6 scripts → 1 output) | `rebuild_and_relabel.py` aggregates all batch scripts into `labeled_records.jsonl` | `label_batch1.py` lines 1-100 → records 1-100 in output |
| Audio/Text files → Ranking | Many:1 | `ranking_01.txt` through `ranking_09.txt` reference paper titles | Each ranking file lists the top-N papers for a search term |

**Implicit relationships** (not expressed in data, only in code):
- Query ↔ Session: queries appear in both `msmarco_sample.txt` and `session_dataset.jsonl`, but no cross-reference key exists.
- Experiment ↔ Experiment: B9 → Reject Calibration (chained), SimCSE → Downstream Eval (chained), but no explicit dependency graph.

---

## 8. What metadata did I need for keywords to become useful?

The zero-shot embedding classifier was near-random with generic placeholders ("Intent 1 > Subcategory 1"). The **class descriptions** are the metadata that make keywords useful:

| Metadata | Where Defined | Why Needed | Impact |
|----------|--------------|------------|--------|
| L1 description | `L1_DESCRIPTIONS` in scripts | 1-2 sentence summary of each L1 category | L1 mean conf: 0.067 → 0.086 (+28%) |
| L2 description | `L2_DESCRIPTIONS` in scripts | Full sentence per L2 subcategory with query examples | L2 mean conf: 0.109 → 0.187 (+71%) |
| L3 real name | `l3l4_mapping.json` | IAB-sourced names where available | Better L3/L4 retrieval when extended |
| Category examples (B8) | `CATEGORY_EXAMPLES` in `run_b8_baseline.py` | Example queries per L1 for LLM prompt | Improves LLM few-shot accuracy |
| Query text length | Sampled in `run_b8_baseline.py` | Head/mid/tail stratification | Prevents length bias in LLM evaluation |
| Ambiguity flag | `labeled_records.jsonl` | `"ambiguous": true/false` | Enables stratification by ambiguity in evaluation |
| Confidence/competitors | `labeled_records.jsonl` | `"confidence"`, `"competing_labels"` | Enables hard-case analysis |

**The single most impactful metadata was the L2 description quality.** Replacing generic "Subcategory 4" with "Investing: queries about stocks, bonds, mutual funds, options trading..." moved the classifier from random to meaningful.

---

## 9. What queries did the frontend/API need to answer?

From the architecture docs and experiment designs:

| Query | Answer | Used For | Frequency |
|-------|--------|----------|-----------|
| "What are the top-K intents for query Q?" | K class names + confidence scores | Product API (internal tool) | Per-query |
| "Should I reject or accept this prediction?" | Accept/reject decision + τ threshold | Reject option (ADR-3) | Per-query |
| "What is the L1 category?" | 1 of 8 L1 names | Fallback when L2 confidence < τ | When L2 is rejected |
| "What is the granularity ladder output?" | L4 (if confident) → L3 → L2 → L1 → reject | Progressive refinement | Per-query |
| "Which L1 has highest mean confidence?" | L1 name + mean confidence | Model health monitoring | Every N queries |
| "What is the effective K for this model?" | Integer count of active classes | Model quality check | Per-experiment |
| "How does accuracy vary by L2 class?" | Per-class accuracy table | Model debugging | Per-evaluation |
| "What is the coverage at τ=0.10?" | Percentage of queries accepted | Threshold tuning | Per-reject-calibration |
| "Which queries are most ambiguous?" | List of ambiguous query IDs | Human review targeting | Batch/periodic |
| "How does SimCSE change the confidence distribution?" | Mean, std, percentiles vs baseline | Pre-training evaluation | Per-experiment |

**API not yet implemented** — current state is script-based evaluation, not a deployable API. The queries above are the requirements for the future API.

---

## 10. What data quality problems appeared because the LLM generated too much?

**The LLM annotation pipeline has not been run** (blocked by API key). However, from the problem formulation and experiment plans:

**Anticipated from B8 design:**
- **Prompt injection**: queries containing "ignore previous instructions" or similar. Flagged in schema with `contains_prompt_injection` field.
- **Response parsing failures**: LLM returns "I think this is..." instead of just the category name. Handled by `parse_response()` fallback (fuzzy match) which silently absorbs errors.
- **Label bleeding**: LLM uses knowledge of the taxonomy structure to guess, rather than actual query understanding. Example: query "java" → forced into Computing because that taxonomy slot is missing a strong query match.

**Observed from human labeling (500 records):**
- **42.6% ambiguous** — even humans disagree on ~half the queries. This is a property of the problem, not a data quality issue per se, but it means any L1/L2 accuracy ceiling is <70% without additional signals.
- **Competing labels** — `competing_labels` field captures ties, enabling hard-case analysis.
- **No malformed records** — `malformed_record` always false; the sample extraction was clean.

**From experiment data:**
- **B9 confidence distributions are bimodal** — most queries cluster near 0.05-0.10 confidence with a long tail. The mean is misleading without the full distribution.
- **Effective K varies by model** — vanilla (39), SimCSE (38), trained (25). The trained model's drop is healthy concentration, but without monitoring it could become collapse.

---

## 11. What transformations happened before data became stored?

| Transformation | Applied To | Where | Preserved? |
|--------------|------------|-------|------------|
| MS MARCO TSV → fixed sample | `queries.tsv` → `msmarco_sample.txt` | First 2,000 lines extracted | Yes, sample is committed |
| IAB TSV → parsed taxonomy | `Content Taxonomy 3.0.tsv` → `l3l4_mapping.json` | `build_real_taxonomy.py` parses tab-separated rows | Yes, mapping stored |
| Batch scripts → aggregated labels | 6 scripts → `labeled_records.jsonl` | `rebuild_and_relabel.py` merges all batches | Yes, source scripts + output stored |
| Query length stratification | Full query set → head/mid/tail sample | `run_b8_baseline.py` samples proportionally | No, sample is random each run (seed not fixed in current code) |
| Session construction | Single queries → 3-query sessions | `build_session_dataset.py` groups by heuristic | Yes, `session_dataset.jsonl` stored |
| Label → L2 description mapping | `["Health & Fitness", "Exercise & Workouts"]` → description text | `train_bi_encoder.py` looks up `L2_NAME_TO_DESC` | No, computed at runtime (but deterministic from taxonomy) |
| Embedding → normalized embedding | Raw encoder output → L2-normalized vector | All scripts: `/ np.linalg.norm(...)` | No, computed on demand |
| SimCSE training checkpoint | HF model format → `models/simcse_query_encoder/` | `run_simcse_pretraining.py` saves `pytorch_model.bin` + `config.json` | Yes, model checkpoint stored |
| Bi-encoder training checkpoint | SimCSE model → fine-tuned model | `train_bi_encoder.py` saves best epoch | Yes, model checkpoint stored |

**Not preserved (but could be regenerated):**
- Individual query embeddings (not stored; ~500 MB for all queries)
- Full similarity matrices (O(N × K); ~32 MB for 500×64 but O(N²) for larger)
- Raw LLM responses (not generated yet; would be stored if B8 runs)

---

## 12. What would need to be versioned to make results reproducible?

| Artifact | Versioning Mechanism | Current State |
|----------|---------------------|---------------|
| **Taxonomy** | Version string in `labeled_records.jsonl`: `"taxonomy_version": "deepl-search_v1_L1-L4"` | Present in labels, not in scripts |
| **Model checkpoint** | Git LFS or model registry | Stored in `models/*/` directory, not versioned |
| **Experiment queries** | Fixed sample file | `msmarco_sample.txt` is deterministic (first 2K lines) |
| **Model config** | Hyperparameters captured in experiment JSON | Present in `bi_encoder_training_results.json` (epochs, lr, batch_size, temperature) |
| **Training script version** | Git commit hash | Not recorded in experiment JSON |
| **Labeling audit** | Commit hash + timestamp in `labeling_audit.md` | Present with labeling dates |
| **Python environment** | `requirements.txt` or `pyproject.toml` | **Missing** — critical gap. Current setup requires knowing `sentence-transformers==2.7.0` + transformers + torch |
| **Random seeds** | Fixed seeds in code | SimCSE: no seed. Bi-encoder: `np.random.seed(42)`. B8: random.sample with no seed. **Inconsistent.** |
| **LLM model + prompt** | Model name + prompt text in script | `run_b8_baseline.py` captures model name but prompt is hardcoded. If the prompt changes, results change. |

**Minimal reproducible experiment spec (what I'd freeze for a paper):**
1. Git commit hash
2. `requirements.txt` (Python deps with pinned versions)
3. `msmarco_sample.txt` (fixed query sample)
4. `labels/output/labeled_records.jsonl` (fixed labels)
5. Seed value for all random operations
6. Taxonomy version string
7. For LLM experiments: exact prompt template + model name + temperature + max_tokens

---

## 13. What parts of the database could become training data?

| Data | Could Train | Suitability | Gap |
|------|------------|-------------|-----|
| 500 labeled records (L1-L4) | Bi-encoder (MNR) | **Currently used** — 400 train / 100 val | Need more labels for commercial-grade model |
| Unlabeled MS MARCO queries (808K) | SimCSE pre-training | **Currently used** — 20K used for SimCSE | Remaining 788K are unused; could extend pre-training |
| Session pairs (1,000 × 3) | SimCSE (supervised variant) | **Currently used** — evaluation only | Could be training data instead of eval-only |
| Class descriptions (64 L2) | Bi-encoder (MNR positives) | **Currently used** — encoded to match queries | Descriptions are hand-written; could be optimized |
| Rejected queries (from reject option) | Hard-negative mining | Not yet used | Queries where model had low confidence are the most valuable training examples |
| Ambiguous queries (213 of 500) | Multi-label classification | Not yet used | Current training treats them as single-label; could use competing_labels |
| LLM-generated labels (planned, ~1K-5K) | Distillation / co-training | Not yet generated | Would need human calibration per ADR-5 |
| B8 LLM responses (planned) | Weak supervision / label model | Not yet generated | Could apply Snorkel-style labeling functions |

**Training data gap**: The bi-encoder uses only L2 descriptions as positive pairs. It ignores:
- L3/L4 descriptions (finer granularity)
- Session context (ADR-1 says it matters)
- Competing labels (multi-label signal)
- Rejected queries (hard negatives)

---

## 14. What parts of the database are product state rather than ML data?

| Artifact | Classification | Rationale |
|----------|---------------|-----------|
| Model weights (`models/*/`) | **ML Data** | Directly encode the learned function; versioning needed |
| Experiment results (`experiments/*.json`) | **ML Data** | Required for model selection and threshold tuning |
| Taxonomy (`l3l4_mapping.json`, L1/L2_DESCRIPTIONS) | **Product State** | The class definitions ARE the product; they define what the system can recognize. Changing the taxonomy changes the product. |
| Reject threshold τ | **Product State** | Determines coverage/accuracy tradeoff; set by business requirement, not ML |
| Granularity ladder fallback order | **Product State** | L4→L3→L2→L1→reject is a product decision, not an ML decision |
| Confidence interpretation guide (mapping conf scores to "high/medium/low") | **Product State** | Post-hoc interpretation layer; depends on user-facing expectations |
| Model training code (`scripts/train_bi_encoder.py`) | **Neither** (infrastructure) | Not data, not product; it's the transformation pipeline between them |
| Labeling audit (`labels/audit/labeling_audit.md`) | **ML Data** | Validates the training data quality |
| AGENTS.md | **Product State** (operational) | Session context for maintainers; not part of the ML pipeline |

**Boundary case**: The taxonomy lives at the boundary. It is simultaneously:
- **ML data** (the output space Y in the function f: X → Y)
- **Product state** (the set of things the product can identify)

Changing a class name affects both model training and product semantics. The `taxonomy_version` field in `labeled_records.jsonl` is the correct mechanism to track this, but it needs to be propagated to the model training pipeline.

---

## 15. What schema decisions forced a particular interpretation of the problem?

| Decision | Schema Element | Interpretation Imposed | Alternative Foreclosed |
|----------|---------------|----------------------|----------------------|
| Fixed 8×8×8 structure per L1 | Each L1 has exactly 8 L2, each L2 has exactly 8 L3 | Intents are uniformly distributed across the hierarchy | Variable branching (more specific L1s have more L2s). This compresses some L1s and stretches others. |
| 4-level hierarchy | `label: [L1, L2, L3, L4]` | Intent is a path from root to leaf | Flat classification (predict 1 of 3843 directly). Hierarchical softmax without 4-level constraint. |
| L2 as primary training target | Bi-encoder trained on L2 descriptions only | L2 is the "sweet spot" for the model | Training at L4 (too sparse) or L1 (too coarse). Pre-judges which level the model can learn. |
| Single label per query | `label[0]` is the primary intent | Every query has exactly one correct intent | Multi-label classification. 42.6% of labels are ambiguous → single-label is a simplification. |
| 500-record fixed sample | `msmarco_sample.txt` has exactly 2,000 lines | 500 labels are representative of 808K queries | Stratified random sample. Fixed sample can't capture rare classes or temporal drift. |
| Reject option as threshold | `confidence >= τ` → accept, else reject | All low-confidence predictions are equally unreliable | Class-specific thresholds (some classes need higher confidence). |
| Bi-encoder + cosine similarity | `q_embed @ d_embed.T` | Intent is about semantic similarity in embedding space | Cross-encoder (direct relevance scoring), or logistic regression on embeddings. |
| MNR loss (in-batch negatives) | `sim(q_i, d_j) for all i,j in batch` | All non-matching descriptions in a batch are negatives | Hard negative mining, or cross-batch negatives. MNR works well but the quality of negatives depends on batch composition. |
| SimCSE pre-training (unsupervised) | Same-query, different-dropout pairs | Query-dropout pairs are a useful pre-training signal | Supervised pre-training (another task), or no pre-training. |
| IAB-based taxonomy replacing YQT | L2 names from 2026 mapping | The "real" categories are the IAB Content Taxomony 3.0 classes | YQT names (old), or domain-specific names, or learned clusters. |
| Explicit "ambiguous" flag | `ambiguous: true/false` in labeled records | Ambiguity is binary | Continuous ambiguity score, or multi-label with all competing intents. |

**The most consequential schema decision**: fixing the hierarchy at 8×8×8 per L1. This imposes uniform granularity — `Shopping & Commerce` has the same number of L2 slots as `Arts & Entertainment`, regardless of whether commercial search intent is naturally more diverse. The taxonomy structure encodes a strong prior about the geometry of search intent.
