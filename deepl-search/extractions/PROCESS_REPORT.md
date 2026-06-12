# Multi-Agent Extraction Process Report

## Overview
- Total sources: 326
- Processed: 325
- Unprocessed: 1
- Total concepts extracted: 3391

## Agent Inventory

### agent01 (Timoshenko, Jansen, BeiWang, EECS)
- **Description**: Timoshenko (customer needs/JTBD from UGC), Jansen (query reformulation patterns), BeiWang (IR survey), EECS (feedback loops in recommendation)
- **Sources processed**: 4 (Timoshenko_Hauser_Customer_Needs_from_UGC, jansen_patterns_query_reformulation, IR_Survey_BeiWang_2026, EECS-2022-178)
- **Total concepts extracted**: 31
- **Output files produced**: 1 (agent01_timoshenko_jansen_beiwang_eecs.json)
- **Failures/Issues**: None
- **Notes**: High-quality extractions with detailed findings across 4 web-sources papers. Concepts have strong structure with finding/category/implication/open_question/testable_hypothesis.

### agent02 (Other / KWE / Lookalike)
- **Description**: Keyword extraction (KWE), lookalike audience expansion, and other ML papers
- **Sources processed**: Multiple papers across Other, Keywords Extraction, Lookalike categories
- **Total concepts extracted**: 112
- **Output files produced**: 1 (agent02_other_kwe_lookalike_compiled.json)
- **Failures/Issues**: None
- **Notes**: Covers diverse topics from lookalike audience models to keyword extraction to contrastive learning. Consistent concept structure.

### agent03 (Embeddings / MF / Ranking / Search)
- **Description**: Embedding methods, matrix factorization, ranking models, and search
- **Sources processed**: Multiple papers across Embeddings, MF, Ranking, Search categories
- **Total concepts extracted**: 40
- **Output files produced**: 1 (agent03_embeddings_mf_ranking_search_compiled.json)
- **Failures/Issues**: Slightly different output format - concepts are flat (no nested `concepts` array). Each entry is self-contained with finding/category at top level.
- **Notes**: Comprehensive coverage of embedding-based retrieval and recommendation papers. Concepts have finding/category/implication/open_question/testable_hypothesis fields.

### agent_batch (Batch Generation - Individual Extractions)
- **Description**: Individual per-paper extractions across all categories (agents: agent5_final, agent_batch_generation, and some agent03-flagged files)
- **Sources processed**: 270 individual files
- **Total concepts extracted**: 3152
- **Output files produced**: 270 individual JSON files
- **Failures/Issues**: None
- **Notes**: Each paper gets its own JSON file. Consistent format with source_group and agent fields. Most files have 1 concept each (101 out of 270), some have up to 20. Three different agent IDs present in this batch (agent5_final, agent_batch_generation, agent03_embeddings_mf_ranking_search_compiled) suggesting multi-pass or multi-agent extraction.

### agent6_remaining (Final Batch - Remaining Groups)
- **Description**: Final pass covering previously unprocessed groups: CV, GANs, DNN Compression & Acceleration, Nearest Neighbor Search, Neural Machine Translation, NAS, and Surveys
- **Sources processed**: 49 files across 7 groups
- **Total concepts extracted**: 56
- **Output files produced**: 49 individual JSON files
- **Failures/Issues**: None
- **Notes**: All remaining unprocessed sources from Awesome-ML-Papers sub-groups have been processed. Each paper gets its own JSON file with 1-2 concepts each. The only remaining unprocessed source is HowtoReadPaper.pdf (group: Awesome-ML-Papers) which is a meta-reading guide, not a research paper.

## Source Coverage Matrix

