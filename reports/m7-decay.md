# M7 — deterministic decay versus no decay

**Run:** 2026-08-25  
**Pre-registration:** `PREDICTIONS-MEMORY.md` M7  
**Command:** `bash tools/run_gates.sh`

| arm | correct recall | stale false recall | answer rate | fresh useful recall |
|---|---:|---:|---:|---:|
| no decay | 2/4 | 2/4 | 4/4 | 2/2 |
| cutoff decay | 2/4 | 0/4 | 2/4 | 2/2 |

The explicit five-day cutoff archived exactly two older episodes. Their original evidence remained
inspectable and both archive markers retained the same decay explanation. A record exactly on the
cutoff remained active, confirming strict-before boundary behavior.

Decay is retained because it reduced the pre-registered stale-error outcome without reducing fresh
useful recall. Its cost is a two-answer drop through explicit abstention. This is a deterministic
retention-policy result, not evidence of cognitive validity; rehearsal, associative recall, and
working-memory limits remain unimplemented because no measured failure currently requires them.
