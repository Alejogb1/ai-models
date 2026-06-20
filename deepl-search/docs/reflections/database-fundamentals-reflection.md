# Database Fundamentals Reflection

## What building an intent classifier taught me about databases without me realizing it

---

## Introduction

This document reinterprets a machine-learning research project as a case study in database fundamentals. The project — building a hierarchical search intent classifier from 500 human-labeled queries and a trained embedding model — was never intended as a database exercise. Yet it confronted every core database concept: representation, identity, schema, constraints, integrity, provenance, data quality, uncertainty, temporal validity, derived data, reproducibility, query semantics, workload, data independence, and the boundary between storage and computation.

The shift in perspective is this: instead of asking "what did I store?" it asks "what database concepts did the system force me to confront?" The answers reveal that the project is less a machine-learning system with data artifacts and more an implicit database system whose design choices were made without database language to describe them.

---

## 1. Representation

### General database principle

Representation is the mapping from a slice of reality to a data structure. Every database begins by choosing what to model and what to omit. A customer database represents people as having a name, address, and phone number but not their mood, their height, or what they ate for breakfast. Representation is inherently lossy: the database keeps what matters for the intended queries and discards the rest. The art is in knowing which losses are acceptable and which are fatal.

### Why the concept matters

A bad representation makes good queries impossible. If you model time as a string instead of a timestamp, you cannot ask "which records were created in June?" If you model location as a single text field instead of latitude/longitude, you cannot ask "which customers are within 10 km?" The representation determines the question space. What you omit is as consequential as what you include.

### How the project instantiates the concept

The project attempts to represent search intent — an unobservable mental state — as a single path through a 4-level taxonomy. This is a radical compression: a person types 2-4 words and the system asserts a structured category like "Health & Fitness > Exercise & Workouts > Strength Training > Weightlifting." The representation assumes that every query has exactly one correct path, that the taxonomy covers all possible intents, and that the intent is fully determined by the query text alone. All three assumptions are questionable.

### What mistake or uncertainty appears

The representation mistake is treating intent as a property of the query rather than a relationship between the query, the user, their context, and the taxonomy. The database stores intent as an attribute ("this query's intent is X") when it should perhaps be stored as an interpretation ("this annotator assigned category X to this query under these conditions"). The single-label representation collapses the inherent ambiguity of search queries — nearly half of the 500 queries had plausible alternative interpretations.

### What I likely learned

Representation is not neutral. Every database design encodes a theory about what the world is like. The project's theory — that search intent fits cleanly into a 4-level hierarchy — was partially falsified by the data itself. The lesson is that the representation decision belongs at the beginning of the design process, not as an implicit consequence of choosing a taxonomy and a label format.

### How to ask a database expert

How should a database represent a real-world concept when the concept itself is ambiguous, context-dependent, and not directly observable?

---

## 2. Identity

### General database principle

Identity is the mechanism by which a database decides that two records refer to the same thing. A primary key is a stable, unique identifier that survives changes to other attributes. A person might change their address, phone number, and email, but their customer ID remains the same. Without stable identity, relationships become ambiguous, updates become unreliable, and data quality degrades silently.

### Why the concept matters

Identity is the foundation of every relationship in a database. Foreign keys reference primary keys. Joins depend on matching identities. De-duplication requires deciding that two records are the same entity. If identity is based on mutable attributes (name, position in a file, timestamp), it breaks when those attributes change. Stable identity is what allows the database to track entities over time and across transformations.

### How the project instantiates the concept

The project uses file position as identity. The first query in the sample file is "query 0," the second is "query 1," and so on. Labels are aligned to queries by having the same line number in their respective files. This is positional identity — the most fragile form possible. If a single line is added or removed from the query file, every label shifts to the wrong query with no error signal. The project also uses name strings as identity for taxonomy categories: a label says "Health & Fitness" and must match a taxonomy entry with the exact same string. A trailing space or different encoding silently breaks the match.

### What mistake or uncertainty appears

The identity mistake is treating convenience as reliability. Positional identity is easy to implement (no key generation, no lookups) but fails silently under common operations like sorting, filtering, or appending. The project never experienced a failure because the data was carefully curated — but the design is fragile, not robust. The taxonomy name identity is equally fragile: category names look like keys but are unvalidated strings subject to typos, encoding differences, and naming convention drift.

