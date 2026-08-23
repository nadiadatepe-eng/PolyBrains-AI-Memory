# P11 — the parliament under `consensus`: opposition is active, not profitable, and the rule's role is unproven

**Run 2026-08-19. 1000 episodes, 5 arms x 5 shared seeds x 40 episodes. Pre-registered
at `5774fd1` before any number existed. Sweep certified by P11d.**

## The question

P10 found the parliamentary *structure* cuts confident errors while the devil's
advocate contributed nothing on errors (`parl-noopp` matched `parl-3`, t=0.34). The
registered cause was mechanical: `np.ma.max` takes the loudest vote, and an opposing module
argues its **runner-up**, which carries lower evidence by construction. Max has no
channel through which dissent can travel. P11 reruns the same parliament under
`vote_mode="consensus"` (agreement-weighted, frozen at CP-3), which does have one.

All five arms run consensus, including the plain baselines. Reusing P9's max arms
would have confounded the reduction rule with the structure.

## Results

| arm | `any` | unanimous | agree | unan precision | **confident errors** |
|---|---|---|---|---|---|
| plain-1 | 97.50% | 39.00% | 40.50% | 96.13% | 1.50% |
| plain-3 | 91.50% | 77.00% | 85.00% | 90.48% | **8.00%** |
| **parl-3** | **98.50%** | 36.50% | 37.50% | **97.29%** | **1.00%** |
| parl-noopp | 97.00% | 53.00% | 55.50% | 95.53% | 2.50% |
| parl-batch | 98.50% | 27.50% | 28.50% | 96.85% | 1.00% |

- **P11d REPLICATION CONTROL PASSED** — `plain-1` reproduces P7's powered consensus
  arm: 97.50% vs 97.80%, −0.30 pp against a ±4.40 pp noise band. Sweep certified.
- **P11a NOT SUPPORTED** — `parl-3` − `parl-noopp` on confident errors is −1.50 pp,
  t(4)=−1.50. Better than max's t=0.34 but short of the 2.776 bar.
- **P11b SUPPORTED** — `parl-3` has −7.00 pp fewer confident errors than `plain-3`,
  t(4)=−3.50. P10a replicates under the new rule.
- **P11c directionally right, n.s.** — +1.75 pp precision over `parl-noopp`, t=0.78.
- **P11e NOT SUPPORTED** — sequencing gives +9.00 pp agreement, t=2.45, under the bar.

## The finding P11a's headline hides — and the limit of that finding

**Opposition is not inert under consensus.** The contrast it was designed to move:

| `parl-3` − `parl-noopp` | consensus (P11) | max (P10) |
|---|---|---|
| **agreement** | **−18.00 pp, t=−3.06 SIG** | −14.00 pp, t=−2.24 n.s. |
| unanimity | −16.50 pp, t=−2.60 | −14.50 pp, t=−2.61 |
| confident errors | −1.50 pp, t=−1.50 | +0.50 pp, t=0.34 |
| `any` accuracy | +1.50 pp, t=0.88 | +0.00 pp, t=0.00 |

**The honest reading is weaker than "consensus unlocked the opposition".** Under max
the agreement effect was already −14.00 pp and missed the bar only narrowly; consensus
moves it to −18.00 pp and crosses it. Testing that difference directly — a
difference-in-differences on shared seeds, `(parl3−noopp | consensus) − (parl3−noopp |
max)` — gives **−4.00 pp, t(4)=−0.60, n.s.**, with per-seed values ranging
−27.5 to +12.5.

**So this experiment cannot establish that the reduction rule is what freed the
opposition.** What it establishes is narrower and still worth having:

1. Under consensus the opposition **is** measurably active on agreement (t=−3.06),
   which is a positive result about the mechanism, not an inference from a null.
2. It is **not** measurably profitable: the friction buys 1.5 pp of confident errors
   (t=−1.50) and 1.5 pp of `any` (t=0.88).
3. Whether max would do the same given more seeds is **open**. P10's registered
   mechanism claim is *consistent* with these numbers and is **not confirmed by
   them**.

