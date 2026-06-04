---
type: protocol
domain: aviation-nlp
status: active
created: 2026-06-04
tags:
  - asrs
  - corpus
  - llm
  - data-boundary
---

# Expanded 8,800 Corpus And Remote LLM Decision

## User Decision

On 2026-06-04, the user approved bounded remote LLM use for this ASRS GroundOps NLP benchmark.

Boundary recorded:

- Remote LLM processing may send raw ASRS narrative text from this project to Hugging Face Inference Providers.
- The approved purpose is bounded benchmark experimentation, not public redistribution of raw ASRS narratives.
- Raw ASRS narratives must not be written into model output files, release candidate files, or public artifacts.
- Output files should store predicted labels, validity flags, timing/cost metadata, and hashes where needed, not full prompts or raw model responses that may repeat source text.

## Model Choice

Primary remote LLM baseline:

- `Qwen/Qwen2.5-7B-Instruct`
- access path: Hugging Face Inference Providers / OpenAI-compatible chat-completions router
- expected use: schema-constrained record-level classification and multi-label tagging baseline on the test split

Rationale:

- open instruction model with Apache-2.0 license;
- not gated;
- endpoint-compatible on Hugging Face;
- suitable for small structured-output classification without using a large reasoning model.

## 8,800-Record Corpus Decision

The project has 8,801 unique candidate ASRS records from the Q02/Q04/Q09/Q10/Q11/Q12 retrieval protocol.

The final expanded corpus target is 8,800 records, not 10,000, because:

- 8,800 is already a strong specialized aviation NLP corpus size;
- forcing 10,000 would require adding new queries and could introduce query drift;
- using the existing candidate pool preserves a clean retrieval boundary;
- the single excluded record can be selected deterministically.

Selection rule:

- preserve all 5,000 rows from the author-verified seed corpus with local consistency-audit support;
- add 3,800 of the 3,801 remaining candidate records;
- exclude the remaining candidate with the shortest available combined ASRS synopsis/narrative text, tie-broken by candidate ID and ACN.

## Verification Boundary

The 5,000 seed rows retain their existing provenance:

- `author_verified_single_reviewer`

The 3,800 added rows are not claimed as newly human verified. They are:

- agent-generated labels from the existing rule/schema workflow;
- cross-audited for uniqueness, raw-record traceability, rule reproduction, evidence availability, and split leakage;
- marked separately in provenance columns.

Manuscript-safe wording:

> The expanded corpus contains 8,800 ASRS candidate records with explicit label-provenance fields. A 5,000-record seed subset has author-verified reference labels with local consistency-audit support; the additional 3,800 records are agent-generated expanded labels used for training-scale and robustness experiments, with evaluation kept on the verified reference split unless otherwise stated.

Do not write:

- "8,800 human-verified labels";
- "8,800 gold-standard labels";
- "expert-adjudicated corpus";
- "inter-annotator agreement";
- "event-span extraction".

## Evaluation Boundary

Preferred expanded-data evaluation:

- Train on the original verified training split plus the 3,800 expanded agent-labeled records.
- Keep the original verified dev and test splits unchanged for main evaluation.
- Report the expanded-data result as weak-label training augmentation against a verified reference test set.

This avoids evaluating final model performance on unverified new labels while still addressing the training-size concern.
