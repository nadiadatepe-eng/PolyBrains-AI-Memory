# CP-R1 — hardened v0.1 benchmark harness

**Run:** 2026-08-25  
**Command:** `PYTHONPATH=src python3 tools/measure_m2_recall.py --json`

The unchanged v0.1 ranker reproduced 200/200 correct unique-cue retrievals, 40/40 false
retrievals on explicitly unanswerable lexical collisions, 240/240 complete provenance records,
and a 120-to-1,200 examined-record scale control. Removing one expected record changed the result
to 199 correct retrievals and one missed answer.

Each query now carries an independent expected record ID or `null`. The scorer separates correct,
wrong, false, abstained, and missed outcomes. Perturbations swap an expected ID, remove an expected
record, force an abstention, corrupt a payload hash, add an irrelevant record, add serialized and
payload storage, and inject a latency penalty. Every affected metric changes in the registered
direction or the harness fails.

The deterministic result is `reports/cp-r1-v01-result.json`. Wall-clock latency remains human-run
diagnostic output and is excluded from that byte-stable artifact. No v0.2 retrieval policy or
held-out fixture was evaluated in CP-R1.