### What I likely learned

Identity must be explicit and stable. A line number is not a key. A string is not a key unless there is a constraint enforcing its uniqueness and immutability. The project's data relationships work only because a person is manually keeping the files in sync — a database would enforce this automatically.

### How to ask a database expert

What criteria should be used to choose a primary key when the entities are short text strings with no obvious natural identifier?

---

## 3. Schema

### General database principle

A schema is a formal description of the structure, types, and constraints of data. It declares what fields exist, what types they have, which are required, and how they relate. A schema can be explicit (a CREATE TABLE statement, a JSON Schema file, a Protobuf definition) or implicit (convention known to the developers, structure embedded in code). Explicit schemas enable validation, documentation, and tooling; implicit schemas enable speed but create fragility.

### Why the concept matters

Without an explicit schema, every consumer of the data must rediscover its structure. A new developer must read the code to learn that labels have four hierarchy levels, that the first element is the L1 category, that the confidence field is a float between 0 and 1. Different consumers may develop different interpretations of the same data. When the structure changes, there is no single place to update the definition — every piece of code that reads the data must be found and changed.

### How the project instantiates the concept

The project has an implicit schema distributed across multiple files: the label records in JSONL have a consistent 10-field structure, the taxonomy is split across dictionary literals in scripts and a JSON mapping file, the experiment results follow a per-script convention. No formal schema declaration exists anywhere. The structure is documented only by example and by code that reads it. Adding a new field to the label records would require finding every script that parses them and ensuring backward compatibility.

### What mistake or uncertainty appears

The schema mistake is treating structure as self-evident. The label records look self-documenting — the JSON keys are descriptive ("l1", "l2", "confidence", "ambiguous"). But self-documenting is not the same as documented. There is no statement of which fields are required, what values are valid for each field, what the relationship between fields must be, or how the schema evolves. The project has the appearance of structure without the guarantees of a declared schema.

### What I likely learned

A schema is a contract between data producers and data consumers. Without an explicit contract, every producer and consumer negotiates the structure independently, and the negotiation happens through bugs. The project worked because there was one producer (the labeling script) and a small number of consumers — but it would not scale.

### How to ask a database expert

When is an implicit schema (code-defined structure) acceptable, and when does a project need a formal, declared schema?

---

## 4. Constraints

### General database principle

Constraints are rules that data must obey to be considered valid. A NOT NULL constraint ensures a field always has a value. A UNIQUE constraint prevents duplicate records. A CHECK constraint enforces domain-specific rules (e.g., "confidence must be between 0 and 1"). A FOREIGN KEY constraint ensures that a reference points to an existing record. Constraints encode the business logic of data validity at the schema level, making violations impossible rather than just unlikely.

### Why the concept matters

Without constraints, data degrades over time. A missing value here, a duplicate there, a reference to a deleted record — each violation is individually small, but their accumulation makes the database untrustworthy. Constraints push validity checking to the moment of data creation, where errors are cheapest to fix. They serve as executable documentation of what the system believes about its data.

### How the project instantiates the concept

The project has no database-level constraints. The only validity checks are in application code: the label aggregation script checks that every label has 4 non-empty hierarchy levels, and the evaluation scripts crash if a taxonomy name lookup fails. These are implicit, partial, and scattered. There is no constraint saying "every label must reference an existing taxonomy node" enforced at write time. There is no constraint saying "no two labels may reference the same query index." Data is assumed valid until proven otherwise — by a crash.

### What mistake or uncertainty appears

The constraints mistake is relying on code to do what the database should do. Application-level checks are better than nothing, but they are easy to forget, easy to skip, and easy to bypass. A FOREIGN KEY constraint would prevent orphan references regardless of which script writes the data. A UNIQUE constraint on query index would prevent duplicate labels. The project's constraints exist as good intentions in code, not as enforceable guarantees in data.

### What I likely learned

