# M8 — removable agent adapter equivalence

**Run:** 2026-08-25  
**Pre-registration:** `PREDICTIONS-MEMORY.md` M8  
**Command:** `bash tools/run_gates.sh`

The framework-neutral adapter converted explicit agent text and provenance into the existing core
record. Its record serialized byte-for-byte identically to direct `MemoryRecord` construction,
retrieved the same record ID, and matched the core's unmatched-query abstention. Empty observation
text was rejected at the adapter boundary.

The adapter is a separate leaf module: `memory.py` and the package initializer do not import or
export it. Removing that file therefore does not alter record, lifecycle, retrieval,
consolidation, or shared-memory semantics, which remain covered by the M1–M7 gates.

No framework, model-provider, vector-database, network, or Monty dependency was added. No
PolyBrains/Monty adapter or compatibility claim was made because the standalone benchmarks expose
no unanswered question requiring one. The inherited PolyBrains checks remain required before any
future compatibility claim.
