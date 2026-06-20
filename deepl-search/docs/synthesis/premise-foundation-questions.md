# Premise Foundation Questions
Methodology (lines 3-7, 953-981):
1. Identify a foundational assumption — something taken as given without evidence
2. Challenge it — "What if X is not true?" Support with literature (Jansen, Timoshenko, etc.)
3. Enumerate doors — conservative (same architecture, different parameter), moderate (new component), radical (complete redesign)
4. Smallest falsifying experiment — cheapest test with a clear decision rule (TRUE → continue, PARTIAL → adapt, FALSE → redesign)
5. Branch on result — the experiment determines the architecture, not prior preference
Intellectual lineage: Kuhn (paradigm shifts in Structure of Scientific Revolutions), Popperian falsification, Domingos' "a few useful things to know about ML", and lean methodology's "smallest experiment" principle.
> Questioning every foundational assumption to open innovative alternatives.
> If the premise holds → continue. If weakened → adapt. If flipped → radical redesign.

**Method:** For each premise we've been operating under, identify the assumption, challenge it,
and enumerate the doors it opens — from conservative adaptations to radical reimaginings.

---

## Premise 1: The Query Is the Unit of Analysis

### The Assumption

Every component of the current system treats the individual search query as the atomic unit.
The classifier takes one query and returns one intent vector. The taxonomy was designed around
single-query classification. The evaluation measures per-query accuracy.

### The Challenge

**What if the unit should be the session, the user, or the page — not the query?**

A user searching "baby stroller" → "best 2025" → "reviews" → "buy" across four queries is
expressing a single intent trajectory: "purchase research for baby strollers." No single query
carries this complete intent. Jansen et al. (2009) found that 25.8% of query classification
errors vanish when session context is available — because the session *is* the unit of intent,
not the query.

### Doors This Opens

**Door 1.1 — Session-as-unit (conservative):**
Replace single-query classification with session-level classification. Aggregate the last N
queries (N=3-5) as a single input. Architecture: concatenate query embeddings with an RNN or
transformer over the session sequence. The model learns intent trajectories. This eliminates
the Jansen 25.8% error with a modest architecture change.

**Door 1.2 — Intent state machine (moderate):**
Model sessions as a probabilistic state machine over intent classes. A session starts in a
"discovery" state, transitions through "research" → "comparison" → "purchase intent." Each
state has a different emission distribution over queries. This captures the temporal structure
of intent evolution. Query-to-intent becomes query-to-state-transition.

**Door 1.3 — User-as-unit (radical):**
Aggregate all queries from a user over a time window (7 days, 30 days) into a user intent
profile. The model predicts a user's overall intent vector, and individual queries are
contextualized within it. A user who has clicked on 50 running shoe pages in the last week
is in "running shoe purchase research" — regardless of whether the current query is "best
running shoes" or "weather today" (the latter might be checking weather for their run).

**Door 1.4 — Page-as-unit (lateral):**
What if we're solving the wrong problem? Users don't search — they *land*. Instead of
classifying the query, classify the **landing page** the user ends up on. The intent is in
the content consumed, not the query string. Architecture: content classifier (page text →
intent vector) replaces query classifier. Query is just a noisy signal for the page the user
actually wanted.

**Door 1.5 — Session synthesis (the synthetic context approach from GAP-2):**
Train a model to **impute the missing session context** from the query alone. Given query Q,
predict the distribution of session states that typically produce Q. This turns the session
context from a required input into a latent variable — the model learns the context from
historical session data and uses it at inference time even when only the query is available.

**Door 1.6 — Multi-resolution unit:**
Use different units for different levels of the taxonomy. L1 (macro-category) is predicted
from user-level aggregates (this user mostly shops). L4 (specific intent) is predicted from
the current query-session. The taxonomy hierarchy becomes a resolution hierarchy, not just
a prefix tree.

---

## Premise 2: Intent Lives in Query Text

### The Assumption

The query string contains sufficient information to determine the user's intent. The system
takes raw query text as input and maps it to an intent class.

### The Challenge

**What if the query text is not the carrier of intent but a pointer to a context where
intent is resolved?**

The same query "best running shoes" reflects:
- Shopping intent (user who has never bought running shoes)
- Comparison-shopping intent (user who has read 5 reviews, detectable from session history)
- Information-seeking intent (user researching the category before purchase)
- Seasonal re-check (user checking if their model is still the best)
- Work-related (SEO analyst researching the category for content strategy)

The query text is ambiguous not because of model limitations but because intent *does not live
in the query*. It lives in the **intersection of query, user state, and context**. The query
is a pointer to a context — it disambiguates only when the context is known.

### Doors This Opens

**Door 2.1 — Behavioral signal augmentation (conservative):**
Augment query input with behavioral features: user's historical click entropy, session dwell
time before query, device type, time since last query, number of queries in session. These
features are available at inference time (no user history required) and carry intent signal.
A gradient-boosted model over query + behavioral features outperforms a pure text model.

**Door 2.2 — Query as latent variable query (moderate):**
Model intent as $P(\text{intent} \mid \text{query, context})$ where context is a latent
variable inferred from the query via a learned prior. This is a variational autoencoder
architecture: the encoder maps query → latent context distribution; the decoder maps
(query, latent context) → intent distribution. At inference, sample from the latent prior.

**Door 2.3 — Distant supervision from user behavior (radical):**
Don't learn intent from text at all. Learn it from **post-query behavior**. Given a query Q:
- User clicks result R and dwells >30s → the intent is the theme of R
- User bounces within 5s → the intent was not satisfied by R
- User refines the query → the original intent was too broad
- User converts (buys, signs up) → the intent was commercial

Train on (query, result, behavior) triples from search logs. The model learns to predict
intent from query+result without any human labels. This is behavioral supervision —
potentially unlimited training data at zero annotation cost.

**Door 2.4 — Multi-modal intent inference (moderate):**
Search queries are not the only signal. On a shopping site: product page views, cart adds,
wishlist saves. On a content site: article reads, video watches, scroll depth. On a
social platform: likes, shares, follows. Each of these is an expression of intent in a
different modality. Fuse them: query text + page type + interaction type → intent vector.

