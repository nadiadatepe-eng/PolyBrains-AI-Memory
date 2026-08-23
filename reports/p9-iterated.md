# P9 — Iterated voting: vote, then vote on the result of that vote

**Nadi's question, 2026-08-19.** Pre-registered at `0d9b386` before the mechanism was
built. Mechanism fixed and verified live at `203c6f3`. 3 arms × 5 seeds × 40 episodes
= 600 episodes.

Reproduce:

```bash
bash tools/run_p9.sh                                       # ~75 min
upstream/tbp.monty/.venv/bin/python tools/analyse_p9.py
upstream/tbp.monty/.venv/bin/python tests/probe_p9_dead_rounds.py   # liveness
```

## Result: all four predictions supported

| rounds | `any` (≥1 of 5) | `majority` (≥3) | `unanimous` (5 of 5) | mean modules correct |
|---|---|---|---|---|
| 1 | **96.50%** | 93.50% | 43.50% | 4.050 |
| 2 | 94.50% | 92.50% | 66.00% | 4.335 |
| 3 | 90.50% | 88.50% | **79.00%** | 4.340 |

- **P9a supported** — unanimity rises 43.50 → 66.00% from one round to two,
  **+22.50 pp, t(4)=10.76**.
- **P9b supported** — the gain saturates: +22.50 pp then +13.00 pp.
- **P9c supported** — agreement rises monotonically; 5-of-5 episodes go
  87 → 132 → 158 of 200.
- **P9d supported** — under `AnyLMsMatch` iteration *hurts*, and worsens per round:
  −2.00 pp then −4.00 pp (t=−2.36).

**Control passes:** `rounds=1` reproduces P7's max arm within noise
(+0.10 pp, t=0.15).

## What it means

**Iterated voting buys agreement and pays for it in independence, and the exchange
rate is steep.** Three rounds convert a 6 pp loss under `any` into a **+35.50 pp gain
under unanimity**. Nothing here is free: the same mechanism moves both numbers in
opposite directions, which is the sharpest demonstration yet of P8's point that the
scoring criterion decides whether voting looks good or bad.

Note `mean modules correct` saturates hard — 4.050 → 4.335 → 4.340. Round 3 adds
almost nothing on the threshold-free metric while still adding 13 pp of unanimity.
That is consistent with round 3 pushing already-agreeing modules over the 5-of-5 line
rather than making more modules correct.

## Not a dead mechanism, and not module dropout

Both failure modes that have bitten this project before were checked *before* the
numbers were believed:

- **Evidence really moves:** round 1 shifts 23,634 total evidence; rounds 2+3 shift
  43,685 more (184.8% of round 1). `tests/probe_p9_dead_rounds.py`.
- **`send_none` is flat at 53.8% in every round** (922 voting, 1073 silent, identical
  across rounds 1/2/3). Modules are *not* falling silent as rounds increase, so the
  convergence is real consensus and not P6's dropout artefact.

## Two voided sweeps before this one

Recorded because the failures are more instructive than the result.

1. **`n_eval_epochs=1`** (`bc65468`). `Predefined.__call__` indexes rotations by
   *epoch*, so only the first of four OOD rotations was evaluated: 10 episodes per
   run instead of 40. Completed without error, produced clean-looking numbers.
2. **Wrong `_vote` overridden** (`203c6f3`). The subclass transcribed
   `monty_base.py:302`, but `MontyForGraphMatching` overrides `_vote` at
   `graph_matching.py:389` and that is what runs. The real one calls
   `_combine_votes()`, which transforms votes into the receiver's reference frame.
   Skipping it meant **no votes were delivered in any round, including `rounds=1`** —
   73 minutes of compute producing an entirely dead mechanism, again with no error.

**Both were caught by the pre-registered replication control**, not by inspection:
`rounds=1` came out +3.60 pp from P7 instead of ~0. Without that control, the second
sweep would have been reported as "iterated voting changes nothing" — a clean,
plausible, completely false null.

The gate now includes a structural check: our `_vote` must call every helper the real
parent calls, and the parent defining `_vote` must be `MontyForGraphMatching`. That
check fails on the old code.

## Threats

- 5 seeds, not 10 as in P7/P8 — t(4) needs |t|>2.776, and P9d's first step (t=−1.63)
  does not clear it individually though the trend does.
- Still single-object episodes.
- `rounds=3` is the largest tested; where the saturation actually stops is unknown.
- Unanimity on 5 modules where 2 are deliberately noised remains a demanding
  criterion, and the defence is the threshold-free metric, not the unanimity number.

**Publication decision remains Nadi's and is not taken.**
