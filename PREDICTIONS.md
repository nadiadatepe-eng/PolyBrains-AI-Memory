# PREDICTIONS.md

**Append-only.** Entries are committed *before* the run they describe. Never edited after the
fact — a corrected prediction is a new entry that references the old one.

Without this file, "honest reporting" quietly becomes "we reported the runs we liked", and it
does so unintentionally.

---

## 2026-08-18 · Pre-registration for CP-5 (E0–E3)

Written before any accuracy number from a multi-rotation model has been observed. The only
accuracy figure seen so far is CP-0's 60%, which came from a single-rotation model and is a
liveness check, not a baseline.

### Rotation split, fixed now

From `reports/rotation-blocker.md`, 9 of 14 rotations run under MuJoCo.

- **In-domain (train):** `[0,0,0]`, `[0,90,0]`, `[0,270,0]`, `[90,0,0]`, `[90,180,0]`
- **Out-of-distribution (test):** `[35,45,0]`, `[325,45,0]`, `[35,315,0]`, `[325,315,0]`
- **Excluded, with reasons:** `[0,180,0]` (no visible target under MuJoCo camera geometry);
  `[35,135,0]`, `[325,135,0]`, `[35,225,0]`, `[325,225,0]` (upstream `get_correct_k_n`
  null-handling bug). Both documented; neither is a silent drop.

Rationale for the split: train on axis-aligned poses, test on oblique ones. This is a
defensible OOD notion and it was chosen by which rotations *run*, not by which give good
numbers, because no numbers exist yet.

### Noise floor

Before any arm comparison, run the baseline arm 5 times with different seeds and record the
spread. **Any effect smaller than that spread is not an effect** and will be reported as
underpowered.

### E0 — replication