**Door 2.5 — Intent as revealed preference:**
Abandon the idea that intent is hidden in the user's mind and needs to be "detected."
Define intent operationally: a user's intent is the set of actions they are likely to take.
Learn to predict actions (click product, read review, watch video, compare prices) directly
from query text. The intent class is a summary of predicted actions, not an underlying truth.

**Door 2.6 — Generative intent refinement:**
Use an LLM to generate the context that disambiguates the query. Prompt: "Given the search
query 'best running shoes,' what are 3 plausible user scenarios that would produce this
query?" Use the generated scenarios as synthetic context for downstream classification.
This is cheap ($0.001 per query) and works today.

---

## Premise 3: 3,843 Classes Is the Correct Target

### The Assumption

The output space is fixed at 3,843 leaf classes, structured as 8→64→512→3,843. This is the
optimal granularity for intent classification.

### The Challenge

**What if the taxonomy should be learned from the data, not imposed on it?**

The 3,843 count is an artifact of Yahoo!'s 2008–2010 committee process. The entropy analysis
(intent-topology-memo §4) shows that at K=3,843, the marginal information gain per class is
0.15 bits — barely measurable. At 2M labeled queries, the bottom 50% of classes have <5
examples each. The taxonomy asserts a granularity that the data cannot support.

### Doors This Opens

**Door 3.1 — Data-driven granularity (conservative):**
Instead of fixing K=3,843, use the data to find the optimal K. Train the model at multiple
resolutions (K=500, 1K, 2K, 3K, 3,843, 5K). For each K, measure (a) coverage (fraction of
queries assigned to a leaf class), (b) density (median queries per class), (c) F1 on a
held-out set. The optimal K is where marginal F1 gain per class drops below a threshold.
This is the **empirical elbow**, not the analytic one. It may be 800 or 1,500 or 5,000 —
the data decides.

**Door 3.2 — Variable-resolution taxonomy (moderate):**
Let different branches of the taxonomy have different depths. Some L1 categories (Shopping,
Technology) may support 8→64→512→3,843. Others (Education, Health) may only support
8→32→128 (shallower because fewer fine-grained distinctions are learnable). The taxonomy
becomes an unbalanced tree, pruned per-branch by the available data density.

**Door 3.3 — Flat embedding with learned structure (radical):**
Don't use a taxonomy at all. Learn a 64-dim or 128-dim embedding space for queries. Let
clustering emerge naturally. Post-hoc, map emergent clusters to YQT classes for
interpretability. The model discovers the granularity the data supports; the taxonomy serves
as a *labeling* of the emergent structure, not a *constraint* on it.

**Door 3.4 — Hierarchical latent variable model:**
Replace the fixed taxonomy with a learned latent hierarchy. Train a deep generative model
where the latent space has a tree structure (a hierarchical VAE or a nested Chinese
Restaurant Process). The model learns how many L1 categories, L2 categories, etc. the data
supports. No fixed K at any level. This is non-parametric Bayesian — the complexity grows
with the data.

**Door 3.5 — Adaptive granularity per query:**
Don't force every query to an L4 leaf. Classify at the coarsest level supported by
confidence. A query with high confidence → L4 leaf. A query with low confidence → L3
parent. A query with very low confidence → L1 macro-category. The model adaptively selects
the right resolution for each query. This is **hierarchical classification with a
confidence-based stopping rule**.

**Door 3.6 — Soft taxonomy (label embedding):**
Replace hard class IDs with continuous label embeddings. Each query maps to a point in
$\mathbb{R}^d$. Each intent concept is also a point. The "class" is the nearest neighbor.
But "nearest" is defined by a learned metric that can shift as data accumulates. The
taxonomy is the embedding space — it supports a continuum of granularity, not discrete
classes.

**Door 3.7 — Octohedral structure as regularization prior:**
Use the 8→64→512→3,843 structure as a Bayesian prior, not a fixed constraint. The model
starts with the YQT skeleton as its initial hypothesis. As data accumulates, the structure
can change. New branches can grow, low-density branches can merge. This is the **living
taxonomy** approach: the octohedral structure guides initialization but does not constrain
learning.

---

## Premise 4: Human Labels Are Ground Truth

### The Assumption

The training data consists of (query, intent_class) pairs labeled by human annotators.
The annotators' judgments define the correct answer. The model's goal is to match human
judgment.

### The Challenge

**What if human labels are not ground truth but a weak signal with known biases?**

Timoshenko found inter-annotator agreement of 70% — meaning 30% of labels are effectively
random (different annotators disagree). NotebookLM found agreement plateaus at 85-90%.
If annotators agree at 70%, and the model achieves 75%, the model has "outperformed" humans
on a task where humans can't agree on the answer. The 75% F1 is not meaningful accuracy —
it is partially memorizing one annotator's idiosyncratic judgments over another's.

Moreover, human annotators cannot access the session context, user history, or behavioral
signals that the model could use. They label from query text alone (or with minimal context).
The human label is a lower bound on what the model could achieve with richer inputs.

### Doors This Opens

**Door 4.1 — Multi-annotator consensus model (conservative):**
Collect labels from 3+ annotators per query. Train the model on the consensus distribution,
not a single label. Use a soft target: $P(\text{class}_i) = \frac{\text{annotators who chose
class}_i}{\text{total annotators}}$. The model learns that some queries are ambiguous
(distribution has high entropy). This is **label smoothing with a principled basis**.

**Door 4.2 — Learn from disagreement, not despite it (moderate):**
Annotator disagreement is signal, not noise. Train a secondary model that predicts *which*
queries will have high inter-annotator disagreement. These are the queries where session
context, user history, or behavioral signals are most needed. Build a cascade:
- High agreement queries → fast classifier
- Low agreement queries → context-augmented classifier (uses session/history data)
This allocates expensive computation to the queries that need it most.