Constraints are not overhead; they are insurance. Every missing constraint is a class of corruption that the system cannot detect until it causes a visible failure. The project got lucky because the data was carefully curated by a single person — but constraint violations would be inevitable with multiple data sources or automated label generation.

### How to ask a database expert

What is the minimum set of constraints that should be applied to any dataset before it is used for model training?

---

## 5. Integrity

### General database principle

Integrity is the property that data is consistent, correct, and internally non-contradictory. Referential integrity means every foreign key points to an existing primary key. Domain integrity means every value falls within its allowed range. Entity integrity means every record is uniquely identifiable. Integrity is the umbrella concept that constraints enforce. A database with integrity can be trusted; one without it requires constant vigilance.

### Why the concept matters

Integrity violations propagate. A broken foreign key in one table means every join involving that table produces incomplete results. A duplicate record means aggregate queries double-count. A NULL where a value is expected means downstream computations produce garbage. Integrity violations are rarely isolated — they spread through queries, reports, and decisions that depend on the data.

### How the project instantiates the concept

The project has multiple integrity vulnerabilities. The most serious is the positional alignment between queries and labels: if one file is edited without the other, every label becomes attached to the wrong query with no signal of corruption. A second vulnerability is the name-string matching between labels and taxonomy: a typo in a category name creates an orphan label that references nothing. A third is the lack of split tracking during training: the same query could appear in both training and validation sets, inflating accuracy metrics without detection.

### What mistake or uncertainty appears

The integrity mistake is assuming that manual curation prevents corruption. Because a single person creates and maintains the data, the system never needed integrity enforcement — the person was the integrity mechanism. But a person is not a database constraint. People make typos, forget steps, and introduce inconsistencies that automated enforcement would catch immediately.

### What I likely learned

Integrity cannot be maintained by hand. It must be designed into the data system. The project's data remained clean because of careful manual work, but the design itself provides no guarantees. A database professional would have added foreign keys, uniqueness constraints, and referential checks before writing the first label.

### How to ask a database expert

How should referential integrity be maintained when data is stored as semi-structured files (JSON, JSONL) rather than in a relational database?

---

## 6. Provenance

### General database principle

Provenance is the record of where data came from and how it was produced. It answers three questions: origin (what source produced this record?), transformation (what process created it from its inputs?), and custody (who or what has handled it?). Provenance can be fine-grained (per record) or coarse-grained (per dataset). It is the data about data — the metadata that makes data trustworthy or questionable.

### Why the concept matters

Without provenance, data is a black box. You cannot tell whether a label was written by a domain expert or a novice, whether it was produced by a human or an algorithm, whether it was validated or assumed. Provenance enables trust decisions at the record level rather than at the dataset level. It also enables debugging: when a result is wrong, provenance tells you which step in the pipeline introduced the error.

### How the project instantiates the concept

The project has partial provenance. Label records can be traced back to batch scripts through the `record_index` field, and the batch scripts document the labeling process. But this provenance is indirect: there is no annotator ID, no labeling session timestamp, no version of the labeling guidelines. For trained models, provenance is almost absent: the model directory contains weights but no record of which data was used for training, what hyperparameters were set, or what the validation accuracy was. Experiment results capture configuration but not the data version or the environment.

### What mistake or uncertainty appears

The provenance mistake is treating "we know how this was produced" as equivalent to "the data records this knowledge." The project team knows where the labels came from, but that knowledge is in their heads, not in the data. If a new person inherits the project, they must reconstruct provenance from directory names, file dates, and conversation. Provenance that is not recorded is provenance that will be lost.

### What I likely learned

Provenance is not documentation; it is part of the data. A record without provenance information is incomplete. The project's labels are well-provenanced among the people who created them, but the provenance is social, not structural. Making it structural would require adding a few fields (annotator_id, label_timestamp, labeling_guidelines_version) to every label record.

### How to ask a database expert

What is the minimal provenance schema that makes a dataset auditable without requiring disproportionate storage or complexity?

---

## 7. Data quality

### General database principle

Data quality is the degree to which data is fit for its intended use. It has multiple dimensions: accuracy (does the data reflect reality?), completeness (are all expected records present?), consistency (are records free of contradictions?), timeliness (is the data current?), and validity (do values conform to expected formats and ranges?). Data quality is relative to purpose: a dataset that is high-quality for one use (e.g., aggregate trend analysis) may be low-quality for another (e.g., individual-level decision-making).

