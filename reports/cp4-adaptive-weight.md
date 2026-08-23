# CP-4 — Adaptive vote weight

**Date:** 2026-08-18 · **Gate: MET.** 77 PolyBrains tests pass (15 new).
Run log: `reports/cp4-weight-log.txt`

## The gap being closed

CP-1 confirmed that `vote_weight` is assigned once at `learning_module.py:285` and never
updated anywhere in the class. No mechanism exists by which a module repeatedly wrong outside
its training distribution becomes quieter, nor by which one reliably right on novel input
becomes louder.

## What was built

`src/polybrains/weights.py` — `AdaptiveVoteWeight`. The weight tracks an EMA of whether the
module's vote agreed with the outcome, evaluated **only on out-of-domain episodes**.

## Two invariants, from the polymath specification

These are not implementation details; they are the specification expressed as code, and both
are enforced by tests.

**1. A module is never silenced.** `W_MIN = 0.1`, a hard positive floor. "Become a beginner
without losing intellectual confidence" requires that a module which has been wrong can still
be heard.

**2. Recovery from the floor must be possible.** A one-way ratchet would encode exactly the
entrenchment the project sets out to study. Measured: a module at the floor recovers past its
starting weight given sustained evidence, but a single success does not restore it.

## The H2 clause, enforced in the mechanism

`update(was_correct=True, out_of_domain=False)` changes nothing. **In-domain confidence buys
no influence.** This is H2 written into the weight rule rather than left to the experiment:
the failure mode where a module confident on familiar input captures the consensus cannot
arise through this channel.

## Measured (seed 20260818, 200 episodes)

| Module | final w | score |
|---|---|---|
| reliable OOD (90% right) | **1.9992** | 1.000 |
| mediocre (50% right) | 1.0255 | 0.513 |
| unreliable (20% right) | **0.1946** | 0.053 |
| frozen ablation (90% right) | **1.0000** | 0.500 |

Recovery:

| | w |
|---|---|
| after 200 failures | 0.1000 (floor, never 0) |
| after 1 success | 0.2800 (not instant) |
| after 200 successes | 2.0000 (recovered past start) |

In-domain: 100 successes leave w unchanged at 1.0000.

## Frozen before any accuracy comparison

`W_MIN = 0.1`, `W_MAX = 2.0`, `EMA_ALPHA = 0.1`, guarded by `TestConstantsFrozen`.

## Not claimed

No accuracy claim. CP-4's gate is only that w(t) moves in the right direction on a toy task
with a known-unreliable module, that the invariants hold, and that `frozen=True` reproduces
upstream's constant exactly. Whether adaptive weighting helps is CP-5's question.

## Still blocking CP-5

- MuJoCo object placement (CP-0 finding) still limits training to one rotation, so no real
  baseline exists yet.
- Hydra configs to select `vote_mode` and weight mode per arm are not written.
- `AdaptiveVoteWeight` is not yet wired into `ConsensusEvidenceGraphLM`; it needs an
  episode-outcome hook, which is CP-5 work.

## Reproduce

```bash
cd ~/PolyBrains/upstream/tbp.monty
PYTHONPATH=~/PolyBrains/src .venv/bin/python -m pytest ~/PolyBrains/tests/test_weights.py -q
```
