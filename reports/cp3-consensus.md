# CP-3 — Consensus rule and dissent signal

**Date:** 2026-08-18 · **Sha:** upstream pinned at `0c81b1f`
**Gate: MET.** 62 PolyBrains tests pass; upstream unchanged at 590 passed / 1 benign failure.

## What was built

| File | Role |
|---|---|
| `src/polybrains/consensus.py` | `reduce_votes()`, `dissent_index()`, `capture_rate()` |
| `src/polybrains/learning_module.py` | `ConsensusEvidenceGraphLM`, one overridden method |
| `tests/test_vote_path.py` | 10 characterization tests — the HabitatSim safety net |
| `tests/test_consensus.py` | 27 tests incl. the bit-identical gate |
| `tests/test_lm_equivalence.py` | 25 tests driving the real method on both classes |

Upstream was not edited. `ConsensusEvidenceGraphLM` subclasses `EvidenceGraphLM` and
overrides exactly one method, `_update_evidence_with_vote`, transcribed from
`learning_module.py:902-963` with two changes: the reduction at line 938, and dissent
recording.

## The gate, in three parts

**1. Behaviour-preserving.** `vote_mode="max"` must be bit-identical to upstream.
Verified twice: on the reduction in isolation (12 mask/k combinations), and by driving the
real `_update_evidence_with_vote` on both classes with identical inputs across 20 seed/vote
combinations, comparing final hypothesis evidence with `np.array_equal`. **Passes.**

This is what makes the later comparison honest: the baseline arm runs the same code as the
experimental arms, so any accuracy difference is attributable to the rule.

**2. Instrumentation correct.** Capture rate is 1.0 under `max`, by construction — measured
both synthetically and in situ. **Passes.**

**3. The knob does something.** `consensus` mode provably changes the evidence, or the
experiment would be vacuous. **Passes.**

## The three modes

| Mode | Rule |
|---|---|
| `max` | upstream: `np.ma.max` over the neighbourhood |
| `mean` | plain average — a naive control separating "any change" from "this change" |
| `consensus` | agreement-weighted mean: each vote weighted by `exp(-|v_i - v_l| / tau)` averaged over its neighbours |

Worked example, the two cases the stock rule cannot distinguish:

| Neighbourhood | `max` | `consensus` | D-index |
|---|---|---|---|
| 0.95 / 0.42 / 0.40 (one loud voice) | **0.95** | **0.527** | 0.255 |
| 0.90 / 0.88 / 0.89 (genuine agreement) | 0.90 | 0.890 | 0.008 |

Capture rate: **1.0** under `max`, **0.0** under `consensus` on the contested case. A lone
confident module no longer sets the answer; a mutually agreeing group is preserved intact.

## Frozen before any accuracy was looked at

- `CONSENSUS_TAU = 0.15`, guarded by `test_tau_is_frozen`.
- D-index = population std of the unmasked neighbourhood, clipped to [0,1]; a single vote
  scores 0 because it cannot disagree with anything.

Both definitions were fixed before running any experiment. A dispersion measure tuned after
seeing results is a free parameter, not a finding.

## Not yet done

- No accuracy claim. CP-3 deliberately makes none.
- Hydra configs to select `vote_mode` per arm — needed for CP-5.
- MuJoCo object placement still limits training to one rotation (CP-0 finding), so a real
  baseline is still blocked.

## Reproduce

```bash
cd ~/PolyBrains/upstream/tbp.monty
PYTHONPATH=~/PolyBrains/src .venv/bin/python -m pytest ~/PolyBrains/tests/ -q
```