### Why the concept matters

Poor data quality undermines every downstream use. A machine learning model trained on low-quality data learns the wrong patterns. A report based on low-quality data makes wrong recommendations. A decision based on low-quality data is uninformed at best and harmful at worst. Data quality is not a property of the data alone — it is a property of the data relative to its use.

### How the project instantiates the concept

The project's data quality has several known issues. The labels were produced by a single annotator, so inter-annotator agreement is unknown — the 74.8% accuracy might partially reflect learning that annotator's preferences rather than generalizable intent patterns. The query sample is the first 2,000 lines of the MS MARCO dataset (alphanumeric ordering by document ID), introducing ordering bias; some L2 categories have many examples while others have 1-2. The MS MARCO queries are from 2016-2018, meaning the model would deploy on 2026 queries — an 8-year temporal gap. All three of these are data quality issues, but none are detected or flagged by the system.

### What mistake or uncertainty appears

The data quality mistake is treating data quality as binary (valid/invalid) rather than dimensional. The system checks whether a label has the right number of fields but does not assess its accuracy, its timeliness, or its representativeness. Data quality is not a property the system measures; it is a property the project owner intuits. The system cannot answer "how trustworthy is this label?" because trustworthiness is not represented in the data.

### What I likely learned

Data quality must be measured, not assumed. The project's metrics (74.8% accuracy) are meaningful only to the extent that the underlying data is high-quality. If the labels are biased, the accuracy is inflated. If the sample is skewed, the accuracy is unrepresentative. A data quality assessment before training would have revealed these risks before they became embedded in model weights.

### How to ask a database expert

What systematic process should be followed to assess and document the quality of a dataset before it is used for model training or evaluation?

---

## 8. Uncertainty

### General database principle

Uncertainty is the representation of doubt, ambiguity, or disagreement in data. A database can represent uncertainty at multiple levels: at the value level (this confidence score is 0.8, meaning 80% likely), at the record level (this label is disputed by two annotators), or at the schema level (this field represents an interpretation, not a fact). Most databases are designed for certainty: they store facts and assume they are true. Representing uncertainty requires additional fields, additional records, or a different data model.

### Why the concept matters

Ignoring uncertainty creates false precision. A system that stores "this query is about Health & Fitness" without storing "this is the annotator's best guess, with 0.7 confidence, and two alternative categories exist" is presenting an interpretation as a fact. This matters when the data is used for training: the model learns to treat all labels as equally true, even though some are confident assertions and others are uncertain guesses.

### How the project instantiates the concept

The project captures uncertainty in its label schema but does not act on it. Each label record has a `confidence` field (0 to 1), an `ambiguous` boolean flag, and a `competing_labels` array listing alternative categories. These fields represent uncertainty explicitly. However, the training process ignores them: every label is treated as equally valid, regardless of confidence or ambiguity. The model learns from uncertain and certain labels with equal weight. The uncertainty is stored but not consumed.

### What mistake or uncertainty appears

The uncertainty mistake is storing uncertainty information without using it. The fields exist — they were designed into the schema — but the training pipeline does not weight by confidence, does not use competing labels for multi-label training, and does not stratify evaluation by ambiguity. The uncertainty data is a dead column: written but never read. This is a design pattern where the schema anticipates a future that the rest of the system is not ready for.

### What I likely learned

Storing uncertainty is only half the work. The other half is consuming it: weighting training examples by confidence, evaluating separately on ambiguous vs. unambiguous queries, and using competing labels for multi-label evaluation. A database that stores but ignores uncertainty is not capturing doubt; it is collecting inert metadata.

### How to ask a database expert

What data models or storage patterns are appropriate for representing uncertain, ambiguous, or disputed annotations without losing the ability to query them as determinate facts?

---

## 9. Temporal validity

### General database principle

Temporal validity is the representation of time in data: when a record was created, when it was last modified, when the information it contains was true in the real world, and when it ceased to be true. Databases distinguish transaction time (when the database recorded the data) from valid time (when the data was true in reality). Temporal data enables historical queries, trend analysis, and the detection of stale or outdated information.

