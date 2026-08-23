# P10 — Parliamentary voting: the structure works, the opposition does not

**Nadi's design, 2026-08-19.** Pre-registered at `5b8d64f` before the mechanism was
built. 3 arms × 5 seeds × 40 episodes = 600 new episodes, plus P9's two arms as
controls. Mechanism gated (`tests/test_parliament.py`, 11 checks) and verified live
before the sweep.

Reproduce:

```bash
bash tools/run_p10.sh                                        # ~90 min
upstream/tbp.monty/.venv/bin/python tools/analyse_p10.py
```

## Result

| arm | `any` | all-5 agree | mean correct | precision of agreement | **confident errors** |
|---|---|---|---|---|---|
| plain-1 (one exchange) | 96.50% | 45.00% | 4.050 | 96.59% | 1.50% |
| **plain-3** (three plain rounds) | 90.50% | **87.00%** | 4.340 | 90.84% | **8.00%** |
| **parl-3** (propose→oppose→oppose) | 96.50% | 38.50% | 3.955 | 94.31% | **2.50%** |
| parl-noopp (same phases, no opposition) | 96.50% | 52.50% | 4.100 | 96.14% | 2.00% |
| parl-batch (opposition, no sequencing) | 99.50% | 31.00% | 3.930 | 98.57% | 0.50% |

A **confident error** is an episode where all five modules name the *same* object and
that object is *wrong* — measured from `most_likely_object`, not inferred.

### Pre-registered verdicts

- **P10a SUPPORTED.** `parl-3` has **−5.50 pp fewer confident errors** than `plain-3`
  (8.00% → 2.50%), **t(4)=−3.77**. The design does prevent the failure it was aimed at.
- **P10b directionally right, not significant.** Precision of agreement +3.47 pp
  (90.84% → 94.31%), t=1.47.
- **P10c SUPPORTED.** `parl-3` reaches agreement far less often, −43.00 pp,
  **t(4)=−12.04**. Opposition is friction, exactly as predicted.
- **P10d — the control that decides the interpretation.** `parl-noopp` (identical
  phase structure, *no* opposition) is statistically indistinguishable from `parl-3`
  on every measure: confident errors +0.50 pp (t=0.34), precision −1.83 pp (t=−0.65),
  agreement −14.50 pp (t=−2.61, n.s. at t(4) crit 2.776).
- **P10e NOT SUPPORTED.** Sequential vs batch: +5.50 pp, t=1.12.

## What this means, stated plainly

**Nadi's structure delivers what it promised: three rounds of plain iteration
quadruple confident errors (1.5% → 8.0%), and the parliamentary structure holds them
at 2.5% while keeping `any`-accuracy at 96.50% instead of P9's 90.50%.** Against
`plain-3` at equal exchange count, that is a real and significant win.

**But the devil's advocate contributes nothing.** `parl-noopp` — the same phases with
every module voting its honest best — performs the same or slightly better. So the
benefit comes from **who speaks when**, not from anyone arguing against the majority.

The honest one-line summary: *staged, few-speakers-at-a-time voting resists false
consensus; adversarial content does not add to it.*

## Why the opposition failed, and it is not the idea's fault

Two mechanism findings explain it, both verified rather than assumed:

**1. `np.ma.max` cannot represent dissent.** The reduction takes the loudest vote in
a hypothesis' neighbourhood (`learning_module.py:938`, confirmed at the pinned sha).
A devil's advocate argues its *runner-up*, which by construction carries **lower**
evidence than what the majority argues. Under a max rule a lower number is simply
discarded. The opposition was not ignored by accident — **the aggregation rule has no
channel through which opposition can be expressed.** This was registered as the
mechanism risk in `PREDICTIONS.md` before the run.

**2. "One by one" made every phase single-speaker.** Instrumenting the live path
(`(modules arguing, modules supplying pose)` per delivery) shows **at most one module
ever argues per exchange** — 2180 delivery events, none with more than one arguer.
Sequential mode splits the propose phase into three separate one-speaker exchanges
too. That is a faithful reading of Nadi's "one by one", but it means `parl-3` is not
"three propose, then one challenges" — it is five consecutive single-speaker
exchanges, two of which argue a runner-up. **The phase labels are weaker than they
look, and the measured effect is about speaker count per exchange.**

This also explains `parl-batch`, which looks best on paper (0.50% confident errors,
98.57% precision): batching collapses the propose phase to one exchange, so the whole
arm is only three exchanges. It buys safety by doing less voting, not by arguing
better.

## What would test the opposition idea properly

The idea is not refuted; it was tested through a rule that cannot carry it.

1. **Give dissent a channel.** Run the parliament with `vote_mode="consensus"` (ours,
   already built) instead of `max`. Agreement-weighted reduction can in principle
   represent opposition; max cannot. **This is the obvious next run and it is cheap.**
2. **Try the veto reading** — opposition sends *negative* evidence against the leading
   hypothesis, rather than arguing a runner-up. Under max, negative evidence still
   loses; under consensus it need not.
3. **Separate speaker-count from phase-structure**, since P10 confounds them: a
   3-speakers-at-once propose phase followed by single-speaker challenges would
   isolate what the phases actually contribute.

## Threats

- 5 seeds; t(4) needs |t|>2.776, so only the two large effects clear it.
- P10d is a null used to interpret a positive result. It is a *failure to detect* a
  difference, not proof of no difference; with 5 seeds the −14.50 pp agreement gap
  (t=−2.61) is suggestive and underpowered.
- Single-object episodes throughout.

**Publication decision remains Nadi's and is not taken.**
