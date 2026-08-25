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
