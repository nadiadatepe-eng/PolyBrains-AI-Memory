# CP-R3 — lexical robustness and replication

**Run:** 2026-08-25  
**Pre-registration:** commit `7b7ba90`  
**Arms:** unchanged v0.1 and frozen minimum normalized query coverage 3/4

| seed | arm | correct | false | answer rate | abstention precision / recall | provenance | examined | storage |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 11 | v0.1 | 2/4 | 1/2 | 66.7% | 50% / 50% | 100% | 31 | 3,376 B |
| 11 | minimum-3/4 | 2/4 | 0/2 | 50% | 66.7% / 100% | 100% | 31 | 3,376 B |
| 23 | v0.1 | 2/4 | 1/2 | 66.7% | 50% / 50% | 100% | 31 | 3,376 B |
| 23 | minimum-3/4 | 1/4 | 0/2 | 33.3% | 50% / 100% | 100% | 31 | 3,376 B |
| 37 | v0.1 | 2/4 | 1/2 | 66.7% | 50% / 50% | 100% | 31 | 3,376 B |
| 37 | minimum-3/4 | 2/4 | 1/2 | 66.7% | 50% / 50% | 100% | 31 | 3,376 B |

Seed 11 replicated the CP-R2 held-out result. Seed 23 reduced the collision but also abstained on
the valid correction, losing 25 percentage points of correct retrieval. Seed 37 answered the
one-token collision, so false retrieval did not improve. The candidate therefore fails the
conjunctive replication gate and is rejected rather than promoted to the core.

Per-class outcomes are preserved in `reports/cp-r3-result.json`. Across every seed, exact and
token-order queries were correct, paraphrases were missed, the high-confidence contradictory
prior beat the observed outcome, stale records stayed hidden behind corrections, and unmatched
queries abstained. All owner/frame swaps produced identical outcomes. Provenance, examined-record
cost, storage, isolation, lifecycle, disagreement, and shared consolidation remained unchanged.
No run was invalid; all positive, mixed, and negative outcomes are retained.

Latency medians ranged from 22,198 to 79,786.5 ns and p95 from 81,641 to 93,389 ns; timing was
descriptive and no arm exceeded the registered 2x median limit. The complete raw metric summary is
machine-readable in the JSON report.
