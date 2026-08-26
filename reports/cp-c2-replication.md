# CP-C2 — contradiction reliability replication

**Run:** 2026-08-26
**Candidate freeze:** `6cc1bc2`
**Config:** `b0f4dae0d46171f5502e6607a8126ac546297adb28bd257b9dc289fd89732f52`

The outcome/provenance rule passed the registered replication gate on seeds 11, 23, and 37. It
returned both answerable records, made no wrong or false retrievals, correctly abstained twice,
and missed no answers on every seed. Similarity-only returned 1 correct, 1 wrong, and 2 false on
every seed. Confidence-ranked did the same on seeds 11 and 37; reversed confidence made its
verified answer correct on seed 23, but it still made both unsupported false returns.

| seed | similarity correct/wrong/false | confidence correct/wrong/false | outcome correct/wrong/false | examined | storage |
|---:|---:|---:|---:|---:|---:|
| 11 | 1 / 1 / 2 | 1 / 1 / 2 | 2 / 0 / 0 | 32 | 3,734 B |
| 23 | 1 / 1 / 2 | 2 / 0 / 2 | 2 / 0 / 0 | 32 | 3,722 B |
| 37 | 1 / 1 / 2 | 1 / 1 / 2 | 2 / 0 / 0 | 32 | 4,193 B |

All returned records had complete provenance, all policies examined the same active private
records, and every owner/frame swap preserved returned IDs and abstention reasons. Seed 37 ignored
the superseded stale support and followed its active correcting evidence. Candidate median latency
was below both controls on all three measured runs, inside the 3× ceiling.

The result supports only explicit linked evidence: it does not validate source labels,
confidence, similarity, agreement, or recency as correctness signals. The policy stays in the
benchmark rather than entering the core API; broader evidence can justify that integration later.