**Door 4.3 — Labels as weak supervision + behavioral refinement (radical):**
Use human labels only to initialize the model. Then refine with behavioral supervision
(see Door 2.3). The training signal shifts from "what the annotator said" to "what the user
actually did." A query labeled "Shopping" by an annotator, but which consistently leads to
informational pages → the behavioral signal corrects the annotation. The model learns intent
from revealed behavior, not stated judgment.

**Door 4.4 — Active label acquisition for disagreement:**
Instead of labeling a random sample, label only the queries the model is most uncertain
about. Train on the current model's uncertainty + human labels for uncertain queries only.
This is standard active learning, but applied to the label acquisition bottleneck. JointMap
(2005.13783v2) showed 80% label savings.

**Door 4.5 — LLM-as-annotator with confidence calibration:**
Use an LLM (GPT-4o, Claude 3.5) as the primary annotator. The LLM labels each query with a
confidence score. Only queries with LLM confidence below a threshold (<0.7) go to human
annotators. This reduces human annotation volume by 80-90% while maintaining quality.
The LLM's confidence calibration can be validated against a small human-labeled set.

**Door 4.6 — Label-free evaluation via behavioral validation:**
Instead of measuring F1 against human labels, measure **behavioral consistency**: does the
model's classification predict user behavior? For a query classified as "Shopping," does the
user click on product pages at a higher rate than for "Information" queries? If yes, the
model's classification is useful even if it doesn't match human labels. This breaks the
dependency on ground truth entirely.

**Door 4.7 — Intent as an invariant across annotators:**
Train a model that predicts the **intersection** of annotator judgments, not the union.
If annotator A labels "Shopping" and annotator B labels "Comparison," there exists a latent
class "Purchase Research" that encompasses both. Train a VAE that learns this latent class
structure. The model discovers the intent categories that are invariant across human
annotation styles — potentially more robust than any single annotator's labels.

---

## Premise 5: Classification Is the Correct Paradigm

### The Assumption

Intent prediction is a classification problem: the query belongs to one or more discrete
classes. The model's job is to predict the correct class label.

### The Challenge

**What if classification is the wrong mathematical framing for this problem?**

Classification assumes:
1. **Exhaustive classes:** Every query belongs to exactly one class (or a known set).
2. **Mutually exclusive boundaries:** Classes have decision boundaries; queries are on one
   side or the other.
3. **Fixed label set:** The set of classes is known a priori and does not change.

All three assumptions are violated in the intent domain:
1. Queries can express novel intents not in the taxonomy.
2. Intents blend into each other — "Shopping" and "Comparison" are not separated by a
   boundary but by a continuum.
3. New intents emerge continuously (NFTs, AI assistants, new products).

### Doors This Opens

**Door 5.1 — Retrieval instead of classification (conservative):**
Frame as retrieval: for each query, retrieve the top-K most similar intent classes from the
taxonomy. Use a bi-encoder (query encoder + class encoder) with cosine similarity. No
decision boundary — just similarity. Handles novel intents (if no class is similar enough,
retrieval returns nothing) and graded relevance (classes have similarity scores, not
membership probabilities).

**Door 5.2 — Ranking instead of classification (moderate):**
Frame as ranking: for each query, produce a ranked list of intent classes. The evaluation
metric is NDCG or MAP, not F1. This avoids the thresholding problem (thresholds are
arbitrary and domain-dependent) and naturally supports multi-label (the top-K can include
multiple relevant classes).

**Door 5.3 — Density estimation in intent space (radical):**
Learn a density model over the joint space of (query, intent). A query is a point in query
embedding space; an intent class is a region in the same space. Instead of classifying,
estimate $P(\text{query} \mid \text{intent})$ for each intent, then use Bayes' rule to get
$P(\text{intent} \mid \text{query})$. This naturally handles multi-label (queries can fall
into overlapping regions) and out-of-taxonomy queries (queries in low-density regions are
novel).

**Door 5.4 — Multi-task: predict intent + behavior + content:**
Instead of a single classification head, train a multi-task model that simultaneously
predicts:
- Intent class (classification head)
- User behavior (click-through rate, dwell time — regression head)
- Content type (product page, review, article — classification head)
- Conversion probability (binary classification head)

The shared representation learns richer features because it must explain multiple aspects of
the user's experience. The intent classification benefits from the auxiliary tasks — this is
the standard multi-task learning result (Caruana, 1997).

**Door 5.5 — Contrastive learning of intent similarity:**
Don't predict classes at all. Learn an embedding space where queries with the same behavior
pattern (same click distribution) are close, and queries with different behavior patterns are
far. The intent class is then a cluster in this space, not a label. This is self-supervised:
the training signal is behavioral similarity, not human annotation.

**Door 5.6 — Set prediction for multi-intent queries:**
For queries with multiple intents, predict a **set** rather than a vector. Set prediction is
a distinct mathematical paradigm: the model outputs a variable-size set of classes, and the
loss is a bipartite matching between predicted and true sets (the Hungarian loss used in
object detection). This handles the variable number of intents per query naturally — some
queries have 1 intent, some have 3+.

**Door 5.7 — Generative modeling of the query-intent joint distribution:**
Train a masked language model (like BERT but on query-intent pairs) that can both:
- Given a query, predict the intent distribution (fill in the masked [INTENT] token)
- Given an intent, generate likely queries (inverse mapping)

The generative framing captures the full joint distribution $P(\text{query, intent})$ rather
than just the conditional $P(\text{intent} \mid \text{query})$. The inverse mapping
(intent → queries) is useful for understanding what each intent class means operationally.

---

## Premise 6: F1 Measures Success

### The Assumption

The model's performance is measured by F1 (harmonic mean of precision and recall) on a
held-out test set. Higher F1 = better model.

### The Challenge

**What if F1 is actively misleading product development?**

F1 penalizes all errors equally. A cross-L1 error (predicting "Health" when true is
"Shopping") costs the same as a within-L3 error (predicting "Road Running" when true is
"Trail Running"). In any real product, these costs differ by orders of magnitude.

F1 also ignores the **decision context**. An error on a high-volume query with commercial
intent (lost revenue) costs more than an error on a rare informational query (essentially
free). F1 treats them identically.

