#!/usr/bin/env python3
"""Gates on the P14 (E-null) configs, asserted before the sweep runs.

The P13 lesson: a smoke test before the sweep caught an arm that would have
produced clean-looking numbers measuring silence rather than disagreement.
This file is the same discipline applied to the one thing P14 depends on --
that the held-out object is genuinely held out.

**If `dice` is in the pretraining list, P14 measures nothing** and every number
it produces would still look plausible. That is the failure this file exists to
prevent, and it cannot be caught by reading the output.

Run with `bash tools/run_gates.sh`, or directly -- this file HAS a `__main__`,
unlike four of the six older gate files, which exit 0 having asserted nothing.
"""
from __future__ import annotations

import os
import sys

import yaml

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(HERE, "configs", "experiment")

HELD_OUT = "dice"
ALL_OBJECTS = {
    "mug", "bowl", "potted_meat_can", "spoon", "strawberry",
    "mustard_bottle", "dice", "golf_ball", "c_lego_duplo", "banana",
}

results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print("%-5s %-62s %s" % ("PASS" if ok else "FAIL", name, detail))


def load(arm):
    with open(os.path.join(EXP, "%s.yaml" % arm), encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def cfg_of(doc):
    return doc["experiment"]["config"]


def main() -> int:
    pre = cfg_of(load("p14_pretrain9"))
    train_objs = pre["train_env_interface_args"]["object_names"]

    # 1: the whole experiment rests on this one fact.
    check("1  the held-out object is NOT in the pretraining list",
          HELD_OUT not in train_objs,
          "%s in %s" % (HELD_OUT, train_objs) if HELD_OUT in train_objs else "")

    check("2  pretraining covers exactly the other nine",
          set(train_objs) == ALL_OBJECTS - {HELD_OUT} and len(train_objs) == 9,
          "%d objects: %s" % (len(train_objs), sorted(train_objs)))

    # 3: a model trained on nine objects but LOADED by an arm pointing at the
    # ten-object model would silently restore the correct answer to the
    # hypothesis space, and the experiment would quietly become a normal one.
    for arm in ("p14_holdout_max", "p14_holdout_novote", "p14_trained_max"):
        path = cfg_of(load(arm))["model_name_or_path"]
        check("3  %s loads the nine-object model" % arm,
              "pb_holdout9_5lm" in path, path)

    # 4: the treatment arms must evaluate ONLY the impossible object.
    for arm in ("p14_holdout_max", "p14_holdout_novote"):
        objs = cfg_of(load(arm))["eval_env_interface_args"]["object_names"]
        check("4  %s evaluates only the held-out object" % arm,
              objs == [HELD_OUT], "%s" % objs)

    # 5: the control must evaluate a TRAINED object, or it controls nothing.
    ctrl = cfg_of(load("p14_trained_max"))["eval_env_interface_args"]["object_names"]
    check("5  the control evaluates a TRAINED object",
          len(ctrl) == 1 and ctrl[0] in train_objs,
          "%s (trained: %s)" % (ctrl, ctrl[0] in train_objs if ctrl else "?"))

    # 6: novote must actually disable voting. P9 lost 73 minutes to a vote path
    # that looked disabled and was not.
    nov = cfg_of(load("p14_holdout_novote"))
    disabled = nov.get("monty_config", {}).get("lm_to_lm_vote_matrix", "MISSING")
    check("6  novote really disables the vote matrix",
          disabled is None, "lm_to_lm_vote_matrix=%r" % disabled)

    # 6b: and the treatment arm must NOT disable it -- otherwise both arms are
    # the same arm and the comparison is between a thing and itself.
    mx = cfg_of(load("p14_holdout_max"))
    check("6b the voting arm still has voting enabled",
          "monty_config" not in mx or
          mx.get("monty_config", {}).get("lm_to_lm_vote_matrix", "unset") != None,
          "monty_config=%r" % mx.get("monty_config"))

    # 7: the arms must differ in exactly one way. If the two holdout arms are
    # byte-identical apart from the run name, the sweep compares nothing.
    a = load("p14_holdout_max")
    b = load("p14_holdout_novote")
    check("7  the two holdout arms are not the same config",
          a != b, "identical" if a == b else "")

    # 8: rotations must match the earlier sweeps, or the replication control
    # cannot be compared against P7/P8's numbers.
    rots = [tuple(r) for r in load("p14_holdout_max")["polybrains"]["eval_rotations"]]
    expected = [(35, 45, 0), (325, 45, 0), (35, 315, 0), (325, 315, 0)]
    check("8  eval rotations match the P7/P8 arms",
          rots == expected, "%s" % rots)

    # 9: CONTROL on this file. Gates 1-8 are all assertions about parsed YAML;
    # if the loader silently returned empty dicts every one of them could pass
    # vacuously. This is CP-7B R8's lesson, one project over.
    check("9  CONTROL: the configs are non-empty and were really parsed",
          len(train_objs) > 0 and len(pre) > 5 and "polybrains" in a,
          "%d train objects, %d config keys" % (len(train_objs), len(pre)))

    failed = [n for n, ok, _ in results if not ok]
    print("\n%d/%d checks passed" % (len(results) - len(failed), len(results)))
    if failed:
        print("SWEEP MUST NOT RUN -- fix these first:")
        for n in failed:
            print("  %s" % n)
    return 1 if failed else 0


def test_p14_configs():
    assert main() == 0, "see the printed report above"


if __name__ == "__main__":
    sys.exit(main())
