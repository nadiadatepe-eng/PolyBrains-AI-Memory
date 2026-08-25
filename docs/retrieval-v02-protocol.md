# v0.2 retrieval-quality protocol

## Question

Can a deterministic lexical policy reduce v0.1's false retrieval on lexical collisions without
buying that reduction through unacceptable correct-answer loss or hidden cost?

This protocol freezes measurement before policy implementation. It does not select a scorer,
threshold, margin, embedding model, or synthesis rule.

## Frozen fixtures

| split | records | queries | SHA-256 |
|---|---:|---:|---|
| `configs/retrieval/v02-development.json` | 8 | 6 | `47b15a50296b4ec248937739a6d375c78c856130ef7511e882b222238df280d3` |
| `configs/retrieval/v02-heldout.json` | 8 | 6 | `f241fe5d12a00aba3eb85dec261547eae63d6351228673d144c6e9b1374c8fd0` |

Each split contains exactly one query in each class:

- `answerable-exact`: the expected private record shares literal content tokens.
- `answerable-paraphrase`: the expected private record uses different content vocabulary.
- `unanswerable-lexical-collision`: a distractor overlaps, but ground truth requires abstention.
- `corrected-stale`: an expected correction supersedes an older record.
- `contradictory`: a lower-confidence observed outcome conflicts with a confident prior.
- `unmatched`: no record answers the query; ground truth requires abstention.

Owner/frame, source, confidence, and timestamps are fixture inputs, never correctness labels.
Changing a fixture invalidates its hash; corrections require a new fixture version and appended
pre-registration rather than an in-place edit.

## Development and held-out discipline

- Policy families and parameters may use only the development split.
- The held-out split may be run once after the candidate policy and all parameters are frozen.
- v0.1 remains the unchanged control on both splits.
- A failed candidate remains a reportable result; it is not retuned on held-out labels.

## Metrics

For each query, exactly one outcome is recorded:

- **correct retrieval**: expected ID is non-null and the returned ID matches it.
- **wrong retrieval**: expected ID is non-null and a different ID is returned.
- **false retrieval**: expected ID is null and any record is returned.
- **correct abstention**: expected ID is null and no record is returned.
- **missed answer**: expected ID is non-null and no record is returned.

Report, separately and per query class:

- correct retrieval rate over answerable queries;
- wrong retrieval rate over answerable queries;
- false retrieval rate over unanswerable queries;
- answer rate over all queries;
- abstention precision (correct abstentions / all abstentions);
- abstention recall (correct abstentions / unanswerable queries);
- provenance completeness over returned records;
- records examined per query, median and p95 wall-clock latency, and serialized storage bytes.

Zero-denominator metrics are `null`, never zero. Confidence, overlap, agreement, and retrieval
score are explanatory fields and cannot substitute for correctness.

## Acceptance margins

H-R1 passes only if the frozen candidate, on held-out evaluation:

1. reduces false retrieval by at least **50 percentage points** versus v0.1;
2. loses no more than **5 percentage points** of correct retrieval on answerable queries;
3. preserves **100% provenance completeness** and all v0.1 isolation/lifecycle/shared-memory gates;
4. examines no more records per query than v0.1;
5. uses no more than **2×** v0.1 median latency and **1.1×** serialized storage; and
6. shows the same false-retrieval direction on the development split.

All six clauses are mandatory. Lower false retrieval with excessive missed answers is negative,
not success. Wall-clock timing is descriptive if environmental noise reverses a ratio; the
deterministic examined-record control remains mandatory and an unstable timing run is repeated in
full, never selectively.

## Controls that make the harness fail

- Swap an expected answer ID: one correct retrieval must become wrong.
- Remove an expected record: one answerable query must become a missed answer.
- Return the lexical distractor for an unanswerable collision: false retrieval must increase.
- Convert a false return to `None`: correct abstention must increase and answer rate must decrease.
- Remove a required provenance field or corrupt the payload hash: provenance completeness must fall.
- Add ten irrelevant private records: examined-record cost must increase by exactly ten for the
  scan baseline.

The replication control swaps owner/frame labels while preserving content and expected mappings;
metrics must follow the mappings, not the literal labels.

## Rival explanations

- **Threshold-only refusal:** false retrieval falls only because answer rate collapses. The
  correct-retrieval margin separates this from useful calibration.
- **Confidence is correctness:** the contradictory fixtures make the highest-confidence record
  wrong by observed outcome.
- **Recency solves retrieval:** corrected/stale cases can benefit from lifecycle state, while
  lexical collisions and paraphrases remain independent controls.
- **Frame isolation is the improvement:** both arms use identical owner/frame boundaries; only the
  scoring/abstention policy may differ.
- **Held-out tuning:** fixture hashes, one-run discipline, and append-only results make post-hoc
  policy changes an invalid run.
- **The fixture is too small:** CP-R0 freezes the smallest falsifiable gate; CP-R3 must replicate
  direction across deterministic seeds before a release claim.

## Invalid runs

A run is invalid if fixture hashes differ, an expected label changes after policy work begins,
arms use different candidate boundaries, held-out results influence parameters, any metric is
inferred rather than computed, a zero denominator is reported as zero, a required control cannot
go red, or a v0.1 regression gate fails. Otherwise negative results remain valid.

## Exclusions

No embeddings, vector database, language model, generated answer, network service, Monty adapter,
shared-memory policy change, or cognitive mechanism. CP-R4 may reconsider semantic retrieval only
after CP-R2/R3 measure a lexical gap that survives this protocol.