F1 is a proxy for what matters. The question is: how good a proxy?

### Doors This Opens

**Door 6.1 — Cost-weighted F1 (conservative):**
Replace standard F1 with cost-weighted F1, where each error is weighted by the cost matrix
defined in Step 1 (cross-L1 errors weighted 1.0, within-L3 errors weighted 0.1, commercial
FPs weighted 2.0). This immediately aligns the metric with product reality.

**Door 6.2 — Utility-based evaluation (moderate):**
Stop measuring F1 on the model. Measure the product outcome directly:
- For ad use case: advertiser ROI, user ad click-through rate
- For analytics use case: time analyst spends validating vs. acting on the data
- For content use case: user engagement rate, session length
The model is evaluated by the improvement it drives in these metrics, not by its agreement
with human labels.

**Door 6.3 — Multi-metric dashboard:**
Replace single F1 with a dashboard of metrics, each measuring a different aspect of quality:
- **Precision@3 on head classes** (does the model get the common queries right?)
- **Recall on tail classes** (does the model find the rare, valuable intents?)
- **Temporal stability** (does the same query get the same intent next week?)
- **Cross-L1 error rate** (are gross errors rare?)
- **Calibration error** (does confidence 0.7 mean 70% correct?)
- **Novelty detection rate** (how often does the model flag a new intent?)
The model development process optimizes the metric that is currently worst, not a single
number.

**Door 6.4 — Human-in-the-loop evaluation:**
Instead of an automated F1 score, use a human-in-the-loop evaluation where an analyst
reviews a sample of model predictions weekly and provides qualitative feedback. The analyst
can identify systematic error patterns that F1 cannot: "The model is confusing brand names
with product categories, especially in the technology vertical." This is expensive but
produces insights no automated metric can capture.

**Door 6.5 — Online A/B testing as primary evaluation:**
The only metric that matters is the online metric. Run A/B tests:
- Treatment: model-based intent classification serves content/ads
- Control: existing keyword-based or heuristic approach
- Measure: user engagement, advertiser ROI, analyst productivity
If treatment outperforms control on the online metric, the model is good regardless of its
F1 score. If it doesn't, the model needs to change regardless of its F1 score.

**Door 6.6 — Task-specific evaluation for each consumer:**
Different consumers get different evaluation reports:
- For the analytics dashboard: distributional similarity (KL divergence between predicted
  and true intent distributions over a time window)
- For the ad server: Precision@commercial, recall@commercial, latency percentiles
- For the content recommender: NDCG@3, Mean Reciprocal Rank
- For the market research tool: trend detection recall, false alarm rate
Each consumer evaluates the model on the metric that predicts their outcome of interest.

---

## Premise 7: The Taxonomy Is Static

### The Assumption

The 3,843-class tree is immutable. IDs are fixed. New classes are never added. Queries
outside the taxonomy fall to a catch-all "Other" class.

### The Challenge

**What if a static taxonomy is impossible at web scale?**

New products, brands, and needs emerge weekly. "Semaglutide" (a weight-loss drug) generated
5M+ searches in 2023 — it was not in any pre-2020 taxonomy. The YQT taxonomy itself was
frozen in 2015. A static taxonomy on a dynamic phenomenon guarantees coverage decay.

### Doors This Opens

**Door 7.1 — Periodic taxonomy refresh (conservative):**
Replace the static taxonomy with a versioned taxonomy that releases a new version every 6-12
months. Each version is a superset of the previous version (classes are never removed, only
added or split). A mapping table from old IDs to new IDs maintains backward compatibility.
This is what Wikipedia does (the category hierarchy evolves) and what Google Merchant does
(5,527 categories in the 2024 version, up from ~4,000 in 2020).

**Door 7.2 — Living taxonomy with birth/death processes (moderate):**
Implement a continuous evolution mechanism:
- **Birth:** When the "Other" class accumulates >X queries in a time window, run clustering
  on those queries. If a dense cluster emerges, create a new L4 class for it, nested under
  the appropriate L3 parent. A human reviews and approves.
- **Death:** When an L4 class has <Y queries for Z consecutive months, merge it into its L3
  parent. Its queries are re-assigned.
- **Split:** When an L4 class has high internal diversity (queries form 2+ sub-clusters),
  split it into multiple L4 classes.

This is the **living taxonomy** — it grows, shrinks, and restructures in response to the
query stream.

**Door 7.3 — Continuous embedding update without taxonomy change (moderate):**
Keep the taxonomy IDs fixed but update the embedding centroids continuously. As new queries
arrive, the centroid for each class shifts to reflect the current query distribution. The
classes are conceptually the same (their IDs are stable) but their denotation evolves. This
is what Google does: the taxonomy is stable, but the BERT model that maps queries to classes
is updated quarterly.

**Door 7.4 — Versioned taxonomy with migration (radical):**
Every year, release a new taxonomy version. Each version is independently constructed (it
does not need to be backward compatible). The system maintains a version-to-version mapping
table. A query classified in v2024.1 can be mapped to v2025.1 through the mapping. This
requires a human-in-the-loop mapping process but allows the taxonomy to fully reflect the
current query landscape without being constrained by 2008 committee decisions.

**Door 7.5 — Taxonomy as emergent property of embedding space:**
Decouple the taxonomy (human-readable labels and hierarchy) from the classification system
(embedding space with learned structure). The embedding space evolves continuously. The
taxonomy is a **snapshot** of the embedding space at a point in time, generated by
clustering and labeling the emergent clusters. Each snapshot becomes a new taxonomy version.
Users interact with the snapshot; the model trains on the evolving embedding.

---

## Premise 8: English-First, Multilingual Later

### The Assumption

The taxonomy is English-centric. Non-English queries will be handled later, possibly via
translation before classification.

### The Challenge

**What if the taxonomy should be multilingual from day one?**

