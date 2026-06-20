# Step 2: Problem Derivation

> Formally specify the function $f: \mathcal{X} \rightarrow \mathcal{Y}$ that the model must approximate.
> Trace every design choice to its experimental or analytical warrant.
> If a choice is not warranted, state it as a working assumption with a revision trigger.

---

## 1. Traceability Map

Every element of the specification traces to a source:

| Element | Source | Status |
|---------|--------|--------|
| Input = session-level text (Last N queries) | Exp 1: 87.6% prediction change with session | FALSIFIED premise → redesign |
| Input = raw query (fallback) | Exp 1: single-query still usable as degenerate session | Working assumption |
| Preprocessing = spell correction | Exp 11: 82.5% change from misspellings | FALSIFIED premise → essential |
| Preprocessing = normalization pipeline | Jansen (2009): 58.5% of errors from misspellings | Literature-justified |
| Output = distribution over hierarchy | Exp 3: 72.8% L1 self-consistency | WEAKENED premise → adapt |
| Output = reject option | Exp 12: 0% coverage at $\tau=0.5$ | FALSIFIED premise → essential |
| Output = granularity ladder | Exp 3: effective K << 3843 | Derived from Exp 3 |
| Paradigm = bi-encoder retrieval | Exp 5: 47.7 mean labels per query | WEAKENED premise → shift |
| Evaluation = cost-weighted F1 | Exp 6: ranking stable but conditionally | HOLDS with secondary |
| Taxonomy = 8 L1 x 8 L2 x 8 L3 x ~7.5 L4 | Premise Foundation Door 3.1–3.7 | Working hypothesis |
| $K$ = 3843 (effective: TBD) | Exp 3: 1/3843 classes with >1% share | Must be empirically determined |

---

## 2. Input Space $\mathcal{X}$

### 2.1 Formal Definition

Let the input be a tuple:

$$\mathcal{X} = \mathcal{T} \times \mathcal{B}$$

where:
- $\mathcal{T}$ is the **text context**: a sequence of $N$ query strings from the current search session
- $\mathcal{B}$ is the **behavioral context** (optional, may be empty): device type, time of day, session length

### 2.2 Session Text

For a session of $N$ queries $q_1, q_2, \ldots, q_N$ in chronological order:

$$x_{\text{text}} = \text{Preprocess}(\text{Concat}(q_1, q_2, \ldots, q_N))$$

The preprocessing function $\text{Preprocess}: \Sigma^* \rightarrow \Sigma^*$ is:
1. Spell-correction (SymSpell or lightweight neural, max edit distance 2)
2. Case normalization
3. Punctuation stripping
4. Number normalization ("10" $\rightarrow$ "ten")

**Warrant:** Exp 11 found 82.5% of predictions change under synthetic misspellings. Jansen (2009) found 58.5% of real-world classification errors due to misspelling.

### 2.3 Session Length

Default session length $N = 3$ (current query + 2 preceding). Rationale:
- Jansen et al. (2009): mean session length is 2.8 queries
- Exp 1: concatenating 2 queries (q1 + q2) changes 87.6% of predictions vs q2 alone
- Longer sessions ($N > 5$) dilute the current query's signal

**Working assumption:** $N=3$ is optimal. Revision trigger: if a labeled experiment shows $N=5$ outperforms $N=3$ by $\geq 3$ F1 points, increase to $N=5$.

### 2.4 Behavioral Context

Available at inference time for an internal tool:
- `device_type`: {"desktop", "mobile", "tablet"}
- `hour_of_day`: integer 0–23
- `session_query_count`: integer, number of queries so far in session

**Not available:**
- User click history (no user identity)
- Previous session history (no cookie/persistence)
- Dwell time (not captured by query log)

**Working assumption:** Behavioral context is optional and zero-padded when missing. Revision trigger: if the data pipeline adds user IDs or click logs, incorporate Door 2.1 (behavioral signal augmentation).

### 2.5 Out-of-Distribution Detection

