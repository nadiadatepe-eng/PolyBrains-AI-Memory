#!/usr/bin/env python3
"""Generate P12 arm configs: H2's actual test.

H2: *weighting votes by a module's IN-DOMAIN confidence destroys the OOD
advantage, because one module confident on familiar input captures the
consensus.*

Three arms, differing ONLY in what evidence moves the vote weight:

  p12_frozen     w(t) never moves. Upstream behaviour. The replication control:
                 must reproduce P7's powered consensus arm within noise.
  p12_ood        weight tracks OUT-of-domain correctness -- the polymath design,
                 where being right on novel input earns influence.
  p12_indomain   weight tracks IN-domain correctness -- H2's failure mode.

All three run `vote_mode: consensus`, because a weight only matters if the
reduction rule reads it: `np.ma.max` takes the loudest vote regardless of how
that vote was scaled, which would make every arm identical by construction.
That is the P10 lesson applied before the run rather than after.

The experiment class is swapped to AdaptiveWeightExperiment, which is what
actually feeds outcomes to w(t). `adaptive_weight: true` alone leaves the weight
frozen at w_init for the whole run -- see tests/test_adaptive_weight.py.

## The mixed rotation schedule, and why it is required

P7's eval visits four OOD rotations and nothing else. Run on that schedule,
`p12_indomain` would NEVER see an in-domain episode, so its weight would never
move and it would be a dead arm indistinguishable from `frozen` -- the failure
this project has now shipped five times, caught here before the run instead.

H2 is a claim about a module that is confident BECAUSE it is familiar, so the
episode stream must contain both kinds. All arms therefore evaluate a mixed
schedule: the 5 pretraining rotations interleaved with the 4 oblique OOD ones.
Accuracy is reported on the OOD subset only -- the in-domain episodes are there
to let confidence accumulate, exactly as H2 describes.

This changes the denominator relative to P7, so `p12_frozen` is the replication
control and is compared on its OOD episodes alone.
"""
from pathlib import Path

CFG = Path(__file__).resolve().parents[1] / "configs" / "experiment"
base = (CFG / "p7_e1_ood_consensus.yaml").read_text()

HEADER = """# @package _global_
# P12 -- H2: {desc}
#
# H2 was NEVER RUN before this: adaptive_weight was false in 24 of 24 configs and
# record_episode_outcome was called nowhere outside tests. See the 2026-08-19
# audit in PREDICTIONS.md. Gated by tests/test_adaptive_weight.py, which fails
# if outcomes stop reaching w(t).
"""

ARMS = {
    "p12_frozen":   dict(src="frozen",   adaptive="false",
                         desc="w(t) frozen -- upstream control"),
    "p12_ood":      dict(src="ood",      adaptive="true",
                         desc="weight earned on OUT-of-domain correctness"),
    "p12_indomain": dict(src="indomain", adaptive="true",
                         desc="weight earned on IN-domain correctness (the failure mode)"),
}

TARGET = ("  _target_: tbp.monty.frameworks.experiments."
          "object_recognition_experiments.MontyObjectRecognitionExperiment\n")
ANCHOR = "  config:\n    show_sensor_output: false\n"

for name, a in ARMS.items():
    s = base[base.index("defaults:"):]
    s = HEADER.format(desc=a["desc"]) + s
    assert TARGET in s and ANCHOR in s, "p7 consensus config shape changed"
    s = s.replace("run_name: p7_e1_ood_consensus", f"run_name: {name}")
    s = s.replace("  adaptive_weight: false\n", f"  adaptive_weight: {a['adaptive']}\n")
    s = s.replace(TARGET,
                  "  _target_: polybrains.adaptive_experiment.AdaptiveWeightExperiment\n"
                  f"  weight_source: {a['src']}\n"
                  "  indomain_rotations: ${polybrains.indomain_rotations}\n")
    # Mixed schedule: in-domain episodes must occur or the indomain arm is dead.
    s = s.replace("  eval_rotations:\n",
                  "  # The 5 rotations pb_indomain_5lm was pretrained on. Episodes at\n"
                  "  # these rotations let confidence accumulate; they are EXCLUDED from\n"
                  "  # the accuracy denominator by tools/analyse_p12.py.\n"
                  "  indomain_rotations:\n"
                  "    - [0, 0, 0]\n"
                  "    - [0, 90, 0]\n"
                  "    - [0, 270, 0]\n"
                  "    - [90, 0, 0]\n"
                  "    - [90, 180, 0]\n"
                  "  # Mixed schedule: 5 in-domain + 4 OOD, one rotation per epoch.\n"
                  "  eval_rotations:\n"
                  "    - [0, 0, 0]\n"
                  "    - [0, 90, 0]\n"
                  "    - [0, 270, 0]\n"
                  "    - [90, 0, 0]\n"
                  "    - [90, 180, 0]\n")
    (CFG / f"{name}.yaml").write_text(s)
    print("wrote", name)
