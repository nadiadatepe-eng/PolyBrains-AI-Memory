# v0.3 contradiction-reliability protocol

## Question

When relevant private memories contradict, can explicit stored outcome/provenance links reduce
wrong retrieval without hiding the improvement as abstention?

This protocol freezes the fixtures, arms, metrics, margins, controls, and replication cases before
the outcome/provenance policy is implemented. Similarity, confidence, source names, agreement,
recency, and ground-truth labels are not correctness evidence.

## Frozen fixtures

| split | records | queries | SHA-256 |
|---|---:|---:|---|
| development | 7 | 3 | `2eeccbf54ba01f2a7764c9da89b0b4699e6aaa7ecdccdbe6086a5a893b705ebe` |
| held-out | 7 | 3 | `5bd18782f753c75dee126dcd8190f16538836309abca080ded1ad84cdc795ef2` |
| replication | 3 seeds | 4 classes/seed | `b0f4dae0d46171f5502e6607a8126ac546297adb28bd257b9dc289fd89732f52` |

Every arm receives the same active records, owner/frame filter, query text, and frozen candidate
IDs. `expected_record_id` is visible only to scoring. The classes are:

- **verified contradiction:** two relevant candidates conflict; a separate active record explicitly
  supports the lower-confidence observed candidate and contradicts the prior;
- **unverified contradiction:** two relevant candidates conflict without linked outcome evidence;
- **uncontested exact:** one relevant candidate must still be returned; and
- **missing outcome:** replication-only conflict where the outcome link is absent and abstention is
  correct.

Seed 23 reverses the confidence ordering. Seed 37 supersedes stale evidence with a correction.
Owner/frame labels are swapped in a separate arm without changing expected IDs.

## Frozen arms

1. **similarity-only:** highest token overlap, then record ID; confidence is ignored.
2. **confidence-ranked:** highest confidence, then overlap and record ID.
3. **outcome-provenance:** if one candidate exists, return it; for a conflict, count active records
   that explicitly name each candidate in `supports` and `contradicts`. Return the unique positive
   net-evidence winner; otherwise abstain.

The outcome/provenance arm may inspect only stored links after normal lifecycle and frame filters.
It may not inspect source strings, expected IDs, fixture class, or confidence. No new record type,
core scorer, dependency, embedding, or generated answer is permitted during selection.

## Metrics and acceptance

Use the v0.2 mutually exclusive retrieval outcomes and report correct, wrong, false, correct
abstention, and missed answer counts separately. Also report answer rate, abstention precision and
recall, provenance completeness, active private records examined, median/p95 latency, and
serialized storage.

H-C1 passes held-out only if outcome/provenance gating, versus both controls:

1. reduces wrong retrieval by at least **50 percentage points**;
2. does not reduce correct retrieval and produces **zero missed answers**;
3. reduces false retrieval by at least **50 percentage points** on the unverified conflict;
4. preserves **100% provenance completeness**, owner/frame isolation, and all v0.2 gates;
5. examines the same active private records, changes no storage, and stays within **3×** control
   median latency; and
6. shows the same correct/wrong/false direction on development and every replication seed.

All clauses are conjunctive. Timing is descriptive if environmental noise alone violates its
ratio; repeat the complete run, never a selected query.

## Controls that must go red

- Replace the verified expected ID with the prior: correct becomes wrong.
- Remove the supporting link: verified retrieval becomes an abstention.
- Reverse support and contradiction links: the wrong candidate is returned.
- Remove the exact candidate: one correct answer becomes missed.
- Force a candidate on the unverified conflict: false retrieval increases.
- Remove a provenance field or corrupt a payload hash: completeness falls.
- Add one active private record: examined cost increases by one for every arm.
- Swap only record owner/frame labels: the swap equivalence assertion fails.

## Invalid and negative runs

A hash mismatch, changed candidate boundary, label access by a policy, unequal active-record scans,
post-held-out tuning, missing class/seed/arm, swap mismatch, metric that cannot go red, or v0.2 gate
regression makes a run invalid. Otherwise a failed margin is a valid negative result and the policy
is rejected.

## Exclusions

No RAG, generation, vector database, new embedding model, semantic fine-tuning, shared-memory
change, source-label allowlist, or rule equating confidence, agreement, similarity, provenance,
recency, or outcome vocabulary with correctness.