The input space includes queries that should not be classified:
- Random keystrokes: "asdf", "test test test"
- Navigational queries: "facebook", "youtube"
- Extremely specific queries: "restaurants near me that serve vegan gluten-free Ethiopian food"

The classifier must detect these and return `reject=True` rather than forcing a prediction.

**Warrant:** Exp 12: at $\tau=0.5$, 100% of queries are rejected. The current classifier assigns near-random classes to all inputs. A reject option is essential (Door 12.1).

---

## 3. Output Space $\mathcal{Y}$

### 3.1 Formal Definition

$$\mathcal{Y} = \mathcal{H} \times \{0,1\} \times \{\text{predict}, \text{reject}\}$$

where:
- $\mathcal{H} = \bigcup_{l=1}^{4} \Delta^{K_l}$ is a **hierarchical distribution** over $K_l$ classes at level $l$
- $\{0,1\}$ is a **commercial intent flag**
- $\{\text{predict}, \text{reject}\}$ is a **rejection decision**

### 3.2 Hierarchical Distribution

At each level $l \in \{1,2,3,4\}$:

$$P_l(\text{intent}_i \mid x) \in \Delta^{K_l}$$

where:
- $K_1 = 8$ (L1 macro-categories)
- $K_2 = 64$ (L2 sub-categories)
- $K_3 = 512$ (L3 sub-categories)
- $K_4 = 3843$ (L4 leaf intents)

The hierarchy is a tree: each L4 leaf has exactly one L3 parent, one L2 grandparent, one L1 great-grandparent. The distribution satisfies:

$$P_{l+1}(c \mid x) \leq P_l(\text{parent}(c) \mid x)$$

i.e., the probability of a child class cannot exceed the probability of its parent (hierarchical coherence).

### 3.3 Effective Granularity

The granularity ladder (Door 12.4) adapts to the query:

$$l^*(x) = \max\{l \in \{1,2,3,4\} : \max_i P_l(\text{intent}_i \mid x) > \tau_l\}$$

where $\tau_l$ are level-specific thresholds:
- $\tau_1 = 0.3$ (L1: moderate confidence needed)
- $\tau_2 = 0.4$ (L2: higher confidence)
- $\tau_3 = 0.5$ (L3: high confidence)
- $\tau_4 = 0.6$ (L4: very high confidence)

If no level meets its threshold, the model returns `reject=True` and no prediction.

**Warrant:** Exp 3 found that only 1 of 3,843 L4 classes captures >1% of queries. Forcing all queries to L4 is not supported by the data. The granularity ladder extracts the maximum information the model is confident about.

### 3.4 Commercial Intent Flag

$$\text{commercial}(x) = \mathbb{1}\left[\sum_{c \in \mathcal{C}} P_4(c \mid x) > \theta_c\right]$$

where $\mathcal{C}$ is the set of commercial intent classes (approximately 31% of all classes, per the 3.08:1 pruning ratio from `ads_mapping.py`), and $\theta_c$ is a threshold calibrated to achieve precision $\geq 0.90$ on a held-out validation set.

**Working assumption:** $\theta_c$ can be derived from the probability distribution without training a separate binary classifier. Revision trigger: if this approach yields precision < 0.85, train a dedicated commercial-intent classifier (Door 6.3, ad-specific precision).

### 3.5 Rejection Decision

$$\text{reject}(x) = \mathbb{1}\left[\max_{c} P_4(c \mid x) < \tau_{\text{reject}}\right]$$

The reject threshold $\tau_{\text{reject}}$ is set to maximize coverage while maintaining Precision@1 $\geq 0.80$ on a held-out set.

---

## 4. Loss Function $\ell$

### 4.1 Cost Matrix

Let $C(y, \hat{y})$ be the cost of predicting output $\hat{y}$ when the true output is $y$.

For hierarchical classification:

