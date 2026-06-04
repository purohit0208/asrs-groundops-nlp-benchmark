---
type: policy
domain: aviation-nlp
status: active
created: 2026-06-03
tags:
  - asrs
  - annotation
  - provenance
  - publication-ethics
---

# Label Provenance And Verification Policy

## Decision

The ASRS GroundOps NLP corpus now has three label-provenance layers:

1. Original agent-silver layer:
   - file: `data\manifests\silver_corpus_5000_labels_2026-06-03.csv`;
   - status: `agent_silver_v0_2`;
   - verification status: `not_human_verified`.

2. Derived single-author verified layer:
   - file: `data\manifests\author_verified_single_reviewer_labels_5000_2026-06-03.csv`;
   - status: `author_verified_single_reviewer`;
   - basis: user/author reported in the local Codex thread on 2026-06-03 that the corpus was verified and no problems were found;
   - audit: `reports\author_verification_cross_audit_5000_2026-06-03.md`.

3. Active local consistency-audit support:
   - active file: `data\manifests\author_verified_single_reviewer_labels_5000_2026-06-03.csv`;
   - active status: `author_verified_single_reviewer`;
   - audit: `reports\author_verification_cross_audit_5000_2026-06-03.md`;
   - support: row uniqueness, raw-record traceability, rule consistency, date-window consistency, evidence-snippet availability in working files, duplicate-ACN checks, and split-leakage checks.

The active file may be called author-verified reference labels with local consistency-audit support. It should not be described as formal expert consensus, independently adjudicated gold, second-reviewer verified, or inter-annotator-agreement-backed data unless those artifacts are added later.

## Why This Matters

A journal reviewer can reasonably ask how labels were produced. The provenance must therefore distinguish the original agent labels, the author's reported verification, and the agent cross-audits. Blending these into an unsupported "gold standard" claim would create an avoidable publication risk.

The stronger publication path is to be explicit:

- large public ASRS candidate pool;
- reproducible query protocol;
- predefined schema;
- agent-assisted initial labeling;
- author verification as reported by the author;
- transparent quality audit;
- honest limitation that independent annotation, inter-annotator agreement, disagreement ledger, and adjudication details are not present in this workspace.

## Allowed Terms

Use these terms for the original agent layer:

- `silver-standard corpus`;
- `agent-labeled corpus`;
- `AI-assisted labels`;
- `weak-label benchmark`;
- `agent_silver_v0_2`;
- `not_human_verified`.

Use these terms for the derived verified layer:

- `single-author-verified reference labels`;
- `author-verified single-reviewer labels`;
- `sole-author reviewed labels`;
- `author_verified_single_reviewer`.

Use these terms for the active author-verified local-audit layer:

- `author-verified reference labels`;
- `author-verified reference labels with local consistency-audit support`;
- `author_verified_single_reviewer`.

## Disallowed Terms

Do not use these terms for the current corpus without qualification:

- `human gold`;
- `gold standard`;
- `expert consensus`;
- `independently adjudicated`;
- `multi-annotator ground truth`;
- `expert-annotated gold`.

If `gold standard` is used at all, define it narrowly and explicitly disclose that independent annotation, inter-annotator agreement, disagreement, and adjudication artifacts are not present in the workspace.

## Current Corpus Status

As of 2026-06-03:

- expanded candidate pool: 8,801 unique ASRS records from Q02/Q04/Q09/Q10/Q11/Q12 after local 2011-2025 filtering;
- silver corpus: 5,000 records;
- original labeler: agent workflow;
- original label version: `agent_silver_v0_2`;
- active derived verification status: `author_verified_single_reviewer`;
- screening result: 4,203 likely relevant, 783 likely exclusions, 14 uncertain.
- cross-audit result: 0 blocking consistency errors.
- record-level split package: 3,499 train, 750 dev, 751 test, with 0 duplicate ACNs and 0 exact normalized-text hashes crossing splits.

## Manuscript Wording

Recommended methods wording:

> Candidate reports were collected from NASA ASRS Database Online using a reproducible query protocol. Draft labels were generated through an agent-assisted workflow based on a predefined annotation schema. The resulting 5,000-record label file was reviewed by the author. A reproducible cross-audit checked row uniqueness, raw-record traceability, rule consistency, date-window consistency, and evidence-span availability. The current artifacts do not include an inter-annotator agreement calculation, a disagreement ledger, independent expert review, or formal adjudication.

Recommended limitation wording:

> The corpus uses author-verified reference labels with local consistency-audit support. This design enables larger-scale public aviation narrative experimentation, but the current artifacts do not provide inter-annotator agreement, a disagreement ledger, or formal expert adjudication. Future work should add a documented independent verification subset.

## Evaluation Rule

For the current corpus:

- report model scores against author-verified reference labels with local consistency-audit support;
- do not call the test set independently adjudicated gold;
- include uncertainty and error analysis;
- preserve the original `not_human_verified` agent layer and the `author_verified_single_reviewer` layer in released metadata;
- use ASRS caveats about voluntary, self-reported, non-prevalence data.

## If Human Verification Is Added Later

If another human reviewer later verifies a subset:

1. create a separate file named with `independent_human_verified_subset`;
2. record reviewer identity or role, date, schema version, and decision fields;
3. preserve original agent labels separately;
4. report any disagreements against the single-author labels;
5. use that subset for independent agreement/adjudication analysis.