### Why the concept matters

Without temporal information, a database is a snapshot with no context. You cannot tell whether a record from 2018 is still valid in 2026. You cannot reconstruct the state of the database at a previous point in time. You cannot detect data staleness or temporal drift. Time is one of the few universal dimensions across all data, and ignoring it means losing the ability to ask "when?" about anything.

### How the project instantiates the concept

The project has almost no temporal metadata. Labels have no creation timestamp, no audit timestamp. Model checkpoints have filesystem modification times but no embedded training date. Experiment result files have no execution timestamp. The query data is from MS MARCO (2016-2018), but this temporal context is not recorded in the data — it is known only from external knowledge about the dataset. The taxonomy was defined in 2026 but carries no version date.

### What mistake or uncertainty appears

The temporal mistake is treating data creation as instantaneous and permanent. The project's data appears timeless: labels don't expire, model weights don't age, experiment results don't become obsolete. But they do. A label made in 2026 reflects 2026 language and culture. The same query typed in 2030 might have a different intent. The model trained on 2018 data becomes less accurate as language evolves. Without temporal metadata, the system cannot detect or respond to this drift.

### What I likely learned

Every data record should have a timestamp. The cost is trivial (a few bytes per record), and the benefit is the ability to ask temporal questions: "was this label created before or after the taxonomy change?" "Is this model accuracy measurement still relevant?" "Which version of the labeling guidelines was in effect when this record was created?"

### How to ask a database expert

What temporal metadata should be required for every record in a system that trains and evaluates machine learning models over time?

---

## 10. Derived data

### General database principle

Derived data is data produced by computation from other data. A materialized view is derived data stored for performance. An aggregate is derived data summarizing many records. A prediction is derived data produced by a model. The distinction between base data (observed, captured, entered) and derived data (computed, inferred, predicted) is fundamental: base data is a fact about the world, while derived data is a fact about the computation.

### Why the concept matters

Confusing derived data with base data leads to circular reasoning and loss of evidentiary value. If you train a model on predictions from another model, you risk amplifying errors or learning the training model's biases rather than patterns in reality. If you store derived aggregates without storing the base data they were computed from, you lose the ability to audit, recompute, or refine them. The boundary between observation and computation must be explicit.

### How the project instantiates the concept

The project has multiple layers of derived data. Model predictions are derived (computed by the model from query text and category descriptions). Experiment metrics (accuracy, mean confidence, effective K) are derived (aggregated from many predictions against labels). The SimCSE pre-trained embeddings are derived (computed by a training process from raw query text). The distinction between these and base data (the query text, the human labels) is clear to the project owner but not encoded in the data itself. There is no field marking a value as "computed" vs. "observed."

### What mistake or uncertainty appears

The derived data mistake is storing derived aggregates without storing the base data needed to recompute or inspect them. Experiment result files contain accuracy and confidence distributions but not per-query predictions. If someone asks "which queries did the model get wrong?", the answer requires re-running the entire evaluation pipeline. The derived data is stored in a form that is useful for summary but not for debugging. Furthermore, the model weights themselves are a form of derived data — they are the result of a computation (training) on base data (labels + queries) — but they carry no metadata about that computation.

### What I likely learned

Derived data should be stored with enough context to be auditable. An accuracy number without the per-query predictions it summarizes is a claim without evidence. A model checkpoint without the training configuration and data version it was produced from is a black box. The database principle of "store atomic facts, derive aggregates" would have prevented both problems.

### How to ask a database expert

When should derived data be stored as materialized results, and when should it be recomputed on demand? What metadata should accompany each stored derived result?

---

## 11. Reproducibility

### General database principle

Reproducibility is the ability to regenerate a result from stored data and metadata. A reproducible result is one where given the same inputs and the same process, the same output is produced. Reproducibility requires: (a) the inputs are versioned and accessible, (b) the process is deterministic or its random variations are captured, (c) the environment is documented, and (d) the output is linked to its inputs.

### Why the concept matters

