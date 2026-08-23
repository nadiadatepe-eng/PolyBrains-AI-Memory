#!/usr/bin/env python3
"""Gates on the P15 configs, asserted before the sweep runs.

Same discipline as `test_p14_configs.py`, generalised to four held-out objects.
**The failure this prevents:** one of the four silently left in the training
set. Every number would still look plausible, and the per-object breakdown
would show that object agreeing for an entirely ordinary reason.

Has a `__main__` and prints "N/N checks passed".
"""
from __future__ import annotations

import os
import sys

import yaml

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(HERE, "configs", "experiment")

HELD_OUT = ["dice", "banana", "mug", "strawberry"]
ALL_OBJECTS = {
    "mug", "bowl", "potted_meat_can", "spoon", "strawberry",
    "mustard_bottle", "dice", "golf_ball", "c_lego_duplo", "banana",
}

results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print("%-5s %-64s %s" % ("PASS" if ok else "FAIL", name, detail))


def load(arm):
    with open(os.path.join(EXP, "%s.yaml" % arm), encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def cfg_of(doc):
    return doc["experiment"]["config"]


def main() -> int:
    pre = cfg_of(load("p15_pretrain6"))
    train_objs = pre["train_env_interface_args"]["object_names"]

    # 1: the whole experiment rests on this. Checked PER OBJECT, because a
    # single leaked object would be invisible in a set comparison that only
    # counts.
    for obj in HELD_OUT:
        check("1  %-10s is NOT in the pretraining list" % obj,
              obj not in train_objs,
              "LEAKED" if obj in train_objs else "")

    check("2  pretraining covers exactly the other six",
          set(train_objs) == ALL_OBJECTS - set(HELD_OUT) and len(train_objs) == 6,
          "%d objects: %s" % (len(train_objs), sorted(train_objs)))

    # 3: every arm must load the SIX-object model. Pointing at P14's nine-object
    # model would silently restore mug and strawberry to the hypothesis space.
    arms = ["p15_%s_%s" % (o, m) for o in HELD_OUT for m in ("max", "novote")]
    arms.append("p15_trained_max")
    for arm in arms:
        path = cfg_of(load(arm))["model_name_or_path"]
        ok = "pb_holdout6_5lm" in path
        if not ok:
            check("3  %s loads the six-object model" % arm, ok, path)
    check("3  every arm loads the six-object model",
          all("pb_holdout6_5lm" in cfg_of(load(a))["model_name_or_path"]
              for a in arms), "%d arms" % len(arms))

    # 4: each held-out arm evaluates ONLY its own object.
    for obj in HELD_OUT:
        for mode in ("max", "novote"):
            got = cfg_of(load("p15_%s_%s" % (obj, mode)))[
                "eval_env_interface_args"]["object_names"]
            ok = got == [obj]
            if not ok:
                check("4  p15_%s_%s evaluates only %s" % (obj, mode, obj),
                      ok, "%s" % got)
    check("4  each held-out arm evaluates only its own object",
          all(cfg_of(load("p15_%s_%s" % (o, m)))["eval_env_interface_args"]
              ["object_names"] == [o]
              for o in HELD_OUT for m in ("max", "novote")),
          "%d arms" % (2 * len(HELD_OUT)))

    # 5: the control must evaluate a TRAINED object.
    ctrl = cfg_of(load("p15_trained_max"))["eval_env_interface_args"]["object_names"]
    check("5  the control evaluates a TRAINED object",
          len(ctrl) == 1 and ctrl[0] in train_objs, "%s" % ctrl)

    # 6: novote must really disable voting; max must NOT.
    for obj in HELD_OUT:
        nov = cfg_of(load("p15_%s_novote" % obj))
        got = nov.get("monty_config", {}).get("lm_to_lm_vote_matrix", "MISSING")
        if got is not None:
            check("6  p15_%s_novote disables the vote matrix" % obj, False,
                  "%r" % got)
    check("6  every novote arm really disables the vote matrix",
          all(cfg_of(load("p15_%s_novote" % o)).get("monty_config", {})
              .get("lm_to_lm_vote_matrix", "MISSING") is None
              for o in HELD_OUT), "%d arms" % len(HELD_OUT))

    check("6b every max arm still has voting enabled",
          all(cfg_of(load("p15_%s_max" % o)).get("monty_config") is None
              for o in HELD_OUT), "")

    # 7: max and novote must actually differ, or the comparison is with itself.
    check("7  max and novote differ for every object",
          all(load("p15_%s_max" % o) != load("p15_%s_novote" % o)
              for o in HELD_OUT), "")

    # 8: the four held-out objects must be DISTINCT. A duplicate would look
    # like four objects and be three, and the shape-diversity argument -- the
    # entire reason for P15 -- would be quietly false.
    check("8  the four held-out objects are distinct",
          len(set(HELD_OUT)) == 4, "%s" % HELD_OUT)

    # 9: rotations match P14 and the P7/P8 arms.
    rots = [tuple(r) for r in load("p15_dice_max")["polybrains"]["eval_rotations"]]
    check("9  eval rotations match P14 and the P7/P8 arms",
          rots == [(35, 45, 0), (325, 45, 0), (35, 315, 0), (325, 315, 0)],
          "%s" % rots)

    # 10: CONTROL on this file. Every gate above reads parsed YAML; if the
    # loader returned empty dicts they could all pass vacuously.
    check("10 CONTROL: the configs are non-empty and were really parsed",
          len(train_objs) == 6 and len(pre) > 5
          and "polybrains" in load("p15_dice_max"),
          "%d train objects, %d config keys" % (len(train_objs), len(pre)))

    failed = [n for n, ok, _ in results if not ok]
    print("\n%d/%d checks passed" % (len(results) - len(failed), len(results)))
    if failed:
        print("SWEEP MUST NOT RUN -- fix these first:")
        for n in failed:
            print("  %s" % n)
    return 1 if failed else 0


def test_p15_configs():
    assert main() == 0, "see the printed report above"


if __name__ == "__main__":
    sys.exit(main())
