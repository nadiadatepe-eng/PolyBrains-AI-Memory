# M1 — private-frame retrieval versus pooling

**Run:** 2026-08-23  
**Pre-registration:** `PREDICTIONS-MEMORY.md` M1  
**Command:** `bash tools/run_gates.sh`

All three controls passed: deterministic record round-trip and provenance validation, abstention
on an unmatched query, and rejection of a cross-owner/frame private read.

| arm | correct / answerable | false / all | abstention control | provenance |
|---|---:|---:|---:|---:|
| private owner/frame retrieval | 2/2 (100%) | 0/3 (0%) | pass | 2/2 (100%) |
| pooled retrieval | 1/2 (50%) | 1/3 (33.3%) | pass | 1/1 (100%) |

The observed result matches the registered prediction. On this deliberately minimal fixture,
private retrieval prevents the higher-confidence episode from another frame becoming agent A's
answer. This passes M1's fixture-level acceptance rule; it is not evidence for H-M2 and does not
establish general retrieval quality.

The gate also verifies that supersession and tombstoning preserve all prior records while removing
superseded payloads from retrieval.
