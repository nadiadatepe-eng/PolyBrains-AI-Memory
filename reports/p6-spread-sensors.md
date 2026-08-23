# P6 — The spread-sensor task, and why it failed as a fix

**Date:** 2026-08-18 · **Sha:** `0c81b1f` · Pre-registered as **P6** in `PREDICTIONS.md`

**Result: P6 is refuted, and the way it failed is more useful than success would have been.**

---

## The intent

P4 showed voting harms accuracy on the stock task, but also that the task barely produces
disagreement (D-index ≈ 0.04; five sensor patches sit **1 cm apart** and see nearly the same
surface). Every hypothesis in this project is about *disagreeing* modules, so P6 widened the
patch separation 8x, from 0.01 to 0.08, to build a task where the vote rules could diverge.

## What was predicted

> With sensor patches widely separated, D-index rises above 0.15 and the vote rules stop being
> identical.

## What happened

Surface indicators looked like success. Inter-module disagreement on object identity rose from
**1/10 to 7/10 episodes**, and per-module accuracy went from near-uniform `[9,9,9,9,8]` to
varied `[10,4,5,5,6]`.

Then the arms were run properly, 5 seeds each:

| arm | accuracy | per-module acc | unanimous-correct | failure correlation |
|---|---|---|---|---|
| `max` (upstream) | 100.0% | 64.0% | 38.0% | 0% |
| `consensus` | 100.0% | 64.0% | 38.0% | 0% |
| **no voting** | 100.0% | 64.0% | 38.0% | 0% |

**Identical to the decimal on every metric.** Three different rules, including one with voting
switched off entirely, produced indistinguishable results.

## Why — instrumented, not guessed

Three different rules giving byte-identical numbers is not a plausible experimental outcome,
so the vote path was instrumented directly (`send_out_vote` return values and whether incoming
votes changed any evidence):

| task | `send_out_vote` returned `None` | vote receipts | receipts that changed evidence |
|---|---|---|---|
| **stock (0.01)** | 2090 / 3295 = **63%** | 1270 | **1163 (92%)** |
| **spread (0.08)** | 24979 / 28485 = **88%** | 555 | **121 (22%)** |

Upstream's own comment at `learning_module.py:433` explains it:

> We don't want the LM to vote if it hasn't gotten input yet (**can happen with multiple LMs
> if some start off the object**)

**Spreading the sensors did not create disagreement between voting modules. It knocked most
modules off the object, so they stopped voting at all.** The apparent "disagreement" I measured
was modules having no opinion, not modules holding conflicting opinions.

With the vote path 88% silent and only 22% of the remaining receipts having any effect, the
aggregation rule cannot matter. The identical results are exactly what an inert mechanism
predicts.

## The lesson, which is the real finding

**Disagreement between modules and modules failing to see the object are different things, and
a naive geometric manipulation produces the second while looking like the first.**

Any future attempt to induce disagreement must be verified at the vote path, not inferred from
output statistics. The check is cheap: instrument `send_out_vote` and count `None` returns.

This also retroactively validates the P4 result. The stock task, whatever its limitations, has
a *live* vote path — 92% of receipts change evidence. P4's finding that voting causes
correlated failure was measured on a mechanism that was actually running.

## What a correct disagreement task needs

Modules must **see the object and disagree about it**, which rules out geometric separation
large enough to lose the target. Candidates:

1. **Feature corruption** — inject noise into a subset of modules' sensory input while keeping
   all patches on the object. Disagreement without absence.
2. **Conflicting priors** — pretrain modules on different object subsets so they hold genuinely
   different models of the same input.
3. **Ambiguous objects** — objects whose local surfaces are shared (the YCB set has several
   near-identical cans and boxes), so modules on different patches legitimately infer
   different identities.
4. **Moderate separation** — sweep 0.01 → 0.08 and find the point where `send_none` stays near
   the stock 63% while identity disagreement rises. There may be no such point, which would
   itself be worth reporting.

Option 1 is the most controlled and is registered as **P7**.

## Status of the hypotheses after P6

Unchanged. **H1 is not supported** (P4). **H2 remains untested**: no task yet built produces
disagreement between modules that are all voting.

## Reproduce

```bash
cd ~/PolyBrains/upstream/tbp.monty
PYTHONPATH=~/PolyBrains/src .venv/bin/python -c "
exec(open('/tmp/spy.py').read())
import sys, os
sys.argv=['run.py','-cd',os.path.expanduser('~/PolyBrains/configs'),'-cn','experiment',
          'experiment=p6_e1_ood_max','++experiment.config.logging.wandb_id=spy']
from tbp.monty.frameworks.run_env import setup_env; setup_env()
from tbp.monty.frameworks.run import main; main()"
```
The spy script is reproduced in `tools/vote_spy.py`.
