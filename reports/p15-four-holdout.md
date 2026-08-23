# P15 — four held-out objects: the attractor is perceptual, and P14 overstated

**Run 2026-08-20.** Pre-registered at `801412e` before the six-object model was
pretrained. Follows `reports/p14-enull.md`.

Reproduce:

```bash
python3 tools/make_p15_configs.py
PYTHONPATH=src upstream/tbp.monty/.venv/bin/python tests/test_p15_configs.py
bash tools/run_p15.sh
upstream/tbp.monty/.venv/bin/python tools/analyse_p15.py
```

## What P14 left open

P14 held out one object, `dice`, and the modules converged on `golf_ball` 92
times in 94. But both are small and round, so *"they agreed because `dice`
genuinely resembles `golf_ball`"* was never excluded. **One object cannot
separate coordination from perceptual similarity.**

P15 holds out four, chosen to differ in shape: `dice` (cube), `banana` (long
curve), `mug` (handled cylinder), `strawberry` (small taper). Pretrained on the
remaining six; all four verified absent from LM_0's graph memory by reading
`model.pt`.

## Result

Controls first: **C1** every held-out arm exactly 0.00% correct, **C2** the
trained-object control 100.00%, **C3** `send_none` 0.00%. The six-object model
is not weaker than P14's nine-object one, so the comparison holds.

| held out | max unanimity | novote | gap | attractor (max arm) |
|---|---|---|---|---|
| `dice` | 95.00% | 75.00% | +20.00 | `golf_ball` 94/95 |
| `banana` | **35.00%** | 20.00% | +15.00 | `mustard_bottle` 78/100 |
| `mug` | **20.00%** | 35.00% | −15.00 | `bowl` 37/100 |
| `strawberry` | **100.00%** | 100.00% | +0.00 | `golf_ball` 100/100 |
| **mean** | **62.50%** | 57.50% | +5.00 | — |

## Verdicts

**P15a NOT SUPPORTED.** Predicted ≥60% mean *and no object below 25%*. The mean
is 62.50%, which clears its bar — but `mug` is at **20.00%**, which fails the
per-object floor. **The compound prediction fails, and it fails on exactly the
clause that was written to stop a mean from hiding an object.**

Had P15 reported only the mean, it would have read as a clean replication of
P14. The per-object breakdown was made mandatory in the pre-registration for
this reason, and it earned its place on the first run.

**P15b SUPPORTED — and this is the finding.** Three distinct attractors across
four objects:

| held out | converged on | plausible? |
|---|---|---|
| `dice` | `golf_ball` | small, compact |
| `banana` | `mustard_bottle` | **long, tapered** |
| `mug` | `bowl` | **open vessel** |
| `strawberry` | `golf_ball` | small, rounded |

The modules do not have one fixed fallback answer. **Each unseen object is
mapped to its nearest trained neighbour**, and the mapping is perceptually
sensible in every case — `banana` to the other long object, `mug` to the other
vessel, not to `golf_ball`.

**P15c SUPPORTED, replicating P14's central surprise.** Voting adds +5.00 pp
over no voting (t=0.63, n.s.), inside the ±10 pp band. **57.50% of the
agreement is present with the vote path disabled.**

## What this changes about P14's reading

**P14's conclusion was too strong, and P15 corrects it in a specific way.**

P14 said unanimity carries "a large coordination component". P15 says the
mechanism is **not coordination at all** — it is a *shared perceptual prior*.
Five modules with the same architecture and the same six-object training map an
unseen object to the same nearest neighbour, because they are alike, not
because they confer. The vote adds almost nothing (P15c).

**This is still Nadi's point, and arguably a cleaner version of it.** The
agreement is real, total in the `strawberry` case, and carries **zero
information about truth** — every one of those unanimous answers is wrong. But
it is not produced by inspectors deferring to each other. It is produced by
inspectors who were trained alike, which is why it appears even when they cannot
communicate.

Nadi's social example maps onto this exactly: people who like you agree, and
their agreement is determined *before you speak* — not by a process of
deferring during the conversation.

## The variance is itself a result

Unanimity ranges from **20% to 100%** across four objects. That range is wider
than most effects this project has measured, and it says agreement-when-wrong
depends strongly on **how close the unseen object is to something known**:

- `strawberry` → `golf_ball` at 100/100: an unseen object that is *very* close
  to a trained one produces total false consensus.
- `mug` → `bowl` at only 37/100 with 20% unanimity: an object with a
  distinctive feature (the handle) that no trained object shares leaves the
  modules genuinely uncertain, and **uncertainty shows up as disagreement**.

**That is the useful, publishable relation:** false consensus is highest exactly
where the unknown resembles the known. It is lowest where the unknown is
genuinely novel. A system agreeing confidently is evidence that the input looked
familiar, not that the answer is right.

## Threats

- **4 episodes per run**, so unanimity moves in 25 pp steps per seed. The
  `strawberry` (100%) and `mug` (20%) extremes are far outside that
  granularity; `banana` at 35% is not, and should not be read finely.
- **Seed 42 fails on `dice` only** — upstream's
  `surface_normal_total_least_squares` (`sensor_processing.py:444`) asserts a
  real eigendecomposition and on one viewpoint it is not. Identical on both
  arms, so neutral for the max-vs-novote contrast, exactly as pre-registered.
- **`mug`'s gap is negative** (−15 pp: novote agrees *more* than voting). With
  n=5 and 25 pp granularity this is not distinguishable from noise, and it is
  reported rather than smoothed.
- **Six-object training is a smaller prior than nine.** The control rules out a
  *broken* model but not a *differently-shaped* one.

## What follows

1. **Report unanimity against a per-object baseline**, not one project-wide
   constant. P14 proposed subtracting a single floor; P15 shows the floor moves
   between 20% and 100% depending on the object.
2. **The deference measurement is now the priority** and its interpretation has
   changed: P15c says there is very little deference to find. The interesting
   question is no longer "who changed their mind" but "how much of what looks
   like consensus was fixed at training time".
3. **H1's second clause needs restating.** It scales the advantage with module
   *disagreement*; P15 shows disagreement is largely a function of how novel the
   input is, which is a property of the input, not of the modules.

**Publication decision remains Nadi's and is not taken.**
