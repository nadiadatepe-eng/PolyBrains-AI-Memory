# M2 — private episodic retrieval measurements

**Run:** 2026-08-25  
**Pre-registration:** `PREDICTIONS-MEMORY.md` M2  
**Command:** `PYTHONPATH=src python3 tools/measure_m2_recall.py`

| arm/control | recall@1 |
|---|---:|
| private exact-token retrieval | 200/200 (100.0%) |
| no memory | 0/200 (0.0%) |
| one expected episode removed | 199/200 (99.5%) |

| additional measure | result |
|---|---:|
| false retrieval on unanswerable distractors | 40/40 (100.0%) |
| no-memory false retrieval | 0/40 |
| provenance completeness | 240/240 (100.0%) |
| examined records/query, 120 → 1,200 records | 120 → 1,200 (10.0×) |
| median latency | 0.128 → 1.273 ms |
| p95 latency | 0.131 → 1.374 ms |
| payload storage growth | 11.23× |
| serialized storage growth | 10.04× |

The isolation control also passed: a cross-owner/frame read raised `PermissionError`. The removal
control proves the recall measurement loses exactly one hit when one expected episode is absent.

The false-retrieval result is deliberately negative: exact lexical overlap cannot distinguish a
stored distractor from an answerable memory, so it answers every distractor query instead of
abstaining. This is the measured gap that a later retrieval policy must beat.

Latency used repeated wall-clock timings; examined-record cost is reported separately rather than
treated as time. Storage compared one 120-record store with a 1,200-record store at the same
target/distractor ratio. These measurements close CP-M2 without claiming semantic, paraphrase, or
noisy-query quality.
