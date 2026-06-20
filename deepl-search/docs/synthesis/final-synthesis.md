# Final Synthesis: From Problem Formulation to Architecture

> This document synthesizes Steps 1-5 and the Phase 1 experiments into a unified
> architecture specification. Every design choice is traced to its warrant.
> Every assumption has a revision trigger.

---

## 1. The Problem (Restated)

Given a search session (current query + prior context), predict the user's intent at the appropriate granularity, with a reject option for uncertain cases, and flag commercial intent.

**The problem is learnable** if we target $K_{\text{eff}} \approx 200$-$300$ and use session-level input. At $K=3843$ with a $10K+$ label budget, it is not learnable — the tail classes will have <5 examples each.

---

## 2. What We Know (Empirically)

Phase 1 experiments on 2K MS MARCO queries with the embedding classifier:

| Finding | Source | Severity |
|---------|--------|----------|
| Session context changes 87.6% of predictions | Exp 1 | Query alone is insufficient |
| Misspellings change 82.5% of predictions | Exp 11 | Preprocessing is essential |
| No query has confidence >0.5 | Exp 12 | Reject option is essential |
| L1 self-consistency only 72.8% | Exp 3 | Effective K < 3843 |
| Mean 47.7 non-zero labels per query | Exp 5 | Retrieval > classification |
| Zero-shot classifier = near-random (0.07-0.14) | Exp 3 | Generic descriptions cripple the classifier |
| F1 and cost-weighted F1 rank models identically | Exp 6 | F1 is a sufficient proxy (with caveats) |

---

## 3. Architecture Specification

### 3.1 Data Pipeline

```
Raw Session (N=3 queries)
    │
    ▼
[Spell Correction] ─── SymSpell, max edit distance 2
    │                   (Exp 11: 82.5% change rate → essential)
    ▼
[Query Normalization] ─ Case, punctuation, number normalization
    │
    ▼
[Session Concatenation] ── "q1 [SEP] q2 [SEP] q3"
    │                       (Exp 1: 87.6% prediction change → essential)
    ▼
[Behavioral Features] ── device_type, hour, session_length
    │                    (optional, zero-padded if missing)
    ▼
[Bi-Encoder Query Encoder] ── all-MiniLM-L6-v2 (or fine-tuned variant)
```

### 3.2 Model Architecture

```
Query Text ──► [Query Encoder (BERT)] ──► q_embed (384d)
                                                │
Class Descriptions ──► [Class Encoder (shared)] ──► C_embeds (K × 384d)
                                                │
                                                ▼
                                    [Cosine Similarity]
                                                │
                                                ▼
                                    [Hierarchical Softmax]
                                    L1 (8) ← L2 (64) ← L3 (512) ← L4 (3843)
                                                │
                                    ┌───────────┴───────────┐
                                    ▼                       ▼
                            [Commercial Flag]        [Reject Option]
                            (threshold on           (confidence < τ → reject,
                             sum over                 fall back to coarser level)
                             commercial classes)
```

### 3.3 Training Strategy

| Phase | Objective | Data | Duration |
|-------|-----------|------|----------|
| Contrastive pre-training | Session structure (same-session = positive pairs) | Unlabeled session logs | 1 week |
| Supervised fine-tuning L1+L2 | Hierarchical CE loss with level weights | Labeled queries (20K+) | 2 weeks |
| L3-L4 expansion | Fine-tune on more granular labels | Additional labels (10K+) | 1 week |
| Active learning loop | Targeted acquisition for uncertain queries | Model uncertainty scores | Ongoing |

### 3.4 Deployment Architecture

```
Request ──► [Preprocessor] ──► [Bi-Encoder] ──► [Confidence Check]
                         spell-correct +     q_embed @ C_embeds    │
                         normalize + concat                        ▼
                                                          Threshold ≥ τ_l?
                                                         ┌────┴────┐
                                                         Yes       No
                                                         │         │
                                                         ▼         ▼
                                                    Return L4   τ_{l-1} check
                                                    prediction → ... → reject
```

### 3.5 Evaluation Stack

| Stage | Metric | Gate |
|-------|--------|------|
| Training | CW-F1 on validation set | > previous best |
| Model selection | Stratified report (head/mid/tail) | Tail/head ratio > 0.50 |
| Pre-production | Full robustness suite | All robustness targets met |
| Shadow | Behavioral validation (click rate) | No regression vs baseline |
| Canary (1%) | A/B test vs production | Statistically significant win |

---

## 4. What's Different from the Original Design

| Original | Now | Why |
|----------|-----|-----|
| Train at K=3843 | Train at K=200-300, expand later | Exp 3: only 1/3843 classes gets >1% of queries |
| Query-only input | Session input (N=3) | Exp 1: 87.6% prediction change with context |
| Softmax classification | Bi-encoder retrieval | Exp 5: 47.7 mean labels/query; retrieval is natural fit |
| Raw text input | Spell-corrected + normalized | Exp 11: 82.5% change from misspellings |
| Always predict a class | Reject option + granularity ladder | Exp 12: 0% coverage at τ=0.5 |
| Single-output model | Multi-task (intent + commercial + session length) | Step 2 §5.2: multi-task improves representations |
| 6-month timeline, sequential | Contrastive pre-training (immediate) + active learning (ongoing) | Step 3 §4.2: marginal returns guide allocation |
| Human labels as sole signal | LLM-as-annotator (primary) + human validation (calibration) | Step 3 §6.2: 50x cheaper, enables 500K labels |

