# PolyBrains-AI-Memory — Predictions

Append-only pre-registration ledger for memory experiments. Do not edit an entry after its run
begins; append a correction with the reason instead.

## M1 — private-frame retrieval versus pooling

**Registered:** 2026-08-23, before implementation or execution.

**Fixture and controls:** frozen in `docs/memory-proposal.md`. Two owner/frame pairs assign
incompatible meanings to `bank`; both retrieval arms use the same exact-token, confidence, recency,
and record-ID ordering. The private arm restricts candidates to the requesting owner/frame. The
pooled arm does not. An unmatched query gates abstention, and an unauthorized-frame read gates
isolation.

**Prediction:** private retrieval will return 2/2 correct records; pooled retrieval will return
1/2 correct because the higher-confidence financial episode crosses into `a/map-a`. Both arms will
abstain on the unmatched query. Provenance completeness will be 100%, and cross-frame private reads
will fail.

**Acceptance:** private false retrieval must be lower than pooled false retrieval; private correct
retrieval may trail pooled by at most 5 percentage points; provenance completeness must be 100%;
isolation must hold. Any failed control makes the run invalid rather than negative.

**Falsification:** H-M1 fails this fixture if pooling is no worse, private retrieval exceeds the
recall-loss margin, or the fixture cannot make the claimed metric fail for its intended reason.
This entry makes no prediction for H-M2.

### M1 result — 2026-08-23

Valid run. All registered controls passed. Private retrieval returned 2/2 correct with 0/3 false;
pooling returned 1/2 correct with 1/3 false; both abstained on the unmatched query. Provenance was
complete and the unauthorized private read failed. The fixture-level acceptance rule passed.
Report: `reports/m1-private-retrieval.md`.

## M2 — private episodic recall baseline

**Registered:** 2026-08-25, before implementation or execution.

**Fixture and controls:** two private owner/frame stores, each containing 100 active episodes with
a unique lexical cue and 20 higher-confidence distractors. Query each cue once and score only the
exact expected record as correct. The no-memory arm receives the same 200 answerable queries but
no records. Removing one expected episode is the recall-loss control; cross-frame reads remain
forbidden.

**Prediction:** exact-token private retrieval will recall 200/200 records (100% recall@1), while
the no-memory arm recalls 0/200. The one-record removal control must reduce recall to 199/200, and
the isolation control must reject a cross-frame read.

**Acceptance:** the run is valid only if the removal control lowers recall by exactly one result
and isolation holds. This is a deterministic software baseline, not evidence that lexical
retrieval generalizes beyond unique cues.

**Falsification:** the baseline fails if private retrieval misses any present expected record, the
no-memory arm returns a record, the recall metric cannot detect the removed episode, or private
isolation fails.

### M2 recall result — 2026-08-25

Valid run. Private exact-token retrieval recalled 200/200 expected records; the no-memory arm
recalled 0/200. Removing one expected episode reduced recall to 199/200, and the unauthorized
cross-frame read failed. Report: `reports/m2-private-recall.md`.

## M3 — popular false episode consolidation

**Registered:** 2026-08-25, before implementation or execution.

**Fixture and controls:** one owner/frame contains three 0.99-confidence episodes asserting the
same false claim and one 0.60-confidence episode asserting the true claim. The observed-outcome
set verifies only the true episode. Compare no consolidation, agreement/confidence consolidation,
and outcome-gated consolidation. Both consolidation policies must use the same exact-payload
groups and retain every input record ID as either supporting or contradicting evidence.

**Prediction:** no consolidation emits zero semantic records; agreement/confidence emits the
popular false claim; outcome gating emits the verified true claim. Each emitted record compresses
four episodes to one semantic record (25%) while retaining 4/4 evidence links. The true minority
is retained as a contradiction under the naive arm, and all three false episodes are retained as
contradictions under the conservative arm.

**Acceptance:** outcome gating must produce zero false consolidations versus one for the naive
arm, retain all contradictions, and permit the complete input ID set to be reconstructed from its
supporting and contradicting links. An empty verified-outcome set must abstain.

**Falsification:** H-M2 fails this fixture if the popular false claim is outcome-gated, the true
claim is lost, any minority/contradicting episode disappears from the evidence links, or the
metric/control cannot distinguish the two policies. This standalone semantic fixture is not yet
evidence about shared multi-agent propagation.

### M3 result — 2026-08-25

Valid run. No consolidation emitted zero semantic records. Agreement/confidence consolidation
emitted the popular false claim (one false consolidation); outcome-gated consolidation emitted
the verified true claim (zero false consolidations). Both semantic records retained 4/4 episode
IDs across supporting and contradicting links, compressed four episodes to one semantic record
(25%), and an empty outcome set abstained. Report: `reports/m3-consolidation.md`.