Opposition is **audible but not profitable** on this task; the claim that it became
audible *because of the rule* is not supported at n=5.

## Why: the errors are already gone

`parl-3` sits at 1.00% confident errors and 98.50% `any`. `plain-1` — one plain
exchange, no parliament at all — sits at 1.50% and 97.50%. **There is almost nothing
left for opposition to prevent.** The 8.00% error rate that P10 measured is a wound
that *plain iteration* inflicts (3 rounds take agreement to 85% and errors to 8%);
the parliamentary structure's contribution is to not inflict it. Opposition is then
asked to improve on a 1% error floor with 5 seeds x 40 episodes, which cannot
resolve differences below roughly 2 pp.

**This is a power limitation, not a demonstration of no effect.** A test capable of
resolving 1.5 pp at this floor needs several times the episodes.

## The rule barely matters, again

Holding the structure fixed and changing only the reduction rule:

| arm | consensus − max, confident errors | `any` |
|---|---|---|
| parl-3 | −1.50 pp (t=−1.50) | +2.00 pp (t=1.63) |
| parl-noopp | +0.50 pp (t=0.34) | +0.50 pp (t=1.00) |

Nothing significant. This is now the **third** experiment to land there: P8 found all
three vote rules within 1.6 pp under every criterion, P10 found the same, P11 confirms
it with the parliament on top. *Whether* and *how* modules exchange votes moves results
by tens of points; *which arithmetic* reduces them moves almost nothing.

## Verification actually run over the final result

Every check below was run against the committed 25-run set, not against work in
progress:

- **25/25 runs at exactly 40 episodes**, and no stale `eval_stats_old.csv` left in
  any run directory.
- **All 6 gates pass** (`test_parliament`, `test_consensus`, `test_iterated_vote`,
  `test_lm_equivalence`, `test_vote_path`, `test_weights`).
- **Live hydra configs confirm the intended variable, per arm** — every arm ran
  `vote_mode: consensus` and `n_eval_epochs: 4`, with the correct `monty_class`
  and only `opposing_phases` / `sequential` / `vote_rounds` differing. Read from
  the configs Hydra actually composed, not from the yaml we wrote.
- **All 4 OOD rotations evaluated, perfectly balanced** (50 rows each) in every arm.
  The rotations are the pre-registered oblique set, not the in-domain ones. This is
  the epoch trap that voided a P9 sweep, checked here from the output.
- **The 5 arms are not byte-identical** — distinct behaviour hashes over
  `primary_performance` + `most_likely_object`. P9 produced identical arms once.
- **Liveness verified per arm, not just once**: `parl-3`, `parl-noopp` and
  `parl-batch` each show all three phases moving evidence with `send_none` at 0.0%
  (`parl-noopp` deltas 20957 / 10046 / 11311; `parl-batch` 36190 / 13607 / 15902).
  The delivery counts also confirm `parl-batch` really batches — 4025 deliveries in
  phase 1 where the sequential arms make 12495.
- **The refusal guard was proven live**: truncating one run to 20 episodes makes the
  analysis refuse to report, and restoring it reproduces every number exactly.

## Method note — one run was contaminated and the guard caught it

`p11_plain1_s42` produced **73 episodes** instead of 40. An aborted first launch had
written 33 episodes, and Monty **appends** to an existing `eval_stats.csv`, so the real
run added to a stranger's rows. The episode-count assertion in `run_p11.sh` flagged it;
the run was deleted and redone cleanly. `run_p11.sh` now removes the run directory
before each run, closing the hole at the source.

Had the guard not been there, the replication control would have been computed over a
half-contaminated arm — and P11d is the check that certifies every other number.

## Standing

- The parliamentary structure holds: **P11b replicates P10a** under a different rule.
- Opposition works as *friction* under consensus (−18 pp agreement, significant) and
  is not detectable as *benefit* at this power.
- **H2 remains unsupported and untouched.**
- **Publication decision is Nadi's and is not taken.**