Translation-before-classification loses cultural context. "Ropa" (Spanish for "clothing") and
"clothing" are the same intent, but a Spanish speaker searching "ropa deportiva" may have
different purchase intent than an English speaker searching "sportswear" (different brands,
different price sensitivity, different seasonality). Translation erases these distinctions.
Cross-lingual embeddings (LASER, LaBSE) embed sentences from 93 languages in a shared space
without translation, preserving cultural context.

### Doors This Opens

**Door 8.1 — Cross-lingual embedding space (conservative):**
Use a cross-lingual sentence encoder (LaBSE, LASER, or multilingual SBERT) for both query
embedding and class definition embedding. English, Spanish, Japanese, etc. queries about
"running shoes" all map to the same region in embedding space. The classifier operates in
this shared space — no translation step required. Empirical result from LASER: zero-shot
cross-lingual transfer achieves >80% of supervised accuracy.

**Door 8.2 — Language-agnostic class definitions (moderate):**
Define each intent class not by an English name but by a **multilingual definition set**:
3-5 representative queries in each supported language. The class definition for "Running
Shoes" includes "running shoes," "zapatillas para correr," "ランニングシューズ," etc.
The embedding centroid of the definition set becomes the class anchor. A query's distance
to this centroid is language-independent.

**Door 8.3 — Language-specific sub-branches (lateral):**
Keep the top 3 levels of the taxonomy language-agnostic (L1–L3 are universal). At L4,
allow language-specific leaf classes. "Fútbol" (Spanish) and "soccer" (American English)
refer to the same sport but have different cultural associations, advertiser landscapes,
and seasonal patterns. Language-specific L4 leaves capture these differences while sharing
the universal L1-L3 structure.

**Door 8.4 — Intra-language synonym clusters:**
For each language, learn synonym clusters (sets of words/phrases that express the same
intent within that language). A query in any language maps to a synonym cluster, then the
cluster maps to an intent class. This decouples the number of surface forms from the number
of intent classes — 100 languages × 10 synonyms each = 1,000 surface forms mapping to 1
intent class. The model learns the synonym structure from unlabeled query logs via
distributional similarity.

**Door 8.5 — Intent universality hypothesis testing:**
Use the cross-lingual model as a **test** of the Octohedral Hypothesis. If the same
8→64→512→3,843 structure emerges independently from non-English search logs (Baidu for
Chinese, Naver for Korean, Yandex for Russian), then the structure is truly universal.
If different structures emerge, the Octohedral convergence is a Western-market phenomenon,
not a cognitive universal. This turns the multilingual problem into a scientific experiment.

---

## Premise 9: The Data Bottleneck Is Labels

### The Assumption

The scarce resource is labeled training data. We need more human annotations to improve the
model.

### The Challenge

**What if the bottleneck is not labels but query diversity?**

At 2M labeled queries, the bottom 50% of classes have <5 examples. Adding more labels at
the same query distribution does not help the tail — it just densifies the head. The tail
classes have few examples not because they are unlabeled but because **few queries belong
to them**. The Zipf distribution means that even with infinite labels, the tail classes will
always have few examples. The bottleneck is the natural frequency of rare intents, not the
annotation budget.

### Doors This Opens

**Door 9.1 — Synthetic query generation for tail classes (conservative):**
Use an LLM to generate synthetic queries for low-volume intent classes. Prompt: "Generate
50 realistic search queries that express the intent {Intent Name} in a {Language} search
engine." This costs <$0.50 per class. For the 2,000 tail classes, that's ~$1,000 for
100,000 synthetic queries. The synthetic queries are not as good as real ones (distribution
shift), but they provide the initial density that allows the model to learn the tail at all.
This is the **data augmentation escape valve**.

**Door 9.2 — Few-shot / meta-learning for rare intents (moderate):**
Instead of generating synthetic data, learn a meta-learning algorithm (MAML, Prototypical
Networks) that can classify a new intent from 1-5 examples. The meta-learner is trained on
head classes (which have many examples) and generalizes to tail classes (which have few).
The model learns "how to learn a new intent" rather than memorizing each intent's decision
boundary. Literature: MAML achieves 85%+ accuracy with 5 examples per class.

**Door 9.3 — Intent decomposition into primitives (radical):**
Decompose each intent class into a set of **atomic intent primitives**: {Commercial, Social,
Temporal urgency, Geographic scope, Product category, Brand relevance, ...}. Instead of
learning 3,843 independent classes, learn to predict 15-20 primitives from the query, then
combine them compositionally to form intent classes. A class is a pattern over primitives:
"Shopping for running shoes" = {Commercial=true, ProductCategory=AthleticFootwear,
BrandRelevance=Medium, ...}. New intents are new combinations of existing primitives —
learnable from few examples because the primitives transfer.

**Door 9.4 — Transfer from head to tail via prototype refinement:**
Train a prototype-based classifier: each class is represented by a prototype (a weighted
average of its training examples). For tail classes, initialize the prototype using the
class definition text (zero-shot). Then refine the prototype using the few available
training examples. This is the simplest form of few-shot learning and requires no special
meta-learning infrastructure. As head classes accumulate data, their prototypes improve,
and the shared representation benefits the tail classes.

**Door 9.5 — Search-log mining for unlabeled tail queries:**
Instead of generating synthetic queries, mine real queries from search logs that plausibly
belong to tail classes. Use a weak heuristic: queries with click patterns similar to the
tail class's definition (e.g., for "Running Shoe Reviews," find queries that lead to review
sites about running shoes). These weak labels aren't perfect but provide initial density
at zero cost. This is **distant supervision**.

**Door 9.6 — Active generation: model-in-the-loop query creation:**
Use the model itself to identify where it needs more data. Train a preliminary model.
Identify queries where the model's confidence is low (entropy > threshold). For those
queries, generate synthetic variants (via back-translation, synonym substitution, or LLM
prompting) that express the same intent with different surface forms. This is **targeted
data augmentation** — it densifies the decision boundaries the model finds hardest, not
random classes.

---

## Premise 10: The Octohedral Taxonomy Is Universal

### The Assumption

The 8→64→512→3,843 structure discovered in Yahoo! and Google taxonomies is a universal
attractor — any optimal web-scale intent taxonomy converges to this structure.