---

## 5. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Distribution shift from training to deployment | High | High | Continuous drift monitoring (Step 5 §5.1); online centroid updates (Door 13.2) |
| LLM-as-annotator produces biased labels | Medium | High | Human validation set (5K queries) for calibration; measure LLM-human agreement |
| Session encoder adds noise (context from unrelated prior query) | Medium | Medium | Ablation study (Step 5 §5.3); train with session masking |
| Effective K is still too high (200-300 not feasible with 20K labels) | Low-Medium | Medium | Fall back to L1+L2 only; target L1=8, L2=64 first |
| Embedding classifier with real descriptions still underperforms LLM | Medium | High | Deploy LLM classifier as production; training must beat it (Step 4 §3) |
| Annotation budget insufficient for 20K labels | Low | Medium | Use LLM-as-annotator (500K labels for ~$10); human budget is for calibration only |

---

## 6. Next Actions

### Immediate (Week 1-2)
- [ ] Install SymSpell and integrate into preprocessing pipeline (Exp 11 finding)
- [ ] Run B8 (LLM zero-shot baseline) on 500 queries — requires API key (~$0.50)
- [ ] Replace generic taxonomy descriptions with improved names and measure B9
- [ ] Set up contrastive pre-training on session logs (unlabeled data is abundant)

### Short-Term (Week 3-4)
- [ ] Run Exp 4: inter-annotator agreement study ($200, 200 queries, 3 annotators each)
- [ ] Run Exp 2: LLM context augmentation on 500 ambiguous queries ($5)
- [ ] Acquire first 1K human-labeled queries for seed training data
- [ ] Train initial L1+L2 model; evaluate against LLM baseline

### Medium-Term (Month 2-3)
- [ ] Scale to 20K+ labels (LLM-as-annotator pipeline)
- [ ] Expand to L3 granularity
- [ ] Active learning loop for tail class coverage
- [ ] Shadow deployment for behavioral validation

---

## 7. Documents Created/Updated

| Document | Purpose |
|----------|---------|
| `step-1-product-decision-analysis.md` | 4 use cases, cost matrix structure, 6 GAPs (existing, GAPs filled) |
| `step-2-problem-derivation.md` | Formal specification of X, Y, loss function |
| `step-3-learnability-analysis.md` | Sample complexity, irreducible error, PAC feasibility |
| `step-4-baseline-establishment.md` | 9 baselines from random to LLM, decision rules |
| `step-5-evaluation-protocol.md` | Cost-weighted F1, stratification, calibration, robustness |
| `experimental-premise-resolution.md` | 12 experiments with Phase 1 results, decision log |
| `phase1_experiments.py` | 6 zero-cost experiments executed on 2K MS MARCO queries |
| `exp{1,3,5,6,11,12}_*.json` | Raw experimental results |

---

## 8. Architecture Decision Records

### ADR-1: Session-Level Input
**Decision:** Use last N=3 queries concatenated as the input unit.
**Warrant:** Exp 1: 87.6% prediction change with session context.
**Alternatives considered:** Single query (rejected: insufficient signal), bi-encoder over each query separately (rejected: higher complexity, same signal).

### ADR-2: Spell Correction Preprocessor
**Decision:** SymSpell with max edit distance 2, before all other processing.
**Warrant:** Exp 11: 82.5% prediction change from synthetic misspellings. Jansen: 58.5% of real errors from misspellings.
**Alternatives considered:** Neural spell-corrector (too heavy), no correction (rejected: largest error source addressed).

### ADR-3: Reject Option with Granularity Ladder
**Decision:** Reject when confidence < τ at all 4 levels; report at highest granularity where confidence exceeds threshold.
**Warrant:** Exp 12: 0% of queries have confidence > 0.5. Forced classification is near-random.
**Alternatives considered:** Always classify (rejected: produces misleading labels for low-confidence queries), single reject threshold (rejected: granularity ladder extracts maximum information).

### ADR-4: Bi-Encoder Retrieval Paradigm
**Decision:** Retrieve top-K classes by cosine similarity; no linear classification head.
**Warrant:** Exp 5: 47.7 mean non-zero labels per query (diffuse, characteristic of retrieval, not classification).
**Alternatives considered:** Softmax classifier (rejected: forces single-class predictions), ranking loss (equivalent under common settings).

### ADR-5: LLM-as-Annotator Primary, Human Calibration
**Decision:** Use GPT-4o-mini for bulk labeling; human validation on 5K queries for calibration.
**Warrant:** Step 3 §6.2: 50x cheaper than human annotation, enables 500K labels for ~$10.
**Risk:** LLM may produce biased labels. Mitigation: measure LLM-human agreement on calibration set; if <80% agreement, increase human validation proportion.

### ADR-6: Effective K = 200-300, Expanding
**Decision:** Train initial model at K=64 (L2), expand to K=200-300 (L3 head) as data accumulates.
**Warrant:** Step 3 §2.2: at 20K labels, L4 (3843) gets ~5 examples/class — insufficient. L3 head (200-300) gets ~67 examples/class — sufficient.
**Alternatives considered:** K=3843 from start (rejected: insufficient data density), K=8 only (rejected: too coarse for product value).

---

*This synthesis replaces all prior project documents. The Track A/B/C structure is superseded by the 5-step problem formulation sequence. The taxonomy skeleton and pipeline code remain as the implementation baseline but should be reinterpreted through the lens of this specification.*
