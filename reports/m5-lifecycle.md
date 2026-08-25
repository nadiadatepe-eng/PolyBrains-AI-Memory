# M5 — explicit lifecycle and privacy deletion

**Run:** 2026-08-25  
**Pre-registration:** `PREDICTIONS-MEMORY.md` M5  
**Command:** `bash tools/run_gates.sh`

| state/action | payload retained | retrievable | audit evidence |
|---|---:|---:|---|
| superseded stale fact | yes | no | original record + correction link |
| archived by decay | yes | no | archive marker + reason |
| forgotten | no in marker; historical source retained | no | forgotten marker + reason |
| physically deleted | no | no | payload-free tombstone + reason |

The correction was retrieved before decay and retrieval abstained afterward. Physical deletion
removed the complete 18-byte `privacy secret-731` payload from the store, reducing stored payload
bytes by 18 while retaining tombstone metadata. A missing reason and a second transition from an
already superseded record were both rejected.

The compression control linked its semantic record to both surviving episode IDs. These controls
cover deterministic lifecycle mechanics; they do not choose retention durations or schedule
automatic decay.