$$C(y, \hat{y}) = 
\begin{cases} 
0 & \text{if } y = \hat{y} \text{ (correct)} \\
0.1 & \text{if } y \text{ and } \hat{y} \text{ share L3 parent (within-L3 error)} \\
0.3 & \text{if } y \text{ and } \hat{y} \text{ share L1 parent (within-L1, cross-L3)} \\
1.0 & \text{if } y \text{ and } \hat{y} \text{ have different L1 parents (cross-L1 error)} \\
0.5 & \text{if } \hat{y} = \text{reject (abstention cost)}
\end{cases}$$

**Warrant:** These values are carried forward from Step 1 (Product Decision Analysis, §4.1) and are not yet validated against actual product outcomes. They represent a reasoned estimate of relative error severity.

### 4.2 Frequency Weighting

Following the Zipf distribution with $\alpha \approx 1.1$:

$$C_{\text{total}}(y, \hat{y}) = C(y, \hat{y}) \times w(f_y)$$

where $f_y$ is the frequency of class $y$ and:

$$w(f) = \frac{1}{\sqrt{f}}$$

This gives higher per-query weight to rare classes (tail queries are more valuable individually) while maintaining aggregate head dominance.

**Warrant:** Derived from the Zipf analysis in `ads_mapping.py` and the cost matrix structure in Step 1 (§4.3). The $\frac{1}{\sqrt{f}}$ form balances per-query value with aggregate impact.

### 4.3 Commercial Asymmetry

For the commercial intent flag:

$$C(\hat{c}, c) =
\begin{cases}
2.0 & \text{if } \hat{c}=1, c=0 \text{ (false positive commercial)} \\
0.5 & \text{if } \hat{c}=0, c=1 \text{ (false negative commercial)} \\
0 & \text{otherwise}
\end{cases}$$

**Warrant:** Step 1 (§4.2). The 4:1 FP:FN ratio reflects the higher cost of showing irrelevant ads vs. missing a commercial opportunity. This is a literature-derived estimate (Varian, 2007; Bottou et al., 2013).

### 4.4 Training Loss

For training, use a differentiable surrogate:

$$\mathcal{L}(\theta) = \frac{1}{|\mathcal{D}|} \sum_{(x, y) \in \mathcal{D}} \left[ \mathcal{L}_{\text{hier}}(x, y) + \lambda \mathcal{L}_{\text{commercial}}(x, y) \right]$$

where:
- $\mathcal{L}_{\text{hier}}$ is a hierarchical cross-entropy loss with level-specific weights:
  $$\mathcal{L}_{\text{hier}} = \sum_{l=1}^{4} \alpha_l \cdot \text{CE}(P_l, \hat{P}_l)$$
  with $\alpha = [0.1, 0.15, 0.25, 0.50]$ (higher weight on finer granularity, where errors are more nuanced)
- $\mathcal{L}_{\text{commercial}}$ is a weighted binary cross-entropy on the commercial flag:
  $$\mathcal{L}_{\text{commercial}} = 2.0 \cdot \text{FP} + 0.5 \cdot \text{FN}$$
- $\lambda = 0.1$ is the commercial loss weight (commercial flag is an auxiliary task)

**Warrant:** The hierarchical loss weights are a design choice. Revision trigger: if Exp 6 with real model predictions shows F1 ranking diverges from cost-weighted ranking, switch to direct cost-weighted optimization (Door 6.1).

---

## 5. Learning Paradigm

### 5.1 Bi-Encoder Retrieval

The primary inference paradigm is **bi-encoder retrieval** (Door 5.1):

$$f(x) = \arg\max_{c \in \mathcal{Y}} \text{sim}(E_Q(x), E_C(c))$$

where:
- $E_Q: \mathcal{X} \rightarrow \mathbb{R}^d$ is the query encoder (transformer over session text)
- $E_C: \mathcal{Y} \rightarrow \mathbb{R}^d$ is the class encoder (transformer over class definition text)
- $\text{sim}$ is cosine similarity

