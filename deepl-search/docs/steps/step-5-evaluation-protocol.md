# Step 5: Evaluation Protocol

> Derive the evaluation metric from the cost matrix.
> Stratify by all dimensions that affect error cost.
> Never report a single number without its breakdown.

---

## 1. Primary Metric: Cost-Weighted Hierarchical F1

### 1.1 Definition

Adapted from the cost matrix in Step 2 (§4.1):

$$\text{CW-F1} = \frac{2 \cdot \text{CW-Precision} \cdot \text{CW-Recall}}{\text{CW-Precision} + \text{CW-Recall}}$$

where:

$$\text{CW-Precision} = \frac{\sum_{i: \hat{y}_i \neq \text{reject}} w(y_i, \hat{y}_i) \cdot \mathbb{1}[y_i = \hat{y}_i]}{\sum_{i: \hat{y}_i \neq \text{reject}} w(y_i, \hat{y}_i)}$$

$$\text{CW-Recall} = \frac{\sum_{i: \hat{y}_i \neq \text{reject}} w(y_i, \hat{y}_i) \cdot \mathbb{1}[y_i = \hat{y}_i]}{\sum_i w(y_i, y_i)}$$

and $w(y, \hat{y})$ is the inverse cost weight:

$$w(y, \hat{y}) = 
\begin{cases}
1.0 & \text{if correct} \\
0.1 & \text{if within-L3 error} \\
0.3 & \text{if within-L1 error} \\
1.0 & \text{if cross-L1 error}
\end{cases}$$

Rejected queries (reject=True) are excluded from both numerator and denominator — they contribute zero to both precision and recall. Their cost is captured by the **reject rate** metric.

### 1.2 Why Not Standard F1?

Standard F1 treats all errors equally. Our cost matrix has errors ranging from 0.1 (within-L3) to 1.0 (cross-L1) — a 10x range. A model that makes only within-L3 errors could have the same F1 as one that makes only cross-L1 errors, but the latter is 10x worse in practice.

### 1.3 Secondary Metric: Standard Macro F1

Report for comparability with literature, but never as the primary decision metric.

---

## 2. Stratification Dimensions

Every metric must be reported stratified by:

### 2.1 Frequency Stratum

| Stratum | Definition | % of Queries | Expected Accuracy | Why Report Separately |
|---------|-----------|-------------|-------------------|----------------------|
| Head | Top 10% of classes by frequency | ~50% | Highest | Drives aggregate product metrics |
| Mid | Next 30% of classes | ~35% | Moderate | Representative of "typical" performance |
| Tail | Bottom 60% of classes | ~15% | Lowest | Differentiates the product; most valuable for niche discovery |

**Decision rule:** The tail accuracy must be at least 50% of head accuracy. If head accuracy is 80% but tail is 15%, the model is memorizing frequent classes and failing at the differentiation value proposition.

### 2.2 Ambiguity Stratum

| Stratum | Definition | Expected Accuracy |
|---------|-----------|-------------------|
| Low-ambiguity | Single dominant intent (P_{max} > 0.8 in human labels) | Highest |
| Medium-ambiguity | 2-3 plausible intents | Moderate |
| High-ambiguity | 4+ plausible intents or unanimous annotator disagreement | Lowest (may be <50%) |

**Measure:** Use the entropy of the multi-annotator consensus distribution. Queries with high entropy are inherently ambiguous — the model should reflect this by distributing probability mass, not forcing a single class.

### 2.3 Session Position

| Position | Definition |
|----------|-----------|
| First query | No prior context in session |
| Mid-session | Query 2-3 in a multi-query session |
| Last query | Final query before a long dwell or conversion |

Track whether accuracy improves with session position (evidence that session context helps) or degrades (evidence that session noise accumulates).

### 2.4 Commercial Intent

| Stratum | Definition | Cost Weight |
|---------|-----------|-------------|
| Commercial | Query has purchase intent (from label or behavior) | 2x for FP |
| Non-commercial | Informational, navigational, or exploratory | 1x |

### 2.5 Query Length

| Stratum | Definition | Notes |
|---------|-----------|-------|
| Short | 1-2 words | Highest ambiguity; "nike" = many intents |
| Medium | 3-5 words | Typical query length |
| Long | 6+ words | Rare but specific; "best running shoes for flat feet under $100" |

---

## 3. Reject Metric

The reject option (Door 12.1, Step 2 §3.5) introduces a coverage-accuracy tradeoff:

$$\text{Coverage} = \frac{|\{i: \text{reject}(x_i) = \text{false}\}|}{|\mathcal{D}_{\text{test}}|}$$

$$\text{Accuracy}_{\text{accepted}} = \frac{|\{i: y_i = \hat{y}_i \land \text{reject}(x_i) = \text{false}\}|}{|\{i: \text{reject}(x_i) = \text{false}\}|}$$