## M4 — frame-aware retrieval and explicit claim exchange

**Registered:** 2026-08-25, before implementation or execution.

**Fixture and controls:** reuse the frozen M1 `bank` fixture and identical lexical ranking. The
pooled arm answers both owner/frame requests from both records. The frame-aware arm ranks inside
each private store, then exchanges both results as separate claims without selecting a global
winner. Each claim reports its source record, lexical-overlap score, records examined,
contradictions, and abstention. An event-time cutoff and exact-source filter must independently
exclude an otherwise matching record.

**Prediction:** frame-aware retrieval returns 2/2 correct answers, 2/2 answer rate, zero confident
errors, and examines two records total. Pooled retrieval returns 1/2 correct, 2/2 answer rate, one
0.99-confidence error, and examines four records total when answering both requests. Each
frame-aware claim scores one lexical token and names the other frame's incompatible claim as a
contradiction. The unmatched query yields two explicit abstentions.

**Acceptance:** frame-aware correctness must exceed pooled correctness without lowering answer
rate; correctness, answer rate, confident errors, and examined-record cost must be reported
separately. Both filter controls and explicit abstention must pass. Any global winner substituted
for the two frame claims invalidates the run.

**Falsification:** H-M1 fails this fixture if frame boundaries do not prevent the pooled error,
the independent arm loses an answer, contradictions or abstentions disappear during exchange, or
the cost/score instrumentation cannot change when a candidate is added or removed.

### M4 result — 2026-08-25

Valid run. Frame-aware retrieval returned 2/2 correct at a 2/2 answer rate, zero confident errors,
and two examined records. Pooled retrieval returned 1/2 correct at the same 2/2 answer rate, one
0.99-confidence error, and four examined records. Both frame claims scored one lexical token,
retained the incompatible other-frame claim as a contradiction, and the unmatched query produced
two explicit abstentions. Event-time and source exclusion controls passed. Report:
`reports/m4-frame-aware-retrieval.md`.

## M5 — explicit lifecycle and privacy deletion

**Registered:** 2026-08-25, before implementation or execution.

**Fixture and controls:** one private store writes a stale fact, corrects it with a reason, archives
the correction as a decay action, forgets a second fact, and physically deletes a third fact
containing the protected token `secret-731`. Lifecycle changes are immutable superseding records;
physical deletion is the sole exception and must leave a payload-free tombstone. A semantic
compression record must retain links to all surviving evidence. Missing reasons and transitions
from an already superseded record are invalid controls.

**Prediction:** retrieval returns the correction before decay and abstains afterward. Archived and
forgotten states remain distinguishable and inspectable; the superseded stale record remains in
history. Physical deletion removes every copy of `secret-731` while retaining a tombstone naming
the deleted ID and its reason. Compression retains every supporting evidence ID. Stored payload
bytes fall by exactly the deleted payload length.

**Acceptance:** every transition/control must behave as predicted, serialized transition records
must preserve reasons, no protected bytes may survive deletion, and semantic compression must be
traceable to surviving episode IDs.

**Falsification:** CP-M5 fails if a stale/corrected fact remains retrievable after decay, forgetting
is indistinguishable from archival or deletion, supersession erases history, deletion leaves the
protected payload anywhere in the store, an unexplained lifecycle action is accepted, or
compression loses its evidence chain.

### M5 result — 2026-08-25

Valid run. Correction became retrievable while the stale record remained inspectable; decay then
archived the correction and retrieval abstained. Archived, forgotten, superseded, and physically
deleted states remained distinguishable. Privacy deletion removed the full 18-byte protected
payload and left a payload-free tombstone with its target and reason. Missing-reason and repeated-
transition controls failed as required. Semantic compression retained both surviving evidence IDs.
Report: `reports/m5-lifecycle.md`.

## M6 — signed shared claims under a correlated prior

**Registered:** 2026-08-25, before implementation or execution.

**Fixture and controls:** six shared-memory members. Three publish 0.99-confidence false claims
with distinct evidence IDs but the same `correlated-prior` provenance; one publishes a
0.60-confidence true claim whose evidence is later outcome-verified; one signs an explicit
abstention; one remains silent. Claims use deterministic standard-library HMAC authentication and
carry evidence references, not private-store access. Compare pooled writes, majority,
highest-confidence, and outcome-gated consolidation. Reuse M3's three-false/one-true shape as the
replication control.

**Prediction:** pooled writes retain both false and true shared records; majority and confidence
select false; conservative consolidation abstains before verification and selects true after the
true evidence ID is verified. False-memory propagation is one shared false record under pooled,
majority, and confidence, versus zero under conservative. Their contamination radius is all six
authorized shared readers versus zero. Useful recall of the true claim is 1 for pooled and
post-verification conservative, 0 for majority/confidence. Conservative recovery is 0-to-1 useful
truth after outcome verification.

