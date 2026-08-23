# P12 — H2's first real test: refuted, and in the opposite direction

**Run 2026-08-19. 1350 episodes, 3 arms x 5 seeds x 90 episodes (40 OOD + 50 in-domain).
Pre-registered at `9c57278` before any number existed. Certified by P12d.**

## What H2 said, and why this is the first test of it

H2: *weighting votes by each module's in-domain confidence destroys the OOD advantage,
because a single high-confidence module can capture the consensus.* It was the
**load-bearing** hypothesis per the 2026-08-18 venue decision.

**It had never been run.** `adaptive_weight` was `false` in 24 of 24 configs and
`record_episode_outcome` — the only path by which w(t) can move — was called nowhere
outside the tests. Four experiments recorded "H2 not supported" from prose describing
*other* experiments: E2 varied a threshold, P7/P8 compared reduction rules.

Three arms differing **only** in what evidence moves the vote weight:

| arm | w(t) learns from | role |
|---|---|---|
| `frozen` | nothing | upstream, and the replication control |
| `ood` | out-of-domain correctness | the polymath design |
| `indomain` | in-domain correctness | **H2's failure mode** |

## P12e — liveness, checked before any accuracy number

| arm | w(t) moved | mean spread |
|---|---|---|
| frozen | **0/5 seeds** | 1.00 |
| ood | **5/5 seeds** | 1.56 |
| indomain | **5/5 seeds** | 1.49 |

And it moved *correctly*. In `p12_ood_s42` the final weights track each module's OOD
accuracy exactly as designed:

| module | final w(t) | OOD-correct |
|---|---|---|
| LM_0 | 1.839 | 98.9% |
| LM_1 | 1.836 | 96.7% |
| LM_2 | 1.839 | 96.7% |
| **LM_3** | **1.438** | **64.4%** |
| **LM_4** | **1.471** | **70.0%** |

Modules 3 and 4 carry the injected noise per the P7 design, and they ended measurably
quieter. **This is the first time the adaptive weight mechanism has demonstrably done
anything in a real experiment in this project.**

## Results (OOD episodes only, 40 of 90 per run)

| arm | `any` | unanimous | mean corr | unan prec | conf wrong | w spread |
|---|---|---|---|---|---|---|
| frozen | **99.00%** | 36.50% | 3.960 | 97.49% | 1.00% | 1.00 |
| ood | 97.00% | 48.00% | 4.085 | 95.99% | 2.00% | 1.56 |
| indomain | 97.00% | **58.00%** | **4.325** | 94.92% | 3.00% | 1.49 |

**P12d REPLICATION CONTROL PASSED** — `frozen` gives 99.00% against P7's powered
consensus 97.80%, +1.20 pp inside a ±4.40 pp band. Sweep certified.

## Verdicts

- **P12a NOT SUPPORTED, and the sign is inverted.** `indomain` was predicted to score
  *worse* than `frozen` under unanimity. It scores **+21.50 pp better** (t(4)=5.00).
- **P12b NOT SUPPORTED.** Weight spread was predicted higher under `indomain`; it is
  marginally *lower* (−0.067x, t=−0.58, n.s.). **No capture signature.**
- **P12c SUPPORTED.** `ood` is not worse than `frozen` — it is +11.50 pp on unanimity
  (t=2.13). The constructive claim survives.

## Is the unanimity gain just more agreement on wrong answers?

That is the obvious objection, and it is the same one P8 had to answer. **No.** On the
threshold-free metric, which cannot be gamed by agreement:

| contrast | mean modules correct | t(4) |
|---|---|---|
| `indomain` − `frozen` | **+0.365** | **3.61 SIG** |
| `ood` − `frozen` | +0.125 | 1.03 n.s. |

More modules are individually right, not merely more aligned. The cost side is real
but not significant at n=5: confident errors +2.00 pp (t=1.63) and `any` −2.00 pp
(t=−1.63).

## A confound I did not report initially, found by re-checking the whole result

**The rotation schedule is blocked, not interleaved.** `Predefined` indexes rotations
by *epoch*, so all 50 in-domain episodes run first (epochs 1–5) and all 40 OOD episodes
after (epochs 6–9). That means the two adaptive arms adapt in different phases:

| arm | first weight change | spread entering the OOD phase | spread at end |
|---|---|---|---|
| `ood` | episode **50** | 1.209 | 1.279 |
| `indomain` | episode **0** | **1.372** | 1.372 |

`indomain` enters the measured OOD phase with weights **already fully differentiated**;
`ood` enters it at 1.0 and differentiates *during* the phase being measured.

**What this invalidates:** any `ood`-vs-`indomain` accuracy ranking. That comparison
confounds *what the weight was trained on* with *when it finished training*. It was
never a pre-registered prediction — P12b compares weight **spread**, not accuracy — but
it must not be read out of the results table either.

**What this does not touch, and in fact strengthens:** the H2 refutation. H2 predicts
that in-domain-trained weights capture the consensus and harm OOD performance. The
blocked schedule hands `indomain` the **most favourable possible setup** for that
mechanism: it arrives at the OOD phase with a fully in-domain-trained weight. The
predicted harm still does not appear — unanimity +21.50 pp (t=5.00), modules correct
+0.365 (t=3.61), confident errors +2.00 pp (t=1.63, n.s.). **A confound that favours
the hypothesis cannot explain the hypothesis failing.**

## Reading

**H2 is refuted as stated.** In-domain-confidence weighting did not capture the
consensus and did not destroy the multi-frame advantage. It **improved** the number of
modules reaching the right answer.

The likely reason is visible in the mechanism: `AdaptiveVoteWeight` is bounded
(`w_min=0.1`, `w_max=2.0`) and driven by an EMA, so no module can run away with the
vote — a 1.49x spread is not capture. **H2's failure mode requires an unbounded weight,
and the polymath specification's own "never silence a module" invariant, frozen at CP-4
before any accuracy was seen, is what prevents it.** That is a satisfying result: the
safety constraint written for ethical reasons turns out to be the thing that blocks the
predicted failure.

**A caveat that must not be lost.** Both weighting arms lose 2 pp of `any` accuracy
while gaining unanimity, which is the *same trade* P9 found for iterated voting. That
this appears again through a completely different mechanism is worth its own test.

## Standing

- **H2: REFUTED as stated** (was: never tested). The mechanism works, and the predicted
  harm does not occur under a bounded weight.
- H1 clause 1: criterion-dependent (P8). H1 clause 2: still untested (P13).
- **Publication decision is Nadi's and is not taken.**
