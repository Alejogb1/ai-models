# A Critical Examination of the Problem Formulation Gap in the Deepl Search Intent Classification System

> Working paper — Problem Formulation Critique
> **Date:** 2026-06-11
> **Status:** Not a specification. A diagnosis of what is missing before a specification can exist.

---

## 1. Preamble: The Constructor–Strategy Pitfall

A well-documented failure mode in applied machine learning is the **constructor–strategy pitfall**: the tendency to commit to a solution architecture before the problem is formally specified (Hand, 2006; Domingos, 2012). The engineering appeal of a concrete structure — a taxonomy of known size, a hierarchy of specified depth, a model class with attractive properties — exerts a gravitational pull that short-circuits the problem formulation phase. Once a technical artifact exists (the taxonomy skeleton, the API endpoints, the embedding index), it becomes the de facto problem specification: queries must be classified into these 3,843 classes because that is what the system does. The circularity is invisible from within the engineering perspective.

This document examines how that pitfall manifested in the Deepl Search project, what remains unspecified, and what questions must be answered before the problem can be considered formally defined.

---

## 2. The Function That Was Never Specified

### 2.1 The Mathematical Vacuum

Any supervised machine learning system learns an approximation of some target function:

$$f: \mathcal{X} \rightarrow \mathcal{Y}$$

where $\mathcal{X}$ is the input space and $\mathcal{Y}$ is the output space. The choice of $\mathcal{X}$, $\mathcal{Y}$, and the loss function $\ell: \mathcal{Y} \times \mathcal{Y} \rightarrow \mathbb{R}_{\geq 0}$ together constitute the **problem specification**. Without this specification, there is no supervised learning problem — there is only a data transformation pipeline in search of a purpose.

The current system has:

| Component | Current State | Status |
|-----------|---------------|--------|
| $\mathcal{X}$ (input space) | Implicitly: query text (strings of ≤500 characters) | Not formally specified |
| $\mathcal{Y}$ (output space) | Implicitly: $\{0,1\}^{3843}$ (binary vector over leaf classes) | Not formally specified |
| $\ell$ (loss function) | Cross-entropy with hierarchical softmax, proposed in requirements | Not justified from first principles |
| $\mathcal{D}$ (data distribution) | Not specified | MS MARCO sample used for experiments; no known relationship to deployment distribution |
| Optimality criterion | Not specified | F1 proposed as default metric, not derived from product constraints |

**The core observation:** the current system has architecture but no specification. The taxonomy structure, model class, and evaluation metric were selected before the function was defined. This is logically equivalent to choosing the hyperparameters of a model before deciding what it should predict — a category error in the ML workflow.

### 2.2 The Taxonomic Fallacy

The central architectural decision — that the output space should be the 8→64→512→3,843 YQT-derived taxonomy — rests on an unexamined syllogism:

> Major premise: Yahoo!'s search advertising system successfully used this taxonomy.
> Minor premise: Deepl Search is building a search intelligence system.
> Conclusion: Deepl Search should use this taxonomy.

The minor premise conflates "search intelligence" (undefined) with Yahoo!'s specific instantiation. Yahoo!'s taxonomy was designed to maximize **advertiser bid density** per class — a constraint that arises from the economics of sponsored search auctions (Varian, 2007). Deepl Search's product objective has not been specified with equivalent precision. If Deepl Search's objective differs — if the system serves content recommendation, user behavior analysis, trend detection, or any of a dozen other search-intelligence functions — then the optimal taxonomy for that objective may differ structurally from the YQT.

The fact that two independent taxonomies converge on the same structure (the Octohedral convergence) is evidence that there exists a universal constraint structure for web-scale search **given the economic objective of advertising optimization**. It is not evidence that the same structure is optimal for any other objective. The octohedral structure may be an advertiser-specific attractor, not a universal one — but the current project treats it as the latter without argument.

---

## 3. The Input Space Problem: Does Intent Live in Query Text?

### 3.1 The Insufficiency Theorem

The fundamental question — whether query text alone contains sufficient information to determine intent — can be formalized:

Let $Q$ be the space of query strings, $H$ be the space of user history states (previous queries, clicks, dwell times, session context), and $Y$ be the space of intent labels. The true intent is a function of query **and** history:

$$\text{Intent}_{\text{true}}: Q \times H \rightarrow Y$$

If we learn a classifier that conditions only on query text:

$$\hat{f}: Q \rightarrow Y$$

then the irreducible error is:

$$\mathbb{E}_{q,h}[\ell(\hat{f}(q), \text{Intent}_{\text{true}}(q,h))]$$

This error is bounded below by the ambiguity of intent given query text alone. Empirically, **this ambiguity is non-trivial**. The same query "best running shoes" reflects a shopping intent for a novice, a comparison-shopping intent for someone who has already read reviews (detectable from session history), or an information-seeking intent for someone researching the category before purchase. Jansen et al. (2009) found that 25.8% of query classification errors were attributable to session-level effects invisible from single-query text.

**Implication:** If $\mathcal{X} = Q$ (query text only), the irreducible error may exceed the required accuracy threshold regardless of model capacity. This is not a data or architecture problem — it is a problem formulation problem. The function we have told the model to learn may not exist in the input space we have given it.

### 3.2 The Conflation of Correlation and Causation

A query classifier trained on query text alone does not learn to detect intent — it learns the **correlation between surface lexical features and intent labels**. If "buy" appears in the query, the classifier predicts "Shopping." This works for queries containing "buy," "price," "cheap," "discount." It fails for "best running shoes" (ambiguous between shopping and research) and for "Nike Air Max size 10" (entity resolution, not intent).

The literature provides explicit evidence of this lexical shortcut. In the Query2Interest system (Pinterest, 2020), the fastText classifier achieves its accuracy by exploiting n-gram correlations — "recipe," "diy," "how to" signal informational intent; "buy," "shop," "price" signal commercial intent. This is not intent detection; it is **surface-form pattern matching** that correlates with intent under the training distribution. When the deployment distribution shifts (new products, new slang, new query patterns), the lexical correlations break and accuracy degrades — which is why temporal drift is a known failure mode (Beitzel et al., 2007).

The architecture documentation describes the system as an "intent classifier," but no formal argument has been given that the function it learns **generalizes beyond lexical correlation**. This is the difference between prediction and understanding — and the system, as specified, is capable only of the former.

---

## 4. The Output Space Problem: What Does "Prediction" Mean Here?

### 4.1 The Classification–Retrieval Ambiguity

The current framing is "3,843-way multi-label classification," but this collapses several fundamentally distinct mathematical objects:

| Framing | Output Representation | Loss Function | Inference Procedure | Example Product Use Case |
|---------|---------------------|---------------|-------------------|-------------------------|
| Single-label classification | $f(q) \in \{1, \dots, 3843\}$ | Cross-entropy | $\arg\max$ | "This query IS intent X" |
| Multi-label classification | $f(q) \in \{0,1\}^{3843}$ | Binary cross-entropy per class | Threshold at 0.5 | "This query expresses intents {X, Y}" |
| Ranking | $f(q)$ produces a permutation of $\{1, \dots, 3843\}$ | Pairwise / NDCG / ListNet | Top-K | "These are the TOP 5 intents for this query" |
| Retrieval (bi-encoder) | $f(q) \in \mathbb{R}^d$, $g(c) \in \mathbb{R}^d$ | Contrastive (InfoNCE, triplet) | Nearest neighbors | "Which intents are SIMILAR to this query?" |
| Distribution prediction | $f(q) \in \Delta^{3842}$ (probability simplex) | KL divergence | Full distribution | "The intent profile of this query is [0.5, 0.3, ...]" |
| Density estimation | $f(q) \in \mathbb{R}^d$ (embedding) + density model of classes | Likelihood | MAP assignment | "Given this query embedding, which class region does it fall in?" |

Each framing is a **different function** with different mathematical properties, data requirements, and failure modes. The current system has not selected one. The classifier returns a list of labels with scores (which could be interpreted as ranking, multi-label, or distribution prediction), but the training loss was not specified (cross-entropy was proposed for single-label classification in the requirements). The evaluation metric is F1 (classification), but the product may benefit more from Precision@3 (ranking), NDCG (ranking with graded relevance), or KL divergence (distribution matching).

The critical point is that these are not interchangeable. A model trained with cross-entropy loss optimizes for a fundamentally different objective than a model trained with contrastive loss. Using one loss with a different evaluation metric constitutes a **specification mismatch** — the model is optimized for A and evaluated on B, with no formal relationship between the two. The F1 score of a model trained with cross-entropy may be arbitrarily far from the F1 of the same architecture trained with contrastive loss, and neither may correlate with product outcomes.

