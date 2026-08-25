# CP-R2 — held-out lexical calibration result

**Run:** 2026-08-25, once after candidate freeze at `bf1aa68`  
**Arms:** unchanged v0.1 versus frozen minimum normalized query coverage 3/4

| held-out metric | v0.1 | minimum-3/4 |
|---|---:|---:|
| correct retrieval | 2/4 (50%) | 2/4 (50%) |
| false retrieval | 1/2 (50%) | 0/2 (0%) |
| wrong retrieval | 1/4 (25%) | 1/4 (25%) |
| answer rate | 4/6 (66.7%) | 3/6 (50%) |
| abstention precision | 1/2 (50%) | 2/3 (66.7%) |
| abstention recall | 1/2 (50%) | 2/2 (100%) |
| provenance completeness | 4/4 (100%) | 3/3 (100%) |
| records examined | 31 | 31 |
| median latency | 74,932 ns | 51,094.5 ns |
| p95 latency | 82,350 ns | 81,493 ns |
| serialized storage | 3,364 bytes | 3,364 bytes |

The candidate meets the registered held-out margins: false retrieval fell 50 percentage points,
correct retrieval did not fall, provenance stayed complete, examined-record and storage costs did
not increase, and measured median latency stayed below 2×. Development showed the same false-
retrieval direction.

This is mixed evidence, not a release claim. On development, the same threshold reduced correct
retrieval by 25 percentage points because the valid correction and lexical collision both scored
1/2. The held-out correction happened to score 1. The policy is retained only for CP-R3
replication and is not promoted into the memory core.
