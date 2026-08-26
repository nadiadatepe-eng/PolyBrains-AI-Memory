# PolyBrains-AI-Memory — TODO

The inherited PolyBrains checkpoint ledger is preserved unchanged in `ORIGIN-TODO.md`. Its
results constrain this project but do not count as evidence for the memory hypotheses below.

## Research claims

- **H-M1:** Compared with one pooled memory, independent per-frame retrieval followed by
  disagreement-preserving synthesis reduces confident shared errors without reducing correct
  answer rate beyond a pre-registered margin.
- **H-M2:** Conservative consolidation using provenance and observed outcomes produces fewer
  false shared memories than consolidation based on agreement or confidence alone.

Agreement, confidence, retrieval score, and correctness are separate measurements. None may be
used as a substitute for another.

## CP-M0 · Contract and baseline — done

- [x] Import PolyBrains at `fb8071d` into an independent repository.
- [x] Preserve its source, tests, reports, predictions, decisions, and research sources.
- [x] Record Nadi as creator and maintainer and Codex (OpenAI) as AI co-author.
- [x] Separate the active memory roadmap from the inherited PolyBrains ledger.
- [x] Write `docs/memory-proposal.md` with H-M1, H-M2, rival explanations, exclusions, and
      falsification conditions.
- [x] Create append-only `PREDICTIONS-MEMORY.md` for the new experiments; keep inherited
      `PREDICTIONS.md` historical.
- [x] Freeze the first benchmark, metrics, acceptance margins, and replication control before
      implementing a memory policy.

Gate: the proposal permits a negative result, and every claimed metric has a smallest fixture that
can make it fail for the intended reason.

## CP-M1 · Explicit memory record — baseline implemented

- [x] Define one versioned, model-independent record for short-term, episodic, semantic, and
      long-term memory.
- [x] Require identity, owning agent and frame, source, event time, write time, confidence,
      lifecycle state, and links to supporting, contradicting, and superseded records.
- [x] Keep payload bytes distinct from claims about those bytes.
- [x] Provide deterministic serialization and validation using the Python standard library.
- [x] Reject missing provenance, invalid transitions, and silent in-place history rewrites.

Gate: round-trip bytes are deterministic; malformed and provenance-free records fail; prior
versions remain inspectable after update or deletion.

## CP-M2 · Private episodic memory — baseline implemented

- [x] Give each agent/frame an independent append-only episodic store.
- [x] Implement explicit write, retrieve, supersede, and tombstone operations.
- [x] Establish a no-memory baseline and exact-match/recency retrieval baseline.
- [x] Measure recall beyond the frozen M1 micro-fixture.
- [x] Measure false retrieval, provenance completeness, latency, and storage growth beyond the
      frozen M1 micro-fixture.

Gate: two private stores cannot read or mutate one another without an explicit claim exchange, and
the replication control reproduces the frozen baseline.

## CP-M3 · Semantic consolidation — baseline implemented

- [x] Derive semantic records from episodes without deleting their evidence chain.
- [x] Compare no consolidation, naive agreement/confidence consolidation, and conservative
      provenance/outcome consolidation.
- [x] Preserve contradictions and minority evidence as first-class state.
- [x] Measure false consolidation, contradiction retention, compression ratio, and reversibility.

Gate: a deliberately popular false episode cannot become verified semantic memory merely through
repetition or confidence.

## CP-M4 · Frame-aware retrieval — baseline implemented

- [x] Retrieve independently inside each frame before combining results.
- [x] Start with deterministic lexical, temporal, and provenance filters; add embeddings only if a
      measured retrieval gap justifies them.
- [x] Return claims with source records, scores, contradictions, and abstentions.
- [x] Compare pooled retrieval with independent retrieval plus synthesis on the frozen benchmark.

Gate: H-M1 can fail; retrieval quality, answer rate, confident error, and cost are reported
separately.

## CP-M5 · Memory lifecycle — baseline implemented

- [x] Define legal transitions for writing, correction, supersession, decay, compression,
      archival, forgetting, and deletion.
- [x] Distinguish inaccessible, forgotten, superseded, and physically deleted records.
- [x] Test retention policies against stale facts, corrected facts, privacy deletion, and bounded
      storage.
- [x] Preserve an auditable explanation for every automatic lifecycle action.

Gate: deletion removes the protected payload, supersession preserves history, and compression can
be traced back to surviving evidence.

## CP-M6 · Shared and collaborative memory — baseline implemented

- [x] Exchange signed claims and evidence references rather than exposing private stores.
- [x] Define private, shared, and public scopes with explicit read/write authority.
- [x] Represent agreement, contradiction, uncertainty, silence, and abstention independently.
- [x] Compare pooled writes, majority writes, confidence-weighted writes, and conservative shared
      consolidation.
