# CP-0 — Feasibility on this machine

**Date:** 2026-08-18
**Gate:** can this hardware run Monty end to end, and how fast?
**Verdict: PASS.** Full 5-learning-module voting pipeline runs in under a minute.

---

## Hardware

| | |
|---|---|
| CPU | Intel i5-9600K @ 3.70 GHz, 6 cores |
| RAM | 15.5 GiB |
| Disk | 356 GB free on `/` |
| GPU | NVIDIA (present, **not used** — CPU-only torch) |

## Software as actually installed

| | |
|---|---|
| Monty | `tbp.monty` **0.46.0**, pinned sha `0c81b1f2537eb08bb906859cc69d2b5caf55b6fd` (2026-08-14) |
| Python | **3.12.3** — *not* 3.8 |
| torch | 2.13.0+**cpu** |
| Simulator | **MuJoCo 3.11.0** |
| Env | `~/PolyBrains/upstream/tbp.monty/.venv` (uv), isolated, nothing global touched |

---

## Measured results

### Test suites

| Suite | Result | Wall | Peak RSS |
|---|---|---|---|
| `tests/unit` (no MuJoCo) | **518 passed, 4 skipped** | 19.0 s | 586 MB |
| `tests/integration` (no MuJoCo) | 21 passed, **17 skipped** | 8.2 s | 580 MB |
| `tests/unit + integration` (MuJoCo) | **590 passed, 1 failed, 30 skipped** | 23.8 s | 900 MB |

The 1 failure is benign: `test_renderer_for_res_returns_different_renderers` trips a
hypothesis timing deadline (382 ms vs a 200 ms limit) under software GL. Not a correctness
failure. Not ours.

### Experiments

| Run | Config | Wall | Peak RSS | Exit |
|---|---|---|---|---|
| Pretrain, 5 LMs, 10 objects, 1 rotation | `cp0_pretrain_5lms_mujoco` | **47.4 s** | 1.17 GB | 0 |
| Eval, 5 LMs voting, 50 episodes | `cp0_eval_5lms_mujoco` | **57.7 s** | 1.30 GB | 0 |

Upstream reports 4 min for the comparable `randrot_noise_10distinctobj_5lms_dist_agent`.
**We are in the same order of magnitude.** Compute is not a blocker.

### Accuracy — with a caveat that matters

50 episodes, 10 objects x 5 random rotations:

| Outcome | Count |
|---|---|
| correct | 15 |
| correct_mlh | 15 |
| confused | 16 |
| confused_mlh | 4 |

**60% correct (30/50). Upstream reports 99% for the equivalent experiment.**

This gap is explained and expected, not a mystery: the model was pretrained on **one
rotation** (`[[0,0,0]]`) instead of the full 14-rotation set, to get through the gate
quickly. It is then evaluated on *random* rotations. This is an undertrained model, and the
number is a pipeline-liveness check, **not** a baseline. A real baseline requires full
pretraining and is CP-5 work.

---

## What blocked, and how it was resolved

| Problem | Resolution |
|---|---|
| `torch-scatter` build fails: system CUDA 12.6 vs torch's 13.0 | Never imported by Monty (only `torch_geometric` is, in 3 files). Installed deps explicitly, then `pip install -e . --no-deps`. |
| **HabitatSim is unavailable on Linux** — PyPI wheel is `macosx_13_0_arm64` only, and cp310 only | **Use MuJoCo.** 18 of 63 experiment configs have `_mujoco` variants, including the 5-LM voting one we need. |
| `wandb.util.generate_id` missing in wandb 0.28.2 | Upstream pins an older wandb API. Override `logging.wandb_id` on the command line. |
| YCB textures rejected: "incorrect PNG signature" | The tarballs contain macOS `._` resource-fork files that sort first. Filter with `! -name "._*"`. |
| `ValueError: no visible target object` | The habitat-tuned `rotations_all` set puts objects out of the MuJoCo camera's view. Constrained to `[[0,0,0]]` for this gate. **Open issue for CP-5.** |
| `monty_handlers: []` writes no stats | Use `${monty.class:...BasicCSVStatsHandler}` — a class reference, not an instantiated `_target_`. |

## Dataset

YCB obtained **directly from the official S3 bucket**, bypassing
`habitat_sim.utils.datasets_download` entirely. MuJoCo needs only `textured.obj` +
`texture_map.png` per object.

- 10 objects, **64 MB**, 14 s to download
- Path: `~/tbp/data/mujoco/objects/ycb/<name>/`
- Script: `~/PolyBrains/tools/fetch_ycb.sh`

---

## Consequences for the plan

1. **The compute risk is downgraded from high to low.** Runs are ~1 min, not hours. The plan's §8 must be updated.
2. **The Python 3.8 risk is dead.** 3.12 works; `requires-python = '>=3.8'` with an explicit uv path for 3.9+.
3. **A new risk replaces both: HabitatSim is unavailable on this platform.** We are committed to the MuJoCo path. Consequences:
   - The 17 skipped integration tests include `evidence_lm_test.py` — a test for **the exact module we intend to modify**. We will be modifying code whose integration test we cannot run.
   - **Mitigation, and it is now a CP-3 requirement:** write our own integration test for the vote path against MuJoCo. Not optional.
   - Upstream's published benchmark numbers are Habitat-based, so **we cannot compare our absolute numbers to their table.** All comparisons must be internal: our arms against each other, on MuJoCo.
4. **Object placement needs fixing for MuJoCo before CP-5.** The full rotation set puts objects out of view. Either re-tune the camera or define a MuJoCo-valid rotation set. This is real work, not a config typo.
5. **The 5-LM vote matrix is already all-to-all** (`conf/monty/connectivity/5lm_5sm.yaml`). That is the exact file the H2 experiments will vary.

## Reproduce

```bash
cd ~/PolyBrains/upstream/tbp.monty
export MONTY_DATA=~/tbp/data \
       MONTY_MODELS=~/tbp/results/monty/pretrained_models \
       MONTY_LOGS=~/tbp/results/monty

# pretrain
.venv/bin/python run.py -cd ~/PolyBrains/configs -cn experiment \
  'experiment=cp0_pretrain_5lms_mujoco' \
  '++experiment.config.logging.wandb_id=cp0test' \
  '++experiment.config.n_train_epochs=1' \
  '++experiment.config.train_env_interface_args.object_init_sampler.rotations=[[0,0,0]]'

# eval with voting
.venv/bin/python run.py -cd ~/PolyBrains/configs -cn experiment \
  'experiment=cp0_eval_5lms_mujoco' \
  '++experiment.config.logging.wandb_id=cp0eval' \
  '++experiment.config.n_eval_epochs=1' \
  '++experiment.config.logging.monty_handlers=["${monty.class:tbp.monty.frameworks.loggers.monty_handlers.BasicCSVStatsHandler}"]'
```

Output: `~/tbp/results/monty/projects/monty_runs/randrot_noise_10distinctobj_5lms_dist_agent/eval_stats.csv`