*Prediction:* stock Monty with 5 LMs, trained on the 5 in-domain rotations, exceeds 60%
in-domain accuracy (CP-0's single-rotation figure).
*Would falsify:* accuracy at or below 60% in-domain, which would mean something is wrong with
the setup rather than with any hypothesis.

### E1 — multi-frame vs single-frame OOD (H1)

*Prediction:* 5-LM voting shows a **larger OOD delta** (OOD accuracy minus in-domain
accuracy, i.e. a smaller drop) than a 1-LM configuration. The 5-LM advantage in-domain is
predicted to be small or absent.
*Would falsify H1:* no OOD difference, or 5-LM worse OOD.
*Confounder to check:* if 5-LM is better *everywhere*, suspect capacity rather than structure,
and say so.

### E2 — confidence weighting (H2, load-bearing)

*Prediction:* three arms, `vote_mode` in {`max`, `consensus`, confidence-weighted}.
Capture rate is expected near 1.0 for `max` (already verified by construction) and lower for
`consensus`. **H2 predicts the OOD delta collapses as capture rate rises.**
*Would falsify H2:* OOD delta unchanged across arms, or `consensus` worse OOD than `max`.

### E3 — diversity vs count (the control that can kill H1)

*Prediction:* 5 diverse LMs beat 5 near-clone LMs on the OOD delta, and the difference tracks
the D-index.
*Would falsify H1's second clause:* clones perform as well as diverse modules. **Per CP-2 this
outcome would favour Gentner's systematicity account over ours**, and we would report that.

### E4 — adaptive weight (exploratory)

**No directional prediction registered.** w(t) is measured on a module deliberately untrained
on the test object. This is exploratory and will be reported as such; any result is
descriptive, not confirmatory.

### Standing commitments

1. Every arm's run directory is kept, including failed and null runs.
2. `CONSENSUS_TAU=0.15`, `W_MIN=0.1`, `W_MAX=2.0`, `EMA_ALPHA=0.1` and the D-index definition
   are frozen and test-guarded. If any is changed, the change is a new entry here with its
   reason, and every affected result is re-run.
3. "Underpowered" is a permitted outcome and will be stated plainly rather than hidden behind
   a favourable subgroup.

---

## 2026-08-18 (later) · Outcomes of the CP-5 entry above

Recorded after the runs. The entry above is unedited.

| Prediction | Outcome |
|---|---|
| E0 >60% in-domain | **MET.** 100.0% (50/50), all 5 seeds. |
| E1 5-LM shows larger OOD delta than 1-LM | **NOT TESTED.** The 1-LM arm was not run. |
| E2 OOD delta collapses as capture rate rises | **UNDERPOWERED.** consensus−max = −0.80 pp against a 5.26 pp noise floor. |
| E3 diverse beats clones | **NOT RUN.** |
| E4 adaptive weight | not run, no prediction was registered |

### A prediction I made mid-investigation and then refuted

While investigating why the rules were indistinguishable, I predicted from a synthetic model
that **lowering `vote_evidence_threshold` would widen the consensus-vs-max gap**, because
votes above 0.8 are near-unanimous by construction.

**Refuted.** Measured gaps at thresholds 0.8 / 0.5 / 0.2 / 0.05 were −1.0, +6.0, 0.0, +1.0 pp
— no trend, all inside the noise floor. The synthetic model assumed uniform votes over
[threshold, 1]; real votes cluster near the top regardless of the threshold.

Recorded because it was wrong, and because it was formed *after* seeing the null, which makes
it exploratory rather than confirmatory.

---

## 2026-08-18 · NEW pre-registration, for the next round

Written now, before any of these runs exist.

### P1 — the threshold effect (replication of an exploratory finding)

Lowering `vote_evidence_threshold` from 0.8 to 0.2 raised OOD accuracy by **+9.5 pp**
(87.50% → 97.00%) across both vote rules and both seeds, n=4 per cell.

**This was NOT pre-registered.** It was found while investigating the E2 null and is
exploratory. It is registered here for a clean test.

*Prediction:* with 5 seeds per threshold and `max_total_steps` raised to 20000 so no run
truncates, threshold 0.2 beats 0.8 on OOD accuracy by **more than the noise floor** measured
in that same run set.
*Would falsify:* difference at or below the noise floor, or reversed.
*Confound to rule out:* lower thresholds cost ~90% more runtime and more steps per episode.
The gain must survive equalising the step budget, or it is a compute effect and not a
threshold effect. **This confound must be tested, not assumed away.**

### P2 — H1 proper, which has not actually been tested

*Prediction:* a 1-LM arm shows a **larger** in-domain-to-OOD drop than the 5-LM arm.
*Would falsify H1:* no difference, or 1-LM drops less.

### P3 — E3, the fork against Gentner (per `reports/rivals.md`)

*Prediction:* 5 diverse LMs beat 5 near-clone LMs on OOD accuracy, and the difference tracks
the D-index.
*Would falsify H1's second clause:* clones do as well. **Per CP-2 that outcome favours
systematicity over our account, and we report it as such.**

### Standing note on power

The current setup cannot resolve effects below ~5 pp. Any future claim smaller than that
requires more episodes or a harder task, and will otherwise be reported as underpowered.

---

## 2026-08-18 (evening) · Correction notice

**A methodological error was found in my own analysis before publication.**

`eval_stats.csv` has one row per learning module per episode. I counted rows as episodes,
which inflated multi-LM sample sizes 5x (a 5-LM run of 10 episodes reports 50 rows) and
conflated per-module performance with system performance.

Corrected with `tools/episode_accuracy.py`. Effect on the record:

| | as reported | corrected |
|---|---|---|
| 5-LM OOD, max | 94.0% "n=50" | **96.0%**, n=10 episodes |
| consensus − max | −0.80 pp | **0.00 pp**, identical every seed |
| E0 in-domain | 100% | 100% (unchanged) |

The vote-rule null got *stronger*: the three rules are now exactly identical.

**New arm run after the correction:** 1 LM, no voting, 5 seeds.

| arm | in-domain | OOD | drop |
|---|---|---|---|
| 5 LMs | 100.0% | 96.0% | −4.0 pp |
| 1 LM | 72.0% | 64.0% | −8.0 pp |

Directionally consistent with H1 (+4.0 pp), **but not claimed as support**: the 1-LM arm is
worse in-domain too, so capacity is confounded with voting; +4.0 pp is a third of the 1-LM
arm's 11.40 pp seed noise; and n=10 episodes cannot resolve below 10 pp.

### P4 — the clean H1 test, registered now

*Prediction:* a 5-LM system with **voting disabled** (`lm_to_lm_vote_matrix: null`) drops more
from in-domain to OOD than the identical 5-LM system with voting enabled.
*Why this is the right test:* same model, same training, same capacity, one variable. The
1-LM vs 5-LM comparison run today cannot separate voting from capacity and should not be
reported as if it could.
*Would falsify H1:* no difference, or voting-off drops less.

---

## 2026-08-18 (evening) · P4 outcome: H1 NOT SUPPORTED

The clean test ran. Same 5-LM model, voting on vs off, 5 seeds each.

| arm | in-domain | OOD | drop |
|---|---|---|---|
| voting ON | 100.0% | 96.0% | −4.0 pp |
| voting OFF | 100.0% | **100.0%** | 0.0 pp |

**P4 predicted voting-off would drop MORE. It dropped LESS — in fact not at all.**
H1 is not supported on this task. Voting cost 4.0 pp.

### Mechanism, which is the useful part

Voting did not reduce module failures (7 vs 8 across 50 episodes). It made them **correlated**:

| | any module failed | ALL modules failed | correlation |
|---|---|---|---|
| voting ON | 7 | **2** | **29%** |
| voting OFF | 8 | **0** | **0%** |

On the `dice` episode every module was individually correct with voting off, and all five
failed together with voting on. Since the match criterion is `AnyLMsMatch`, independent
failures are survivable and correlated ones are not.

This is what `np.ma.max` aggregation predicts (CP-1 finding (a)): one confident error captures
the consensus. It is H2's mechanism showing up as harm to H1.

### Registered now, before the next runs

**P5 — failure correlation is the right dependent variable.**
*Prediction:* the `consensus` rule produces lower failure correlation than `max` on a task
where modules genuinely disagree.
*Note:* on the current task all three rules are identical, so this REQUIRES the harder task in
P6 first. Running it on the present task would be a null by construction.

**P6 — build a task with real disagreement.**
The current setup has D-index ≈ 0.04: five patches see the same object from nearly the same
pose. Every claim in this project is about *disagreeing* modules, and this task has almost no
disagreement.
*Prediction:* with sensor patches widely separated, or with noise injected into a subset of
modules, D-index rises above 0.15 and the vote rules stop being identical.
*Would falsify:* rules remain identical even under induced disagreement, which would mean the
aggregation is irrelevant in Monty regardless of task.

**Standing:** the no-vote arm is at ceiling (100%, sd 0.00) so it can only show absence of
harm, never advantage. A harder task is required before any claim that voting helps or hurts
in general.

---

## 2026-08-18 (evening) · P6 outcome: REFUTED, and instructively so

Predicted: spreading sensor patches 8x (0.01 → 0.08) raises disagreement and makes the vote
rules diverge.

**All three arms — `max`, `consensus`, and voting entirely disabled — gave identical results
to the decimal** (100% accuracy, 64.0% per-module, 38.0% unanimous, 0% failure correlation,
5 seeds each).

### Why, measured at the vote path rather than inferred

| task | `send_out_vote` → `None` | receipts | receipts changing evidence |
|---|---|---|---|
| stock (0.01) | 63% | 1270 | **1163 (92%)** |
| spread (0.08) | **88%** | 555 | **121 (22%)** |

Spreading the sensors did not make modules disagree. It knocked them **off the object**, so
they stopped voting. Upstream's own comment says this can happen "if some start off the
object". The "7/10 episodes of disagreement" I measured was modules having no opinion, not
modules holding conflicting ones.

**Lesson: disagreement and absence look identical in output statistics and are opposite at the
mechanism.** Any future disagreement manipulation must be verified by instrumenting
`send_out_vote`, not by reading output variance. Tool: `tools/vote_spy.py`.

This retroactively strengthens P4: the stock task has a live vote path (92% of receipts change
evidence), so P4's correlated-failure finding was measured on a mechanism that was running.

### P7 — registered now: induce disagreement without absence

*Method:* keep all five patches at the stock 0.01 separation so every module stays on the
object, and inject sensory noise into a subset (2 of 5) of modules.
*Prediction:* `send_out_vote → None` stays near the stock 63%, while modules disagree about
object identity; and under those conditions `consensus` produces **lower failure correlation**
than `max`.
*Would falsify:* rules remain identical even with a live vote path and genuine disagreement,
which would mean the aggregation rule is irrelevant in Monty regardless of task.
*Mandatory check before interpreting any result:* report `send_none` percentage alongside
accuracy. A result from a silent vote path means nothing.

---

## 2026-08-18 (evening) · P7 testbed validated, arms not yet run

Built the noise-based disagreement task: sensor modules 3 and 4 get 5-10x stock noise,
modules 0-2 stay clean, **patch positions unchanged** so every module stays on the object.

**Mandatory vote-path check (the P6 lesson), single probe run:**

| task | `send_none` | receipts | effective |
|---|---|---|---|
| stock | 63% | 1270 | 92% |
| P6 spread (broken) | **88%** | 555 | 22% |
| **P7 noise** | **60%** | 2490 | **68%** |

**The vote path is live.** P7 avoids P6's failure mode by construction.

Probe run (seed 42, `max` rule): 90% system accuracy; per-module 9/8/9 clean vs **6/5 noisy**;
modules named different objects in **6/10 episodes**. Genuine disagreement among modules that
are all voting — the first such task in this project.

### P7 predictions, registered before the arms are run

*P7a:* `consensus` produces **lower failure correlation** than `max` on this task.
*P7b:* `consensus` beats `max` on system accuracy, because the two noisy modules should not be
able to capture the consensus under an agreement-weighted rule but can under `np.ma.max`.
*Would falsify:* rules remain identical (as on the stock task), or `consensus` is worse.

*Confound to check:* the noisy modules are worse individually, so any `consensus` advantage
must be shown to come from resisting capture, not merely from down-weighting bad modules.
The `mean` arm is the control: if `mean` matches `consensus`, the effect is plain averaging
and not agreement-weighting.

**Not yet run.** Awaiting Nadi's decision on whether to pursue H2 or write up the negative
result.

---

## 2026-08-19 · P7 POWERED OUTCOME (2000 episodes)

40/40 runs, 50 episodes each, zero truncated.

| arm | accuracy | failure correlation |
|---|---|---|
| max (upstream) | 97.00% | 5.1% |
| mean (control) | 97.40% | 4.3% |
| consensus | 97.80% | 3.7% |
| **no voting** | **99.80%** | **0.2%** |

**P7a — consensus lowers failure correlation: NOT SUPPORTED.** 5.1% → 3.7%, z=0.84, n.s.

**P7b — consensus beats max on accuracy: NOT SUPPORTED.** Paired t(9)=1.08 on +0.80 pp.
Wins 4, loses 1, ties 5. Directionally right, not significant.

**Control behaved as designed:** `mean` gained only +0.40 pp.

**H1 — REFUTED, significantly.** No voting beats max by **+2.80 pp, paired t(9)=4.58,
p<0.05.** The only significant accuracy effect in the study, and it opposes the founding
hypothesis.

### Analysis error, corrected

My first script used sd/√n as the threshold and printed "P7b: SUPPORTED" at +0.80 pp vs a
0.64 pp bar. **Wrong test.** The arms share seeds, so a paired t-test is required; it gives
t=1.08, not significant. Script fixed, mistake recorded in its comments. Had I not re-checked,
this file would claim support H2 does not have.

### Status of both hypotheses

- **H1: refuted.** Voting costs accuracy on every task with a live vote path.
- **H2: not supported.** There is no multi-frame advantage to destroy.

### What is NOT yet tested, and would threaten the interpretation

- **`AnyLMsMatch` favours independent modules by construction.** With a unanimity criterion,
  voting might win. This is the most obvious threat and it is untested.
- All arms are near ceiling (97–99.8%), compressing effects into a 3 pp band.
- Single object per episode; Monty's voting is aimed at ambiguous/multi-object scenes.

**No further runs pending. Awaiting Nadi's decision on publication.**

---

## 2026-08-19 · P8 — UNANIMITY CRITERION (registered before any number is computed)

**The reviewer objection.** All results so far score an episode correct under
`AnyLMsMatch`: correct if **any** of 5 modules reaches a correct terminal state. That
criterion rewards module *independence* by construction — 5 independent modules get 5
lottery tickets, and voting, which makes modules agree, throws tickets away. Under this
criterion "voting harms accuracy" may be a statement about the scoring rule rather than
about voting.

**What P8 does.** Re-score the existing P7 runs (40 runs x 50 episodes = 2000 episodes,
`a88c029`, data in `~/tbp/results/monty/projects/monty_runs/pow_p7_*`) under three
criteria. **No new episodes are run**, so nothing about the runs can be tuned to the
result; only the read-out changes.

- `any`   — ≥1 of 5 modules correct (what we have used; upstream's `AnyLMsMatch`)
- `majority` — ≥3 of 5 modules correct
- `unanimous` — all 5 modules correct

### Predictions

*P8a:* Under `unanimous`, the **no-voting advantage shrinks**. Voting exists to make
modules agree, so unanimity should reward it.

*P8b (the sharp one):* Under `unanimous`, **voting beats no voting** — the sign of the
H1 effect flips. If this holds, the H1 refutation is criterion-dependent and must not
be reported as a general result.

*P8c:* `majority` sits between the two, monotonically.

**Would falsify:** no-voting still wins under `unanimous`, or the ordering is
non-monotonic across the three criteria.

**Interpretation fixed in advance, so it cannot be chosen after seeing the numbers:**

- If P8b holds → the H1 refutation is **an artefact of `AnyLMsMatch`** and the paper's
  central claim must be restated as criterion-relative. This weakens the current result.
- If P8b fails and no-voting still wins under unanimity → the refutation **survives its
  most obvious threat** and is substantially stronger than it is today.

Both outcomes are publishable. The second is a better paper, which is precisely why the
prediction is written down first.

**Confound to check:** unanimity mechanically lowers accuracy in every arm, which could
compress all arms toward a floor and mask differences the way the 97–99.8 % ceiling
compresses them today. Report per-arm absolute accuracy under each criterion, not only
the differences, so a floor effect is visible rather than inferred.

---

## 2026-08-19 · P8 OUTCOME — all three predictions supported, H1 refutation does not survive

Re-scored P7's 2000 episodes. No new runs.

| criterion | no voting − max | t(9) | verdict |
|---|---|---|---|
| `any` (AnyLMsMatch) | +2.80 pp | 4.58 | voting harms |
| `majority` | +0.20 pp | 0.13 | n.s. |
| `unanimous` | **−30.20 pp** | **−14.40** | **voting helps** |

**P8a SUPPORTED** — advantage shrank (+2.80 → −30.20).
**P8b SUPPORTED** — sign flipped, significantly; no voting loses 10/10 seeds.
**P8c SUPPORTED** — monotonic across the three criteria.

**Consequence, as fixed in advance:** the H1 refutation is **criterion-dependent** and
must not be reported as a general result. This is the outcome I labelled as the weaker
paper, and it is what the data gave.

### Circularity check (not pre-registered — added on seeing a 30 pp effect)

Unanimity rewards agreement and voting manufactures agreement, so the flip could have been
true by construction. Tested on **mean modules-correct per episode**, which has no
threshold and cannot favour either read-out: voting gains **+0.564 modules/episode,
t(9)=15.11**, lifting 277 episodes and dragging 75, with zero 5→0 collapses. So the flip is
**not** circular — voting propagates correct evidence.

This check was added after seeing the result, which makes it exploratory rather than
confirmatory. Recorded as such.

### What this contradicts in the earlier record

"Voting creates correlated failure" (P7, `a88c029`) reported all-fail episodes rising
1 → 15 under `any`. That number is correct and reproduces. But voting simultaneously moves
261 three-correct episodes up to four and five correct, which the earlier report did not
say. **Reporting the tail without the bulk was one-sided.**

### Standing of the hypotheses

- **H1: refutation withdrawn.** The sign of the effect is set by the scoring rule.
- **H2: still not supported**, and unaffected — `consensus` 40.20% vs `max` 41.00% under
  unanimity. All three rules stay within 1.6 pp under every criterion while voting-vs-no-
  voting moves 30 pp.

**Publication decision remains Nadi's and is not taken.**

---

## 2026-08-19 · P9 — ITERATED VOTING (registered before the mechanism is built)

**Nadi's question:** what if we vote on an already-voted result? Vote once, then vote on
the result of that vote, then again — rounds 1, 2, 3.

**Why it is worth asking now.** P8 showed voting genuinely propagates correct evidence
(+0.564 modules/episode on a threshold-free metric), not merely agreement. If one exchange
propagates evidence, more exchanges either keep propagating (accuracy rises, modules
converge) or they amplify whatever the first round produced, including errors. Both are
informative, and they are distinguishable.

**The mechanism.** `monty_base.py:302` `_vote()` is exactly one gather-then-scatter per
step: collect `send_out_vote()` from every LM, route via `lm_to_lm_vote_matrix`, call
`receive_votes()`. Because `receive_votes()` **mutates each LM's own evidence**, calling the
whole block again re-reads the updated evidence — so iteration is a loop around the existing
block, requiring no change to the rule and no upstream edit. Implemented as a subclass in
`src/polybrains/`, per the thin-layer contract.

Arms: `rounds=1` (identical to every run so far, and the replication check), `rounds=2`,
`rounds=3`. All other variables held at P7's settings, including the noise on modules 3+4.

### Predictions

*P9a:* Accuracy under **unanimity** rises from `rounds=1` to `rounds=2`. More exchange, more
propagation.

*P9b (the interesting one):* the gain is **sub-linear and saturating** — round 2 → 3 adds
less than round 1 → 2. Evidence that is already shared cannot be propagated twice.

*P9c:* **Agreement rises monotonically with rounds** (mean modules-correct and the
5-of-5 count both increase), because each round pulls hypotheses toward the same peaks.

*P9d — the failure mode worth catching:* under `AnyLMsMatch`, iterated voting is **worse**
than one round, and worsens with each round. `np.ma.max` means the loudest vote captures the
neighbourhood; iterating hands the captured value back as input, so a confident error should
compound. If P9c and P9d both hold, iteration buys agreement at the cost of independence,
which is precisely the trade P8 exposed.

**Would falsify the useful reading:** accuracy flat across rounds under every criterion (the
vote is already at a fixed point after one round), or `send_none`% climbing with rounds,
which would mean modules are dropping out rather than converging — the P6 failure, and the
reason `send_none`% is mandatory in any report.

**Cheap enough to be honest about:** ~58 s per 50-episode run, so 3 arms x 5 seeds is under
15 minutes. There is no excuse for an underpowered version of this test.

**Confound to check:** more rounds means more compute per step, not merely more voting. The
control is that `rounds=1` must reproduce P7's numbers exactly; if it does not, the loop
changed something other than the number of exchanges.

---

## 2026-08-19 · P9 OUTCOME — all four predictions supported

600 episodes on a verified-live vote path (`203c6f3`). Two earlier sweeps voided;
see `reports/p9-iterated.md`.

| rounds | `any` | `majority` | `unanimous` | mean correct |
|---|---|---|---|---|
| 1 | 96.50% | 93.50% | 43.50% | 4.050 |
| 2 | 94.50% | 92.50% | 66.00% | 4.335 |
| 3 | 90.50% | 88.50% | **79.00%** | 4.340 |

- **P9a SUPPORTED** — unanimity +22.50 pp from 1→2 rounds, t(4)=10.76
- **P9b SUPPORTED** — saturates: +22.50 then +13.00
- **P9c SUPPORTED** — monotonic; 5-of-5 episodes 87 → 132 → 158
- **P9d SUPPORTED** — under `AnyLMsMatch` iteration hurts, −2.00 then −4.00 pp

Control passes: `rounds=1` reproduces P7's max arm, +0.10 pp, t=0.15.

**Reading:** iteration buys agreement and pays in independence. Three rounds turn a
6 pp loss under `any` into a +35.50 pp gain under unanimity — the same mechanism,
opposite signs, which sharpens P8's finding that the criterion decides the verdict.

**Liveness checked before believing it** (both prior failure modes): evidence moves
23,634 in round 1 and 43,685 more in rounds 2+3; `send_none` is **flat at 53.8%** in
every round, so this is convergence, not P6-style dropout.

**Two voided sweeps, both caught by the pre-registered control rather than by
inspection.** `n_eval_epochs=1` evaluated 1 of 4 OOD rotations; and the subclass
overrode `monty_base.py:302` when the live method is `graph_matching.py:389`, so no
votes were delivered in any round. Both completed cleanly and produced plausible
numbers. Had the control not existed, the second would have been published as
"iterated voting changes nothing".

**Publication decision remains Nadi's and is not taken.**

---

## 2026-08-19 · P10 — PARLIAMENTARY VOTING (registered before the mechanism is built)

**Nadi's design.** Three phases per step instead of one exchange:

1. **Propose** — modules 0,1,2 vote normally.
2. **Oppose** — module 3 plays devil's advocate against phase 1: it votes for its
   *runner-up* object hypothesis, not its own best. One module, one pass.
3. **Second opposition** — module 4 does the same against the state left by phases
   1 *and* 2.

Within a phase, modules vote **one by one**: each sees the evidence updates caused by
the modules before it, so order is a real variable rather than a formality.

Nadi's success criterion, stated in his words: *"the answers will be more genuine
because of 2 levels of confirmation."* Made measurable below.

**The 30/20/10 in Nadi's original sketch refers to agent counts, not learning
modules.** Monty is pretrained here with 5 LMs, so the structure maps 3/1/1. The
shape is what is under test, not the headcount.

### Why devil's advocate is not just "more voting"

P9 established that any extra exchange raises agreement: 3 plain rounds took unanimity
43.50 → 79.00%. So "P10 raises unanimity" would be an uninformative result. The
question is whether **opposition buys something plain repetition does not.**

Hence the controls are the point:

- `plain-3` — three plain iterated rounds (P9's `rounds=3` arm), same exchange count
- `parl-3` — the three-phase parliamentary structure
- `parl-noopp` — three phases where the "opposition" modules vote normally, isolating
  the *structure* from the *opposition*

### Predictions

*P10a:* `parl-3` produces **fewer high-confidence errors** than `plain-3` — episodes
where all 5 modules agree on the WRONG object. This is the operational form of "more
genuine": confident agreement should become harder to reach, and what survives should
be right more often.

*P10b (the sharp one):* **precision of unanimity rises.** Of episodes reaching 5-of-5
agreement, the fraction that are correct is higher under `parl-3` than `plain-3`, even
if `parl-3` reaches unanimity less often. Two-level confirmation should trade quantity
of agreement for quality of agreement.

*P10c:* `parl-3` reaches unanimity **less often** than `plain-3`. Opposition is
friction; if it does not slow convergence it is probably not doing anything.

*P10d:* the `parl-noopp` control sits between the two. If `parl-noopp` matches
`parl-3`, the effect is the phase structure and NOT the opposition, and P10a/b do not
support the idea.

*P10e:* module order within a phase matters — shuffling the sequential order changes
the outcome measurably. If order is irrelevant, "one by one" is not doing what the
design assumes.

### The mechanism risk, stated in advance

The reduction is `np.ma.max` (`learning_module.py:938`, verified at the pinned sha):
the loudest vote in a neighbourhood wins outright. **A devil's advocate's dissent may
therefore be structurally ignored** — max cannot represent opposition, only volume.
If P10 shows no effect, this is the first thing to check, and *that* would itself be a
publishable finding about the aggregation rule rather than about parliaments.

**Would falsify the idea:** `parl-3` and `plain-3` indistinguishable on P10a and P10b;
or `parl-noopp` explains the whole effect; or unanimity precision *falls* under
opposition.

**Mandatory before any number is believed** (three sweeps have now been voided for
exactly these):
- `send_none`% per phase — silence and dissent are opposite at the mechanism (P6)
- evidence-delta per phase — a phase that moves no evidence is dead (P9)
- a replication control — the propose-only arm must reproduce P7's max arm

**Publication decision remains Nadi's and is not taken.**

---

## 2026-08-19 · P10 OUTCOME — structure works, opposition does not

600 new episodes on a gated, verified-live mechanism.

| arm | `any` | agree | precision | **confident errors** |
|---|---|---|---|---|
| plain-1 | 96.50% | 45.00% | 96.59% | 1.50% |
| plain-3 | 90.50% | 87.00% | 90.84% | **8.00%** |
| **parl-3** | 96.50% | 38.50% | 94.31% | **2.50%** |
| parl-noopp | 96.50% | 52.50% | 96.14% | 2.00% |
| parl-batch | 99.50% | 31.00% | 98.57% | 0.50% |

- **P10a SUPPORTED** — −5.50 pp confident errors vs `plain-3`, t(4)=−3.77
- **P10b directionally right, n.s.** — +3.47 pp precision, t=1.47
- **P10c SUPPORTED** — −43.00 pp agreement, t(4)=−12.04
- **P10d — the control decides it.** `parl-noopp` is indistinguishable from `parl-3`
  on all three measures (t = 0.34, −0.65, −2.61). **The benefit is the phase
  structure, not the opposition.**
- **P10e NOT SUPPORTED** — sequencing changes nothing measurable (t=1.12)

**Reading:** staged, few-speakers-per-exchange voting genuinely resists false
consensus — three plain rounds quadruple confident errors (1.5→8.0%) while the
parliamentary structure holds them at 2.5% *and* keeps `any` at 96.50% rather than
90.50%. Adversarial content adds nothing on top.

**Two mechanism findings explain the null**, both verified:

1. **`np.ma.max` has no channel for dissent.** A devil's advocate argues its
   runner-up, which carries lower evidence by construction, and max discards lower
   numbers. Registered as the risk before the run.
2. **"One by one" made every phase single-speaker.** Live instrumentation over 2180
   delivery events shows **at most one module ever argues per exchange**. `parl-3` is
   five consecutive one-speaker exchanges, not three-propose-then-challenge. Faithful
   to the instruction, but the phase labels overstate what ran.

**The opposition idea is not refuted — it was tested through a rule that cannot
carry it.** The fair next test is the same parliament under `vote_mode="consensus"`,
which is already built.

**Publication decision remains Nadi's and is not taken.**

---

## 2026-08-19 · P11 PRE-REGISTRATION — the parliament under `consensus`

Registered **before** `tools/run_p11.sh` was run and before any P11 number existed.

P10 tested Nadi's parliament through `np.ma.max`, a rule that takes the loudest
vote. An opposing module argues its **runner-up**, which carries lower evidence by
construction, so max discards it: the idea was tested through a rule that cannot
carry it. `vote_mode="consensus"` (agreement-weighted mean, frozen at CP-3 before
any accuracy was seen) discounts a lone loud vote and amplifies a mutually-agreeing
group, so dissent has a channel. This is the fair test.

Five arms, all `consensus`, 5 shared seeds x 40 episodes = 1000 episodes.
`plain-1`/`plain-3` are re-run under consensus rather than reused from P9 (whose
arms are all `max`): comparing a consensus parliament against a max baseline would
confound the rule with the structure.

**P11a (the whole question).** Under `consensus`, `parl-3` separates from
`parl-noopp` on confident errors — the opposition contributes something the phase
structure alone does not. Under `max` this gap was t=0.34, indistinguishable.
*Falsified if* |t| ≤ 2.776 again.

**P11b.** `parl-3` has fewer confident errors than `plain-3` at equal exchange
count, replicating P10a's direction under the new rule.

**P11c.** Unanimity precision is higher under `parl-3` than `parl-noopp`. P10b was
directionally right but n.s. (t=1.47) against `plain-3`; the sharper contrast is
against the structural control.

**P11d (replication control — voids the sweep if it fails).** `p11_plain1` must
reproduce P7's powered consensus arm within noise. If it does not, something other
than the parliament changed and no comparison is readable.

**P11e (sequencing).** `parl-batch` differs from `parl-3`. NOT SUPPORTED under max
(t=1.12); registered again because consensus is order-sensitive in a way max is not.

**What a null means.** If P11a fails too, the finding is that **Monty's vote path
cannot express opposition under any reduction rule we have** — max discards the
dissenting number, consensus dilutes it — and that is a publishable statement about
the aggregation interface rather than about parliaments.

**Mandatory checks before any number is believed** (four sweeps voided so far):
`n_eval_epochs=4` with a 40-episode assertion, the P11d replication control,
per-phase evidence-delta liveness, and `send_none`% per phase.

**Publication decision remains Nadi's and is not taken.**

---

## 2026-08-19 · P11 OUTCOME — opposition becomes audible, and still does not pay

1000 episodes. **P11d replication control PASSED** (`plain-1` 97.50% vs P7's powered
consensus 97.80%, −0.30 pp against a ±4.40 pp band), so the sweep is certified.

| arm | `any` | agree | precision | **confident errors** |
|---|---|---|---|---|
| plain-1 | 97.50% | 40.50% | 96.13% | 1.50% |
| plain-3 | 91.50% | 85.00% | 90.48% | **8.00%** |
| **parl-3** | 98.50% | 37.50% | 97.29% | **1.00%** |
| parl-noopp | 97.00% | 55.50% | 95.53% | 2.50% |
| parl-batch | 98.50% | 28.50% | 96.85% | 1.00% |

- **P11a NOT SUPPORTED** — −1.50 pp confident errors vs `parl-noopp`, t(4)=−1.50
- **P11b SUPPORTED** — −7.00 pp vs `plain-3`, t(4)=−3.50 (P10a replicates under a new rule)
- **P11c directionally right, n.s.** — +1.75 pp precision, t=0.78
- **P11e NOT SUPPORTED** — sequencing +9.00 pp agreement, t=2.45, under the bar

**The registered mechanism claim is confirmed, and it changes the reading.** Under
`max` the opposition was inert on every measure. Under `consensus` it is not:
`parl-3` − `parl-noopp` on **agreement is −18.00 pp, t(4)=−3.06, significant**
(unanimity −16.50 pp, t=−2.60). The devil's advocate now genuinely makes agreement
harder to reach. **It just does not convert that friction into accuracy** — the 18 pp
it destroys buys 1.5 pp of confident errors and 1.5 pp of `any`, neither significant.

**P11a's null is power-limited, not a clean refutation.** `parl-3` sits at a 1.00%
error floor and `plain-1` at 1.50%: there is almost nothing left to prevent, and
5 seeds x 40 episodes cannot resolve below ~2 pp. The 8.00% rate is a wound *plain
iteration* inflicts; the structure's contribution is to not inflict it.

**Third confirmation that the rule barely matters**: consensus − max, structure held
fixed, is n.s. on every arm and measure (largest |t| = 1.63). P8, P10 and P11 now all
say the same thing — *whether* modules exchange votes moves tens of points, *which
arithmetic* reduces them moves almost nothing.

**Method:** `p11_plain1_s42` produced 73 episodes because Monty appends to an existing
`eval_stats.csv` and an aborted launch had left 33 rows. The episode-count guard caught
it, the run was redone, and `run_p11.sh` now clears the run directory first. That run
feeds the replication control, so the guard protected every other number.

**H2 remains unsupported and untouched. Publication decision is Nadi's and is not taken.**

---

## 2026-08-19 · P11 CORRECTION — the rule's role is NOT established

Written the same day, after rechecking the P11 outcome above rather than trusting it.

The outcome entry says the opposition was "inert under `max`" and became active under
`consensus`. **Rechecking the max arms shows that was overstated.** `parl-3` −
`parl-noopp` on agreement under `max` was already **−14.00 pp, t(4)=−2.24** — not null,
just under the 2.776 bar. Consensus gives −18.00 pp, t=−3.06, which crosses it.

The claim "consensus gives dissent a channel max did not" therefore requires the two
effects to *differ*, which is a difference-in-differences on shared seeds:

    (parl3 - noopp | consensus) - (parl3 - noopp | max)
      = -4.00 pp,  t(4) = -0.60,  n.s.   per-seed: -27.5, -7.5, +12.5, 0.0, +2.5

**Not supported.** P10's registered mechanism claim is *consistent* with P11 and is
**not confirmed by it**. What stands:

- under `consensus` the opposition is measurably active on agreement (t=−3.06),
  a positive result rather than an inference from a null;
- it is not measurably profitable (errors t=−1.50, `any` t=0.88);
- whether `max` would show the same with more seeds is **open**.

The P11a and P11b verdicts above are unaffected. The over-claim was in the *reading*,
not in the pre-registered tests, and it was caught by testing the comparison the
reading actually depends on.

---

## 2026-08-19 · AUDIT — what H1 and H2 have actually been tested on

Written when Nadi asked whether to reconsider H2 and continue with H1. Read from the
configs and run directories, not from this file's own prior summaries.

### H2 has never been run. Not once.

H2 is: *weighting votes by in-domain confidence destroys the OOD advantage.* The
mechanism for it is `polybrains/weights.py` (`AdaptiveVoteWeight`, w(t)), built and
gated at CP-4 on 2026-08-18.

**`adaptive_weight: false` appears in 24 of 24 experiment configs. No config sets it
true. No Hydra output records it true.** So every "H2 not supported" line in this file
— at P4, P7 and P8 — is a statement about *something else*: E2 varied
`vote_evidence_threshold`, and P7/P8 compared `max` vs `consensus` vs `mean`. Those are
reduction-rule and filtering experiments. **They do not touch confidence weighting.**

This is not a small bookkeeping error. It is the same failure this project keeps
catching in its sweeps — a mechanism that exists, is gated, looks tested, and never
ran — except here it survived four experiments because the *conclusion* was recorded
in prose rather than derived from an arm.

**Corrected status: H2 is UNTESTED, not unsupported.**

### H1's second clause has never been tested either

H1 has two clauses. Clause 1 (multi-frame beats single-frame OOD) has been run
repeatedly. **Clause 2 — that the advantage scales with module *disagreement*, not
module *count* — requires varying module count, and only 1-LM and 5-LM exist.** Two
points cannot separate "scales with count" from "scales with disagreement", and the
pre-registered control for it (near-copy modules, which should buy nothing under H1)
was never built.

The D-index is measured at ≈0.04 on the standard task, so the disagreement axis has
almost no range either. Both terms of the clause are unmeasured.

**Corrected status: H1 clause 1 is criterion-dependent (P8). H1 clause 2 is UNTESTED.**

### What this changes

The project has spent P9, P10 and P11 on the *protocol of exchange* — a genuinely
productive line that produced three replicated findings — while the two clauses the
project was founded on sat unrun. That was not a decision; it was drift.

**Registered now, before either is run**, so the audit cannot be quietly reframed later:

**P12 — H2, the real test.** Arms: `adaptive_weight` off (upstream) vs on, under
`consensus`, on the OOD rotations, 5 seeds. *Prediction:* in-domain-confidence
weighting raises the capture rate and reduces the multi-frame advantage under the
unanimity criterion. *Falsified if* w(t) moves and nothing downstream changes, which
would say the weight is not load-bearing in Monty's vote path.
**Mandatory:** report w(t) trajectories per module. A weight that never leaves w_init
means the arm is dead, and this project has shipped four dead arms already.

**P13 — H1 clause 2.** Module counts 1, 3, 5, 7 crossed with a near-copy control
(modules seeing near-identical patches). *Prediction:* advantage tracks the D-index,
not the module count; near-copies buy nothing. *Falsified if* advantage grows with
count at constant disagreement.

Both are cheap on this hardware and reuse existing mechanisms. **P12 first**: it is
the load-bearing hypothesis per the 2026-08-18 venue decision, and it is one config
flag away from running.

**Publication stays deferred by Nadi's decision, 2026-08-19.**

---

## 2026-08-19 · FULL VERIFICATION PASS (Nadi's instruction, before continuing)

Everything to date re-checked from run output rather than from this file's prose.
`tools/audit_configs.py` is the reusable form of it and exits non-zero if any
finding touches a published number.

### One real bug found, in unreleased P12 code

`AdaptiveWeightExperiment.post_episode` called `super()` **before** reading the
episode's target. Upstream's `post_episode` ends by calling
`env_interface.post_episode()`, which **advances `primary_target` to the next
episode** — upstream flags this itself at `monty_experiment.py:584`. So every
module was scored against the *wrong* episode.

A live smoke run showed it plainly: **all 5 modules marked incorrect while their
MLH matched the target exactly**, driving w(t) down to 0.209 on pure artefact.
After the fix the same run gives **88/100 correct** and weights that rise to 1.88.

**No published result is affected** — P12 has not been run. The gate missed it
because the test stub neutralised `super()`; `test_adaptive_weight.py` now
simulates the target advance and fails if the read moves back after `super()`.
Verified by reintroducing the bug and confirming the gate reports it.

### Everything already published: verified clean

- **Zero findings affecting published numbers.** 46 findings, all in superseded
  or documented runs.
- **The epoch trap does not touch any published result.** The `p7_e1_ood_*_s4X`
  runs with 1 rotation are early, superseded runs; every analyser reads
  `pow_p7_*`, which have **50 episodes over 4 rotations** in all 10 seeds.
- **No unexplained dead arms.** Two identity findings are documented and
  expected: `p6_* max == consensus` **is** P6's own refutation (modules knocked
  off the object, `send_out_vote` None 88% of the time, so no rule had votes to
  reduce), and `cp5_* == e2_08_*` because E2's 0.8 arm *is* the default
  threshold. Confirmed by checking a continuous column, not just outcomes:
  9 of 10 powered P7 seeds distinguish all four arms.
- **One incomplete run, already handled.** `e2_05_e1_ood_consensus_s42` has 30
  episodes of 50; `reports/cp5-results.md` already excludes it and reports that
  threshold as n=1.
- **No config drift.** Committed yaml matches the Hydra config each run used.
- **All verdicts reproduce**: P7 (not significant), P8 (a/b/c supported, plus the
  DuckDB second engine matching all four headline numbers), P9 (a/b/c supported),
  P10 (a/c supported, b n.s., e not supported), P11 (b supported, a n.s.).
- **Gates: 81 assertions + 3 script gates, all pass.**

### Method note on my own audit

My first pass compared `most_likely_evidence`, which is **empty** in these CSVs,
and so reported "SAME WIRING (bug)" for arms that are genuinely different. Caught
by asking why *every* pair matched including `novote`, which cannot be identical
to anything. Comparing an empty column returns identity for free — the audit tool
now checks that the column carries values before drawing a conclusion.

---

## 2026-08-19 · P12 PRE-REGISTRATION — H2's first real test

Registered **before** `tools/run_p12.sh` was run and before any P12 number existed.
H2 has never been tested (see the audit above): `adaptive_weight` was false in 24 of
24 configs and nothing outside the tests ever called `record_episode_outcome`.

**H2 as written in the plan:** *weighting votes by each module's in-domain confidence
destroys the OOD advantage, because a single high-confidence module can capture the
consensus.*

Three arms x 5 seeds x 90 episodes (10 objects x 9 rotations), differing **only** in
what evidence moves the vote weight:

| arm | w(t) learns from | meaning |
|---|---|---|
| `p12_frozen` | nothing (w = w_init) | upstream, and the replication control |
| `p12_ood` | out-of-domain correctness | the polymath design |
| `p12_indomain` | in-domain correctness | **H2's failure mode** |

All under `vote_mode: consensus`: `max` takes the loudest vote regardless of how it was
scaled, so a weight cannot express itself through it and all three arms would be
identical by construction. That is the P10 lesson applied in advance.

**Mixed rotation schedule (5 in-domain + 4 OOD, one per epoch).** P7's OOD-only stream
would never give the `indomain` arm an in-domain episode to learn from, making it a dead
arm indistinguishable from `frozen`. Accuracy is reported on the **OOD subset only**;
the in-domain episodes exist so confidence can accumulate, exactly as H2 describes.

**P12a (the hypothesis).** `p12_indomain` scores WORSE than `p12_frozen` on OOD
episodes under unanimity. *Falsified if* it matches or beats frozen.

**P12b (the mechanism).** Weight spread across modules is HIGHER under `indomain` than
under `ood` — capture means one module getting loud. Measured as max(w)/min(w) at the
end of the run.

**P12c (the polymath direction).** `p12_ood` is no worse than `p12_frozen` on OOD
episodes. This is the constructive claim: earning influence on novel input should not
hurt. *Falsified if* `ood` is significantly worse.

**P12d (replication control — voids the sweep if it fails).** `p12_frozen` must
reproduce P7's powered consensus arm on its OOD episodes within noise. Frozen w(t) is
upstream behaviour, so a difference means the harness changed something else.

**P12e (liveness — not a hypothesis, a precondition).** w(t) must MOVE in both
adaptive arms and must NOT move in `frozen`. Reported from `weight_trace` before any
accuracy number is read. **A frozen trace in an adaptive arm voids that arm**, and this
project has shipped five dead arms already.

**What a null means.** If `indomain` and `ood` and `frozen` all land together, the
finding is that Monty's vote path is insensitive to vote weight at this scale — which,
given that three experiments already found the reduction rule near-irrelevant, would be
a fourth instance of the same pattern and worth stating as such.

**Publication stays deferred by Nadi's decision.**

---

## 2026-08-19 · ANALYSER FLAW FOUND BY VALIDATION (before P12 produced a number)

`tools/analyse_p12.py` had never run on real data, so it was validated the way a
mechanism is: fed synthetic runs whose correct verdict is known in advance
(`tests/test_analyse_p12.py`, three scenarios — H2 true, H2 false, dead arm).

**Scenario 1 failed.** With `indomain` at 1-of-5 modules correct and `frozen` at
5-of-5 — an unmissable effect — the analyser reported:

    P12a: difference -100.00 pp   t(4) = 0.00
    VERDICT: directionally right, n.s.

**Cause.** `paired()` returned `t=0.0` whenever the seed-to-seed standard deviation
was zero. But zero variance with a non-zero mean means *every seed moved by the same
amount*, which is the **strongest** possible evidence, not the weakest. The old code
reported a perfect, perfectly-consistent effect as "not significant".

**Fixed in `analyse_p12.py`, `analyse_p11.py` and `analyse_p10.py`**, which shared the
convention: zero variance with a zero mean stays `t=0`; zero variance with a real
effect returns ±inf, and every caller already compares `|t|` against a threshold.

**No published result is affected.** Checked directly: no P9/P10/P11 contrast on any
reported measure had zero variance with a non-zero mean. P10's and P11's verdicts are
byte-identical after the fix.

This is the second flaw today found in analysis code rather than in a mechanism — the
first being P11's over-claim, which was a reading error. **Config audits do not catch
either.** `tools/run_gates.sh` now runs the analyser validator alongside the mechanism
gates.

---

## 2026-08-19 · P13 SCOPING — the blocker is bigger than "just add seeds"

Checked while P12 ran, so the estimate is from the repo rather than from memory.

**P13 needs 3-LM and 7-LM systems, and neither exists at any level:**

- **Connectivity**: upstream ships `1lm_1sm`, `2lm_2sm`, `5lm_5sm` only. A 3-LM and
  a 7-LM `lm_to_lm_vote_matrix` must be written. The format is simple (each LM lists
  its peers) so this is generatable, not hard.
- **Sensor modules**: `5sm_camera` and `2sm_camera_dist` exist; 3-SM and 7-SM do not.
- **Motor**: `distant_2` and `distant_5` exist; `distant_3` and `distant_7` do not.
- **Pretrained models**: only `pb_indomain_1lm` and `pb_indomain_5lm` exist. **Each
  module count needs its own pretraining run** — the models are not interchangeable
  because a 5-LM model has five per-module graphs.

So P13 is roughly: generate 3 config families x 3 files, run 2 pretraining sweeps,
then run the eval sweep. That is a session of work, not an afternoon of seeds, and it
is worth saying plainly rather than discovering at run time.

**The near-copy control is separate and cheaper.** It needs no new module count: keep
5 LMs and reduce the sensor patch separation so the modules see nearly the same
surface. That directly tests H1's clause — near-copies should buy nothing — and reuses
the existing 5-LM model. **It should be run first**, and it is the honest minimum for
saying anything about H1's second clause.

Note that P6 already moved patch separation in the *opposite* direction (8x wider) and
knocked modules off the object entirely. Narrowing carries the mirror risk, so the
`send_none`% check is mandatory.

---

## 2026-08-19 · P12e LIVENESS VERIFIED ON A REAL ADAPTIVE ARM (mid-sweep)

Recorded before the sweep finished, so it cannot be reframed by whatever the accuracy
numbers turn out to be. The precondition H2 rests on now holds in a live run:

`p12_ood_s42`, 450 trace rows (90 episodes x 5 modules):

| module | final w(t) | OOD-correct rate |
|---|---|---|
| learning_module_0 | 1.839 | 98.9% |
| learning_module_1 | 1.836 | 96.7% |
| learning_module_2 | 1.839 | 96.7% |
| learning_module_3 | **1.438** | **64.4%** |
| learning_module_4 | **1.471** | **70.0%** |

**w(t) moved (1.0 → 1.44–1.84) and it moved in the right direction**: modules 3 and 4
carry the injected noise per the P7 design, and they ended measurably quieter than the
three clean modules. This is the first time in this project that the adaptive weight
mechanism has demonstrably done anything in a real experiment.

The `frozen` arm writes its trace too and stays flat at 1.0 across all 450 rows, so
"never moved" is now provably distinct from "never ran" — the ambiguity that has voided
sweeps here five times.

**This says nothing yet about whether H2 is true.** It says the experiment is capable
of answering it, which is exactly what four previous "H2 not supported" claims could
not say.

---

## 2026-08-19 · P12 OUTCOME — H2 REFUTED, and the sign is inverted

1350 episodes, 3 arms x 5 seeds x 90. **P12d replication control PASSED** (`frozen`
99.00% vs P7's powered consensus 97.80%, +1.20 pp against a ±4.40 pp band).
**P12e liveness verified live before any accuracy number** — w(t) moved in 5/5 seeds
in both adaptive arms, 0/5 in frozen, and tracked per-module OOD accuracy correctly.

| arm | `any` | unanimous | mean corr | conf wrong | w spread |
|---|---|---|---|---|---|
| frozen | 99.00% | 36.50% | 3.960 | 1.00% | 1.00 |
| ood | 97.00% | 48.00% | 4.085 | 2.00% | 1.56 |
| indomain | 97.00% | **58.00%** | **4.325** | 3.00% | 1.49 |

- **P12a NOT SUPPORTED — the sign is inverted.** `indomain` was predicted to score
  WORSE than `frozen` under unanimity. It scores **+21.50 pp BETTER**, t(4)=5.00.
- **P12b NOT SUPPORTED.** Weight spread is marginally *lower* under `indomain`
  (−0.067x, t=−0.58). **No capture signature at all.**
- **P12c SUPPORTED.** `ood` is not worse than `frozen`: +11.50 pp unanimity (t=2.13).

**Not an agreement artefact.** On the threshold-free metric — the same defence P8
needed — `indomain` − `frozen` is **+0.365 modules correct per episode, t(4)=3.61**.
More modules are individually right, not merely more aligned.

**Why H2 fails, and it is the interesting part.** `AdaptiveVoteWeight` is bounded
(`w_min=0.1`, `w_max=2.0`) with an EMA, so no module can run away with the vote — a
1.49x spread is not capture. **H2's failure mode requires an unbounded weight, and the
polymath specification's own "never silence a module, always allow recovery" invariant
— frozen at CP-4 before any accuracy was seen — is what prevents it.** The safety
constraint written for ethical reasons blocks the predicted failure.

**Caveat that must not be lost:** both weighting arms trade 2 pp of `any` for large
unanimity gains, which is the SAME trade P9 found for iterated voting through a
completely different mechanism. That recurrence deserves its own test.

**Standing: H2 REFUTED as stated** (previously recorded as "not supported", actually
never tested). H1 clause 1 criterion-dependent; H1 clause 2 still untested.

**Publication decision remains Nadi's and is not taken.**

---

## 2026-08-19 · P12 CORRECTION — a confound I did not report, found by re-checking

The P12 outcome above was written from the analyser's summary. Re-checking the whole
result afterwards surfaced a design property that belongs in the record.

**The rotation schedule is blocked, not interleaved.** `Predefined` indexes by *epoch*,
so all 50 in-domain episodes run first (epochs 1–5) and all 40 OOD episodes after
(epochs 6–9). Verified from the live weight traces, consistent across all 5 seeds:

    ood      : first weight change at episode 50   (spread 1.209 entering OOD phase)
    indomain : first weight change at episode 0    (spread 1.372 entering OOD phase)

So `indomain` enters the measured OOD phase with weights **already fully
differentiated**, while `ood` differentiates *during* the phase being measured.

**What this invalidates:** any `ood`-vs-`indomain` accuracy ranking, because it
confounds *what the weight learned from* with *when it finished learning*. That was
never a pre-registered prediction — P12b compares weight **spread**, not accuracy — but
the results table invites the inference, so `tools/analyse_p12.py` now prints the
confound and explicitly warns against that reading.

**What this does not touch, and in fact strengthens: the H2 refutation.** H2 predicts
in-domain-trained weights capture the consensus and harm OOD performance. The blocked
order hands `indomain` the **most favourable possible setup** for that mechanism — it
arrives at the OOD phase with a fully in-domain-trained weight — and the predicted harm
still does not appear (unanimity +21.50 pp t=5.00; modules correct +0.365 t=3.61;
confident errors +2.00 pp t=1.63 n.s.). **A confound that favours a hypothesis cannot
explain that hypothesis failing.**

**Full requirement-to-check trace over the finished sweep**, all 15 runs verified at 90
episodes with 9 balanced rotations, the analyser's in-domain set verified equal to both
`pb_pretrain_indomain.yaml` and the P12 configs, and no two arms byte-identical on a
continuous column in any seed:

| requirement | check | observed |
|---|---|---|
| P12a | paired t, 5 shared seeds | +21.50 pp, t=5.00 — NOT SUPPORTED (inverted) |
| P12b | max(w)/min(w) from live traces | −0.067x, t=−0.58 — NOT SUPPORTED |
| P12c | paired t | +11.50 pp, t=2.13 — SUPPORTED |
| P12d | vs P7 powered consensus | 99.00% vs 97.80%, band ±4.40 — PASSED |
| P12e | trace scan per arm | frozen 0/5, ood 5/5, indomain 5/5 — OK |
| not circular | threshold-free metric | +0.365 modules/episode, t=3.61 — SIG |

---

## 2026-08-19 · P13 PRE-REGISTRATION — H1 clause 2, the disagreement axis

Registered **before** `tools/run_p13.sh` was run and before any P13 number existed.
Gated by `tests/test_p13_configs.py`, which was verified by sabotage.

H1 clause 2: *the multi-frame advantage scales with how much the modules DISAGREE
during inference, not with how many modules there are.* **Never tested** — only 1-LM
and 5-LM runs exist, and two points cannot separate the two explanations.

**This experiment tests the disagreement term, not the count term.** The count term
needs 3-LM and 7-LM systems, which upstream does not ship and which each need their own
pretraining run. The disagreement term needs neither: hold the module count at **5** and
vary how much the sensor patches overlap. This is the pre-registered near-copy control —
under H1, modules that are near-copies of each other should buy nothing.

Four arms x 5 seeds x 40 OOD episodes, one variable (patch separation), all reusing
`pb_indomain_5lm`:

| arm | separation | meaning |
|---|---|---|
| `p13_sep000` | 0.000 | all five patches coincide — **true near-copies** |
| `p13_sep0025` | 0.0025 | quarter of stock |
| `p13_sep001` | 0.01 | **STOCK — replication control**, byte-identical to upstream |
| `p13_sep004` | 0.04 | 4x stock, deliberately below P6's failed 0.08 |

**P13a (the hypothesis).** The voting advantage — voting arms minus the single-module
baseline, or here the spread between arms — **grows with separation**. At `sep000` the
five modules are near-copies and voting should buy nothing over one module.
*Falsified if* `sep000` performs the same as `sep001`/`sep004`.

**P13b (the mechanism, and the load-bearing one).** The **D-index rises monotonically
with separation**. If it does not, the manipulation failed and P13a is untestable —
this is the same lesson as P6 and must be checked before any accuracy claim.

**P13c (unanimity).** Unanimity is **highest at `sep000`** and falls with separation.
Near-copies agree trivially; that agreement is not evidence of correctness. This is the
prediction that distinguishes "agreement" from "independent corroboration", which P8,
P9 and P12 have all shown is the axis that matters here.

**P13d (replication control — voids the sweep if it fails).** `p13_sep001` must
reproduce P7's powered max arm within noise. Its environment body is asserted
byte-identical to upstream stock, so a difference means the harness changed something.

**P13e (liveness — a precondition, not a hypothesis).** `send_none`% must stay near the
stock ~63% in every arm. **P6 moved this exact variable to 0.08 and produced silence,
not disagreement: 88% of votes were None.** An arm whose vote path went quiet is not
evidence about disagreement, and 0.04 is chosen below 0.08 for that reason. Reported
from `tools/vote_spy.py` **before** any accuracy number is read.

**What a null means.** If the D-index does not move with separation (P13b fails), the
finding is that *this codebase cannot produce module disagreement by geometry alone* —
which, with P6, would be two independent attempts on the same axis and worth stating as
a property of the substrate rather than of the hypothesis.

**Publication stays deferred by Nadi's decision.**

---

## 2026-08-19 · P13e PRE-SWEEP LIVENESS — the 0.04 arm is unusable, caught before running

Smoke-tested each separation on 1 epoch under `tools/vote_spy.py` **before** launching
the sweep, because P13e is a precondition rather than a hypothesis.

| arm | separation | `send_none`% | verdict |
|---|---|---|---|
| `p13_sep000` | 0.000 | **38.4%** | healthy, well below stock |
| `p13_sep001` | 0.010 (stock) | **60.3%** | matches the known ~63% baseline |
| `p13_sep004` | 0.040 | **83.2%** | **UNUSABLE — this is P6's failure again** |

**`p13_sep004` must be dropped or replaced before the sweep runs.** P6 failed at 0.08
with 88% silence; 0.04 gives 83.2%, which is the same failure mode a little further
down the curve. I picked 0.04 as "deliberately below P6's 0.08" and that reasoning was
wrong — the silence curve is steep, and 4x stock is already past the usable range.

**Had this not been checked first**, the sweep would have produced a clean-looking
`sep004` arm whose vote path was 83% silent, and any "more separation, worse voting"
reading would have been measuring absence rather than disagreement. That is exactly the
P6 lesson, and this is the first time in the project it was caught *before* burning a
sweep instead of after.

**Revised design for the next session:** replace 0.04 with **0.02** (2x stock) and
smoke-test it the same way; keep the arm only if `send_none`% stays near stock. If 0.02
is also unusable, the honest finding is that **this substrate cannot produce module
disagreement by geometry in the widening direction at all** — two independent attempts
(P6 at 0.08, P13 at 0.04) both hitting silence — and the disagreement axis must be
approached through noise (as P7 did) rather than through patch placement.

The narrowing direction is unaffected: `sep000` at 38.4% is the healthiest arm of the
three, so the near-copy half of the design is sound.

**Nothing was swept. No P13 accuracy number exists.**

---

## P14 (E-null) — leave-one-out: is unanimity about truth, or about coordination?

**Pre-registered 2026-08-20, before the held-out model is pretrained and before
any number exists.** Reasoning: `reports/reconsideration-consensus.md`.

### The question

Nadi's critique: *a consensus does not need to be true. Given four alternatives
that are all wrong and no option to abstain, agreeing is the rational move,
because dissent costs something and buys nothing.*

Every experiment in this project so far evaluates objects that are **in the
pretrained set** — verified: `train_distinctobj_predefined.yaml` and
`eval_distinctobj_random.yaml` carry the identical 10-object list. The correct
answer has always been available. **This is the first run where it is not.**

### Design

- Pretrain 5 LMs on **9 objects**, holding out `dice` — chosen because P4's
  false-consensus episode was `dice`, so the same object that produced 5-correct
  → 5-wrong under voting is now the impossible one.
- Evaluate on the held-out object only. Every module must answer; **none can be
  correct**, because the target is absent from every module's graph memory.
- Arms: `max` (upstream vote) vs `novote`, 5 seeds each, same rotations as P7/P8.

### Predictions, in order of how much they would change the project

**P14a — unanimity stays well above zero on an impossible target.**
Concretely: **≥ 15% unanimous** under voting. If modules converge on one wrong
label when correctness is unavailable, unanimity measures **coordination**, and
every unanimity number in this project carries that component.

**P14b — voting raises agreement on the impossible target relative to novote.**
This is the load-bearing one. Under `novote`, five independent modules guessing
among 9 wrong labels should rarely agree. If voting lifts that materially, the
mechanism manufactures consensus **independently of truth**, which is exactly
Nadi's claim.

**P14c — `send_none`% does not explain the result.** Reported alongside every
number. If modules simply go silent rather than agreeing, that is absence, not
consensus, and P14a/b are void (the P6 lesson).

### What refutes the critique

**Unanimity collapses to near zero (< 5%) and voting does not raise it.** That
would mean agreement in this substrate requires a correct attractor, consensus
here does track truth, and H1's read-out is sounder than the reconsideration
argues.

### Controls, mandatory

1. **Replication control:** the same held-out model evaluated on a **trained**
   object must reproduce known accuracy (~97% `any`). If it does not, the
   9-object pretraining is broken and the sweep is void.
2. **Impossibility control:** accuracy on the held-out object must be **exactly
   0%** under every criterion. Any non-zero correctness means the object leaked
   into training and the run means nothing.
3. **Episode count asserted** per run; run directory cleared first (Monty
   appends).
4. **`send_none`% reported** per arm.

### Committed before the run

No P14 number exists at the time of this commit. The pretraining has not been
launched.

### P14 addendum — an upstream numerical failure on seed 42, found during the run

**Recorded 2026-08-20 while the sweep was still running, before any verdict.**

`p14_holdout_max_s42` and `p14_holdout_novote_s42` both exit rc=1 after **3 of
4 episodes**. Diagnosed with `HYDRA_FULL_ERROR=1`:

```
sensor_processing.py:444, surface_normal_total_least_squares
  assert np.isreal(eig_val).all() and np.isreal(eig_vec).all()
AssertionError
```

**This is upstream's code, not ours, and not a config error.** The total
least-squares surface-normal estimator asserts its eigendecomposition is real;
on one viewpoint of the held-out object it returns complex values. It is
deterministic — the same seed fails identically on both arms, which is what
identifies it as a *viewpoint* property rather than randomness.

**How it is handled, decided before seeing the numbers:** seed 42 contributes
3 episodes instead of 4 on both holdout arms. Because it fails **identically on
both arms**, dropping it does not favour either side of the P14b contrast. The
analysis will report both: n=5 with seed 42's 3 episodes, and n=4 with seed 42
excluded. **If those two disagree, the disagreement is the finding and no
verdict is claimed.**

Written down rather than silently dropped: a skipped run with no reason reads
as coverage.

---

## P15 — four held-out objects: is the attractor coordination, or a shared prior?

**Pre-registered 2026-08-20, before the six-object model is pretrained and
before any number exists.** Follows P14 (`reports/p14-enull.md`), which found
90.00% unanimity on an impossible target with **83.33% present without voting
at all**.

### What P14 left open

P14 used one held-out object and the modules converged on `golf_ball` — but
`dice` and `golf_ball` are both small and round, so "they agreed because the
object genuinely resembles golf_ball" is not excluded. **One object cannot
distinguish a coordination effect from a perceptual-similarity effect.**

### Design

Hold out **four** objects chosen to differ in shape, so a single similarity
story cannot explain all four:

| held out | shape | plausible nearest trained object |
|---|---|---|
| `dice` | small cube | `golf_ball` (P14's observed attractor) |
| `banana` | long curved | `spoon` |
| `mug` | handled cylinder | `bowl` |
| `strawberry` | small tapered | `golf_ball` |

Pretrain 5 LMs on the remaining **six**: `bowl`, `potted_meat_can`, `spoon`,
`mustard_bottle`, `golf_ball`, `c_lego_duplo`. Arms `max` and `novote`, 5 seeds,
4 rotations, as P14.

### Predictions

**P15a — unanimity stays high on every held-out object.** ≥60% mean across the
four, and **no object below 25%**. A single low object would show P14's result
depends on which object is held out.

**P15b (the discriminating one) — each held-out object gets its OWN attractor,
and the attractors differ from each other.** If all four converge on the *same*
label, that is a fixed architectural bias, not object-driven similarity. If each
converges on a *different* plausible neighbour, the modules are doing genuine
perceptual matching and agreeing because they share a prior — which is still
Nadi's point, but a different mechanism from coordination, and it must be
reported as such.

**P15c — the no-vote arm stays close to the voting arm**, replicating P14's
central surprise: the agreement does not come from conferring. Predicted gap
< 10 pp.

### What would refute P14's reading

Unanimity collapses on the three *new* held-out objects and only `dice` was
unanimous. That would mean P14 measured a `dice`/`golf_ball` coincidence and
the general claim does not hold.

### Controls, mandatory

1. **Impossibility:** accuracy on each held-out object exactly 0%.
2. **Replication:** a trained object must still score normally on the SIX-object
   model. A model trained on six may be weaker; if the control drops materially
   below P14's 100%, that is reported and the comparison to P14 is qualified.
3. **`send_none`%** reported per arm and per object.
4. **Per-object breakdown mandatory** — a mean over four objects can hide one
   object at 0% and three at 80%.

### Committed before the run

No P15 number exists at the time of this commit. The six-object pretraining has
not been launched.
