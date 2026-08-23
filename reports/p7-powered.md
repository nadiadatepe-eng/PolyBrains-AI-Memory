# P7 — H2's real test, properly powered

**Date:** 2026-08-19 · **Sha:** `0c81b1f` · 4 arms × 10 seeds × 50 episodes = **2000 episodes**
Pre-registered as P7a/P7b in `PREDICTIONS.md`, commit `2f931cb`, **before these runs existed**.
Data integrity: 40/40 runs complete, 50 episodes each, **zero truncated**.

**Result: H2 is not supported. H1 is refuted with a significant effect in the opposite
direction. Not voting beats every voting rule.**

---

## 1. The task, and why it is finally valid

P6 failed because spreading sensors silenced voting rather than stressing it. P7 keeps every
patch at the stock 0.01 separation and instead injects 5–10x noise into **modules 3 and 4
only**. Verified at the mechanism before use:

| task | `send_out_vote` → `None` | receipts effective |
|---|---|---|
| stock | 63% | 92% |
| P6 spread (broken) | **88%** | 22% |
| **P7 noise** | **60%** | **68%** |

The vote path is live. Clean modules score 8–9/10, noisy modules 5–6/10, and modules name
different objects in ~6/10 episodes. **This is genuine disagreement among modules that are all
voting** — the first such task in the project.

## 2. Results

| arm | accuracy | sd | failure correlation |
|---|---|---|---|
| `max` (upstream default) | 97.00% | 1.41 | 5.1% (15/295) |
| `mean` (control) | 97.40% | 2.32 | 4.3% (13/303) |
| `consensus` (ours) | 97.80% | 2.20 | 3.7% (11/299) |
| **no voting** | **99.80%** | 0.63 | **0.2% (1/446)** |

## 3. Verdicts against the pre-registration

**P7b — consensus beats max on accuracy: NOT SUPPORTED.**
Paired by seed (arms share seeds, so pairing is required): **+0.80 pp, sd 2.35, t(9) = 1.08**,
critical |t| = 2.262. Consensus wins 4 seeds, loses 1, ties 5. Directionally right, not
significant.

**P7a — consensus lowers failure correlation: NOT SUPPORTED.**
5.1% → 3.7%, two-proportion z = 0.84, n.s. Directionally right, not significant.

**The control behaved as designed.** `mean` gained only +0.40 pp, so plain averaging does not
explain the (non-significant) consensus gain. Had P7b been significant, the control would have
supported an agreement-weighting interpretation. It was not, so this is moot.

**H1 — voting helps OOD: REFUTED, significantly.**
No voting beats `max` by **+2.80 pp, paired t(9) = 4.58, p < 0.05.** This is the only
significant accuracy effect in the entire study, and it points against the project's founding
hypothesis.

## 4. An analysis error I made and corrected

My first analysis script used `sd/√n` as the comparison threshold and printed
"P7b: **SUPPORTED**" at +0.80 pp against a 0.64 pp threshold.

**That was wrong.** The arms share seeds, so the correct test is a paired t-test on per-seed
differences, which gives t = 1.08 — not significant. The script now performs the paired test
and carries a comment recording the earlier mistake.

Had I not re-checked, this report would have claimed support for H2 that the data does not
provide. Recorded because the error is instructive: a lenient threshold chosen before seeing
data is still a lenient threshold.

## 5. The one robust finding

Across every task with a live vote path, **Monty's voting mechanism costs accuracy and creates
correlated failure**:

| task | no-voting vs voting-on | correlation, voting on → off |
|---|---|---|
| stock (P4) | +4.0 pp | 29% → 0% |
| noisy subset (P7) | **+2.80 pp, p<0.05** | 5.1% → **0.2%** |

Voting does not reduce how often individual modules fail. In P7 it reduced the number of
episodes with any failure (295 vs 446) while **increasing the number where all modules failed
together** (15 vs 1). Under `AnyLMsMatch`, independent failures are survivable and correlated
ones are fatal, so the trade is a bad one.

This is precisely what CP-1's `np.ma.max` finding predicts: the loudest single vote captures
the consensus, and one confident error propagates to every module.

## 6. Limits, stated plainly

1. **All arms are near ceiling** (97–99.8%). Effects are compressed into a 3 pp band, and the
   no-voting arm has almost no room to lose. A harder task could reverse the ranking.
2. **10 objects, one object per episode, MuJoCo only.** Voting exists in Monty largely for
   ambiguous and multi-object scenes; this is not such a task. **The claim is about this
   regime, not about voting in general.**
3. **`AnyLMsMatch` favours independent modules by construction.** With a unanimity criterion,
   voting might win. We did not test that, and it is the most obvious threat to the
   interpretation.
4. **Our consensus rule may simply be the wrong rule.** Its failure to beat `max` significantly
   is evidence about this implementation, not about consensus aggregation in principle.

## 7. Where the project stands

| | Verdict |
|---|---|
| **H1** multi-frame voting helps OOD | **Refuted** (+2.80 pp against, p<0.05) |
| **H2** confidence weighting destroys the advantage | **Not supported.** There is no advantage to destroy; both P7a and P7b are directionally right and non-significant. |

**Publishable content that does not depend on either hypothesis:**

1. A source-level analysis of Monty's aggregation showing it is winner-take-all
   (`np.ma.max`), with the weighting commented out (CP-1).
2. A measured demonstration that this aggregation **creates correlated failure**, reproduced
   on two independent tasks, significant on the powered one.
3. Working instrumentation (D-index, capture rate, `vote_spy`) that Monty lacks.
4. Two methodological cautions: disagreement and absence are indistinguishable in output
   statistics (P6), and `eval_stats.csv` rows are per-module not per-episode (CP-5).

## Reproduce

```bash
python3 ~/PolyBrains/tools/analyse_p7.py
```