- [x] Measure false-memory propagation, contamination radius, recovery, and useful recall.

Gate: one confident agent cannot silently overwrite another frame, and H-M2 is tested against a
replication control and a deliberately correlated-prior condition.

## CP-M7 · Cognitive mechanisms — conditional baseline implemented

- [x] Test decay, rehearsal, episodic-to-semantic consolidation, associative recall, or working
      memory limits only when each mechanism has a software baseline and falsifiable prediction.
- [x] Treat cognitive science as a source of hypotheses, not proof or implementation authority.

Gate: retain only mechanisms that beat their simpler baseline on a pre-registered outcome.

## CP-M8 · Agent and PolyBrains adapters — baseline implemented

- [x] Keep the memory core independent of any model, agent framework, vector database, or Monty.
- [x] Add one minimal agent adapter after CP-M4.
- [x] Do not add a PolyBrains/Monty adapter: no standalone benchmark gap currently justifies one.
- [x] Make no PolyBrains/Monty compatibility claim; the inherited checks remain mandatory before
      any future claim.

Gate: adapters can be removed without changing core record, lifecycle, retrieval, or consolidation
semantics.

## Explicit exclusions for the first release

- No autonomous command execution, credentials, cloud service, or network-dependent memory.
- No opaque “AI decides what to remember” policy without a deterministic comparison.
- No vector database until measured corpus size or retrieval quality requires one.
- No claim that cognitive resemblance implies cognitive validity.
- No publication claim inherited from PolyBrains.

---

# v0.2 roadmap — Retrieval calibration and abstention

The v0.1 baseline is frozen at commit `dedfc80`. Its 40/40 false retrievals on unanswerable
lexical distractors are the motivating failure; do not rewrite that result after improving the
ranker.

## Proposed claim

- **H-R1:** Compared with v0.1 exact-overlap retrieval, a deterministic calibrated lexical policy
  reduces false retrieval on held-out lexical collisions without reducing correct answer rate
  beyond a pre-registered margin.

H-R1 remains a proposal until CP-R0 appends its benchmark, directional prediction, margins, and
falsification conditions to `PREDICTIONS-MEMORY.md`.

## CP-R0 · Freeze the retrieval-quality experiment

- [x] Define answerable exact, answerable paraphrase, unanswerable lexical-collision,
      corrected/stale, contradictory, and unmatched query classes.
- [x] Keep owner/frame boundaries explicit and label correctness independently of overlap,
      confidence, agreement, and retrieval score.
- [x] Split policy-development and held-out evaluation fixtures before tuning.
- [x] Freeze correct retrieval, false retrieval, answer rate, abstention quality, provenance,
      records examined, latency, and storage metrics.
- [x] Pre-register acceptance margins, replication controls, rival explanations, and invalid-run
      conditions in append-only `PREDICTIONS-MEMORY.md`.

Gate: every metric has a smallest fixture that can make it fail for its intended reason, and the
held-out labels are frozen before a new policy is implemented.

## CP-R1 · Reproduce and harden the benchmark harness

- [x] Reproduce v0.1's 200/200 unique-cue recall, 40/40 distractor false retrieval, 240/240
      provenance completeness, and 10× examined-record scale control.
- [x] Add explicit ground-truth query records so a stored distractor is never inferred to be a
      valid answer merely because it overlaps.
- [x] Prove false retrieval, wrong retrieval, and abstention are scored separately.
- [x] Add one perturbation control that changes each reported metric in the expected direction.
- [x] Emit one deterministic machine-readable result alongside the human report.

Gate: the unchanged v0.1 policy reproduces its frozen result and every measurement can go red.

## CP-R2 · Smallest deterministic abstention policy

- [x] Compare the unchanged v0.1 ranker with only standard-library lexical candidates: normalized
      overlap, minimum score, and top-result margin.
- [x] Reuse existing temporal, provenance, lifecycle, and frame filters before adding new scoring.
- [x] Choose policy parameters on the development fixture only; run held-out evaluation once.
- [x] Return the winning record, score components, runner-up margin, evidence, contradictions, and
      an explicit abstention reason.
- [x] Reject any policy that improves false retrieval by silently converting correct answers into
      abstentions beyond the CP-R0 margin.

Gate: a retained policy beats v0.1 on the pre-registered primary outcome while satisfying the
correct-answer and cost margins; otherwise v0.1 remains the result.

## CP-R3 · Robustness and replication

- [x] Replicate across swapped owner/frame labels and at least three deterministic fixture seeds.
- [x] Test paraphrases, token-order changes, shared vocabulary, high-confidence distractors,
      stale/corrected facts, contradictions, and unmatched queries separately.
