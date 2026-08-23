# CP-5 — First results, and what they refute

> **SUPERSEDED 2026-08-18.** The accuracy figures in this file counted CSV rows,
> which are per-learning-module, not per-episode. That inflated multi-LM sample
> sizes 5x. Corrected numbers and the explanation: `reports/cp5-corrected.md`.
> The qualitative conclusions (underpowered, threshold effect direction) survive;
> the magnitudes do not. Kept unedited as the record.


**Date:** 2026-08-18 · **Sha:** `0c81b1f` · Raw: `reports/cp5-results.tsv`, `reports/e2-threshold.tsv`
Pre-registration: `PREDICTIONS.md`, committed `166fbb7`, before any of these numbers existed.

**Summary: H1 and H2 are both UNDERPOWERED at this scale. One prediction of mine was
refuted. One unregistered effect appeared that is larger than anything we set out to test.**

---

## 1. E0 — replication. **Prediction met.**

| | |
|---|---|
| Predicted | >60% in-domain (CP-0's single-rotation figure) |
| Measured | **100.0%** (50/50), identical on all 5 seeds |

The 5-rotation model is properly trained. CP-0's 60% was an undertrained artefact exactly as
recorded, not a property of the system.

**But this creates a problem the plan did not anticipate: the baseline is at ceiling.** Its
seed-to-seed stdev is 0.00 pp, which is useless as a noise floor. The honest floor is the
OOD arms' own spread — see §3.

## 2. E1/E2 — the vote rule. **Underpowered, effect indistinguishable from noise.**

All arms share one pretrained model, so differences cannot come from training. Paired by
seed, since the same seed gives the same episode sequence.

| seed | max | mean | consensus |
|---|---|---|---|
| 42 | 88% | 86% | 86% |
| 43 | 98% | 98% | 98% |
| 44 | 98% | 96% | 96% |
| 45 | 88% | 88% | 88% |
| 46 | 98% | 98% | 98% |
| **mean** | **94.0%** | **93.2%** | **93.2%** |

**Noise floor: pooled OOD stdev = 5.26 pp.** (Baseline stdev is 0.00 because of the ceiling,
so it cannot be used.)

**consensus − max = −0.80 pp.** That is **one sixth of the noise floor**. There is no
detectable effect. Reported as underpowered, which `PREDICTIONS.md` explicitly permits.

**`mean` and `consensus` are byte-identical on all 5 seeds.** Not a plumbing bug — I checked
that `vote_mode` reaches all 5 learning modules in each arm. It is a real property of the
system, explained next.

## 3. Why the rule barely matters — and why my explanation was WRONG

### The hypothesis

Monty's `vote_evidence_threshold` defaults to **0.8** (`learning_module.py:242`). Only
high-confidence votes are ever emitted, so a vote neighbourhood is near-unanimous by
construction and a consensus rule has almost nothing to correct.

Synthetic support, votes drawn uniformly from [threshold, 1.0]:

| threshold | D-index | max | consensus | gap |
|---|---|---|---|---|
| **0.8 (default)** | **0.044** | 0.951 | 0.900 | 0.051 |
| 0.5 | 0.106 | 0.874 | 0.752 | 0.122 |
| 0.2 | 0.174 | 0.801 | 0.599 | 0.202 |
| 0.0 | 0.214 | 0.750 | 0.500 | 0.250 |

**Prediction from this: lowering the threshold should widen the consensus-vs-max gap.**

### The test refuted it

Paired, complete runs only:

| threshold | consensus − max | n seeds |
|---|---|---|
| 0.8 | −1.00 pp | 2 |
| 0.5 | +6.00 pp | 1 |
| 0.2 | 0.00 pp | 2 |
| 0.05 | +1.00 pp | 2 |

**No trend.** Every value sits inside the 5.26 pp noise floor. The synthetic model predicted
a growing gap on the real system and it did not appear.

Why the synthetic model misleads: it assumed votes are uniform over [threshold, 1]. Real
Monty votes are the *scaled* evidences of hypotheses that already survived matching, so they
cluster near the top regardless of where the threshold sits. Lowering the threshold admits
more votes but does not make them meaningfully more spread out.

**This is recorded as a refuted prediction, not quietly dropped.**

## 4. The unregistered finding: the threshold itself matters ~10x more than the rule

| threshold | OOD accuracy | mean runtime |
|---|---|---|
| 0.8 (default) | 87.50% | 51 s |
| 0.5 | 92.67% | 65 s |
| **0.2** | **97.00%** | 97 s |
| 0.05 | 96.50% | 96 s |

**+9.5 pp from 0.8 → 0.2**, versus ≤1 pp for any vote-rule change. This is nearly twice the
noise floor and consistent across both rules and both seeds.

**Caveats, stated because this is the most tempting result to overstate:**
- n = 4 runs per threshold, 2 seeds. Suggestive, not established.
- **Not pre-registered.** It was found while investigating the null, which makes it
  exploratory by definition. It requires its own pre-registered replication before any claim.
- It costs ~90% more runtime.
- 0.2 → 0.05 gives nothing back, so the effect saturates.

If it survives replication it is a plain, useful contribution: *Monty's default
`vote_evidence_threshold` of 0.8 is too conservative for out-of-distribution poses.* That is
an upstream-relevant finding independent of H1 and H2.

## 5. Data integrity: one run excluded

`th=0.5, consensus, seed 45` produced **30 episodes instead of 50** and is excluded from all
paired analyses. Cause: lower thresholds admit more votes, which costs more steps per episode,
and the run hit `max_total_steps: 6000`.

It is excluded because a 30-episode run is not comparable to a 50-episode one, and it is
recorded here because silently averaging it in would have skewed the 0.5 row — which is the
row that most flattered the consensus rule (+6.00 pp).

**Consequence for future runs:** `max_total_steps` must scale with the threshold, or all arms
must use a budget large enough for the slowest.

## 6. A structural constraint discovered

Thresholds below 0 cannot be tested. The CMP `Message` contract asserts
`Confidence must be in [0,1]`, and a negative threshold produces
`AssertionError: Confidence must be in [0,1] but is -0.39`. The synthetic sweep's −0.5 and
−1.0 rows are therefore **unreachable on the real system** and are theory only.

## 7. Status of the hypotheses

| | Verdict |
|---|---|
| **H1** (multi-frame OOD advantage scales with disagreement) | **Not yet tested.** Requires the 1-LM arm and the E3 clone control, neither run. |
| **H2** (confidence weighting destroys the advantage) | **Underpowered.** −0.80 pp against a 5.26 pp floor. No evidence either way. |

**Neither is supported and neither is refuted.** The honest statement is that this scale — 10
objects, 50 episodes, 5 seeds — cannot resolve a sub-1 pp effect. Detecting one would need
either far more episodes or a task where the rules can actually diverge.

## 8. What would make the next round decisive

1. **Get off the ceiling.** In-domain at 100% leaves no headroom. Harder objects, more
   objects, or noisier sensors.
2. **Construct genuine disagreement.** The 5 sensor patches see the same object from nearly
   the same pose, so they rarely disagree. H1 is about *disagreeing* modules and this setup
   barely produces any. This is the deepest problem with the current design.
3. **Run the missing arms:** 1-LM (E1 proper) and the clone control (E3), which CP-2 showed is
   the fork against Gentner.
4. **Replicate the threshold effect** with its own pre-registration.
5. **Raise `max_total_steps`** so low-threshold arms are not truncated.

## Reproduce

```bash
bash ~/PolyBrains/tools/run_cp5.sh           # 20 runs, ~21 min
bash ~/PolyBrains/tools/run_e2_threshold.sh  # 16 runs, ~20 min
```
