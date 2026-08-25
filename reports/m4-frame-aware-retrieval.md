# M4 — frame-aware retrieval and explicit claim exchange

**Run:** 2026-08-25  
**Pre-registration:** `PREDICTIONS-MEMORY.md` M4  
**Command:** `bash tools/run_gates.sh`

| arm | correct | answer rate | confident errors | records examined |
|---|---:|---:|---:|---:|
| frame-aware claims | 2/2 (100%) | 2/2 (100%) | 0/2 | 2 |
| pooled retrieval | 1/2 (50%) | 2/2 (100%) | 1/2 | 4 |

Each private claim had lexical-overlap score 1 and retained the incompatible other-frame record as
a contradiction. No global winner replaced the two claims. The unmatched query emitted two
explicit abstentions; exact-source and event-time cutoffs each excluded an otherwise matching
record.

This passes H-M1 only on the frozen two-frame fixture. Cost here means records actually examined
by the deterministic ranker, not wall time or token usage. Embeddings and a synthesis winner were
not added because this fixture exposes no measured need for either.
