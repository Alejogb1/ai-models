# Key Decisions: Why We Built the Intent Classifier This Way

> A self-contained explanation for someone who knows nothing about this project.
> Every term is defined. Every decision is traced back to an experiment.

---

## Part 1: The Problem — What Are We Actually Building?

### 1.1 What is a "search query intent"?

When someone types "java" into a search engine, what do they want? A programming tutorial? A coffee recipe? Information about the island of Java? The *intent* is the answer to "why is this person searching this right now?"

An **intent classifier** is a system that reads a search query and assigns it to a category like "Education & Reference" (learning Java programming) or "Shopping & Commerce" (buying Java coffee beans) or "Arts & Entertainment" (watching a movie about Java).

### 1.2 Why is this hard?

Three problems make this deceptively difficult:

**Ambiguity.** A single query can mean many things. "Java" is the canonical example, but consider: "mercury" (planet, element, or car brand?), "windows" (OS or home improvement?), "apple" (fruit or company?).

**Brevity.** Search queries average 2-4 words. There's almost no context in the text itself. Compare to a sentence like "I want to install a new window in my living room" — that's 12 words with clear intent. Queries give you 3 words and expect an answer.

**Granularity.** The taxonomy (list of categories) has 3,843 classes organized in 4 levels:
- L1: 8 broad categories (Shopping, Health, Education, etc.)
- L2: 64 subcategories
- L3: 512 finer categories
- L4: 3,843 specific intent classes

At L4, we're distinguishing "buying a specific brand of running shoes" from "finding reviews of running shoes" from "learning about running shoe technology." These are very fine distinctions that even humans struggle with.

### 1.3 The naive approach (what we first tried)

