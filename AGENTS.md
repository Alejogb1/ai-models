# AGENTS.md — Project Context for AI Sessions

## Project: AI Search Query Intent Classifier

Build a hierarchical intent classifier for search queries (8 L1 → 64 L2 → 512 L3 → 3,843 L4 classes) using bi-encoder retrieval with session-level input, spell correction, reject option, and LLM-as-annotator.

## Taxonomy (IAB-based, migrated from YQT)

| L1 | L2 (8 per L1) |
|----|---------------|
| Arts & Entertainment | Visual Arts, Performing Arts, Music, Movies, TV, Literature, Comics & Animation, Celebrities |
| Business & Finance | Investing, Banking, Insurance, Real Estate, Accounting, Small Business, Careers & Jobs, Economy |
| Computers & Technology | Software, Hardware, Programming, Networking, Cybersecurity, AI & Data, Mobile, Cloud & DevOps |
| Education & Reference | K-12, Higher Education, Online Learning, Research, Dictionaries & Thesauri, How-To Guides, Academic Subjects, Test Prep |
| Food & Dining | Restaurants, Recipes, Cooking Tips, Beverages, Nutrition, Cuisine Types, Dining Out, Food Science |
| Health & Fitness | Exercise & Workouts, Mental Health, Medical Conditions, Medications, Alternative Medicine, Nutrition & Diet, Wellness, Senior Health |
| Shopping & Commerce | Clothing, Electronics, Home & Garden, Beauty Products, Sports Gear, Books & Media, Toys & Hobbies, Groceries |
| Travel & Local | Destinations, Hotels, Flight Booking, Public Transit, Maps & Navigation, Local Services, Events, Weather |

Dropped from old YQT: Autos & Vehicles, Home & Garden (now under Shopping), Sports & Recreation.

## Architecture (ADRs)

| ADR | Decision | Experiment Warrant |
|-----|----------|-------------------|
| 1 | Session input (N=3, [SEP] concat) | Exp 1: 87.6% prediction change |
| 2 | SymSpell preprocessor | Exp 11: 82.5% change from misspellings |
| 3 | Reject option + granularity ladder | Exp 12: 0% coverage at τ=0.5 |
| 4 | Bi-encoder retrieval (cosine sim) | Exp 5: 47.7 mean non-zero labels/query |
| 5 | LLM-as-annotator primary + human calibration | Step 3: 50x cheaper, 500K labels for ~$10 |
| 6 | Effective K=200-300, expand from L2 | Step 3: each class needs ~67 examples |

## Completed Experiments

### Phase 1 (zero-cost, already done)
- Exp 1: Session → FALSIFIED
- Exp 3: Granularity → WEAKENED
- Exp 5: Paradigm → WEAKENED
- Exp 6: F1 → HOLDS
- Exp 11: Spell correct → FALSIFIED
- Exp 12: Reject option → FALSIFIED

### B9 Baseline (stale — used old YQT taxonomy, must re-run)
- Replaced generic placeholders with realistic descriptions (old YQT names)
- L1 mean conf: 0.092 (vs 0.067 in Phase 1)
- L2 mean conf: 0.190 (vs 0.109 in Phase 1)
- L2 effective K: 43/64 classes >1% share

### Reject Calibration (stale — based on old B9, must re-run)
- Best L2 operating point: τ=0.10 gives 86.5% coverage
- Granularity ladder barely helps (L1 even worse than L2)
- Full results: experiments/reject_calibration_results.json

### SimCSE Pre-training (valid for new taxonomy — architecture-agnostic)
- Trained all-MiniLM-L6-v2 with SimCSE loss on 20K MS MARCO queries (2 epochs, T=0.5)
- Session pair similarity: +13.3% (0.322 → 0.364)
- **Downstream L2 mean confidence: +51%** (0.190 → 0.286), max: 0.525 → 0.723
- **Downstream eval re-run with new taxonomy:** L1 mean conf 0.094 → 0.150 (+59%), L2 max 0.525 → 0.723
- Effective K dropped: 42 → 35 classes >1% (possible concentration)
- Results: experiments/contrastive_pretraining_results.json, experiments/simcse_downstream_eval.json

