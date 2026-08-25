# M6 — signed shared claims under a correlated prior

**Run:** 2026-08-25  
**Pre-registration:** `PREDICTIONS-MEMORY.md` M6  
**Command:** `bash tools/run_gates.sh`

| policy | false shared records | contamination radius | useful true recall |
|---|---:|---:|---:|
| pooled writes | 1 | 6 | 1 |
| majority | 1 | 6 | 0 |
| highest confidence | 1 | 6 | 0 |
| conservative, before outcome | 0 | 0 | 0 |
| conservative, after outcome | 0 | 0 | 1 |

Three distinct claims shared the same `correlated-prior` provenance and false payload. Their
agreement did not count as independent validation. Conservative consolidation abstained until the
true claim's evidence ID was outcome-verified, then recovered useful recall from 0 to 1. Every
emitted shared record retained supporting and contradicting claim IDs.

The exchange separately retained three-way agreement, the true contradiction, confidence values,
one signed abstention, and one silent member. A member's private claim was visible only to its
author; shared claims were visible to members; a public claim was visible to an outsider. Payload
tampering invalidated the signature, and no policy mutated or overwrote the exchanged claims.

Authentication uses deterministic standard-library HMAC as a local baseline. It is not public-key
identity or protection against a member whose shared secret is compromised.
