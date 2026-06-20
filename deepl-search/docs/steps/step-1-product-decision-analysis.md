# Product Decision Analysis — Step 1

> Who makes what decision using the model's output?
> What is the cost of each error type?
> This document derives the model's purpose from product reality, not from academic convention.

**Status:** Analysis with identified gaps requiring product owner input.
**Gap convention:** [GAP: ...] marks a question only the product owner can answer.

---

## 1. Method

The Product Decision Analysis traces the path from a deployed ML model to the decisions it informs, in reverse:

```
Deployed ML Model → Output → Consumer → Decision → Outcome → Value
```

Each arrow is a dependency: the model exists to produce outputs; those outputs are consumed by an agent; that agent makes a decision based on the output; that decision produces an outcome; that outcome has measurable value. By tracing this chain, we derive:

1. **What the output must be** (the consumer's information need)
2. **What accuracy is required** (the cost of wrong information)
3. **What the model should optimize for** (the decision's utility function)
4. **What inputs are available** (the consumer has access to at decision time)

---

## 2. Candidate Use Cases

Without a formal product specification, we enumerate plausible use cases for an intent classifier in a search-intelligence product. Each is evaluated independently.

### Use Case A: Query-to-Intent Dashboard (Analytics)

| Property | Description |
|----------|-------------|
| Consumer | Product manager, SEO specialist, or business analyst |
| Decision | "Which intent categories are trending this week? Where should we invest content, ads, or product development?" |
| Current information | Raw query logs (unstructured, unlabeled); Google Search Console data (aggregate, no intent classification) |
| Model output | For each query, a distribution over intent classes: $\hat{P}(\text{intent} \mid \text{query})$ |
| How output is used | Aggregated across time periods: count of queries per intent class per week; rank by volume; compute growth rate |
| Consumption pattern | Batch (daily/weekly aggregation); no real-time requirement |
| Unit of analysis | Time series of intent class volumes |

**Error cost analysis:**

| Error Type | Effect | Cost Magnitude |
|------------|--------|----------------|
| Misclassify query Q → Intent A when true is B | Volume for A is inflated, B is deflated. Shifts investment decisions. | Medium. Wrong investment for one time period, corrects next period. |
| Systematic bias (e.g., always classify ambiguous queries as Shopping) | Dashboard shows Shopping growing, but it's actually an artifact. Persistent misallocation of resources. | High. Persists until detected. |
| Random noise (classification errors cancel out across large samples) | Volume estimates are less precise but unbiased. | Low. Averages out at scale. |
| Failure to detect emerging intent (new class) | Emerging trend appears as noise/uncategorized. Delayed response to market shift. | High. Competitor detects it first. |

**Required properties:**
- Unbiasedness of aggregate volume estimates (not per-query accuracy)
- Detection sensitivity for new/emerging patterns
- Temporal consistency (same query should map to same intent this month and next, unless the query itself changed meaning)
- Coverage of novel queries (queries containing new product names or events should not all fall into "Other")

**Cost matrix structure:**
- Asymmetric: misclassifying a head query (high volume) costs more than a tail query (low volume) — but finding the tail accurately is where the differentiation value lies.
- Symmetric within frequency stratum: within the same frequency band, any-to-any misclassification costs are approximately equal (the dashboard averages them out).
- Temporal cost: early detection of emerging intents has high positive value; false alarms of emerging intents have moderate cost (wastes one review cycle).

---

### Use Case B: Ad Targeting / Bid Optimization

| Property | Description |
|----------|-------------|
| Consumer | Automated ad-bidding system (DSP, ad server) |
| Decision | "Which ads should I show this user? What keyword bid should I place?" |
| Current information | Keyword match types (broad, phrase, exact); page content; user demographics |
| Model output | Per-query: top-K intent classes with confidence scores; Boolean flag for "commercial intent" |
| How output is used | Filter eligible ad campaigns (only campaigns targeting matched intents); set bid multiplier based on commercial intent strength |
| Consumption pattern | Real-time (<50ms per query); high throughput (thousands of QPS) |
| Unit of analysis | Single query |

**Error cost analysis:**

| Error Type | Effect | Cost Magnitude |
|------------|--------|----------------|
| False positive commercial intent (classify informational query as Shopping) | User sees irrelevant ads. High bounce rate. Wasted ad spend. | High. Direct financial cost. |
| False negative commercial intent (miss a shopping query) | Missed revenue opportunity. Competitor shows ad instead. | Medium-High. Lost revenue. |
| Misclassify Shopping intent → wrong Shopping subcategory (e.g., Shoes → Electronics) | Irrelevant ads for that specific query. User ignores. | Medium. Wasted impression, but not as damaging as showing ads for informational queries. |
| Correct classification, low confidence (score = 0.3) | No action taken (below threshold). | Low-Medium. Conservative behavior misses some revenue but avoids costly FP errors. |

**Required properties:**
- High precision on "commercial intent" binary flag (FP cost is high)
- High recall for high-value commercial intents (expensive products, high-margin categories)
- Latency: <50ms p95
- Calibrated confidence scores (a score of 0.7 should mean 70% probability of correct class)
- Only use advertiser-pruned subset (~1,247 classes), not all 3,843

**Cost matrix structure:**
- Highly asymmetric: $C(\text{FP}_{\text{commercial}}) \gg C(\text{FN}_{\text{commercial}})$ — false positives are 5-10× more costly than false negatives
- Cross-class costs are **not** uniform: within same L1 parent, misclassification costs are low; across L1 boundaries, costs are high
- The cost matrix depends on advertiser bid prices: misclassifying a "luxury watch" search as "budget watches" loses high-value bid opportunities

---

### Use Case C: Content Recommendation

| Property | Description |
|----------|-------------|
| Consumer | Recommendation engine |
| Decision | "What content should we surface on the search results page or content feed?" |
| Current information | Keyword matching; collaborative filtering; popularity signals |
| Model output | Per-query: top-K intent classes with weights; per-content-item: pre-computed intent vector |
| How output is used | Match query intent vector to content intent vectors via cosine similarity; recommend content with highest similarity |
| Consumption pattern | Real-time (<100ms per query) |
| Unit of analysis | Query–content pair similarity |

**Error cost analysis:**

| Error Type | Effect | Cost Magnitude |
|------------|--------|----------------|
| Query classified → wrong broad intent class | Recommended content is completely off-topic. User bounces. | High. Loss of user trust. |
| Query classified → right L1 but wrong L4 | Recommended content is topically close but not the exact need. User may or may not engage. | Low-Medium. Degraded but not broken experience. |
| Content classified → wrong intent vector | Content never recommended for relevant queries. Lost distribution. | Medium. Lost content engagement. |

**Required properties:**
- High Precision@K for the top intent class (the first impression determines user trust)
- Broad coverage (queries covering niche intents should still receive relevant content — this is where the 3,843-class taxonomy adds value over a smaller taxonomy)
- Similarity metric that reflects graded relevance (cosine similarity on intent vectors)

---

### Use Case D: Market Research / Trend Analysis

| Property | Description |
|----------|-------------|
| Consumer | Brand manager, market researcher, product strategist |
| Decision | "What are consumers searching for in our category? What unmet needs exist?" |
| Current information | Surveys, focus groups, panel data (expensive, slow) |
| Model output | Aggregated intent distributions; "emerging intent" alerts; gap analysis (high query volume, low quality content) |
| How output is used | Analyze intent volume trends; identify gaps between query volume and content/ad coverage; prioritize product or content development |
| Consumption pattern | Batch (weekly reporting) |
| Unit of analysis | Aggregated time series |

**Error cost analysis:**
- Similar structure to Use Case A (Dashboard) but with higher tolerance for noise and higher value for novelty detection
- The primary value is in surfacing intents that are **growing** — these have not been optimized by competitors yet

---

## 3. Consumer Comparison

| Dimension | Analytics Dashboard | Ad Targeting | Content Recommendation | Market Research |
|-----------|-------------------|--------------|----------------------|-----------------|
| Consumer type | Human (analyst) | Automated (ad server) | Automated (recommender) | Human (strategist) |
| Latency requirement | Batch (hours) | Real-time (<50ms) | Real-time (<100ms) | Batch (days) |
| Throughput | Low (hundreds/day) | High (thousands QPS) | High (thousands QPS) | Low (dozens/day) |
| Error tolerance | Medium (averaged out) | Low (FP costs money) | Low (FP loses user trust) | High (analyst filters noise) |
| Output required | Distribution | Binary + top-K | Weighted vector | Distribution + anomaly flags |
| Taxonomy needed | Full (3,843) | Pruned (~1,247) | Full (3,843) | Full (3,843) |
| Primary metric | Distributional similarity | Commercial precision | Precision@1, engagement | Trend detection recall |
| [GAP: Which of these is the primary use case?] | | | | |

---

## 4. Cost Matrix Construction

From the error analysis above, we can derive the cost matrix structure even before we know the exact use case mix. The shape of the cost matrix determines the optimal loss function and evaluation metric.

### 4.1 Cost Matrix Shape

Let $C(i,j)$ be the cost of predicting intent class $i$ when the true intent is $j$.

**Cross-L1 cost (across top-level categories):**
- $C(i,j) = 1.0$ when $i$ and $j$ are in different L1 categories
- Example: predicting "Shopping > Shoes" when true is "Health > Exercise" → cost = 1.0
- Rationale: completely different product verticals; any downstream action based on this prediction will be irrelevant

**Within-L1, cross-L3 cost (same parent, different subcategory):**
- $C(i,j) = 0.3$ when $i$ and $j$ share the same L1 but different L3
- Example: predicting "Shopping > Shoes > Running" when true is "Shopping > Shoes > Casual" → cost = 0.3
- Rationale: same vertical, different specific need; content/ads may still be partially relevant

**Within-L3, cross-L4 cost (same subcategory, different leaf):**
- $C(i,j) = 0.1$ when $i$ and $j$ share the same L3 but different L4
- Example: predicting "Shopping > Shoes > Running > Road" when true is "Shopping > Shoes > Running > Trail" → cost = 0.1
- Rationale: very similar intents; most downstream actions will be similar

**Correct classification:**
- $C(i,i) = 0$

**Predicting "Other" (no classification):**
- $C(\text{Other}, j) = 0.5$ for all $j$
- Rationale: failing to classify is better than a cross-L1 false positive, but worse than a within-L3 misclassification

### 4.2 Commercial Intent Asymmetry

For the ad targeting use case, we add an additional asymmetry:

Let $K$ be the set of commercial intent classes (approximately 31% of all classes, per the 3.08:1 pruning ratio).

- $C(\text{predict commercial class } i, \text{true is non-commercial}) = 2.0$
  - Rationale: showing an ad for a non-commercial query annoys the user and wastes ad spend
- $C(\text{predict non-commercial, true is commercial class } j) = 0.5$
  - Rationale: missed revenue opportunity, but no direct harm

This asymmetry means the optimal classifier is conservative: it should only predict a commercial intent when confidence is high.

### 4.3 Frequency Asymmetry

Following the Zipf distribution ($\alpha = 1.1$), the cost of misclassifying a high-volume query should be scaled by its frequency. A misclassification on the top 100 classes (which cover $\sim 50\%$ of query volume) costs more in aggregate than misclassifying the bottom 3,000 classes (which cover $\sim 10\%$ of volume).

However, the value of correctly classifying the tail is higher per-query precisely because it's rare — tail queries represent unmet needs that competitors are not serving. So:

- Per-query cost: tail > head (individual tail query is more valuable to get right)
- Aggregate cost: head > tail (aggregate volume of head classes dominates)

The cost matrix should weight each class inversely to its frequency:

$$C_{\text{freq}}(i,j) = C(i,j) \times \frac{1}{\sqrt{f_i}}$$

where $f_i$ is the relative frequency of class $i$. This balances per-query value (rare queries are more valuable individually) with aggregate impact (frequent queries dominate total volume).

---

## 5. Derived Requirements for the Model

### 5.1 Output Specification

From the use cases, the model output should be:

$$f: Q \rightarrow \Delta^{3843} \times \{0,1\}$$

where $\Delta^{3843}$ is the probability simplex (distribution over 3,843 classes) and $\{0,1\}$ is a commercial intent flag.

- The distribution $\hat{P}(\text{intent} \mid \text{query})$ supports the analytics, recommendation, and research use cases
- The binary commercial flag supports the ad targeting use case directly
- [GAP: The commercial flag could be derived from the distribution (sum probabilities over commercial classes). Is an explicit binary classifier needed, or is a threshold on the distribution sufficient?]

### 5.2 Error Tolerance (From Cost Matrix)

| Error Type | Max Acceptable Rate | Derivation |
|------------|---------------------|------------|
| Cross-L1 misclassification | <5% of queries | Cost = 1.0; at >5%, dashboard volume estimates are unreliable |
| Within-L1, cross-L3 misclassification | <20% of queries | Cost = 0.3; tolerable for aggregation but degrades per-query quality |
| Commercial FP (non-commercial → commercial) | <2% of non-commercial queries | Cost = 2.0; high cost drives conservative threshold |
| Commercial FN (missed commercial) | <10% of commercial queries | Cost = 0.5; moderate tolerance |
| Coverage gap (query → "Other") | <1% of total volume | Zero-cost "Other" option at 0.5; but should be rare |

[GAP: These are initial estimates. They should be validated through a pilot study where predicted intents are compared with actual user behavior.]

### 5.3 Minimum Viable Performance (MVP Threshold)

At what accuracy does the model become useful? This depends on the primary use case.

**If primary use case is Analytics Dashboard:**
The model is useful when the intent distribution it produces (aggregated over 10,000+ queries) has a KL divergence from the true distribution of <0.1 bits. This is achievable even with per-query accuracy of 40-50%, as long as errors are unbiased. **MVP is met early**, possibly with a simple classifier.

**If primary use case is Ad Targeting:**
The model is useful when commercial precision exceeds 0.90 (fewer than 10% of ad impressions are wasted on non-commercial queries). This is a higher bar. **MVP is not met until the classifier can detect commercial intent with high confidence.**

**If primary use case is Content Recommendation:**
The model is useful when Precision@1 (is the top predicted intent class correct?) exceeds 0.70. Below this, users consistently see off-topic content and stop engaging.

[GAP: Which use case is primary determines the entire model strategy, from data acquisition to evaluation to deployment timeline. This decision must come from the product owner.]

### 5.4 Input Space Specification

From the analysis:

| Input | Required? | Why |
|-------|-----------|-----|
| Query text (raw) | Required | Primary signal |
| Query text (normalized) | Recommended | Jansen: 58.5% of errors from misspellings; spell normalization alone improves accuracy by 3-5% |
| Session context (previous 3 queries) | Recommended for ad use case | Jansen: 25.8% of errors from session-level effects |
| User click history (last 100 clicks) | Optional | Resolves ambiguity for "best running shoes" — user who clicks on review pages has informational intent; user who clicks on product pages has commercial intent |
| Time of day / day of week | Optional | Some intents have temporal patterns (e.g., "pizza delivery" peaks on Friday evening) |
| Device type (mobile vs. desktop) | Optional | Mobile queries are more likely to be local/navigational; desktop queries more likely to be research/comparison |

[GAP: These are literature-derived recommendations. The actual available input data depends on the product's data pipeline.]

---

## 6. What This Means for Everything Downstream

The Product Decision Analysis changes the ML requirements specification. If we commit to specific answers to the GAPs above, the following changes propagate:

### If Primary = Analytics Dashboard:
- Evaluation metric → KL divergence between predicted and true intent distributions (not F1)
- Data requirement → 400K labels (minimum; unbiased sampling across frequency strata)
- Model → fastText (simple, cheap, unbiased at aggregate level)
- Taxonomy → Full 3,843 (dashboard needs coverage, not precision)
- Temporal requirement → Weekly retraining to capture trend shifts
- Baseline → 8-way L1 classifier (covers 80% of dashboard value)

### If Primary = Ad Targeting:
- Evaluation metric → Commercial precision/recall at threshold (not Macro F1)
- Data requirement → 2M+ labels with oversampling of commercial intents
- Model → BERT or cascade (fastText baseline + BERT for ambiguous cases)
- Taxonomy → Pruned 1,247 commercial classes + "Other" for the rest
- Temporal requirement → Real-time (sub-50ms); no batch window
- Baseline → Always predict "non-commercial" (the majority class baseline)

### If Primary = Content Recommendation:
- Evaluation metric → Precision@1, NDCG@3 (rank-based)
- Data requirement → 400K labels with emphasis on pairs (query, intent) that distinguish similar classes
- Model → Bi-encoder (query → embedding, content → embedding, similarity match)
- Taxonomy → Full 3,843 with embedding centroids for each class
- Temporal requirement → Sub-100ms for similarity computation
- Baseline → Most-frequent-content-class heuristic

---

## 7. Open Gaps (Product Owner Decisions Required)

| Gap | Question | Impact on Model |
|-----|----------|-----------------|
| GAP-1 | Primary use case: Analytics, Ads, Content, or all three? | Determines every downstream decision |
| GAP-2 | Available input data: can we access session context? User history? | Determines whether query-only model is sufficient or we need multi-modal input |
| GAP-3 | Deploy target: public API? Internal tool? Enterprise product? | Determines latency, throughput, and privacy requirements |
| GAP-4 | Revenue model: subscription (analytics)? Ad platform (ads)? Content platform? | Cost matrix structure |
| GAP-5 | Minimum viable timeline: when does the product need to ship? | Determines whether we start with fastText (2 weeks) or invest in BERT (3 months) |
| GAP-6 | Labeling budget: what's the maximum annotation spend? | Upper bound on training data volume |

---

## References

- Bottou, L., et al. (2013). Counterfactual reasoning and learning systems. *JMLR*, 14, 3207–3260.
- Domingos, P. (2012). A few useful things to know about machine learning. *CACM*, 55(10), 78–87.
- Elkan, C. (2001). The foundations of cost-sensitive learning. *IJCAI*, 973–978.
- Jansen, B. J., et al. (2009). Patterns of query reformulation during web searching. *JASIST*, 60(7), 1358–1371.
- Varian, H. R. (2007). Position auctions. *International Journal of Industrial Organization*, 25(6), 1163–1178.
- Hand, D. J. (2006). Classifier technology and the illusion of progress. *Statistical Science*, 21(1), 1–14.