- [x] Report per-class correctness, false retrieval, answer rate, abstention quality, provenance,
      latency, examined records, and storage; do not collapse them into one score.
- [x] Verify private-frame retrieval and shared-memory consolidation gates remain unchanged.
- [x] Record negative, mixed, and invalid runs rather than retaining only the best seed.

Gate: the direction of the held-out result replicates without erasing any disagreement,
provenance, isolation, lifecycle, or shared-memory guarantee from v0.1.

## CP-R4 · Semantic retrieval — conditional

- [x] Enter this checkpoint only if CP-R2/R3 measure a paraphrase or vocabulary gap that the
      deterministic lexical policies cannot close within the registered margins.
- [x] Pre-register a lexical-versus-semantic comparison before adding an embedding model,
      vector database, network service, or new dependency.
- [x] Keep embeddings as candidate generation only; preserve deterministic filters, provenance,
      contradictions, scores, abstentions, and an exact lexical control.
- [x] Measure model/download size, indexing time, query latency, storage, reproducibility, and
      retrieval quality separately.
- [x] Remove the semantic path if it does not beat the lexical baseline on the registered outcome.

Gate: no semantic dependency enters the core without a measured retrieval benefit that exceeds
its pre-registered cost and reproducibility margins.

## CP-R5 · v0.2 release gate

- [x] Append results to `PREDICTIONS-MEMORY.md` and add immutable reports for every valid or
      invalid run.
- [x] Update `DECISIONS.md`, `README.md`, and this roadmap without rewriting v0.1 evidence.
- [x] Run the complete gate, the retrieval benchmark, and `git diff --check` from a clean checkout.
- [x] Confirm the agent adapter remains removable and the core remains standard-library-only
      unless CP-R4 independently justified a dependency.
- [x] Commit and tag v0.2 only when all unconditional checkpoints and controls pass.

Gate: a fresh checkout reproduces the selected retrieval result and every v0.1 regression gate;
known failures, conditional exclusions, and measured costs are explicit.

## v0.2 exclusions until evidence changes them

- No language model, generation, or RAG answer synthesis in the retrieval-quality experiment.
- No embedding or vector database before CP-R4's measured-gap gate.
- No tuning on held-out labels and no post-hoc acceptance-margin changes.
- No aggregate score that hides false retrieval, answer loss, provenance loss, or cost.
- No new cognitive mechanism, Monty adapter, or shared-memory policy in this release.

---

# v0.3 roadmap — Relevance is not reliability

The v0.2 semantic candidate recovered paraphrases but still returned the high-confidence
contradictory prior. Similarity solved a vocabulary gap, not correctness.

## Proposed claim

- **H-C1:** When relevant memories contradict, deterministic outcome/provenance gating reduces
  wrong retrieval relative to similarity-only and confidence-ranked controls without converting
  the improvement into excess abstention.

H-C1 remains a proposal until CP-C0 appends its fixtures, directional prediction, margins,
controls, and falsification conditions to `PREDICTIONS-MEMORY.md`.

## CP-C0 · Publish v0.2 and freeze the contradiction experiment

- [x] Add `CITATION.cff` and publish the existing CP-R5 report as the GitHub v0.2 release notes.
- [x] Define the smallest deterministic fixture with a high-confidence prior, contradictory
      observed outcome, provenance, owner/frame boundary, and explicit ground truth.
- [x] Freeze similarity-only, confidence-ranked, and outcome/provenance-gated arms before running
      the new policy.
- [x] Pre-register wrong retrieval, correct retrieval, false retrieval, abstention, provenance,
      examined-record, latency, and storage margins in append-only `PREDICTIONS-MEMORY.md`.

Gate: the fixture and each metric can fail for its claimed reason; no outcome label is available
to the retrieval policy except through an explicit stored record.

## CP-C1 · Smallest deterministic reliability gate

- [x] Reuse existing lifecycle, provenance, owner/frame, and contradiction records before adding
      a new record type or scorer.
- [x] Compare the three frozen arms on development, then run held-out evaluation once.
- [x] Return the selected record, relevant evidence, contradiction set, reliability reason, and
      explicit abstention reason.
- [x] Reject the gate if wrong retrieval falls only because answerable queries become abstentions
      beyond the registered margin.

Gate: outcome/provenance gating beats both controls on every conjunctive margin or is rejected.

## CP-C2 · Replication and v0.3 decision

- [x] Replicate across at least three deterministic seeds, swapped owner/frame labels, reversed
      confidence ordering, stale/corrected outcomes, and missing-outcome controls.
- [x] Keep relevance quality separate from reliability quality; do not collapse them into one
      score.
- [x] Record valid negative, mixed, and invalid runs and keep the v0.1/v0.2 regression gate green.
- [x] Update the prediction ledger, immutable reports, decisions, README, and roadmap before any
      v0.3 tag.