| Source Group | Total Files | Processed | Concepts | Coverage % |
|---|---|---|---|---|
| Awesome-ML-Papers | 1 | 0 | 0 | 0.0% |
| Awesome-ML-Papers/CTR CVR prediction | 37 | 37 | 719 | 100.0% |
| Awesome-ML-Papers/CV | 8 | 8 | 8 | 100.0% |
| Awesome-ML-Papers/DNN Compression and Acceleration | 5 | 5 | 6 | 100.0% |
| Awesome-ML-Papers/Embeddings | 49 | 49 | 50 | 100.0% |
| Awesome-ML-Papers/GANs | 16 | 16 | 18 | 100.0% |
| Awesome-ML-Papers/Keywords Extraction | 8 | 8 | 23 | 100.0% |
| Awesome-ML-Papers/Lookalike | 8 | 8 | 21 | 100.0% |
| Awesome-ML-Papers/MF | 42 | 42 | 42 | 100.0% |
| Awesome-ML-Papers/NAS | 2 | 2 | 2 | 100.0% |
| Awesome-ML-Papers/Nearest Neighbor Search | 8 | 8 | 9 | 100.0% |
| Awesome-ML-Papers/Neural Machine Translation | 5 | 5 | 7 | 100.0% |
| Awesome-ML-Papers/Other | 48 | 48 | 351 | 100.0% |
| Awesome-ML-Papers/Ranking | 14 | 14 | 14 | 100.0% |
| Awesome-ML-Papers/Search | 2 | 2 | 3 | 100.0% |
| Awesome-ML-Papers/Session based Recommendations | 20 | 20 | 384 | 100.0% |
| Awesome-ML-Papers/Shopping | 5 | 5 | 100 | 100.0% |
| Awesome-ML-Papers/Surveys | 5 | 5 | 6 | 100.0% |
| composite-reference | 2 | 2 | 2 | 100.0% |
| web-sources | 41 | 41 | 697 | 100.0% |

## Process Metrics
- **Total extraction JSON files created**: 322
- **Concepts per source (mean)**: 10.43
- **Concepts per source (median)**: 3.5
- **Concepts per source (min)**: 1
- **Concepts per source (max)**: 20

### Category Distribution (across all concepts)

| Category | Count |
|---|---|
| ModelCandidate | 1428 |
| Data | 519 |
| FailureRisk | 362 |
| Baseline | 289 |
| Experiment | 279 |
| TargetConstruct | 161 |
| LabelValidation | 157 |
| BehavioralTests | 56 |
| Model Candidate | 37 |
| Evaluation | 31 |
| Label/Validation | 4 |
| Failure/Risk | 4 |
| Target Construct | 4 |
| Behavioral Tests | 4 |

### Files per Source Group (from extraction files)

| Source Group | Extraction Files |
|---|---|
| Awesome-ML-Papers | 1 |
| Awesome-ML-Papers/CTR CVR prediction | 37 |
| Awesome-ML-Papers/CV | 8 |
| Awesome-ML-Papers/DNN Compression and Acceleration | 5 |
| Awesome-ML-Papers/Embeddings | 49 |
| Awesome-ML-Papers/GANs | 16 |
| Awesome-ML-Papers/Keywords Extraction | 8 |
| Awesome-ML-Papers/Lookalike | 8 |
| Awesome-ML-Papers/MF | 42 |
| Awesome-ML-Papers/NAS | 2 |
| Awesome-ML-Papers/Nearest Neighbor Search | 8 |
| Awesome-ML-Papers/Neural Machine Translation | 5 |
| Awesome-ML-Papers/Other | 48 |
| Awesome-ML-Papers/Ranking | 14 |
| Awesome-ML-Papers/Search | 2 |
| Awesome-ML-Papers/Session based Recommendations | 20 |
| Awesome-ML-Papers/Shopping | 5 |
| Awesome-ML-Papers/Surveys | 5 |
| composite-reference | 2 |
| web-sources | 41 |

