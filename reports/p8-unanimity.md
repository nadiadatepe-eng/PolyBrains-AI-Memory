# P8 — The unanimity criterion overturns the H1 refutation

**Run 2026-08-19.** Pre-registered at `5e363dc` before any number below was computed.
No new episodes: this re-scores the existing P7 data (40 runs × 50 episodes = 2000
episodes, `a88c029`), so nothing about the runs can have been tuned to the outcome.
Only the read-out changes.

Reproduce:

```bash
upstream/tbp.monty/.venv/bin/python tools/analyse_p8.py
upstream/tbp.monty/.venv/bin/python tools/analyse_p8_circularity.py
```

## The objection this tests

Every result so far scored an episode correct under upstream's `AnyLMsMatch`: correct if
**any** of 5 modules reached a correct terminal state. That criterion rewards module
*independence by construction* — five independent modules get five lottery tickets, and
voting, which makes modules agree, throws tickets away. So "voting harms accuracy" may
have been a statement about the scoring rule rather than about voting. It was the most
obvious reviewer objection to P7, and it was untested.

## Result

| arm | `any` (≥1 of 5) | `majority` (≥3) | `unanimous` (5 of 5) |
|---|---|---|---|
| `max` (upstream) | 97.00% | 94.40% | **41.00%** |
| `mean` (control) | 97.40% | 94.60% | 39.40% |
| `consensus` (ours) | 97.80% | 95.00% | 40.20% |
| **no voting** | **99.80%** | 94.60% | **10.80%** |

Paired t-test on per-seed differences, n=10 seeds, no voting − max:

| criterion | difference | t(9) | verdict |
|---|---|---|---|
| `any` | **+2.80 pp** | 4.58 | significant — voting *harms* |
| `majority` | +0.20 pp | 0.13 | n.s. |
| `unanimous` | **−30.20 pp** | **−14.40** | significant — voting *helps* |

Under unanimity, no-voting loses **10 of 10 seeds**. All three pre-registered
predictions supported, including monotonicity: +2.80 → +0.20 → −30.20.

## The result is criterion-dependent, and that is the finding

**H1's refutation does not survive.** It was reported as "voting harms OOD accuracy".
The honest statement is now:

> Under `AnyLMsMatch`, voting costs 2.80 pp. Under unanimity, voting gains 30.20 pp.
> The sign of the effect is set by the scoring rule, not by voting.

The 30.20 pp effect is an order of magnitude larger than the 2.80 pp effect the project's
headline claim rested on.

## Is the flip circular? No — and this had to be checked

Unanimity rewards agreement; voting manufactures agreement. Swapping one biased criterion
for its mirror image would be no progress at all. The discriminating test is a metric with
**no threshold**: mean modules-correct per episode, which cannot favour either read-out.

| arm | 0 | 1 | 2 | 3 | 4 | 5 | mean correct |
|---|---|---|---|---|---|---|---|
| `max` | 15 | 2 | 11 | 103 | 164 | **205** | **4.028** |
| `mean` | 13 | 4 | 10 | 108 | 168 | 197 | 4.010 |
| `consensus` | 11 | 4 | 10 | 110 | 164 | 201 | 4.030 |
| no voting | 1 | 5 | 21 | **261** | 158 | 54 | **3.464** |

Paired against no voting: `max` **+0.564 modules/episode, t(9)=15.11**, significant.
Per-episode, voting **lifts 277 episodes and drags 75, net +202**, with **zero** 5→0
collapses.

Voting is propagating correct evidence, not merely copying. Agreeing on a *wrong* answer
scores zero under unanimity, so a gain in fully-correct episodes cannot be explained by
agreement alone.

## What this does to the earlier findings

- **"Voting creates correlated failure" needs restating.** Under `any`, all-fail episodes
  rose 1 → 15. That is real and reproduced here (no voting has 1 episode at 0 correct,
  `max` has 15). But voting simultaneously moves 261 three-correct episodes up into four-
  and five-correct. Reporting the tail without the bulk was one-sided: the same mechanism
  produces both, and the net on mean correctness is strongly positive.
- **H2 remains not supported and is unaffected.** `consensus` (40.20%) does not beat `max`
  (41.00%) under unanimity either. The three voting rules stay within 1.6 pp of each other
  under every criterion, while voting-vs-no-voting moves 30 pp. **Whether you vote matters
  enormously; which rule you use barely matters at all.**

## Threats that remain

- Still a single object per episode. Monty's voting targets ambiguous multi-object scenes.
- `any` and `majority` are near ceiling (94–99.8%); only `unanimous` has range.
- All three voting rules being nearly identical is itself unexplained and is the obvious
  next question.
- Unanimity on 5 modules where 2 are deliberately noised is a demanding criterion; a
  reviewer may argue it is as arbitrary as `AnyLMsMatch`. The defence is the threshold-free
  metric above, not the unanimity number.

**The correct framing for the paper is no longer "voting harms" but "the measured value of
voting is dominated by the choice of read-out, and that choice was never argued for" —
which is a more useful result and a harder one to dismiss.**

**Publication decision remains Nadi's and is not taken.**
