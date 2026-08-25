# M3 — popular false episode consolidation

**Run:** 2026-08-25  
**Pre-registration:** `PREDICTIONS-MEMORY.md` M3  
**Command:** `bash tools/run_gates.sh`

| policy | semantic records | false consolidations | retained evidence IDs |
|---|---:|---:|---:|
| none | 0 | 0 | episodes remain unchanged |
| agreement/confidence | 1 | 1 | 4/4 |
| verified outcome | 1 | 0 | 4/4 |

Both consolidation arms compressed four episodes to one semantic record (25%). The naive record
kept the true minority episode as a contradiction; the outcome-gated record kept all three false
episodes as contradictions. In both cases, the complete input ID set is reconstructible from the
`supports` and `contradicts` links, while the original episode records remain unchanged.

The empty-outcome control abstained. This passes the CP-M3 fixture gate: repetition and confidence
alone cannot enter the outcome-gated semantic arm. It does not test shared-memory propagation or
claim that missing outcome evidence proves a claim false.