**Acceptance:** signatures and scope authority must gate writes/reads; agreement, contradiction,
confidence, abstention, and silence must remain separately inspectable; every shared record must
retain supporting and contradicting claim IDs. The exchange must remain unchanged after every
policy run, so no confident claim can overwrite another frame. The correlated false majority must
not enter conservative shared memory without verified evidence.

**Falsification:** H-M2 fails this fixture if conservative consolidation admits the correlated
false claim, fails to recover the verified truth, loses disagreement/abstention/silence, exposes a
private claim to another member, accepts a forged write, mutates exchanged claims, or cannot
reproduce M3's naive-versus-outcome result.

### M6 result — 2026-08-25

Valid run. Pooled, majority, and confidence policies each produced one false shared record with a
six-member contamination radius; conservative consolidation produced none. Pooled retained the
true claim, majority/confidence lost it, and conservative useful recall recovered from 0 to 1
after true evidence verification. Three correlated false claims, one contradiction, one explicit
abstention, one silent member, and distinct confidence values remained inspectable. Private,
shared, and public read controls passed; a forged write failed; all exchanged claims remained
unchanged. Report: `reports/m6-shared-memory.md`.

## M7 — deterministic decay versus no decay

**Registered:** 2026-08-25, before implementation or execution.

**Fixture and controls:** compare identical private stores on four unique-cue queries: two old
episodes whose facts are false at evaluation time and two fresh episodes whose facts remain true.
The no-decay arm retains all episodes. The decay arm archives records with event time strictly
before an explicit cutoff, using immutable lifecycle markers with one required reason. A fifth
unscored record exactly on the cutoff gates boundary correctness and must remain active.

**Prediction:** no decay returns 2/4 correct, 2/4 false, and answers 4/4. Cutoff decay returns 2/4
correct, 0/4 false, and answers 2/4; fresh useful recall remains 2/2 in both arms. Exactly two
records are archived, their original evidence remains inspectable, and each marker records the
same decay explanation. The cutoff-boundary control remains retrievable.

**Acceptance:** retain cutoff decay only if it reduces stale false recall from 2 to 0 without
reducing fresh useful recall below 2/2. Correct recall, false recall, and answer rate are separate;
abstention is not scored as correctness. The no-decay arm is the software baseline.

**Falsification:** the mechanism fails if an old false episode remains retrievable, a fresh or
boundary episode is archived, useful recall falls, historical evidence or explanations disappear,
or the metric treats decay-induced abstention as a correct answer. This tests a deterministic
retention policy, not a claim of cognitive resemblance or validity.

### M7 result — 2026-08-25

Valid run. No decay returned 2/4 correct, 2/4 false, and answered 4/4. Cutoff decay returned 2/4
correct, 0/4 false, and answered 2/4, preserving fresh useful recall at 2/2. Exactly two old
records were archived with explanations; their evidence remained inspectable; the record exactly
on the cutoff remained retrievable. The mechanism is retained for its measured stale-error
reduction, not for cognitive resemblance. Report: `reports/m7-decay.md`.

## M8 — removable agent adapter equivalence

**Registered:** 2026-08-25, before implementation or execution.

**Fixture and controls:** a minimal framework-neutral adapter receives one agent observation as
text plus explicit identity, provenance, timestamps, and confidence, then writes through the
existing `MemoryRecord` and `EpisodicStore`. Compare its stored record byte-for-byte with a record
constructed directly through the core, and compare recall identity and abstention. The adapter
lives in a separate module that the core and package initializer do not import. Invalid empty text
is the trust-boundary control.

**Prediction:** adapter and direct-core records serialize to identical bytes; both retrieve the
same record ID for the lexical query and abstain on an unmatched query. Empty text is rejected.
Removing the adapter module leaves all M1–M7 core imports and gates structurally unchanged because
dependency direction is adapter-to-core only.

**Acceptance:** equivalence and validation controls must pass without adding a dependency. No
Monty adapter is accepted unless a standalone benchmark gap is first measured. No PolyBrains or
Monty compatibility is claimed, so inherited checks are not evidence for this run and are not
invoked as a substitute.

**Falsification:** CP-M8 fails if the adapter changes record bytes, ownership, provenance,
retrieval, or abstention; accepts empty text; is imported by the core; adds a provider/framework
dependency; or makes a compatibility claim without the inherited gate.

### M8 result — 2026-08-25

