# CP-R5 — v0.2 release gate

**Run:** 2026-08-26

All unconditional CP-R1–R3 controls passed from a clean checkout. The gate reproduced the frozen
v0.1 result, ran the frozen held-out lexical comparison and three-seed replication, and preserved
the memory, provenance, lifecycle, frame-isolation, consolidation, and adapter checks. The worktree
also passed `git diff --check`.

The minimum-3/4 lexical candidate is rejected: it improved held-out false retrieval from 1/2 to
0/2, but seed 23 lost one correct answer and seed 37 retained the false retrieval. The exact
lexical v0.1 policy remains the standard-library core default.

CP-R4 independently justified retaining the pinned MiniLM semantic path as an optional benchmark.
It recovered 3/3 replication paraphrases and passed every registered quality, reproducibility,
and cost margin. It remains candidate generation in `tools/measure_r4_semantic.py`; no semantic
package, vector database, model provider, network service, or generated answer entered the core or
mandatory gate. The agent adapter remains isolated in `src/polybrains/agent_adapter.py` and absent
from the package exports.

Known failures and exclusions remain explicit: the lexical candidate failed replication, semantic
retrieval still returned the high-confidence contradictory prior, and the first default semantic
resolver was stopped after selecting more than 1.95 GB of compressed GPU/CUDA wheels. No language
model synthesis, held-out retuning, new consolidation rule, cognitive mechanism, or Monty coupling
is included in v0.2.

Evidence: `reports/cp-r1-benchmark-harness.md`, `reports/cp-r2-heldout.md`,
`reports/cp-r3-replication.md`, and `reports/cp-r4-semantic.md`.
