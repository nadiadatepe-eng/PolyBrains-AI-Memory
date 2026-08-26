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

The complete PolyBrains record remains recoverable at source commit `fb8071d`. Its historical
state and measured evidence are preserved in `ORIGIN-STATE.md`, `ORIGIN-TODO.md`,
`PREDICTIONS.md`, `DECISIONS.md`, and `reports/`; inherited executable machinery is not part of
the active memory project. The original PolyBrains project remains separate.

The active roadmap is `TODO.md`; the complete inherited checkpoint ledger is retained unchanged
in `ORIGIN-TODO.md`. The first implementation target is a deterministic, model-independent memory
record and private episodic store in `src/polybrains/memory.py`. The core and its gate use only the
Python standard library. Monty and agent-framework integrations are adapters, not core dependencies.

## v0.2 retrieval result

The exact lexical v0.1 baseline remains the standard-library core policy. A calibrated lexical
threshold reduced false retrieval on the held-out fixture but failed three-seed replication and was
rejected. An optional pinned MiniLM benchmark recovered all three replication paraphrases within
the pre-registered quality and cost margins; it remains candidate generation outside the core and
adds no runtime dependency. See `reports/cp-r5-v02-release.md` for the release evidence and known
limitations.

## Acknowledgements and attribution

This independent project builds on ideas developed by others; their theories and software remain
their work. In particular:

- Jeff Hawkins and collaborators developed Thousand Brains Theory and the reference-frame account
  of cortical intelligence.
- Viviane Clay, Niels Leadholm, Jeff Hawkins, and the Thousand Brains Project developed the Monty
  research platform and its published thousand-brains system.
- Dedre Gentner developed structure-mapping theory; Gentner and Arthur Markman developed its
  comparison with similarity.
- The optional semantic benchmark uses Sentence Transformers and the
  `sentence-transformers/all-MiniLM-L6-v2` model created by its respective authors and maintainers.

The source record and publication links are listed in `reports/sources/README.md` and the relevant
experiment reports. PolyBrains-AI-Memory claims only its own hypotheses, implementations,
measurements, and interpretations; it is not affiliated with or endorsed by those authors or
organizations.