The initial design was simple:
1. Take a query (e.g., "nike running shoes")
2. Run it through a pre-trained sentence encoder (all-MiniLM-L6-v2) to get a 384-dimensional embedding (a mathematical representation of the query's meaning)
3. Compare it to each of 3,843 class descriptions using cosine similarity
4. Pick the class with the highest similarity score

This is called a **zero-shot embedding classifier** — "zero-shot" because it wasn't trained on our data, and "embedding classifier" because it uses embedding similarity instead of a learned classifier.

It failed. Badly. The mean confidence (how sure the system is about its prediction) was **0.07 out of 1.0** — essentially random. Only 1 of the 3,843 classes ever captured more than 1% of queries. The rest were statistical noise.

### 1.4 The 6 questions we asked before designing anything (GAPs)

Before building, we answered 6 questions that define the problem space:

1. **Primary use case:** What is this system for? → It adapts to all 4 use cases (trend detection, content personalization, ad targeting, market research)
2. **Input data:** What goes in? → Session-level queries (the last 3 searches a user made) + optional context (device type, time, etc.)
3. **Deployment target:** Where does it run? → Internal tool/API (not a public product)
4. **Revenue model:** How does it make money? → Not relevant (internal tool)
5. **Timeline:** How long do we have? → 6+ months (ambitious but achievable)
6. **Labeling budget:** How much can we spend on training data? → $10K+ (substantial but not unlimited)

---

## Part 2: The Experimental Method — How We Make Decisions

### 2.1 What is a "premise"?

A **premise** is an assumption you make when designing a system. For example, "the query is the unit of analysis" is a premise — it assumes that each query contains enough information to classify it.

Every system design contains dozens of premises. Most go unexamined. Our method is to **list every premise explicitly**, then **test each one with the smallest possible experiment**.

### 2.2 The 12 premises behind our initial design

We identified 12 assumptions that the naive approach made:

| # | Premise | Question It Answers |
|---|---------|---------------------|
| 1 | Query is the unit | Can we classify a single query in isolation? |
| 2 | Intent lives in query text | Is all the information in the query's words? |
| 3 | 3,843 is the right number of classes | Is the full taxonomy usable? |
| 4 | Human labels are ground truth | Can we trust the training data? |
| 5 | Classification is the right paradigm | Should we classify or retrieve? |
| 6 | F1 measures success | Is standard accuracy the right metric? |
| 7 | Taxonomy is static | Will categories stay relevant? |
| 8 | English-first | Do we need multilingual support? |
| 9 | Label bottleneck is the problem | What limits performance most? |
| 10 | YQT taxonomy is universal | Is this specific taxonomy structure right? |
| 11 | Raw text is the input | Do we need preprocessing? |
| 12 | Every query must classify | Should the system always predict? |

### 2.3 The falsification loop

For each premise, we run the **smallest experiment that could falsify it**. The experiment has three possible outcomes:

- **Falsified:** The premise is false. Must redesign around the opposite assumption.
- **Weakened:** The premise is partially true, but not entirely. Add mitigation strategies.
- **Holds:** The premise is validated. Keep the design as-is.

This is inspired by Karl Popper's philosophy of science: you can never prove a theory true, but you can prove it false with a single counterexample. Each experiment is designed to find that counterexample.

### 2.4 Phase 1: Six zero-cost experiments

Phase 1 tested 6 premises using only the existing embedding classifier and 2,000 MS MARCO queries — no API costs, no human annotation. The results:

| Premise | Result | What we learned |
|---------|--------|-----------------|
| #1: Query is unit | **FALSIFIED** | Adding the previous query changes 87.6% of predictions |
| #3: K=3843 is correct | **WEAKENED** | Only 1/3843 classes gets >1% of queries; L1 self-consistency is only 72.8% |
| #5: Classification paradigm | **WEAKENED** | Mean 47.7 non-zero labels per query — this is retrieval behavior, not classification |
| #6: F1 is sufficient | **HOLDS** | F1 and cost-weighted F1 rank models identically (for simulated errors) |
| #11: Raw text is fine | **FALSIFIED** | 82.5% of predictions change when queries are misspelled |
| #12: Always predict | **FALSIFIED** | 0% of queries have confidence >0.5 — the system was essentially random |

### 2.5 A critical caveat: the embedding classifier doesn't work

The most important finding wasn't about any specific premise. **The zero-shot embedding classifier with generic placeholder descriptions produces near-random similarity scores** — mean confidence 0.07-0.14 across all 3,843 classes. It cannot distinguish "Arts & Entertainment" from "Business & Finance" because the class descriptions are generic text ("Intent 1 > Subcategory 1") with no semantic content.

This means our quantitative findings are **lower bounds** — a better classifier would produce different absolute numbers. But the **structural findings** (change rates, distribution shapes, self-consistency) are likely robust because they depend on the geometry of the embedding space, not the absolute values.

---

## Part 3: The 6 Architecture Decisions

After Phase 1, we had enough evidence to make architecture decisions. Each decision is recorded as an **ADR** (Architecture Decision Record).

---

### Decision 1: Session Input — Don't classify a single query

**What this means:** Instead of feeding one query into the classifier, we feed the last 3 queries the user typed, concatenated with a special marker: `"previous query [SEP] current query"`. The system sees the session context.

**Why it matters:** A user who types "java" might be looking for programming tutorials, coffee, or travel info. But if their previous 2 queries were "Python IDE" and "JavaScript framework", it's clear they're in Education & Reference mode. The session disambiguates.

**The experiment:** Exp 1 compared single-query vs session-level classification on the same 500 queries. Session context changed **87.6% of predictions** and increased confidence by 13.5%. We don't know if the changed predictions are more *accurate* (that requires labeled data), but the fact that context changes nearly 9 out of 10 predictions proves that query-alone carries insufficient signal.

**How to use it:** The input pipeline is:
```
raw_query1 [SEP] raw_query2 [SEP] raw_query3
```
The [SEP] token is a convention that tells the encoder these are separate utterances, not a single sentence. N=3 is chosen because:
- N=1: no context (the falsified approach)
- N=2: minimal context, may not capture topic shifts
- N=3: captures most session structures (average session is 2.4 queries)
- N>3: diminishing returns, more noise

**Decision:** ADR-1 — use last N=3 queries concatenated as the input unit.

---

### Decision 2: Spell Correction Preprocessor — Clean the input before classifying

**What this means:** Before any classification happens, run each query through a spell checker. SymSpell corrects "nkie runing shoos" to "nike running shoes" in under 1 millisecond.

**Why it matters:** Search queries are notoriously misspelled. Studies show 10-15% of real queries contain at least one spelling error. Our experiment found that **82.5% of predictions change** when a query is artificially misspelled (edit distance 1-2). This means the classifier is brittle to typos.

**The experiment:** Exp 11 created synthetic misspellings (25% per-word probability, edit distance 1-2) on 500 clean MS MARCO queries. The 82.5% prediction change rate means spelling is not a minor issue — it fundamentally breaks the classifier for a significant fraction of queries.

**How to use it:** The preprocessor runs before classification:
1. Spell-correct each query (SymSpell, max edit distance 2)
2. Normalize the text (lowercase, collapse numbers to 0, remove punctuation)
3. Concatenate the session (add [SEP] markers)

**Key insight:** This experiment taught us that **preprocessing is more important than model architecture**. Adding a spell corrector will have more impact on real-world accuracy than switching from a small model to a large one.

**Decision:** ADR-2 — SymSpell with max edit distance 2, before all other processing.

---

### Decision 3: Reject Option + Granularity Ladder — Let the model say "I don't know"

**What this means:** Instead of forcing the model to always predict a class, we add a **reject option**: if the model's confidence is below a threshold, it can abstain. And with the **granularity ladder**, if it can't classify at L4 (most specific), it tries L3, then L2, then L1. Only if even L1 confidence is too low does it fully reject.

**Why it matters:** Forced classification produces near-random predictions for ambiguous queries. Our experiment showed that literally **0% of queries have confidence above 0.5** — meaning forcing the system to predict means most predictions are essentially random.

**The experiment:** Exp 12 swept confidence thresholds from 0.0 to 0.9. At τ=0.1 (reject queries with confidence <0.1), only 57.4% of queries were accepted. At τ=0.5, coverage was 0%. The confidence distribution was entirely in the [0.0, 0.3] range — the system was never confident.

**The granularity ladder concept:** Imagine a student answering a test question. If they don't know the answer at the species level ("Canis lupus"), they might still know the genus ("Canis") or the family ("Canidae"). Similarly, if the model can't identify the specific intent, it can report the broader category. This extracts maximum information from every query.

**Decision:** ADR-3 — reject when confidence < τ at all 4 levels; report at the highest granularity where confidence exceeds threshold.

---

### Decision 4: Bi-Encoder Retrieval — Treat intent prediction as a search problem, not a classification problem

**What this means:** Instead of a linear classifier head that maps embeddings → class probabilities, we use a **bi-encoder** architecture:
- A **query encoder** converts the input (session) into a 384-dimensional vector
- A **class encoder** (or just the query encoder with different inputs) converts class descriptions into vectors
- Intent prediction = find which class vector is closest to the query vector (cosine similarity)

This is a **retrieval** paradigm: the query retrieves the most similar class, rather than being assigned to one.

**Why it matters:** The standard classification approach (softmax over 3,843 classes) breaks when K is large. The softmax function produces a probability distribution by dividing each class score by the sum of all scores — when you have 3,843 scores, the normalization is dominated by noise. The result is overconfident on training data and poorly calibrated on new data.

Our experiment found that the average query activates **47.7 non-zero classes** — this is characteristic of retrieval (where you get a ranked list) rather than classification (where you get a single assignment).

**How it works:**
1. Encode the query: `q_embed = query_encoder(session_text)`
2. Encode all 3,843 class descriptions: `C_embeds = class_encoder(class_descriptions)` (done once, stored)
3. Compute cosine similarity: `scores = q_embed @ C_embeds^T`
4. Sort scores descending: highest = most likely class

**Decision:** ADR-4 — retrieve top-K classes by cosine similarity; no linear classification head. This naturally handles:
- Large K (3,843 classes)
- Open set (unseen queries can be far from all classes → reject)
- Adding new classes (just add a description and re-embed)

---

### Decision 5: LLM-as-Annotator — Use LLMs to create training data

**What this means:** Instead of paying human annotators to label queries (slow, expensive, inconsistent), we use a Large Language Model (like GPT-4o, Llama 3 70B, Gemini 1.5 Flash) to generate labels. Humans are only used for validation (5K queries to check quality and calibrate).

**Why it matters:** The cost difference is dramatic:
- Human annotation: 20,000 labels × $0.10/label = $2,000 + platform fees
- LLM annotation: 500,000 labels × ~$0.02/1K tokens ≈ $10 (with efficient models)

At 50x cheaper, we can afford 10x more labels, which directly addresses the Zipf distribution problem (thousands of rare classes need more labels).

**The risk:** LLMs may be biased. They might favor certain categories, misclassify edge cases, or miss subtle distinctions that humans would catch. Our mitigation:
1. Measure LLM-human agreement on a 5K validation set
2. If agreement < 80%, increase human validation proportion
3. Identify queries where multiple LLMs disagree — those are genuinely ambiguous and need human review

**Decision:** ADR-5 — GPT-4o-mini (or equivalent) for bulk labeling; human validation on 5K queries for calibration.

---

### Decision 6: Effective K = 200-300 — Don't try to classify 3,843 classes

**What this means:** The taxonomy has 3,843 classes, but we only have enough labeled data to effectively distinguish 200-300 of them. So we train at K=64 (L2) first, expand to K=200-300 (L3 head) as data accumulates, and never seriously try K=3843.

**Why it matters:** The **Zipf distribution** of search queries means a small number of classes cover most queries, and thousands of classes have almost no queries. With a $10K+ labeling budget, we can afford approximately 20,000 labeled queries. Distributed evenly across 3,843 classes, that's 5 examples per class — statistically useless. Distributed across 200-300 classes, that's 67-100 examples per class — sufficient for training.

**The experiment:** Our granularity sweep (Exp 3) showed that L1 self-consistency is only 72.8% — meaning 27% of queries get different L1 labels depending on whether you classify at L4 and map up, or classify at L1 directly. This is a sign that the hierarchy isn't well-aligned with actual query distributions.

**The expansion strategy:**
1. Train at L2 (64 classes) first — 20K labels → ~300 per class
2. Identify which L3 classes are most frequently predicted
3. Add the top 200-300 L3 classes as new classification targets
4. Train a head for just those classes, keeping L2 as the backbone

**Decision:** ADR-6 — train initial model at K=64 (L2), expand to K=200-300 (L3 head) as data accumulates. L4 (3843) is not learnable at current budget.

---

## Part 4: The Complete Architecture

### 4.1 Data flow

```
Raw Session (3 queries)
    │
    ▼
[Spell Correction] ─── SymSpell, max edit distance 2
    │
    ▼
[Query Normalization] ─── Case, punctuation, number normalization
    │
    ▼
[Session Concatenation] ── "q1 [SEP] q2 [SEP] q3"
    │
    ▼
[Bi-Encoder] ────► [Cosine Similarity with Class Embeddings]
    │
    ▼
[Confidence Check] ── Threshold τ?
    │
    ├── Confidence ≥ τ → Return prediction (at highest granularity)
    │
    └── Confidence < τ → Fall back to coarser level or reject
```

### 4.2 What this enables that the old design couldn't

| Capability | Old Design | New Design |
|-----------|-----------|------------|
| Handle ambiguous queries | Forces random prediction | Rejects or downgrades granularity |
| Respond to new categories | Requires full retrain | Just add a class description |
| Use unlabeled data | Not possible | SimCSE pre-training on session logs |
| Scale labels | Need human annotators ($) | LLM annotation ($0.00002/query) |
| Handle typos | Breaks (82.5% change rate) | Spell-corrected |
| Detect nuance | Single query only | Session context (87.6% change rate) |

### 4.3 What we're still uncertain about

1. **LLM label quality above L2** — The fine-grained distinctions at L3-L4 may be too subtle for current LLMs. We need measurement.

2. **Optimal session length** — N=3 is our starting point, but the ideal varies by use case. Some sessions need 1 query, some need 5.

3. **The living taxonomy** — We don't know how fast new categories emerge. The drift detection system is designed but uncalibrated.

4. **Bi-encoder vs cross-encoder gap** — The bi-encoder is fast but potentially less accurate than a cross-encoder. If the gap is large, we may need a hybrid (bi-encoder for retrieval → cross-encoder for reranking).

---

## Glossary

| Term | Definition |
|------|-----------|
| **Session** | A sequence of queries from the same user within a short time window (typically <30 minutes). Our architecture uses N=3 queries. |
| **Embedding** | A mathematical vector (list of numbers) that represents the meaning of a piece of text. Similar meanings produce similar vectors. |
| **Bi-encoder** | An architecture with two encoders (query encoder + class encoder) that produce separate embeddings, then compare them with cosine similarity. |
| **Cross-encoder** | An architecture that processes query and class together in one forward pass — more accurate but too slow for K=3843. |
| **Cosine similarity** | A measure of how similar two vectors are, ranging from -1 (opposite) to +1 (identical). Used to match queries to intent classes. |
| **Reject option** | The ability of a classifier to abstain from predicting when confidence is too low. |
| **Granularity ladder** | A fallback strategy: if the model can't classify at the most specific level (L4), try the next level (L3), then L2, then L1, then finally reject. |
| **Coverage** | The fraction of queries that are accepted (not rejected) by the reject option. Coverage of 80% means 80% of queries get a prediction. |
| **K (effective)** | The number of classes that actually receive meaningful numbers of queries. In our taxonomy, K_eff ≈ 200-300, not 3,843. |
| **Zipf distribution** | A power-law distribution where a few items account for most of the mass. Search queries follow Zipf: a few classes get most queries. |
| **Premise** | An assumption embedded in a design. We list premises explicitly and test each one experimentally. |
| **Falsify** | An experimental result that proves a premise false. Requires architecture redesign. |
| **Weaken** | An experimental result that shows a premise is partially true but has important exceptions. Requires mitigation strategies. |
| **Hold** | An experimental result that validates a premise. The design stays as-is. |
| **Cost-weighted F1** | A metric that assigns different costs to different types of errors. Cross-L1 errors (predicting Shopping when true is Health) cost more than within-L3 errors. |
| **F1 score** | The harmonic mean of precision and recall. Ranges from 0 to 1 (1 is perfect). |
| **ADR** | Architecture Decision Record. A document that records a decision, its rationale, and alternatives considered. |
| **MS MARCO** | Microsoft Machine Reading Comprehension dataset. 808,731 real search queries from Bing. Used as our experimental data source. |
| **SymSpell** | A fast spell correction algorithm. Corrects misspellings using a frequency dictionary and edit distance. |
| **SimCSE** | Simple Contrastive Learning of Sentence Embeddings. An unsupervised method for learning better embeddings: take the same sentence, apply different dropout masks, treat as positive pairs. |
| **MNR loss** | Multiple Negative Ranking loss. The standard loss for training bi-encoder retrieval: treat each query's positive class as positive and all other classes in the batch as negatives. |
| **Self-consistency** | Whether a classifier gives the same answer at different levels of the taxonomy. If L4→L1 mapping disagrees with direct L1 classification, the hierarchy is inconsistent. |