Without reproducibility, results are anecdotes. An experiment that cannot be reproduced cannot be verified, challenged, or built upon. In research contexts, irreproducibility wastes time and undermines trust. In production contexts, irreproducibility makes debugging impossible: if you cannot recreate a result, you cannot investigate what went wrong.

### How the project instantiates the concept

The project has partial reproducibility. The evaluation pipeline is deterministic: fixed query sample, fixed model checkpoint, deterministic inference. Running `evaluate_bi_encoder.py` twice produces the same numbers. The training pipeline is less reproducible: random seeds are inconsistently set, the train/validation split is random, and the exact data sharding depends on batch ordering. An experiment result file captures hyperparameters but not the data split or the random seed state.

### What mistake or uncertainty appears

The reproducibility mistake is treating the output as sufficient without capturing the process. The experiment JSON says "accuracy: 0.748" but does not say "training used seed 42, 400/100 split, data version v1, taxonomy version v1." Someone rerunning the training might get 0.74 or 0.75 and not know whether the difference is noise or a real change. The project's results are reproducible for evaluation but not for training — and training is where reproducibility matters most.

### What I likely learned

Reproducibility requires capturing the entire context of a computation, not just its inputs and outputs. For model training, this means: random seed, data split indices, data version, model initialization, and environment (library versions). For model evaluation, this means: query set version, model checkpoint identifier, and taxonomy version. The project captures some of this but not all.

### How to ask a database expert

What metadata schema is sufficient to guarantee reproducibility of a machine learning experiment, including both training and evaluation?

---

## 12. Query semantics

### General database principle

Query semantics is the set of questions a database is designed to answer. A database designed for transaction processing (OLTP) optimizes for fast inserts and updates on individual records. A database designed for analytical queries (OLAP) optimizes for aggregations over many records. A database designed for search optimizes for text matching and ranking. The query semantics determine the schema, the indexes, the storage format, and the access patterns.

### Why the concept matters

A database designed without clear query semantics will be optimized for nothing and adequate for few things. If you store data in a format that makes aggregation fast but search slow, you have made a deliberate tradeoff. If you do not know which operations will be most common, you cannot make these tradeoffs intentionally. Query semantics should drive schema design, not the other way around.

### How the project instantiates the concept

The project implicitly supports two query workloads. The first is evaluation: "what is the accuracy, confidence distribution, and effective K for model M on query set Q?" This workload aggregates over many records and is served by experiment JSON files. The second is training data retrieval: "for each query, what is its label and its L2 description?" This workload is per-record and is served by scanning JSONL files. A third workload — production serving ("given a query, what is the predicted intent?") — is not yet supported by any stored data; it would be served by the model at runtime, not by the database.

### What mistake or uncertainty appears

The query semantics mistake is designing the storage format for convenience of data creation rather than for convenience of the most common queries. The JSONL format is easy to write (append a line) but expensive to query (full scan for every access). If the project needed to frequently answer "find all queries labeled as Health & Fitness," the JSONL format would require scanning 500 records every time — trivial at this scale, but a design flaw that would bite at 50,000.

### What I likely learned

The format and structure of stored data should be determined by the questions it needs to answer, not by the convenience of the code that produces it. If the most common query is "get label by query ID," then a key-value store or indexed table would be better than a JSONL file. If the most common query is "aggregate accuracy by L2 class," then a column-oriented format would be better.

### How to ask a database expert

How should query workload analysis drive storage format and schema decisions in a data pipeline that serves both model training and evaluation?

---

## 13. Workload

### General database principle

Workload is the pattern of operations a database system must support: read-heavy vs. write-heavy, point lookups vs. full scans, frequent updates vs. append-only, simple filters vs. complex joins. Understanding the workload is essential for choosing storage technology, indexing strategy, and caching policy. A workload of "one writer, many readers, append-only, aggregate-heavy" suggests a different system than "many writers, few readers, update-heavy, record-level lookups."

### Why the concept matters

Mismatch between workload and system design causes performance problems, complexity problems, or both. An append-only workload forced into an update-in-place system creates write amplification. A read-heavy workload without indexes creates unnecessary full scans. A workload with mixed access patterns (both transactional and analytical) often requires separating the system into a serving layer and an analytics layer.