### 4.2 The Illusion of the Fixed 3,843-Class Space

The decision to fix the output space at 3,843 classes acquires a false precision. Several independent observations undermine the assumption:

**1. The 3,843 count is an artifact of a specific historical process.** The YQT taxonomy was designed by a committee at Yahoo! circa 2008–2010. The specific count of 3,843 is the result of that committee's aggregation and splitting decisions — one committee may have merged "Running Shoes" and "Athletic Footwear" while another kept them separate. The "true" number of learnable distinctions in the query space is unknown and unknowable from committee decisions.

**2. The entropy analysis undermines the precision it claims.** The intent-topology-memo (§4) shows that at K = 3,843, the marginal information gain per additional class is 0.15 bits. At K = 3,184 (Google's pruning threshold), it is 0.2 bits. The difference of 659 classes represents classes whose information content is below 0.05 bits each — below the measurement resolution of the entropy model. These 659 classes are, for practical purposes, indistinguishable from noise.

**3. The data budget cannot support 3,843 classes.** At 2M labeled queries (the upper end of the proposed data budget), the median class has ~20 examples (under Zipf α = 1.1). The bottom quartile of classes have <5 examples. The Universal Sentence Encoder finding (Cer et al., 2018) set a minimum of ~100 examples per class for usable performance. Under this heuristic:
   - Classes with ≥100 examples: ~150 classes (the head)
   - Classes with 20–100 examples: ~400 classes
   - Classes with <20 examples: ~3,293 classes
   
   **At most 550 of 3,843 classes (14%) are learnable from a 2M budget.** The remaining 86% are underspecified. The model will either treat them as indistinguishable noise or overfit to the 2–5 training examples available.

**4. This is not a data problem — it is a formulation problem.** One could argue that more data solves this. But the sample complexity grows superlinearly with the tail: to move the bottom quartile from 5 to 100 examples requires not 20× more data total (the median class already has 20) but a total corpus of ~80M queries — 40× the current budget. This is because the tail follows Zipf, and Zipf tails are expensive: 50% of classes cover only 5–10% of total volume. Saturating the tail requires corpus sizes that are infeasible for any but the largest search engines.

**The proper formulation would derive the learnable granularity from the data budget, not assert it a priori.** If the budget supports 550 learnable classes, the output space should have 550 classes, not 3,843. The remaining classes are noise — they will degrade the model's overall performance by introducing spurious distinctions that cannot be learned.

---

## 5. The Data Problem: The Relationship Between Training and Deployment Distributions Is Unknown

### 5.1 Distribution Shift

The proposed training protocol involves labeling queries via active learning from search logs. The deployment distribution will be whatever queries users submit to Deepl Search — an unknown quantity. These distributions are not identical; they may not even be close.

The MS MARCO dataset (used for all experiments) contains queries sampled from Bing search logs and filtered by human editors for relevance judgments. It is a **judgment corpus**, not a random sample of search traffic. Its distribution differs systematically from production search traffic in ways that affect intent classification:

| Property | MS MARCO | General Web Search (Beitzel, 2007) |
|----------|----------|-----------------------------------|
| Navigational + informational queries | Over-represented (needed for relevance judgments) | ~60% of traffic |
| Commercial queries | Under-represented (harder to judge) | ~30-40% of traffic |
| Mean query length | 5.6 tokens | 7.2 tokens |
| Query diversity (unique rate) | Lower (filtered for judgeability) | Higher (includes misspellings, non-English, spam) |

The relationship between any proposed training distribution and the unknown deployment distribution is **unspecified**. All F1 estimates (0.55–0.65 zero-shot, 0.70–0.80 supervised) are conditional on the training distribution — they may or may not hold at deployment.

### 5.2 The Feedback Loop

If a model classifies a query into an intent class, and the product surfaces content or ads based on that classification, the user's response (click, dwell, bounce) is a function of the model's **own output**. This introduces a feedback loop:

1. Model predicts query → Intent A
2. User sees results optimized for Intent A
3. User clicks on a result (because the UI was designed to maximize clicks)
4. Click is logged as a positive training signal for the (Query, Intent A) pair
5. Model reinforces Intent A prediction for similar queries

This feedback loop creates an **observational confounding**: the model does not observe counterfactual outcomes (what would the user have done if shown results for Intent B?). The logged signal is biased toward the model's existing predictions, suppressing exploration of alternative intents and creating a confirmation bias in the training data.

This is not a minor issue — it is a structural property of deployed ML systems with feedback loops (the "closed-loop" problem in reinforcement learning from logged data; see Bottou et al., 2013). No component of the current specification addresses it. The current framing assumes i.i.d. training data, but a deployed intent classifier generates non-i.i.d. data by influencing the user behavior that produces future training labels.

---

## 6. The Metric Problem: F1 Is Not a Product Requirement

### 6.1 The Proxy Mismatch

The evaluation metric F1 (harmonic mean of precision and recall) was chosen because it is the standard in the text classification literature. Its relationship to product outcomes has not been established:

- **If the product shows a dashboard of "emerging intents this week,"** F1 is not the right metric. F1 penalizes false positives equally to false negatives, but a missed emerging intent costs more than a spurious one (opportunity cost asymmetry). The product needs recall on trending intents more than it needs precision on stable ones.

- **If the product filters ad targeting,** the cost of misclassifying "shoe shopping" as "shoe research" (minor: both are shoe-related) is different from misclassifying "toothbrush" as "computer hardware" (major: completely wrong audience). But F1 weights all cross-class errors equally — a 3,843 × 3,843 uniform cost matrix is implicit.

- **If the product recommends content,** user engagement metrics (CTR, dwell time, session length) are the true objective. F1 is a proxy whose correlation with engagement has not been measured. A model with high F1 may produce poor recommendations (it correctly classifies the intent but the classification does not improve content relevance), and a model with low F1 could produce good recommendations (it is wrong about the intent but the surfaced content is nonetheless useful).

The proper approach would be to define a **cost matrix** $C \in \mathbb{R}^{3843 \times 3843}$ where $C_{ij}$ is the cost of predicting class $i$ when the true class is $j$. F1 is equivalent to $C_{ii} = 0, C_{ij} = 1$ for all $i \neq j$ — the uniform cost assumption. This assumption is almost certainly false for any real product, and its adoption without justification means the evaluation metric is **structurally misaligned** with the product objective.

### 6.2 The Stratification Gap

The requirements document proposes frequency-stratified Macro F1, which addresses one dimension of evaluation bias (frequency). But there are multiple independent stratification dimensions that affect evaluation, each of which reveals different aspects of model behavior:

| Stratification Dimension | Expected Effect | Why It Matters |
|--------------------------|----------------|----------------|
| **Query frequency** (head vs. tail) | Head: F1 > 0.85, Tail: F1 < 0.50 | Tail queries are the long tail product opportunity |
| **Ambiguity level** (inter-annotator disagreement) | Low-ambiguity: F1 > 0.80, High-ambiguity: F1 < 0.40 | High-ambiguity queries fundamentally cannot be classified with high confidence |
| **Query length** (short: <3 tokens, medium: 3–5, long: >5) | Short: lower accuracy (less signal), Long: BERT advantages appear | Determines model selection (fastText for short, BERT for long) |
| **Temporal era** (pre-2020 vs. post-2020) | Queries on new products/events have no training data | Tests the model's ability to generalize beyond training distribution |
| **Commercial vs. informational** | Commercial: higher annotations available, Informational: harder to judge | Asymmetric business value — commercial errors cost ad revenue, informational errors cost trust |
| **Language** (English vs. non-English) | English: F1 ~ baseline, Non-English: F1 – 10–20% | Cross-lingual generalization is not free |

The current evaluation plan stratifies only by frequency. The remaining dimensions are not tracked, so the project has no way of knowing where the model fails or why.

---

## 7. The Baseline Problem: We Do Not Know If the Problem Is Solvable

No trivial baseline has been computed. The literature provides several that should be established before any training:

**Baseline 1: Always predict the majority intent class.**
Under Zipf α = 1.1, the single most frequent intent class accounts for approximately 12% of queries (this is derivable from the rank-frequency distribution). A model that always predicts this class achieves:
- Micro F1 ≈ 0.12 (dominated by the 88% of queries that are NOT the majority class)
- Macro F1 ≈ 0.0003 (1/3,843) — essentially zero
This is the floor. Any useful model must clearly exceed these values.

**Baseline 2: Predict proportionally to class frequency (random weighted by prior).**
A model that produces random labels weighted by the training distribution achieves:
- Expected Micro F1 ≈ 0.003 (the sum of squared class probabilities for 3,843 classes under Zipf)
- This is the "null model" — it captures no information about the query
Any useful model must beat this by a statistically significant margin.

**Baseline 3: Predict the L1 parent class (8-way coarse classification).**
Reducing the problem to 8 classes (the L1 level) makes it comparable to the Hashemi et al. (2016) 14-class experiment, which achieved 90.3% accuracy. If an 8-way classifier achieves >90% accuracy (as literature suggests is feasible), it establishes:
- An **upper bound** on the coarse-grained problem difficulty
- The information lost by moving from 8 → 64 → 512 → 3,843 (accuracy must decrease as granularity increases)
- Whether the fine-grained problem is worth solving at all (if 90% of product value can be captured by 8 coarse classes, the 3,843-class effort may not justify its cost)

**Baseline 4: Lexical match baseline (heuristic rule-based classifier).**
A simple rule-based classifier that assigns classes based on keyword overlap:
- Queries containing "buy," "price," "shop," "order," "purchase" → Shopping
- Queries containing "how to," "what is," "tutorial," "guide" → Information
- Queries containing "vs." "or" "best" "top" → Comparison
This establishes what accuracy is achievable **without any ML**. If the lexical baseline achieves F1 = 0.40 and a BERT model achieves F1 = 0.45, the ML investment captured only 5 points of additional accuracy — a low return.

**Without these baselines, the project has no frame of reference.** A reported F1 of 0.55 is meaningless without knowing whether the lexical baseline scores 0.12 (good: 4.5× improvement) or 0.50 (marginal: 10% relative improvement). The former would justify the model investment; the latter would not.

---

## 8. The Temporal Problem: The Taxonomy Is Static, But Intent Is Dynamic

The taxonomy is specified as fixed (3,843 classes, immutable skeleton). Intent is not static:

**New products create new shopping intents.** "NFT," "AI assistant," "Tesla Cybertruck," "semaglutide" — none of these existed in the YQT's 2010 taxonomy. A system trained on the YQT classes would classify "how to buy an NFT" as "Other" (unclassified) or force it into the nearest existing class (e.g., "Digital Art"), which is wrong. This is not an edge case — every product category experiences this over time.

**Seasonal events shift intent distributions.** "Halloween costumes" appears in search logs for ~6 weeks per year, then effectively vanishes. It is a class with 51 weeks of near-zero volume and 1 week of high volume. A static model trained on year-round data underrepresents seasonal intents. The model performs poorly on these queries during their peak season precisely because they were rare during training.

**Language evolution changes the lexical mapping to intents.** The word "tweet" shifted from referring to birds (2008) to referring to social media posts (2012) to potentially something else (2026). A model that learned the 2008 mapping is wrong in 2026. Word embeddings capture some of this shift, but the taxonomy itself does not — the intent class "Social Media" was unlikely to exist in YQT's 2010 taxonomy at its current granularity.

The requirements document mentions periodic centroid recomputation, but does not specify:

1. **The detection mechanism:** How does the system know a new intent has emerged? The noise class accumulation rate? An external trigger (user report, trending query detection)?

2. **The time scale:** How often does the recomputation occur? Weekly? Monthly? Quarterly? Annually?

3. **The taxonomy update procedure:** When a new class is identified, what is the process for adding it? Who decides? How are existing queries reclassified?

4. **The stability–plasticity tradeoff:** Frequent taxonomy updates improve coverage but break backward compatibility (users who bookmarked or referred to a specific intent class find it renamed or split). Infrequent updates keep stability but increase the noise class.

The dismissal of this problem — "new intent classes are never added; queries that fall outside existing classes are assigned to noise and periodically reviewed for new L4 class creation" (intent-topology-memo, §5.2) — is not a solution but a deferral. The noise class accumulates queries at the rate of neologisms in search traffic. Over time, the noise class becomes the largest class. At that point, the taxonomy must be updated, but there is no specified procedure for doing so. The problem has been named but not solved.

---

## 9. The Problem Formulation Audit: What We Cannot Answer

The following questions are **currently unanswerable** from the project's documentation. Each represents a gap in the problem formulation.

### On the function

1. **What is the precise mathematical definition of $f: \mathcal{X} \rightarrow \mathcal{Y}$ that the system should learn?** Is $\mathcal{X}$ the space of all possible query strings? Is $\mathcal{Y}$ the space of probability distributions over 3,843 classes? The answer cannot be inferred from any existing document.

2. **Is $f$ a function in the mathematical sense (deterministic given input), or is the true mapping stochastic?** If two users enter the same query with different intents, the mapping is not a function — it is a conditional distribution. The current framing assumes a function exists, which is untested.

3. **If the mapping is stochastic, what is the irreducible variance — the aleatoric uncertainty inherent to the query → intent problem?** This sets the upper bound on achievable accuracy, regardless of model capacity or data volume.

### On learnability

4. **Is $f$ learnable from the proposed $\mathcal{X}$ (query text only)?** What is the evidence that query text alone contains sufficient information to determine intent? The Jansen (2009) finding that 25.8% of errors are session-level suggests it is not.

5. **If $\mathcal{X}$ is insufficient, what additional input dimensions would make $f$ learnable?** Session context? User profile? Temporal features? The input space should be expanded until the irreducible error falls below the required threshold.

6. **What is the sample complexity of the proposed hypothesis class?** How many labeled examples are required to achieve the target error rate with probability ≥ 1 − δ under the PAC framework? The current data budget (400K–2M) has no theoretical foundation.

### On evaluation

7. **What is the cost matrix for prediction errors, and how was it derived from product requirements?** Without this, F1 is a meaningless default — it assumes all errors cost the same.

8. **How does the chosen metric correlate with the product's true objective?** If the intended metric is F1, what is the evidence that improving F1 improves product outcomes? Has this correlation been measured, even in a pilot study?

9. **What is the minimum acceptable performance threshold?** Below what F1 value is the model unusable by the product? This determines whether the problem is worth solving at all.

10. **What is the protocol for detecting and responding to distribution shift at deployment?** Static evaluation on held-out data assumes the deployment distribution matches the training distribution — an assumption that is violated for every deployed ML system.

### On the taxonomy

11. **Is the YQT taxonomy optimal for Deepl Search's specific product objective, or merely convenient?** This is the central architectural question, and it has not been answered.

12. **What fraction of the 3,843 classes are learnable from the proposed data budget?** The analytic estimate is <14% (≤550 of 3,843 with ≥100 examples). If this is accurate, the output space must be reduced.

13. **What is the procedure for merging underspecified classes until sufficient data density exists?** If 86% of classes are underspecified, there must be a principled merger strategy, not a uniform "train anyway" approach.

14. **How are new intents detected, evaluated, and integrated into the taxonomy over time?** The noise class is not a solution — it is an acknowledgment that the problem exists.

### On baselines

15. **What does "always predict the most frequent class" score?** (Expected: Micro F1 ≈ 0.12)

16. **What does a lexical heuristic baseline score?** (Expected: F1 ≈ 0.30–0.50, depending on taxonomy specificity)

17. **What does an 8-way parent-level classifier score?** (Expected: accuracy ≥ 0.85, based on Hashemi, 2016)

18. **Does the gap between the lexical baseline and the proposed model justify the model's complexity and cost?** If the lexical baseline achieves F1 = 0.40 and the target is F1 = 0.55, the model closes a 0.15 gap. If training the model costs $50K and the product needs 1M queries/month for 6 months to recover that cost, is the investment justified?

### On the deployment context

19. **At what query volume will the system operate?** This determines whether fastText's CPU throughput (1M queries/second/core) is sufficient or BERT's GPU throughput (~5K queries/second) is needed.

20. **What is the latency requirement?** A real-time ad server needs <10ms per query. A batch analytics pipeline can tolerate 1 second per query. These constraints imply different architectures.

21. **Who or what consumes the model's output?** A human analyst looking at a dashboard can tolerate noise better than an automated ad-bidding system that makes financial decisions based on the classification. The consumer determines the acceptable error rate.

---

## 10. Synthesis: The Current State as a Pre-Paradigmatic Science

The current state of the Deepl Search intent classification project resembles what Kuhn (1962) called the **pre-paradigmatic stage** of a scientific field: a collection of techniques, tools, and observations without a unifying framework that specifies what counts as a solution, what constitutes progress, and how to adjudicate between competing approaches.

The project has produced genuine technical artifacts:
- A verified structural analysis of commercial search taxonomies (intent-topology-memo.md)
- A 3,843-class taxonomy skeleton with SKOS export (src/taxonomy.py)
- An embedding-based classifier (src/classifier.py)
- A FastAPI serving layer (src/api.py)
- A 3.08:1 advertiser pruning model (src/ads_mapping.py)
- A conference-style thesis paper (the_octohedral_intent_hypothesis.md)
- ML training requirements derived from literature (ml-training-requirements.md)

These artifacts are internally coherent. The taxonomy skeleton correctly implements the YQT structure. The embedding classifier produces outputs at sub-30ms latency. The API serves production traffic. The training requirements cite appropriate literature.

**The problem is not that these artifacts are wrong. It is that they are solutions to an unspecified problem.**

The project progressed from literature extraction → taxonomy discovery → architecture decisions → pipeline construction without ever completing the intermediate step that bridges taxonomy to product: **the problem formulation.** This is visible in the questions the project cannot answer:
- What function are we learning? (unknown)
- What data distribution will we encounter? (unknown)
- What cost does each error carry? (unknown)
- What baseline performance indicates success? (unknown)
- What accuracy is required for the product to function? (unknown)

Each of these questions has an answer, but none has been produced. The project jumped from "here is an interesting structural finding about taxonomies" to "here is a 5-module production pipeline" without the essential intermediate step that connects empirical discovery to engineering application.

### A Path Forward

The path to a **paradigmatic** formulation requires completing five steps in order, where each step produces a document that the next step depends on:

**Step 1: Product Decision Analysis**
Who makes what decision using the model's output? What alternatives do they consider? What information do they currently use, and what new information would the model provide? What is the cost of each type of error in that decision context?

**Step 2: Problem Derivation**
From Step 1, derive the mathematical specification:
- $\mathcal{X}$ = what inputs are available at decision time? (query text? session? user? time? page content?)
- $\mathcal{Y}$ = what outputs serve the decision? (single class? ranking? distribution? weight vector?)
- $\ell$ = what are the relative costs of each error type? (cost matrix derived from Step 1)

**Step 3: Learnability Analysis**
Given $\mathcal{X}$, $\mathcal{Y}$, and the available data budget, is $f$ learnable? Compute sample complexity bounds. Compute the irreducible error. If $f$ is not learnable, iterate back to Step 2 (different $\mathcal{X}$, different $\mathcal{Y}$, or different cost structure).

**Step 4: Baseline Establishment**
Compute trivial baselines (most-frequent class, lexical heuristic, coarse-grained classifier). If any baseline meets the required performance from Step 1, the ML model is unnecessary. Document this decision explicitly.

**Step 5: Evaluation Protocol**
From the cost matrix (Step 2), derive the evaluation metric. Stratify by all dimensions that affect error rates (frequency, ambiguity, length, temporality, commerciality, language). Specify the minimum acceptable performance for each stratum.

Only after these five steps can the engineering work — model selection, data acquisition, training, deployment — proceed with confidence that the system being built is the right system to build.

---

## References

- Beitzel, S. M., Jensen, E. C., Chowdhury, A., Frieder, O., & Grossman, D. (2007). Temporal analysis of a very large topically categorized web query log. *Journal of the American Society for Information Science and Technology*, 58(2), 166–178.
- Bottou, L., Peters, J., Quiñonero-Candela, J., Charles, D. X., Chickering, D. M., Portugaly, E., ... & Snelson, E. (2013). Counterfactual reasoning and learning systems: The example of computational advertising. *Journal of Machine Learning Research*, 14(1), 3207–3260.
- Cer, D., Yang, Y., Kong, S. Y., Hua, N., Limtiaco, N., John, R. S., ... & Kurzweil, R. (2018). Universal Sentence Encoder. *arXiv:1803.11175*.
- Domingos, P. (2012). A few useful things to know about machine learning. *Communications of the ACM*, 55(10), 78–87.
- Hand, D. J. (2006). Classifier technology and the illusion of progress. *Statistical Science*, 21(1), 1–14.
- Hashemi, S. H., et al. (2016). Query intent detection using convolutional neural networks. *arXiv:1610.02859*.
- Jansen, B. J., Booth, D. L., & Spink, A. (2009). Patterns of query reformulation during web searching. *Journal of the American Society for Information Science and Technology*, 60(7), 1358–1371.
- Kuhn, T. S. (1962). *The Structure of Scientific Revolutions*. University of Chicago Press.
- Pinterest (2020). Query2Interest: Query to interest mapping at Pinterest.
- Varian, H. R. (2007). Position auctions. *International Journal of Industrial Organization*, 25(6), 1163–1178.
