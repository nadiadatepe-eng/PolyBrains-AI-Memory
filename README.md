# PolyBrains-AI-Memory

Research into explicit external memory for intelligent and multi-agent systems, built from the
PolyBrains multi-frame research lineage.

The central design constraint is that agreement, confidence, and correctness are different
signals. Each module may retain private episodic and semantic memory in its own reference frame;
retrieval and claim exchange must preserve provenance, contradictions, minority evidence, and
abstentions before anything is consolidated into shared long-term memory.

## Initial research areas

- short-term, episodic, semantic, and long-term memory;
- frame-aware retrieval and RAG-style access;
- writing, updating, forgetting, compression, and consolidation;
- private agent memory and governed shared multi-agent memory;
- cognitive inspiration tested as falsifiable mechanisms rather than metaphor.

The complete committed PolyBrains record was imported at source commit `fb8071d`. Historical
state is preserved in `ORIGIN-STATE.md`, `DECISIONS.md`, `PREDICTIONS.md`, and `reports/`.
The original `[source PolyBrains checkout]` project remains separate.

The active roadmap is `TODO.md`; the complete inherited checkpoint ledger is retained unchanged
in `ORIGIN-TODO.md`. The first implementation target is a deterministic, model-independent memory
record and private episodic store. Monty and agent-framework integrations are adapters, not core
dependencies.
