# CP-5 — Corrected results

**Date:** 2026-08-18 · **Sha:** `0c81b1f`
**Supersedes the numbers in `cp5-results.md`.** That file's accuracy figures were computed
wrongly; this one explains the error and gives corrected values.

---

## 0. A methodological error I made, found before publishing

`eval_stats.csv` has **one row per learning module per episode**. I counted rows.

For a 5-LM run of 10 episodes that yields 50 rows, which I reported as "50 episodes". The
error did two things:

1. **Inflated the apparent sample size 5x** for multi-LM arms, and not at all for the 1-LM
   arm — so any 1-LM vs 5-LM comparison would have been indefensible.
2. **Conflated "how many modules were right" with "was the system right".**

Corrected by `tools/episode_accuracy.py`, which groups rows by module and takes one verdict
per episode using the configured match criterion (`AnyLMsMatch`: correct if any module
reached a correct terminal state).

**Every number below is per-episode. n = 10 episodes per run, 5 seeds per arm.**

---

## 1. The corrected table

| arm | in-domain | OOD | drop |
|---|---|---|---|
| **5 LMs, `max` (upstream rule)** | 100.0% | 96.0% | **−4.0 pp** |
| 5 LMs, `mean` | — | 96.0% | — |
| 5 LMs, `consensus` | — | 96.0% | — |
| **1 LM (no voting at all)** | 72.0% | 64.0% | **−8.0 pp** |

Seed-level OOD: 5-LM `[90, 100, 100, 90, 100]` (sd 5.48) · 1-LM `[60, 60, 50, 80, 70]` (sd 11.40).

## 2. The vote rule: no effect, and now exactly zero

Under the corrected counting, **`max`, `mean` and `consensus` all score 96.0%**, identical on
every seed. The earlier −0.80 pp difference was an artefact of row-counting.

This strengthens the CP-5 finding rather than weakening it: at Monty's default
`vote_evidence_threshold` of 0.8, **the aggregation rule does not measurably matter on this
task.** H2 remains untested — not because the mechanism is absent, but because this task never
produces the disagreement H2 is about.

## 3. H1: directionally supported, but NOT established

H1 predicts multi-frame beats single-frame out of distribution, and the corrected numbers are
consistent with it:

- 5-LM drops **4.0 pp** in-domain → OOD
- 1-LM drops **8.0 pp**
- difference **+4.0 pp in H1's favour**

**Why I am not claiming this as support:**

1. **The capacity confound is unresolved.** The 1-LM arm is worse *in-domain too* (72% vs
   100%). It is a different model — different sensor module, different pretraining run — not
   the 5-LM system with voting switched off. **The comparison is 5-LM-system vs
   1-LM-system, which is not the same as testing the effect of voting.**
2. **A ceiling artefact inflates the drop comparison.** A model at 100% can only fall; a model
   at 72% has room in both directions. The "drop" metric is not neutral between them.
3. **+4.0 pp sits inside the noise.** The 1-LM arm's seed-to-seed sd is 11.40 pp. The effect
   is roughly one third of the noise on the weaker arm.
4. **n = 10 episodes per run.** Each episode is worth 10 pp, so nothing finer than 10 pp can
   be resolved within a single run.

**Verdict: H1 is directionally consistent and formally underpowered.** The clean test is a
5-LM system with voting disabled versus the same system with voting on — same model, same
training, one variable. That is not what was run.

## 4. What the exploratory threshold finding looks like now

The `vote_evidence_threshold` sweep in `cp5-results.md` used the same faulty counting. Its
direction (lower threshold → better OOD) came from both rules and both seeds, so it is
probably real, but **the magnitudes in that file are not trustworthy** and it needs re-running
with `tools/episode_accuracy.py`. Registered as P1 in `PREDICTIONS.md`.

## 5. Status

| | Verdict |
|---|---|
| **H1** | Directionally consistent (+4.0 pp), **underpowered and confounded by capacity** |
| **H2** | **Untested.** The vote rule makes zero difference on this task, so there is nothing to weight. |

## 6. The design problem this exposes

The deeper issue is not statistical power. **The five sensor patches view the same object from
nearly the same pose, so they rarely disagree.** H1 and H2 are both claims about
*disagreeing* modules, and this task barely produces disagreement — which is exactly why the
D-index is ~0.04 and why all three rules coincide.

More seeds will not fix that. The next round needs a task where modules genuinely diverge:
widely separated sensor positions, conflicting modalities, or deliberately corrupted input to
a subset of modules.

## Reproduce

```bash
python3 ~/PolyBrains/tools/episode_accuracy.py \
  ~/tbp/results/monty/projects/monty_runs/cp5_e1_ood_max_s4*
```