Valid run. Adapter and direct-core records serialized to identical bytes, returned the same record
ID, and both abstained on the unmatched query. Empty text was rejected. The adapter remains a
separate leaf module absent from the package's core exports, and it added no dependency. No Monty
adapter or compatibility claim was made; inherited PolyBrains checks were therefore not presented
as evidence for this standalone result. Report: `reports/m8-agent-adapter.md`.

## M2b — false retrieval, provenance, latency, and storage growth

**Registered:** 2026-08-25, before implementation or execution.

**Fixture and controls:** extend M2 without changing its ranker. The 240-record small corpus keeps
200 valid unique-cue episodes and 40 high-confidence lexical distractors. Query all 40 distractor
cues as unanswerable cases: any returned record is false retrieval. Check every one of the 240
returned valid-or-false results for all required provenance fields and deterministic hash-checked
round-trip. Compare one 120-record private store with a 1,200-record store containing the same
target/distractor ratio. Measure median and p95 wall-clock retrieval latency over repeated fixed
queries, deterministic records examined per query, payload bytes, and serialized bytes.

**Prediction:** the exact-overlap baseline falsely retrieves 40/40 distractors, while no memory
returns 0/40; this negative result exposes the baseline's abstention weakness rather than being an
invalid run. Provenance completeness is 240/240. Examined-record cost grows from 120 to 1,200 per
query. Record count grows exactly 10×; payload and serialized storage grow between 9× and 12×.
Large-corpus median latency exceeds small-corpus median latency; wall time is descriptive and no
absolute speed threshold is registered.

**Acceptance:** the run is valid only if the no-memory control has zero false retrieval, all
provenance checks pass, examined cost changes exactly 10×, storage growth stays within the
registered range, and both latency distributions are reported. A high false-retrieval rate is a
measured baseline failure, not a reason to tune the ranker after registration.

**Falsification:** the measurement is invalid if distractor retrieval is scored as correct,
abstention is scored as false, provenance omits a required field or hash validation, the scale
control does not change examined cost/storage, or latency is inferred from operation count rather
than timed directly.

### M2b result — 2026-08-25

Valid negative result. Exact lexical retrieval falsely returned 40/40 unanswerable distractors;
no memory returned 0/40. Provenance was complete for 240/240 returned records. Scaling one private
store from 120 to 1,200 records increased examined cost from 120 to 1,200 per query, median/p95
latency from 0.128/0.131 ms to 1.273/1.374 ms, payload storage 11.23×, and serialized storage
10.04×. Report: `reports/m2-private-recall.md`.

## R0 — v0.2 retrieval calibration protocol

**Registered:** 2026-08-25, before implementing or evaluating a v0.2 retrieval policy.

**Fixtures:** development and held-out JSON fixtures, query classes, labels, hashes, metrics,
controls, rivals, acceptance margins, and invalid-run conditions are frozen in
`docs/retrieval-v02-protocol.md`. The development fixture SHA-256 is
`47b15a50296b4ec248937739a6d375c78c856130ef7511e882b222238df280d3`; held-out is
`f241fe5d12a00aba3eb85dec261547eae63d6351228673d144c6e9b1374c8fd0`.

**Directional prediction:** a deterministic calibrated lexical policy can reduce held-out false
retrieval by at least 50 percentage points relative to unchanged v0.1 without losing more than 5
percentage points of correct retrieval. It will preserve provenance and examined-record cost, use
at most 2× median latency and 1.1× serialized storage, and reproduce the false-retrieval direction
on development. No prediction selects which lexical policy will win.

**Acceptance:** all six margins in the protocol are conjunctive. A policy that merely abstains
more and loses answers beyond the margin fails. A valid negative result retains v0.1.

**Falsification:** H-R1 fails if no frozen deterministic policy meets every held-out margin, if the
direction does not replicate on development, or if the harness cannot fail under its registered
perturbations. Any fixture/hash mismatch, label leakage, unequal candidate boundary, post-held-out
tuning, or v0.1 regression makes the run invalid rather than negative.

## R2 — lexical calibration result

**Run:** 2026-08-25. Candidate `minimum-3/4` was frozen at commit `bf1aa68` before one held-out
run. The held-out fixture hash matched R0.

The candidate reduced held-out false retrieval from 1/2 to 0/2 and preserved correct retrieval at
2/4, provenance completeness at 100%, examined records at 31, and serialized storage at 3,364
bytes. Median latency was 51,094.5 ns versus 74,932 ns for v0.1. It met all registered held-out
margins and showed the same false-retrieval direction on development.

The result is mixed: development correct retrieval fell from 2/4 to 1/4 because a valid correction
and lexical collision both scored 1/2. The candidate is retained only for CP-R3 replication and
has not entered the memory core. Report: `reports/cp-r2-heldout.md`.