Gate: retain only a reliability rule whose direction replicates without weakening provenance,
frame isolation, lifecycle history, or abstention accounting.

## CP-C3 · v0.3 release gate

- [ ] Confirm every CP-C0–C2 valid, mixed, negative, or invalid run has an immutable report and
      machine-readable result where applicable.
- [ ] Update `CITATION.cff` to v0.3 and state explicitly that the retained scorer remains a
      benchmark policy outside the core API.
- [ ] Reproduce the complete gate and `git diff --check` from a clean checkout.
- [ ] Tag and publish v0.3 only when the public commit matches the verified checkout.

Gate: v0.3 publishes the narrow replicated result without claiming that provenance or linked
evidence is inherently correct.

## v0.3 exclusions until evidence changes them

- No RAG or generated answer synthesis.
- No vector database, new embedding model, or semantic fine-tuning.
- No rule that treats confidence, agreement, similarity, source labels, or recency as correctness.
- No shared-memory consolidation change before private retrieval reliability is measured.

---

# v0.4 roadmap — Who verifies the verifier?

CP-C2 trusted explicit active evidence links. The next failure surface is whether those links are
authentic, independent, current, and non-circular. Authentication can establish authorship; it
cannot establish correctness.

## Proposed claim

- **H-E1:** Compared with naive link counting and authentication alone, a deterministic gate that
  requires authenticated, active, independently evidenced support reduces wrong consolidation
  under forged, replayed, duplicated, correlated, cyclic, and authorized-but-false evidence
  without unacceptable answer loss.

H-E1 remains a proposal until CP-E0 appends exact fixtures, threat assumptions, margins, controls,
and falsification conditions to `PREDICTIONS-MEMORY.md`.

## CP-E0 · Freeze the evidence-trust experiment

- [ ] Define the trust boundary: member keys authenticate authorship only; expected outcomes remain
      scoring labels and never enter the policy.
- [ ] Freeze cases for forged signatures, replayed claim IDs, duplicated evidence, correlated
      authors, dangling links, cycles, superseded evidence, independent correct evidence,
      authorized false evidence, and explicit abstention.
- [ ] Compare naive link count, authenticated-link count, and authenticated independent-evidence
      gating on identical visible claims and candidate boundaries.
- [ ] Pre-register correctness, wrong/false consolidation, answer loss, abstention, forgery/replay
      rejection, provenance, examined cost, latency, and storage separately.

Gate: each attack and metric has one smallest perturbation that fails for its intended reason.

## CP-E1 · Harden the evidence harness

- [ ] Reuse `SignedClaim`, `ClaimExchange`, lifecycle records, and existing conservative
      consolidation before adding a trust type or dependency.
- [ ] Prove signature validation rejects forgery and duplicate claim IDs reject replay, while an
      authenticated false member remains admissible to the harness.
- [ ] Prove duplicate/correlated support cannot masquerade as independent evidence and cycles or
      dangling links cannot validate themselves.
- [ ] Freeze development selection before one held-out run; retain every negative or invalid run.

Gate: the harness distinguishes authenticity, independence, relevance, confidence, agreement, and
correctness rather than treating any pair as synonyms.

## CP-E2 · Smallest independent-evidence gate

- [ ] Implement only the minimum deterministic rule that survives CP-E1; keep candidate generation
      and evidence validation separate.
- [ ] Return the selected claim, evidence chain, rejected links and reasons, contradictions,
      silent members, and explicit abstention reason.
- [ ] Reject the rule if it reduces wrong consolidation by exceeding the registered correct-answer
      or abstention margin.
- [ ] Keep the core API unchanged unless held-out evidence independently justifies integration.

Gate: the candidate beats both frozen controls on every conjunctive held-out margin or is rejected.

## CP-E3 · Replication and v0.4 decision

- [ ] Replicate across at least three seeds, owner/frame renaming, signer-order permutations,
      reversed confidence, and different correlated-group sizes.
- [ ] Keep attack rejection, retrieval quality, consolidation quality, and cost as separate tables.
- [ ] Record all runs and verify every v0.1–v0.3 regression gate from a clean checkout.
- [ ] Update predictions, immutable reports, decisions, README, roadmap, citation, and release notes
      before any v0.4 tag.

Gate: retain only a rule whose direction replicates without erasing minority evidence,
contradictions, abstentions, provenance, lifecycle history, or private-frame isolation.

## v0.4 exclusions until evidence changes them

- No claim that a valid signature, trusted member, source label, majority, or evidence count is
  proof of correctness.
- No public-key infrastructure, decentralized identity system, trust graph, or external service.
- No learned trust score, language-model judge, RAG synthesis, or vector database.
- No shared-memory default change before the independent-evidence gate replicates.
