# Next session — PolyBrains is PAUSED

**Nadi stopped PolyBrains on 2026-08-20 and moved work to the polymathic
verification agent** (`~/PROPOSAL-polymath-verifier.md`, proposal only, nothing
built). This is a decision, not a stall: do not resume PolyBrains, and do not
propose resuming it, until Nadi says so.

The state below is complete and the tree is clean, so resuming later costs
nothing.

---


State at 2026-08-20, commit `0c648e9`, tree clean. All gates pass (`rc=0`).

## What happened today

Nadi's critique, and it changed the project's reading of its own results:

> A consensus does not need to be true. Given four alternatives that are all
> wrong and no option to abstain, agreeing is the rational move — dissent costs
> something and buys nothing.

**Two experiments were pre-registered, run, and reported.** Both are committed
with their controls, gates and analysers.

### P14 (`reports/p14-enull.md`) — 90.00% unanimity at 0.00% accuracy

Pretrained 5 LMs on **nine** objects, `dice` held out. Every module must
answer, none can be right. All three controls passed: impossibility (exactly
0.00% correct), replication (trained-object arm 100%), silence (`send_none` 0%).

They converged on `golf_ball`, 92 of 94 answers — **and 83.33% of no-vote
episodes were already unanimous with the vote path disabled.**

### P15 (`reports/p15-four-holdout.md`) — the correction, and the better result

Four held-out objects chosen for shape diversity, because `dice` and
`golf_ball` are both round and one object cannot separate coordination from
perceptual similarity.

| held out | max unan | novote | attractor |
|---|---|---|---|
| `strawberry` | 100.00% | 100.00% | `golf_ball` 100/100 |
| `dice` | 95.00% | 75.00% | `golf_ball` 94/95 |
| `banana` | 35.00% | 20.00% | **`mustard_bottle`** 78/100 |
| `mug` | 20.00% | 35.00% | **`bowl`** 37/100 |

**Three distinct attractors.** The mechanism is a **shared perceptual prior**,
not coordination: modules trained alike map an unseen object to its nearest
trained neighbour, and voting adds +5.00 pp (t=0.63, n.s.).

**P15a failed, and usefully.** The mean (62.50%) cleared its 60% bar but `mug`
at 20.00% failed the 25% per-object floor. Reporting only the mean would have
read as a clean replication of P14. The per-object clause was written into the
pre-registration to prevent exactly that, and it earned its place immediately.

## P16 (`reports/p16-baseline-and-confidence.md`) — the sharpest result

No new runs; re-read P15's data. **Unanimity is 100.00% when the system is
right and 100.00% when it is wrong.** Identical at the read-out.

The obvious repair — trust agreement only when confident — **fails and inverts**:
`strawberry` carries *more* evidence than the correct case (+4.02, t(4)=4.70)
while being wrong in every episode. Evidence orders `mug`(4.6) < `banana`(5.9) <
`dice`(15.3) < `strawberry`(25.2), tracking how close the unseen object is to a
trained one — a good novelty signal, a misleading correctness one.

**Agreement, confidence and correctness are three different things.**

## If PolyBrains is resumed, the next step

**Report unanimity against a per-object baseline.** P14 proposed subtracting one
project-wide floor; P15 shows the floor moves between 20% and 100% depending on
how close the unseen object is to something known. A single constant would be
wrong in both directions.

Then, in order:

1. **Restate H1's second clause.** It scales the advantage with module
   *disagreement*; P15 shows disagreement is largely a function of how novel the
   **input** is, which is a property of the input rather than of the modules.
2. **The deference measurement** (`reconsideration-consensus.md` §5.2) — but its
   interpretation has changed. P15c says there is very little deference to find,
   so the question is no longer "who changed their mind" but "how much of what
   looks like consensus was fixed at training time".
3. **P13 is still built, gated and NOT run.** `p13_sep004` must be replaced with
   0.02 and smoke-tested first — see the P13 section in `PREDICTIONS.md`.

## Traps found today, all recorded in the runners

- **`python -m tbp.monty.frameworks.run` exits 0 having done NOTHING.** The
  project uses `run.py -cd <configs> -cn experiment`. Cost one cycle.
- **`wandb_id` must be set explicitly** or hydra fails resolving
  `wandb.util.generate_id`.
- **Upstream bug, seed 42 only:** `surface_normal_total_least_squares`
  (`sensor_processing.py:444`) asserts a real eigendecomposition and on some
  viewpoints it is not. Fails **identically on both arms**, so it is neutral for
  the max-vs-novote contrast. Handling was pre-registered before the numbers
  were seen.
- **`run_gates.sh` was not running the new gates at all.** Now registers
  `test_p13/p14/p15_configs.py` and `test_analyse_p14.py`, each matched against
  its **own** verdict string — accepting either format would let a file pass
  while printing no verdict.

## Verify

```bash
bash tools/run_gates.sh        # ALL GATES PASS, rc=0
upstream/tbp.monty/.venv/bin/python tools/analyse_p14.py
upstream/tbp.monty/.venv/bin/python tools/analyse_p15.py
```

## Also open, unrelated

- **`~/PROPOSAL-polymath-verifier.md` and `.html`** — the adversarial
  verification agent, proposal only, nothing built. Nadi's design decisions are
  in it: the job is **asking**, not evaluating; classes and terminology, never
  instances; frames blind to each other.
- Morpho-HomeGraph is clean and pushed (`219dadf`).
- **Ask before every push to a public remote**, each time
  (the source project's public-push safety note).

**Publication decision remains Nadi's and is not taken.**
