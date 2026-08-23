# P14 (E-null) — unanimity survives when correctness is impossible

**Run 2026-08-20.** Pre-registered at `051390f` before the nine-object model was
pretrained. Controls at `a6b9a3e`, the seed-42 handling at the addendum commit,
both written before any number below existed.

Reproduce:

```bash
python3 tools/make_p14_configs.py
PYTHONPATH=src upstream/tbp.monty/.venv/bin/python tests/test_p14_configs.py
upstream/tbp.monty/.venv/bin/python tests/test_analyse_p14.py
bash tools/run_p14.sh
upstream/tbp.monty/.venv/bin/python tools/analyse_p14.py
```

## The condition this creates, and why it is new

Nadi's critique, 2026-08-20: *a consensus does not need to be true. Given four
alternatives that are all wrong and no option to abstain, agreeing is the
rational move — dissent costs something and buys nothing.*

**Every prior experiment in this project evaluated objects that were in the
pretrained set.** `train_distinctobj_predefined.yaml` and
`eval_distinctobj_random.yaml` carry the identical 10-object list. The correct
answer was always available, so the question "does agreement imply
correctness" was only ever asked under the one condition that flatters it.

P14 removes that. Five LMs pretrained on **nine** objects, `dice` held out —
P4's own false-consensus object. Verified at the model level rather than the
config level: `torch.load` on `model.pt` shows LM_0's graph memory holds nine
objects and `dice` is not among them. **Every module must answer and none can
be right.**

## Result

| arm | unanimous | any correct | `send_none` |
|---|---|---|---|
| `p14_holdout_max` (voting) | **90.00%** | **0.00%** | 0.00% |
| `p14_holdout_novote` | **83.33%** | **0.00%** | 0.00% |
| `p14_trained_max` (control) | 100.00% | 100.00% | 0.00% |

**Controls, all passing, checked before any verdict was read:**

- **C1 impossibility** — accuracy on the held-out object is **exactly 0.00%**
  on both arms. The object did not leak into training.
- **C2 replication** — the trained-object arm scores **100%**. The nine-object
  model works, so the holdout numbers are not an artifact of a broken model.
  This control matters more than the treatment: a broken model fails
  everything, and its unanimity would have looked like a finding.
- **C3 silence** — `send_none` is **0.00%**. Every module answered. This is not
  P6's failure mode wearing a new mask.

## What they agreed on

| arm | converged on |
|---|---|
| `p14_holdout_max` | **`golf_ball` 92 of 94 module-answers** |
| `p14_holdout_novote` | **`golf_ball` 91 of 95** |

Not scatter. Not noise. **A single wrong attractor**, chosen with near-total
consistency, for an object the modules had never seen.

## Verdicts

**P14a SUPPORTED, and by a wide margin.** Predicted ≥15% unanimity on an
impossible target; measured **90.00%**. Unanimity in this substrate does **not**
require a correct answer to be available. It carries a large coordination
component, and every unanimity number in this project contains it.

**P14b SUPPORTED at n=5, NOT SUPPORTED at n=4 — and the honest reading is that
it is unproven.** Voting gives +6.67 pp over no voting (90.00 vs 83.33,
t=0.64, n.s.). **Excluding seed 42 the difference is exactly 0.00 pp**
(87.50 vs 87.50).

The pre-registration committed to reporting both and to claiming no verdict if
they disagreed. **They disagree, so P14b is not claimed.** What the data
supports is the weaker and more interesting statement: **the convergence is
already almost total without any voting at all.**

## The finding, stated carefully

**Nadi's critique is confirmed, and by a stronger route than predicted.**

The prediction was that voting would manufacture consensus on an impossible
target. What happened is that **consensus did not need to be manufactured**:
83% of no-vote episodes were already unanimous on `golf_ball`, with the vote
mechanism entirely disabled.

That relocates the mechanism. The agreement is not produced by modules talking
to each other. It is produced by **five modules sharing the same prior, the
same architecture and the same nine-object training**, so they fail *the same
way* on an unseen object. They agree because they are alike, not because they
conferred.

**This is Nadi's social example in its exact form** — everybody who likes you
agrees, and their agreement carries no information because it was determined
before you spoke. Here the modules' agreement was determined by their shared
training before any vote was cast.

## What this does to H1

**H1 is not refuted. Its read-out is compromised.**

H1's second clause says the advantage scales with module *disagreement*. P14
shows the floor: with an unseen object, five modules agree 83–90% of the time
**while being 100% wrong**. So any unanimity figure in this project is
measuring correctness *plus* an architectural-similarity constant, and nothing
so far has separated the two.

Concretely, P8's headline — voting takes unanimity from 10.80% to 41.00% — was
read as voting producing agreement about a correct answer. P14 shows unanimity
of ~85% is reachable with no voting and no correct answer available at all.
**The two numbers are not on the same scale as we assumed.**

## Threats to this result

- **One held-out object.** `dice` may be unusually confusable with `golf_ball`
  (both small and round). The result would be far stronger with three or four
  held-out objects, and that is the obvious next run.
- **Seed 42 is an upstream failure**, not ours: `sensor_processing.py:444`
  asserts its eigendecomposition is real and on one viewpoint it is not. It
  fails **identically on both arms**, which is why dropping it is neutral for
  the P14b contrast — but it is why P14b is reported as unproven rather than
  supported.
- **4 episodes per run** is a small denominator; each episode moves unanimity
  by 25 pp. P14a's margin (90% vs a 15% threshold) is far outside that
  granularity; P14b's is not, which is the second reason it is not claimed.
- **The analyser was validated on synthetic data with known answers**
  (`tests/test_analyse_p14.py`, 8/8), including the P6 trap where five silent
  modules must not count as unanimous, and the zero-variance bug that once
  reported a −100 pp effect as null.

## What follows

1. **Report unanimity against this floor, not against zero.** An unanimity
   number without the architectural-similarity baseline subtracted overstates
   agreement-about-truth.
2. **Three or four held-out objects**, to remove the `dice`/`golf_ball`
   confusability objection.
3. **The deference measurement** (`reconsideration-consensus.md` §5.2) is now
   more clearly the right next instrument: it separates *modules that agree
   because they are alike* from *modules that changed their minds*.

**Publication decision remains Nadi's and is not taken.**
