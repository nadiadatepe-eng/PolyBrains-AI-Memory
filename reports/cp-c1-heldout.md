# CP-C1 — held-out reliability result

**Run:** 2026-08-26, once after candidate freeze at `ad11787`
**Fixture:** `5bd18782f753c75dee126dcd8190f16538836309abca080ded1ad84cdc795ef2`

The unchanged outcome/provenance candidate passed every registered held-out margin. It returned the
explicitly supported laboratory outcome, abstained on the unsupported dock conflict, and preserved
the uncontested vault answer: 2 correct, 0 wrong, 0 false, 1 correct abstention, and 0 missed
answers. Each control produced 1 correct, 1 wrong, and 1 false retrieval.

All arms examined 18 active private records, serialized the same 2,944 bytes, and had 100%
provenance completeness. Median/p95 latency was 0.060/0.071 ms for outcome/provenance,
0.064/0.069 ms for similarity-only, and 0.064/0.068 ms for confidence-ranked, inside the 3× margin.

The result supports the narrow claim that explicit stored links can distinguish a verified outcome
from a relevant confident prior. It does not show that provenance, source names, recency,
similarity, or confidence imply correctness. Replication remains mandatory.