### How the project instantiates the concept

The project has a clear workload pattern: write once (labels are created once and rarely modified), read many times (labels, taxonomy, and model metadata are read by every training and evaluation script), append-only (new labels can be added but existing labels do not change), with both record-level lookups (get label for query 42) and aggregate queries (compute accuracy across all labels). This workload would be well-served by an indexed key-value store or a simple relational database. Instead, it is served by flat files scanned in Python.

### What mistake or uncertainty appears

The workload mistake is building for the wrong scale. The current 500 records are trivially handled by file scanning, so the workload never forced a better design. But the implicit workload (the set of queries the system needs to answer) suggests a design that would scale poorly — full file scans for every query, no indexes, no query optimization. The system works because the data is small, not because the design is right.

### What I likely learned

Workload determines design. A system that works for 500 records may fail for 50,000, and the failure will not be gradual — it will be a performance cliff when the data no longer fits in memory or when the linear scan time exceeds acceptable latency. Understanding workload before designing storage would have led to different choices even for the small-scale version.

### How to ask a database expert

For a small-scale data pipeline (hundreds to thousands of records) that will eventually need to handle larger volumes, what storage design decisions made early will prevent painful migrations later?

---

## 14. Data independence

### General database principle

Data independence is the separation of the conceptual data model from the implementation details of storage, access, and manipulation. Physical data independence means queries do not depend on how data is stored (e.g., switching from JSON to a database does not require rewriting queries). Logical data independence means applications do not depend on the exact schema (e.g., adding a field to a table does not break existing queries). Data independence is what makes databases flexible rather than brittle.

### Why the concept matters

Without data independence, every change to storage or schema ripples through every consumer. Renaming a field means editing every script that reads it. Switching from JSONL to SQL requires rewriting every query. The lack of data independence is the primary source of fragility in data systems: the coupling between structure and usage is too tight.

### How the project instantiates the concept

The project has no data independence. The taxonomy structure is embedded in script dictionaries: five separate scripts each contain their own copy of the L1 and L2 category names and descriptions. Changing a category name requires editing all five files. The label schema is assumed in every consumer: every script that reads labels expects exactly the current field names and types. Adding a new field to the label records could break any consumer that doesn't handle it gracefully. The query-to-label relationship is implicit in positional alignment — switching to explicit keys would require changing every join.

### What mistake or uncertainty appears

The data independence mistake is hardcoding structure into code instead of externalizing it into data. The taxonomy should be a file that scripts read, not a set of dictionary literals. The label schema should be defined in one place that all consumers import. The query-label relationship should use explicit keys that survive storage changes. Without these, the system is brittle: every change requires editing multiple files, and some edit will inevitably be missed.

### What I likely learned

Data and code should be separable. The taxonomy is data, not code. The label schema is a contract, not an implementation detail. Hardcoding structure into code creates maintenance debt that grows with every new script. The single-source-of-truth principle — one definition of the taxonomy, one definition of the label schema, one mapping between queries and labels — would have prevented the 5-file duplication problem.

### How to ask a database expert

What architectural patterns ensure data independence in systems where the data model evolves frequently and is used by multiple independently developed consumers?

---

## 15. Boundary between database and machine learning

### General database principle

The boundary between database and machine learning is the line between what is stored as data and what is learned as a model. The database holds facts — observations, measurements, annotations. The model holds patterns — relationships, weights, parameters learned from data. The boundary is crossed during training (the model learns from database facts) and during inference (the model produces predictions that could become new database facts). Managing this boundary means being clear about which claims are stored evidence and which are computed inferences.

### Why the concept matters

Confusing the database and the model leads to circular dependencies. If model predictions are stored as facts and then used to train the next model, errors compound. If database facts are treated as model output, the model's uncertainty is lost. The boundary also affects reproducibility: a model without its training data is unverifiable; training data without the model is incomplete.

### How the project instantiates the concept