### The Challenge

**What if the octohedral structure is specific to English-language, advertiser-funded search
circa 2010, not to search intelligence in general?**

The convergence was observed in two companies (Yahoo!, Google) operating in the same market
(English-language web search) under the same economic pressure (advertising revenue). It is
a **market-specific convergence**, not necessarily a cognitive or information-theoretic one.
A search intelligence product designed for a different market (e.g., enterprise knowledge
management, AI-native search, subscription-based search) may converge on a different
optimal structure.

### Doors This Opens

**Door 10.1 — Domain-specific taxonomy construction (conservative):**
Instead of adopting YQT wholesale, construct a Deepl Search-specific taxonomy through a
first-principles process:
1. Define the product's top-level domains (not "Arts & Entertainment" but the product
   categories Deepl Search serves).
2. For each domain, derive the intent categories from user goals within that domain.
3. Expand to the granularity supported by the data budget.
The octohedral structure becomes a **reference point**, not a constraint. If Deepl Search's
domains naturally yield a 5→25→150 structure (like Timoshenko's oral care case), that is
the right structure for Deepl Search.

**Door 10.2 — Octohedral as a prior, not a constraint:**
Use the octohedral structure as a Bayesian prior for the model's output space. The model
starts with the YQT structure as its most likely hypothesis. As data accumulates, the
model can deviate: merge classes that the data cannot distinguish, split classes that the
data reveals as heterogeneous. The octohedral prior prevents overfitting in the low-data
regime; the data overrides the prior as it accumulates.

**Door 10.3 — Alternative attractor search:**
Conduct a systematic search for other convergence points. If advertising economics constrains
to 8→64→512→3,843, what do other constraints produce?
- **Content recommendation** (optimized for engagement, not ads): what structure emerges?
- **Enterprise knowledge management** (optimized for findability, not coverage): what
  structure?
- **E-commerce product taxonomy** (optimized for navigation, not classification): what
  structure? (Answer: deeper, see Google Merchant at depth 7)
- **Scientific literature** (optimized for precision, not breadth): what structure?
  (Answer: deeper, see MeSH or arXiv categories)

Each constraint set produces a different optimal structure. Finding these would establish
the octohedral structure as one point in a **taxonomy design space**, not the universal
attractor.

**Door 10.4 — Minimal taxonomy test:**
What is the **smallest** taxonomy that achieves the product's goals? Start with 8 L1
classes (the fewest plausible macro-categories) and no sub-levels. Test whether the product
works with 8 broad intent classes. If not, add L2 (64 classes). Test again. Add L3 (512).
Test. Add L4. The minimal viable taxonomy is discovered, not asserted. It might be 8 (if
all the product needs is broad categories), 512 (if L4 is too fine-grained to be useful),
or 3,843 (if full coverage is needed). This is a **product experiment**, not an analytic
derivation.

**Door 10.5 — Deep Search-specific taxonomy:**
Design a taxonomy specifically for Deepl Search's use case: **AI-native search intelligence
for understanding query intent in a multi-LLM ecosystem**. This taxonomy might look
different from YQT because:
- LLMs change query behavior (users search differently when they expect AI answers vs.
  keyword results)
- Multi-LLM ecosystem (the product spans ChatGPT, Claude, Gemini, Perplexity — each with
  different query styles)
- Subscription revenue model (not advertiser-funded, so the economic constraint is
  different — viability = user retention, not advertiser bid density)
The taxonomy should be derived from Deepl Search's specific context, not from Yahoo!'s
2008 context.

---

## Premise 11: The Model's Input Is Raw Query Text

### The Assumption

The model receives the raw query string as input. Any preprocessing (spelling correction,
tokenization, normalization) is optional.

### The Challenge

**What if the preprocessing is more important than the model?**

Jansen et al. (2009): 58.5% of classification errors are caused by misspellings. A
spell-correction preprocessor fixes 58.5% of errors — more than switching from fastText to
BERT would fix. Spell normalization alone improves accuracy by 3-5%. Spelling is the largest
source of classification error, and it costs nothing to fix.

### Doors This Opens

**Door 11.1 — Spell-correction preprocessor (conservative):**
Add a spell-correction step before classification. Use a lightweight model (SymSpell,
a neural edit-distance model) that corrects the most common 10,000 query misspellings in
<1ms. This eliminates 58.5% of errors at negligible computational cost.

**Door 11.2 — Query normalization pipeline:**
Build a normalization pipeline that handles:
- Spelling correction (58.5% of errors)
- Case normalization
- Punctuation stripping
- Stop-word removal (or retention depending on intent signal)
- Stemming/lemmatization (for morphologically rich languages)
- Number normalization ("10" vs "ten")
- Abbreviation expansion ("DIY" → "do it yourself")
Each step should be tested for its marginal contribution to classification accuracy, not
applied by default. Some steps (stop-word removal) may hurt intent classification if they
remove signal words.

**Door 11.3 — Multi-query variant aggregation:**
Instead of classifying a single query string, classify multiple variants of the same query:
- Raw query
- Spell-corrected query
- Query with expanded abbreviations
- Query translated to English (if non-English)
- Query with synonyms substituted ("shoes" → "footwear" → "sneakers")
Take a majority vote or average the intent vectors across variants. This is computationally
more expensive (N× the cost) but captures the intent more robustly.

**Door 11.4 — Learned query rewriting:**
Train a small model to rewrite queries in a canonical form before classification. The
rewrite model is trained to minimize: classification error on a downstream classifier +
reconstruction loss. This is an encoder-decoder that learns to "translate" raw queries into
canonical intent-bearing queries. The canonical form captures the query's intent in a
standardized vocabulary, removing surface-form variation.

**Door 11.5 — Query expansion via LLM paraphrase:**
For each query, use an LLM to generate 3-5 paraphrases that express the same intent in
different words. Classify each paraphrase and aggregate. This is expensive ($0.01 per query
with GPT-4o) but captures the intent from multiple lexical angles, reducing the impact of
surface-form idiosyncrasies.

---

## Premise 12: The Model Must Predict a Specific Intent

### The Assumption

For every query, there exists a correct intent class (or set of classes) that the model
should predict. The model's job is to approximate this mapping.

### The Challenge

**What if some queries should not be classified at all?**

A query like "asdf" (random keystrokes) has no intent. A query like "facebook" has an
intent (navigational — go to facebook.com) that is not well captured by any content intent
class. A query like "test test test" is a bot or a user testing the search box. A query
like "restaurants near me that serve vegan gluten-free Ethiopian food and have outdoor
seating" is so specific that no taxonomy class can cover it adequately.

The current system forces every query into some class. The model's confidence may be low
(0.1), but the forced assignment is still made. This degrades the quality of aggregate
statistics — low-confidence predictions add noise.

### Doors This Opens

**Door 12.1 — Reject option (conservative):**
Add a reject option: if the model's confidence is below a threshold (e.g., 0.3), return
"Unknown" instead of forcing a class. The threshold is calibrated on a held-out set. The
system samples unknown queries periodically to detect emerging intents. This is the
**reject classifier** from the cost-sensitive learning literature.

**Door 12.2 — Multiple thresholds per use case:**
Different consumers have different tolerance for uncertainty:
- Dashboard (aggregation): can tolerate low-confidence predictions (they average out)
- Ad targeting: should reject low-confidence predictions (FP cost > FN cost)
- Content recommendation: should reject but fall back to broader L1 class (better to be
  vaguely right than specifically wrong)

Each consumer sets its own confidence threshold. The model returns a distribution; the
consumer decides how much uncertainty to accept. This is the **decision-theoretic
deployment** of a probabilistic classifier.

**Door 12.3 — Intent-aware abstention:**
Train a separate model to predict whether the query is classifiable at all (a
classifiability classifier). Queries predicted as unclassifiable go to a manual review
queue or are assigned to "Other" with a warning flag. This is the **selective
classification** paradigm (El-Yaniv & Wiener, 2010): the model chooses when to predict
and when to abstain, optimizing coverage vs. accuracy at deployment time.

**Door 12.4 — Intent granularity ladder:**
For uncertain queries, classify at the coarsest granularity supported by confidence:
- Confidence >0.7 → predict L4 leaf
- Confidence 0.4–0.7 → predict L3 parent
- Confidence 0.2–0.4 → predict L2 parent
- Confidence <0.2 → predict L1 macro-category or "Unknown"

This is the **hierarchical classifier with confidence-based resolution** — it extracts the
maximum information the model is confident about, rather than forcing a specific-leaf
prediction regardless of confidence.

---

## Premise 13: The Model Is Trained Once and Deployed

### The Assumption

The model goes through a training phase, a validation phase, and a deployment phase. After
deployment, it is periodically retrained (weekly, monthly) with new data. The retraining
process is the same as the initial training process.

### The Challenge

**What if the model should never stop learning?**

The distribution of search queries shifts continuously: new products, events, lexicon,
seasonal patterns. A model trained quarterly is always behind the current query distribution.
By the time the quarterly retrain completes, the distribution has shifted again.

### Doors This Opens

**Door 13.1 — Online learning (conservative):**
Replace batch training with online (streaming) learning. The model updates its parameters
on every query (or every mini-batch of 100 queries). Learning is continuous. The model
adapts to distribution shifts within hours, not weeks. fastText and Vowpal Wabbit both
support online training.

**Door 13.2 — Continuous centroid update (moderate):**
Keep the classification model fixed (fastText weights, BERT parameters) but update the
class centroids continuously. As new queries arrive, each class's embedding centroid shifts
to reflect the current query distribution. The classification boundaries shift with the
centroids. This is low-cost (just averaging) and captures gradual semantic drift.

**Door 13.3 — Online Bayesian updating (radical):**
Use a Bayesian model (e.g., a deep Bayesian neural network trained with variational
inference or MC dropout) that maintains a posterior distribution over its parameters.
Each new query updates the posterior. The model becomes more confident in areas where it
sees many queries and remains uncertain in areas where it sees few. The posterior captures
epistemic uncertainty — the model knows what it doesn't know.

**Door 13.4 — Multi-timescale adaptation:**
Different components of the model adapt at different rates:
- Query → embedding mapping: updated monthly (language evolution is slow)
- Intent centroids: updated weekly (seasonal shifts)
- Classification weights: updated daily (new product launches, breaking news)
- Confidence thresholds: updated hourly (A/B test results)

This multi-timescale architecture separates slow language change from fast intent change,
optimizing compute allocation across adaptation rates.

**Door 13.5 — Concept drift detection:**
Deploy a separate monitoring model that detects when the query distribution has shifted
enough to degrade classification accuracy. The drift detector compares the current
week's query embeddings to the training period's embeddings using a two-sample test (MMD,
Kolmogorov-Smirnov). When drift is detected (p < 0.01), trigger a retraining or centroid
update. This avoids wasted retraining when the distribution is stable and prevents accuracy
degradation when it has shifted.

---

## Premise 14: The Evaluation Metric Is Known Before Deployment

### The Assumption

We can evaluate the model's quality before deploying it to production. The held-out test
set provides an unbiased estimate of deployment performance.

### The Challenge

**What if offline evaluation is systematically optimistic?**

The held-out test set is drawn from the same distribution as the training set. If the
training data was collected under distribution D and deployment encounters distribution D',
offline F1 is an overestimate of deployment F1. The gap between offline and online
performance can be 10-30 points (empirical observation from multiple deployed systems).
The held-out set also cannot capture the feedback loop effect: a deployed model influences
user behavior, which changes the distribution it encounters. Offline evaluation is
fundamentally myopic.

### Doors This Opens

**Door 14.1 — Counterfactual evaluation (conservative):**
Use counterfactual evaluation (off-policy evaluation) to estimate online performance from
offline data. Collect a small amount of data under a randomized policy (e.g., randomly
assign queries to intent classes for 1% of traffic). This data provides an unbiased estimate
of how any model would perform online. The sample size required is modest (10,000 queries)
for reliable estimates.

**Door 14.2 — Interleaving experiments for continuous evaluation (moderate):**
Run interleaving experiments continuously in production: for each query, two models produce
ranked intent lists. The user's actual intent is inferred from their behavior on the
interleaved results (which result they click, how long they dwell). This provides an online
evaluation of any model without requiring a separate A/B test. The interleaving is
transparent to the user (they just see results).

**Door 14.3 — Simulated environment for offline-to-online gap estimation:**
Build a simulator that approximates the deployment environment. The simulator includes:
- A query generator (sample from the deployment distribution)
- A user model (predicts user behavior given model output)
- A feedback loop (user behavior generates new training data)
Train the model in the simulator. Measure the gap between simulated F1 and the final online
F1 estimate. The gap provides a correction factor for offline evaluation.

**Door 14.4 — Multi-stage release evaluation:**
Instead of a single offline-to-online transition, use a multi-stage release:
1. **Offline evaluation** on held-out set (days)
2. **Shadow deployment:** model runs in parallel with production, predictions logged but not
   served. Evaluate against production system's predictions (weeks)
3. **Canary deployment:** 1% of traffic served by new model, 99% by old. A/B comparison
   (weeks)
4. **Full deployment:** 100% traffic, continuous monitoring (ongoing)

Each stage provides progressively more realistic evaluation. If the model fails at any
stage, it is redesigned before progressing.

**Door 14.5 — Behavioral evaluation without labels:**
If the model predicts intent, and the product serves content based on that prediction, then
user behavior is the real evaluation: if users click, stay, and return, the predictions are
useful regardless of F1. Define behavioral metrics:
- **Click yield:** fraction of queries with at least one click on served content
- **Satisfaction rate:** fraction of sessions where user issues 0-1 reformulations after
  first result
- **Conversion rate:** fraction of sessions ending in a desired action (purchase, signup,
  bookmark)
Evaluate the model on these metrics during shadow/canary deployment. They are directly
aligned with product success.

---

## Meta-Premise: The Path to Resolution

### A Decision Tree for Each Premise

For each premise, the project faces a branching decision:

```
Premise X: [Current Assumption]
├── If TRUE → Continue with current architecture (append "verified" to requirement)
├── If PARTIALLY TRUE → Adapt (choose the moderate door)
│   ├── Adaptation cost low → implement immediately
│   ├── Adaptation cost high → schedule for v2
│   └── Depends on product decision → flag as GAP for product owner
└── If FALSE → Redesign (choose the radical door)
    ├── New architecture cost > benefit → reconsider premises
    ├── New architecture feasible → prototype and test
    └── New architecture changes product → escalate to product owner
```

Each premise should be resolved through the smallest experiment that can falsify it.
For example:
- Premise 1 (query is the unit): classify 1,000 session sequences vs. individual queries.
  If session-level F1 > query-level F1 by 5+ points, the premise is falsified.
- Premise 3 (3,843 is optimal): train at K=500, 1K, 2K, 3K, 3,843, 5K. Measure coverage
  and F1. If F1 at K=800 is within 3 points of K=3,843, the premise is weakened.

### The Experimental Minimum

For each premise, answer:
1. **What's the smallest experiment that falsifies this premise?**
2. **What's the cost of that experiment in time/dollars?**
3. **What's the decision rule for accepting vs. rejecting the premise?**

This turns the problem formulation critique into an actionable research program — a set
of experiments that resolve the foundational questions, each with a clear stopping rule.

---

## References

- Bottou, L. (2010). Large-scale machine learning with stochastic gradient descent. *COMPSTAT*.
- Caruana, R. (1997). Multitask learning. *Machine Learning*, 28(1), 41–75.
- Cer, D., et al. (2018). Universal Sentence Encoder. *arXiv:1803.11175*.
- Domingos, P. (2012). A few useful things to know about machine learning. *CACM*, 55(10), 78–87.
- El-Yaniv, R., & Wiener, Y. (2010). On the foundations of noise-free selective classification. *JMLR*, 11, 1605–1641.
- Hand, D. J. (2006). Classifier technology and the illusion of progress. *Statistical Science*, 21(1), 1–14.
- Jansen, B. J., et al. (2009). Patterns of query reformulation during web searching. *JASIST*, 60(7), 1358–1371.
- Kuhn, T. S. (1962). *The Structure of Scientific Revolutions*. University of Chicago Press.
- Smucker, M. D., et al. (2007). A comparison of statistical significance tests for information retrieval evaluation. *CIKM*.
- Varian, H. R. (2007). Position auctions. *International Journal of Industrial Organization*, 25(6), 1163–1178.
- Vaswani, A., et al. (2017). Attention Is All You Need. *NeurIPS*.
- Bengio, Y., et al. (2013). Representation learning: A review and new perspectives. *TPAMI*, 35(8), 1798–1828.
- Tibshirani, R. (1996). Regression shrinkage and selection via the lasso. *JRSSB*, 58(1), 267–288.
- Blei, D. M., et al. (2003). Latent Dirichlet allocation. *JMLR*, 3, 993–1022.
- Lake, B. M., et al. (2015). Human-level concept learning through probabilistic program induction. *Science*, 350(6266), 1332–1338.
- Finn, C., et al. (2017). Model-agnostic meta-learning for fast adaptation of deep networks. *ICML*.
- Snell, J., et al. (2017). Prototypical networks for few-shot learning. *NeurIPS*.
- Artetxe, M., & Schwenk, H. (2019). Massively multilingual sentence embeddings for zero-shot cross-lingual transfer and beyond. *ACL*.
- Elkan, C. (2001). The foundations of cost-sensitive learning. *IJCAI*.
- Bottou, L., et al. (2013). Counterfactual reasoning and learning systems. *JMLR*, 14, 3207–3260.
- Kohavi, R., et al. (2007). Online experimentation at Microsoft. *Data Mining Case Studies*.
- Chapelle, O., et al. (2011). An empirical evaluation of Thompson sampling. *NeurIPS*.