**Warrant:** Exp 5 found that the current classifier distributes confidence across 47.7 classes on average, with 0% single-class predictions. This behavior is characteristic of a dense retrieval system, not a classifier. A bi-encoder retrieval framework naturally produces graded relevance scores and handles the diffuse similarity structure.

### 5.2 Multi-Task Auxiliary Heads

Following Door 5.4, the shared representation feeds auxiliary prediction heads during training:
- Intent class (hierarchical classification head)
- Commercial intent (binary head)
- Session length (regression head — how many more queries will the user issue?)
- Content type prediction (what kind of result would satisfy this query?)

**Warrant:** Multi-task learning improves shared representations (Caruana, 1997). The auxiliary tasks are free during training (require no additional labels — they are observable from the data).

### 5.3 Contrastive Pre-Training

Before supervised fine-tuning, pre-train the query encoder $E_Q$ with contrastive learning (Door 5.5):

$$\mathcal{L}_{\text{contrast}} = -\log \frac{\exp(\text{sim}(E_Q(x_i), E_Q(x_j)) / \tau)}{\sum_{k \neq i} \exp(\text{sim}(E_Q(x_i), E_Q(x_k)) / \tau)}$$

where $(x_i, x_j)$ are queries from the same session (positive pairs) and $x_k$ are queries from different sessions (negative pairs).

**Warrant:** Exp 1 found that session context dramatically changes predictions. Contrastive pre-training on session structure captures this signal without requiring labels.

---

## 6. Open Working Assumptions

| # | Assumption | Revision Trigger | Cost of Being Wrong |
|---|-----------|------------------|---------------------|
| A1 | $N=3$ session length is optimal | Labeled experiment shows $N=5$ > $N=3$ by $\geq 3$ F1 | Higher latency, modest degradation |
| A2 | $\tau_l$ thresholds work as granularity ladder | Calibration analysis shows poor precision-recall tradeoff | Worse user experience for rejected queries |
| A3 | $\theta_c$ from probability distribution suffices | Commercial precision < 0.85 | Wasted ad impressions |
| A4 | $K=3843$ with effective reduction | Exp 3 data-driven K analysis shows optimal $K \ll 3843$ | Diluted training signal, wasted capacity |
| A5 | Behavioral context is optional | Pipeline adds click/user data | Room for improvement later |
| A6 | Cost matrix values are reasonable | Product deployment shows different error costs | Suboptimal optimization target |
| A7 | Multi-task auxiliary heads help | Ablation study shows no improvement | Extra complexity for no gain |

---

## 7. Summary: The Function

The complete function specification:

$$
f: \underbrace{\mathcal{T} \times \mathcal{B}}_{\mathcal{X}} \rightarrow \underbrace{\mathcal{H} \times \{0,1\} \times \{\text{predict}, \text{reject}\}}_{\mathcal{Y}}
$$

With loss:

$$
\min_{\theta} \frac{1}{|\mathcal{D}|} \sum_{(x,y) \in \mathcal{D}} \left[ \sum_{l=1}^{4} \alpha_l \cdot \text{CE}(P_l, \hat{P}_l(x;\theta)) + \lambda \cdot \text{WBCE}(c, \hat{c}(x;\theta)) \right]
$$

subject to:
- Hierarchical coherence: $P_{l+1}(c|x) \leq P_l(\text{parent}(c)|x)$
- Reject option: return $\text{reject}$ if $\max_c P_4(c|x) < \tau_{\text{reject}}$
- Granularity ladder: report at level $l^*$ where confidence > $\tau_l$

This function is learnable if:
1. We can acquire 100+ labeled examples per effective class (at $K_{\text{eff}} \approx 1000$: $\sim 100K$ labels)
2. The embedding space captures query-intent similarity (bi-encoder with contrastive pre-training)
3. The session structure provides a weak supervision signal (contrastive pairs)

**Next step: Step 3 (Learnability Analysis)** — compute sample complexity bounds, irreducible error, and PAC-learning feasibility for this specification.