### 500 Human Labels Created
- 500 MS MARCO queries classified into full L1–L4 hierarchy using IAB-based taxonomy
- 213 ambiguous (42.6%), 0 needing human review
- Labeled via batch scripts (memory-bank/label_batch1.py – label_batch9_10.py)
- Output: labels/output/labeled_records.jsonl
- Audit: labels/audit/labeling_audit.md, Summary: labels/reports/summary.md

### Phase 6: Bi-Encoder Training on 500 Labels (done)
- MNR loss: positive (query, L2_description) pairs, in-batch negatives
- Started from SimCSE-pretrained all-MiniLM-L6-v2, 10 epochs, lr=2e-5, T=0.05
- **L2 accuracy on 500 queries: 74.8%** (vs 24.4% vanilla, vs 28.2% SimCSE-only)
- **L1 accuracy: 84.8%** (vs 44.6% vanilla)
- **Mean confidence: 0.428** (vs 0.191 vanilla, vs 0.294 SimCSE)
- Effective K dropped to 25 (healthy concentration)
- Results: experiments/bi_encoder_training_results.json, experiments/bi_encoder_eval_results.json

## Scripts Available

| Script | Input | Output | Run condition |
|--------|-------|--------|---------------|
| `scripts/run_b8_baseline.py` | MS MARCO queries (auto) | experiments/b8_baseline_results.json | Needs LLM API key |
| `scripts/analyze_b8_baseline.py` | B8 results + cross model | Console + analysis | After B8 results exist |
| `scripts/run_b9_baseline.py` | MS MARCO queries | experiments/b9_baseline_results.json | Self-contained (sentence-transformers) |
| `scripts/run_reject_calibration.py` | B9 results | experiments/reject_calibration_results.json | After B9 |
| `scripts/run_simcse_pretraining.py` | MS MARCO queries + sessions | models/simcse_query_encoder/ | Self-contained |
| `scripts/build_session_dataset.py` | MS MARCO queries | data/session_dataset.jsonl | Self-contained |
| `scripts/preprocessor.py` | Import module | N/A | Reusable import |
| `scripts/llm_annotation_pipeline.py` | MS MARCO queries | data/llm_labeled_queries.jsonl | Needs LLM API key |
| `scripts/train_bi_encoder.py` | 500 labeled records | models/bi_encoder_labeled/ | Self-contained (transformers) |
| `scripts/evaluate_bi_encoder.py` | 500 labeled records | experiments/bi_encoder_eval_results.json | After bi_encoder_labeled exists |

## Key Files

- `key-decisions.md` — Beginner-friendly explanation of all decisions, terms, and concepts
- `final-synthesis.md` — Architecture specification with 6 ADRs, risk register, document map
- `step-2-problem-derivation.md` — Formal specification: X, Y, loss function
- `step-3-learnability-analysis.md` — Sample complexity, irreducible error, PAC bounds
- `step-4-baseline-establishment.md` — 9 baselines (random to LLM), decision rules
- `step-5-evaluation-protocol.md` — CW-F1, stratification, calibration, robustness
- `experimental-premise-resolution.md` — 12 premises, Phase 1 results, decision log

## Data

- MS MARCO train: 808,731 queries (C:\Users\ALEJOO\.ir_datasets\msmarco-passage\train\queries.tsv)
- Session dataset: 1,000 sessions × 3 queries (data/session_dataset.jsonl)
- Human labels: 500 records with full L1-L4 hierarchy (labels/output/labeled_records.jsonl)
- Experiments: experiments/*.json

## Running Experiments

For LLM-dependent scripts (B8, annotation pipeline):
```
$env:LLM_API_BASE = "https://api.groq.com/openai/v1"
$env:LLM_API_KEY = "gsk_your_key_here"
$env:LLM_MODEL = "llama3-70b-8192"
python scripts/run_b8_baseline.py
```

For self-contained experiments:
```
python scripts/run_b9_baseline.py
python scripts/build_session_dataset.py
```

## Next Actions (Priority Order)

1. **Run B8 baseline** (needs LLM API key) — sets "worth training" threshold
2. **Run B8 cross-model agreement** (different LLM, same queries) — lower bound on label reliability
3. **Run LLM annotation pipeline** to create 1K-5K labels (for comparison with existing 500 human labels)
4. **Create more labeled data** (target 1K-2K human labels) to further improve bi-encoder
5. **Investigate SimCSE effective K drop** (42 → 35) — is it concentrating or collapsing?