The project has three layers: the database (queries, labels, taxonomy), the trained model (weights that map text to embedding space), and the evaluation (predictions compared to labels). The boundary between database and model is crossed in the training script: the model reads labels from the database, learns patterns, and produces weights stored as files. The evaluation crosses the boundary again: the model produces predictions, which are compared to database labels to produce derived metrics. The system is clear about which is which — labels are in JSONL, model weights are in a directory — but the dependencies between them are not recorded. Which version of the labels produced which version of the model?

### What mistake or uncertainty appears

The boundary mistake is not version-linking the model to its training data. The model directory contains weights but no reference to which label records were used for training, what data version they came from, or what taxonomy version defined the output space. If the labels are corrected or the taxonomy is refined, the model silently becomes a version mismatch. The boundary between database and model is crossed without a passport — the relationship between the two is not recorded.

### What I likely learned

The model and the database are not independent systems. The model is derived from the database, and its validity depends on the database's validity. Recording the training data version alongside the model weights is not optional — it is the only way to know whether a model is still valid after data changes. The project implicitly understands this (the training script reads specific files) but does not encode it in the stored artifacts.

### How to ask a database expert

How should a system that trains models from database records maintain the linkage between model versions and the data versions they were trained on?

---

## Final synthesis

The project did not merely teach me how to store artifacts. It exposed the core database problem of turning unstable, ambiguous, generated, and interpreted information into stable, valid, queryable, reproducible, and model-usable data. The database lesson is not about files or tables; it is about representation, identity, validity, provenance, uncertainty, and the boundary between facts and computations.

The specific lessons:

1. **Representation is a theory.** Every data structure encodes assumptions about what the world is like. The project assumed that search intent is a single category, which the data partially disproved.

2. **Identity must be explicit.** Positional identity works until it doesn't. The project built fragile relationships on line numbers.

3. **Schema is a contract.** An implicit schema is not a schema. It is a convention waiting to be violated.

4. **Constraints are executable documentation.** The project's business rules lived in code comments, not in data guarantees.

5. **Provenance is part of the data, not commentary.** Without recording origin, every record is a claim without evidence.

6. **Uncertainty must be consumed, not just stored.** Dead columns — fields written but never read — are metadata that never became insight.

7. **Temporal metadata is cheap insurance.** Every record needs a timestamp. There is no excuse not to have one.

8. **Derived data without base data is fragile.** Aggregates without per-query predictions are claims without auditability.

9. **Reproducibility requires capturing the process, not just the output.** A result file without its execution context is an anecdote.

10. **Workload should drive design.** The project's storage format was chosen for writing convenience, not for query frequency.

11. **Data independence prevents coupling.** Hardcoding structure in code creates a maintenance burden that grows with every new consumer.

12. **The database-model boundary must be managed.** Every model checkpoint should reference the data version that produced it.

These lessons were learned by doing — by building a system that worked at small scale and would have failed at larger scale. The project is a typical example of implicit database design: data structures that emerged from code rather than from deliberate schema decisions. Recognizing this pattern is the first step toward making better choices in future systems.

---

## Questions to ask a database expert

1. **Uncertainty**: How should a database represent uncertain or interpreted records — where the value is someone's best guess, not an observed fact?

2. **Prediction as data**: When should a model prediction be stored as data, and when should it remain a computed result that is never persisted?

3. **Multi-source provenance**: How should provenance be represented when data is produced by a mix of humans, automated scripts, trained models, and external data sources?

4. **Generated vs. observed data**: What schema design prevents generated or synthetic data from being confused with observed or manually curated data?

5. **Facts vs. interpretations**: How should a database distinguish facts, human annotations, model predictions, and derived metrics, when all may be stored in the same system?

6. **Data quality for training**: What data-quality rules and validation checks are essential before a dataset is safe to use for model training?

7. **Identity for text**: How should identity be represented when the entities are short text strings that are ambiguous, context-dependent, and lack natural identifiers?

8. **Experiment reproducibility**: What metadata schema is sufficient to guarantee that a machine learning experiment — including training, evaluation, and data dependencies — can be fully reproduced?

9. **Implicit databases**: At what point does a collection of semi-structured files and code that reads them become an implicit database, and what are the signs that a formal database is needed?

10. **Principled redesign**: If you were asked to redesign this project as a principled database system — keeping the same goals and data — what would your schema, constraints, and provenance model look like?