## Known Issues
- **Unprocessed files**: 1 source remains unprocessed (HowtoReadPaper.pdf - a meta-reading guide, not a research paper)
- **Variance in extraction quality**: agent03 produces flat concepts (no nested `concepts` array), while agent01/agent02 nest concepts under a `concepts` key. This inconsistency makes aggregation harder.
- **Source matching**: Some extraction source fields don't match manifest filenames exactly (extra spaces, missing .pdf suffix, different formatting conventions)
- **Composite references**: 2 partial entries (SimClusters/RecWalk composite, PTE + User Embeddings composite) span multiple PDFs and can't be attributed to a single source file

### Agent Reliability Notes
- **agent01**: Reliable, consistent output format. All 4 source entries processed correctly with nested concepts.
- **agent02**: Reliable, consistent output format. All source entries processed with nested concepts.
- **agent03**: Functional but inconsistent format. Entries have `source` + `finding`/`category` at top level (no `concepts` wrapper). Some source names include author/year info which complicates matching.
- **agent_batch (individual)**: Most reliable format - single paper per file with clear source_group. All files follow identical structure.
- **agent6_remaining**: Consistent format matching agent_batch convention. All 49 files use the same schema with nested `concepts` array.

## Recommendations for Future Multi-Agent Extractions

### What Worked Well
- Separating agents by domain focus (agent01=web-sources, agent02=other/KWE/lookalike, agent03=embeddings/MF/ranking/search) creates manageable scope per agent
- The concept template (finding + category + implication + open_question + testable_hypothesis) provides consistent, actionable output
- Individual per-paper extraction files (agent_batch) are cleanest for traceability
- Agent naming convention (agentXX_descriptive_name) makes purpose clear

### What Should Be Done Differently
- **Standardize output format**: All agents should use the same JSON schema. Either always nest under `concepts` or always flatten. Mixing both requires special handling.
- **Standardize source naming**: Source values should consistently match manifest filenames. Strip author/year info, normalize whitespace, include/exclude .pdf consistently.
- **Standardize category values**: Some agents use `ModelCandidate`, others `Model Candidate` (with space). Normalize categories.
- **Track per-source agent attribution**: Each extraction JSON should record which agent produced it for better traceability.

### Suggested Improvements to Agent Prompt Design
- Include explicit output format instruction with JSON schema example
- Require agents to strip `.pdf` from source values to match manifest convention
- Require category values from a fixed enum to prevent slight variations
- Instruct agents to report confidence scores per concept

### Suggested Output Format Standardization
```json
{
  "source": "filename (without .pdf)",
  "source_group": "category",
  "agent": "agent_id",
  "processed_at": "ISO timestamp",
  "concepts": [
    {
      "finding": "...",
      "category": "ModelCandidate|Data|Evaluation|TargetConstruct|FailureRisk|BehavioralTests|LabelValidation|Experiment|Baseline",
      "implication": "...",
      "open_question": "...",
      "testable_hypothesis": "..."
    }
  ]
}
```

### Suggested Instrumentation
- **Token tracking**: Record input tokens, output tokens, and total tokens per agent per file
- **Timing**: Record start_time, end_time, and duration per extraction
- **Cost**: Estimate API cost per extraction based on token usage and model pricing
- **Retry count**: Track how many retries each agent needed
- **Validation errors**: Record schema validation failures per agent
- **Source<->Extraction traceability**: Ensure every extraction JSON records which source file(s) it was derived from

## Final Summary

This marks the completion of the multi-agent extraction pipeline. All 326 sources have been processed (325 with extraction data, 1 intentionally skipped as a non-research meta-guide). The pipeline successfully extracted **3,391 concepts** across 20 source groups, achieving **99.7% coverage** of all research paper sources.

Key achievements:
- **100% coverage** on 18 out of 20 source groups
- **49 remaining papers** processed in the final agent6_remaining batch (CV, GANs, DNN Compression, Nearest Neighbor Search, Neural Machine Translation, NAS, Surveys)
- **56 new concepts** added from the final batch
- **322 extraction JSON files** created across all agents
- The only unprocessed item (HowtoReadPaper.pdf) is a reading methodology guide, not a research paper, and was intentionally excluded
