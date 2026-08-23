# P4 — The clean H1 test: voting made it worse

**Date:** 2026-08-18 · **Sha:** `0c81b1f` · Pre-registered as **P4** in `PREDICTIONS.md`
before the run, after the CP-5 correction exposed that the 1-LM comparison was confounded.

**Result: H1 is not supported. On this task, voting is worse than not voting.**

---

## The design

Everything identical except one variable. Same pretrained 5-LM model, same objects, same OOD
rotations, same seeds. The only difference is `lm_to_lm_vote_matrix: null`, which stops the
modules exchanging votes.

This is the test the earlier 1-LM arm could not perform: that comparison changed model,
sensor module, capacity and training all at once.

## The result

| arm | in-domain | OOD | drop |
|---|---|---|---|
| voting **ON** (upstream default) | 100.0% | **96.0%** | −4.0 pp |
| voting **OFF** | 100.0% | **100.0%** | 0.0 pp |

Per-seed OOD: ON `[90, 100, 100, 90, 100]` (sd 5.48) · OFF `[100, 100, 100, 100, 100]` (sd 0.00).

**Voting cost 4.0 pp.** H1 predicted voting would help out of distribution. It did the
opposite, consistently: the no-vote arm was perfect on every seed.

## Why — the mechanism, not just the number

Per-episode, per-module verdicts on seed 42, OOD:

**voting ON**
```
 ep  LM0 LM1 LM2 LM3 LM4   target
  5   ok  ok  ok  ok  XX   mustard_bottle
  6   XX  XX  XX  XX  XX   dice            <- ALL FIVE FAIL TOGETHER
```

**voting OFF**
```
 ep  LM0 LM1 LM2 LM3 LM4   target
  5   ok  ok  ok  XX  ok   mustard_bottle
  6   ok  ok  ok  ok  ok   dice            <- ALL FIVE CORRECT
  8   ok  XX  ok  XX  ok   c_lego_duplo
```

On `dice`, every module succeeds independently but **all five fail once they talk to each
other.** One module's wrong hypothesis propagated through the vote and became unanimous.

Across all 50 episodes per arm:

| | episodes where any module failed | where **all** failed | correlation |
|---|---|---|---|
| voting ON | 7 | **2** | **29%** |
| voting OFF | 8 | **0** | **0%** |

**Voting does not reduce the number of module failures (7 vs 8). It makes the failures
correlated.** Since the match criterion is `AnyLMsMatch`, independent failures are recoverable
and correlated ones are fatal.

## Why this is exactly the H2 failure mode, arriving through H1's door

CP-1 established that Monty's aggregation is `np.ma.max`: the loudest single vote in the
neighbourhood wins outright, and mutual agreement between quieter modules contributes nothing.

That is precisely a mechanism for turning one confident error into a consensus. **The
correlated-failure result is what winner-take-all aggregation predicts.** H2 said
confidence-weighted aggregation would destroy the multi-frame advantage; here it appears to
have destroyed it so thoroughly that the advantage is negative.

**But we cannot yet claim H2 as supported**, because §"Limits" below applies.

## Limits — why this is a finding and not a conclusion

1. **n = 10 episodes per run, 5 seeds.** Each episode is 10 pp. The 4.0 pp gap rests on 2
   correlated failures across 50 episodes.
2. **The no-vote arm is at ceiling (100%, sd 0.00).** It cannot demonstrate an advantage, only
   an absence of harm. A harder task is needed to see whether voting ever helps.
3. **The task barely produces disagreement.** Five patches view the same object from nearly
   the same pose; D-index ≈ 0.04. This is a poor testbed for any claim about disagreeing
   modules, and it is why the three vote rules are indistinguishable.
4. **Single object per episode.** Voting exists in Monty largely to bind evidence across
   sensors on ambiguous or multi-object scenes. This task may simply not be one where voting
   earns its cost.

**The honest reading: on a task with near-unanimous modules and a single unambiguous object,
Monty's voting adds correlated failure without adding accuracy.** That is a narrow claim about
a specific regime, not a verdict on voting.

## What it means for the project

- **H1 is not supported by the clean test.** Recorded as such.
- **The correlated-failure mechanism is a genuine, reportable finding** and it is independent
  of whether H1 or H2 hold. It also gives the consensus rule a real target: a rule that
  resists capture should reduce failure correlation, which is now a measurable quantity.
- **The next round should measure failure correlation directly**, not just accuracy. That is
  the variable the theory is actually about.

## Reproduce

```bash
cd ~/PolyBrains/upstream/tbp.monty
PYTHONPATH=~/PolyBrains/src .venv/bin/python run.py -cd ~/PolyBrains/configs \
  -cn experiment 'experiment=e1_ood_novote' '++experiment.config.seed=42' \
  '++experiment.config.logging.wandb_id=p4'
python3 ~/PolyBrains/tools/episode_accuracy.py \
  ~/tbp/results/monty/projects/monty_runs/p4_novote_s4*
```
