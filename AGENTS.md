# AGENTS.md — PolyBrains-AI-Memory

## Purpose

- Research explicit external memory beyond model parameters using PolyBrains' multi-frame lineage.
- Build agent memory that preserves provenance, disagreement, abstention, and independent reference
  frames across episodic, semantic, long-term, and shared memory.
- Test the claim that agreement, confidence, and correctness are distinct before consolidating
  private memories into shared knowledge.

## Ownership

- Nadi is creator and maintainer; Codex (OpenAI) is AI coding collaborator and co-author.
- This is an independent project copied from PolyBrains at commit `fb8071d`.
- Claude may continue working in the source PolyBrains checkout; changes never flow between the
  two trees automatically.

## Local Contracts

- `ORIGIN-STATE.md`, `ORIGIN-TODO.md`, existing reports, predictions, and decisions preserve the
  imported research record. Do not rewrite historical evidence to fit the new memory direction.
- New memory hypotheses require pre-registration in append-only `PREDICTIONS-MEMORY.md`, following
  the discipline of the historical `PREDICTIONS.md` without editing it.
- Private module memories remain independently inspectable; shared memory must retain source,
  time, confidence, contradictions, and abstentions.
- Consensus is not validation. No consolidation rule may equate agreement or confidence with
  correctness without a measured control.
- Harnesses and analyses must be able to fail for the reason they claim to test.
- The ignored `upstream/tbp.monty` checkout is reproducible from the pinned SHA recorded in the
  imported documents; do not edit upstream or commit its virtual environment.

## Work Guidance

- Keep the memory core independent of Monty, model providers, agent frameworks, vector databases,
  credentials, and network services.
- Begin with a falsifiable memory proposal and the smallest experiment that separates private
  retrieval, claim exchange, and shared consolidation.
- Reuse the thin `src/polybrains/` layer where it genuinely fits; do not preserve inherited code
  merely because it was copied.
- Prefer explicit records and deterministic transforms over opaque memory frameworks.

## Verification

- The inherited gate is `bash tools/run_gates.sh`; update it when the first memory-specific check
  is added.
- Record measured results and invalid runs with their controls; never convert an inherited result
  into evidence for a new hypothesis without a valid comparison.

## Child DOX Index

- `src/polybrains/` — inherited thin integration and future memory mechanisms.
- `configs/` — experiment configuration.
- `tests/` — gates and probes.
- `reports/` — immutable imported evidence and future experiment reports.
- `docs/` — plans and research diagrams.