**Report the Precision-Coverage curve** over the full range of rejection thresholds. The operating point is chosen where:

$$\text{Coverage} = 0.80 \text{ and } \text{Precision@1} \geq 0.80$$

---

## 4. Calibration Metrics

The model produces confidence scores that should be well-calibrated:

$$\mathbb{E}[P(\text{correct} \mid \text{confidence} = c)] \approx c$$

### 4.1 Expected Calibration Error (ECE)

$$\text{ECE} = \sum_{m=1}^{M} \frac{|B_m|}{n} |\text{acc}(B_m) - \text{conf}(B_m)|$$

where $B_m$ are $M$ equal-width confidence bins.

**Target:** $\text{ECE} < 0.05$ (average calibration error within 5 percentage points).

### 4.2 Commercial Intent Calibration

The commercial intent flag's confidence should also be calibrated:

$$\frac{|\{i: c_i = 1 \land \hat{p}_i > \theta\}|}{|\{i: \hat{p}_i > \theta\}|} \approx \theta$$

where $\hat{p}_i$ is the predicted probability of commercial intent.

---

## 5. Robustness Metrics

### 5.1 Distribution Shift Sensitivity

Measure accuracy on the most recent 10% of queries (by timestamp) vs. the overall test set. A significant drop (>5 points) indicates distribution shift — the model is not generalizing to the current query distribution.

### 5.2 Misspelling Robustness

For a set of 200 queries with synthetic misspellings, measure:

$$\text{Robustness}_{\text{spell}} = \frac{\text{Accuracy}_{\text{misspelled}}}{\text{Accuracy}_{\text{clean}}}$$

**Target:** $\geq 0.90$ (less than 10% accuracy loss from misspellings). If below 0.80, the spell-correction preprocessor is insufficient.

### 5.3 Session Ablation

For a set of 200 multi-query sessions, measure accuracy with and without session context:

$$\text{Session Gain} = \text{Accuracy}_{\text{with session}} - \text{Accuracy}_{\text{query only}}$$

**Target:** $\geq 0.03$ (at least 3 points improvement from session context). If negative, the session encoder is adding noise rather than signal.

---

## 6. Minimum Viable Performance

Derived from the cost matrix and use case requirements:

| Metric | Path to Production | MVP | Target | Stretch |
|--------|-------------------|-----|--------|--------|
| L1 Accuracy | Dashboard use case needs unbiased aggregates (any level) | 50% | 65% | 80%+ |
| L2 CW-F1 | Content recommendation needs Precision@1 > 0.70 | 0.40 | 0.55 | 0.70 |
| Commercial Precision | Ad targeting: FP cost is 2x; need <10% wasted impressions | 0.75 | 0.85 | 0.95 |
| Reject Coverage | 80% of queries accepted at Precision@1 > 0.80 | 60% | 80% | 90% |
| Tail/Head Ratio | Tail accuracy >= 50% of head accuracy | 0.30 | 0.50 | 0.75 |
| ECE | Calibration error | <0.10 | <0.05 | <0.03 |
| Session Gain | Improvement from session context | 0.01 | 0.03 | 0.05 |
| Latency p95 | Internal API | <500ms | <200ms | <100ms |

---

## 7. Reporting Template

Every evaluation report must include:

```
## Evaluation Report v{version}
### Summary
- CW-F1: {value} (head: {value}, mid: {value}, tail: {value})
- Coverage: {value} at Precision@1 ≥ {threshold}
- Reject rate: {value}
- ECE: {value}

### Stratified Results
| Stratum | L1 Acc | L2 CW-F1 | L4 CW-F1 | N |
|---------|--------|----------|----------|---|
| Head    |        |          |          |   |
| Mid     |        |          |          |   |
| Tail    |        |          |          |   |
| Commercial |     |          |          |   |
| Non-commercial | |          |          |   |

### Decision
- [ ] MVP met: proceed to deployment
- [ ] MVP not met: {reason}
- [ ] Regression: {comparison to previous run}
```

---

## 8. Experimentation Cadence

| Stage | Evaluation | Data | Cadence |
|-------|-----------|------|---------|
| Model development | Stratified report on held-out set | 80% train / 20% test | Per training run |
| Model selection | CW-F1 on validation set | Held-out validation (10% of labeled data) | Per hyperparameter search |
| Pre-production | Full stratified report + robustness tests | Separate test set (10% of labeled data, time-separated) | Per candidate model |
| Shadow deployment | Behavioral validation (click rates, bounce rates) | Production traffic (shadow mode) | Weekly |
| Canary (1% traffic) | A/B test against baseline | Production traffic | Continuous during canary |
| Full deployment | Monitoring dashboard (drift detection, accuracy drift) | Production traffic + periodic human review | Continuous |

The evaluation evolves from **offline (accuracy)** → **shadow (behavioral)** → **online (business metrics)**. Each stage filters out models that pass the previous stage but fail on the next.
