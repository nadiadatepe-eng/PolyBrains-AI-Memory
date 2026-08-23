#!/usr/bin/env python3
"""Validate the P14 analyser against synthetic data with a KNOWN answer.

Two of 2026-08-19's flaws lived in analysis code. A config audit cannot find
them, and neither can reading the output, because a broken analyser prints
plausible numbers. So the analyser is fed cases whose verdict is known in
advance and asserted.

Cases: unanimous-and-impossible (the predicted result), scattered (the
refutation), silent (the P6 trap), and leaked (the control that must void the
sweep).

Has a `__main__`. Four of the six older gate files do not, and as scripts they
assert nothing and exit 0.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))

import analyse_p14 as A  # noqa: E402

HEADER = (",primary_performance,stepwise_performance,num_steps,rotation_error,"
          "result,most_likely_object,primary_target_object,"
          "stepwise_target_object,highest_evidence,time,symmetry_evidence\n")

results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print("%-5s %-58s %s" % ("PASS" if ok else "FAIL", name, detail))


def write_run(root, run, episodes, target="dice"):
    """episodes: list of (guess, correct) lists, 5 entries each."""
    d = os.path.join(root, run)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "eval_stats.csv"), "w") as fh:
        fh.write(HEADER)
        i = 0
        for ep in episodes:
            for guess, correct in ep:
                perf = "correct" if correct else "confused"
                fh.write("%d,%s,%s,10,0.1,done,%s,%s,%s,1.0,0.5,0.1\n"
                         % (i, perf, perf, guess, target, target))
                i += 1


def scenario(root, kind):
    """Build all three arms for a known-answer scenario."""
    for seed in A.SEEDS:
        if kind == "unanimous":
            # Every module says the same wrong thing: coordination.
            eps = [[("golf_ball", False)] * 5 for _ in range(4)]
        elif kind == "scattered":
            # Every module says something different: no consensus.
            eps = [[(o, False) for o in
                    ("mug", "bowl", "spoon", "banana", "golf_ball")]
                   for _ in range(4)]
        elif kind == "silent":
            # Nobody answers. Silence must NOT be counted as agreement.
            eps = [[("no_match", False)] * 5 for _ in range(4)]
        write_run(root, "p14_holdout_max_s%d" % seed, eps)
        # novote: always scattered, so "voting raises agreement" is testable
        write_run(root, "p14_holdout_novote_s%d" % seed,
                  [[(o, False) for o in
                    ("mug", "bowl", "spoon", "banana", "strawberry")]
                   for _ in range(4)])
        # control: trained object, correct
        write_run(root, "p14_trained_max_s%d" % seed,
                  [[("mug", True)] * 5 for _ in range(4)], target="mug")


def run_analyser(root):
    old = A.RUNS
    A.RUNS = root
    try:
        arms = {n: A.arm(n) for n in
                ("p14_holdout_max", "p14_holdout_novote", "p14_trained_max")}
        return arms
    finally:
        A.RUNS = old


def main() -> int:
    root = tempfile.mkdtemp(prefix="p14synth")
    try:
        # --- case 1: unanimous on an impossible target ---
        scenario(root, "unanimous")
        arms = run_analyser(root)
        u = A.mean([r["unanimous_pct"] for r in arms["p14_holdout_max"]])
        n = A.mean([r["unanimous_pct"] for r in arms["p14_holdout_novote"]])
        check("1  unanimous-wrong is detected as 100% unanimity", u == 100.0,
              "%.1f%%" % u)
        check("2  scattered novote is detected as 0% unanimity", n == 0.0,
              "%.1f%%" % n)
        check("3  the impossibility control sees 0% correct",
              A.mean([r["any_correct_pct"] for r in arms["p14_holdout_max"]]) == 0.0)
        check("4  the replication control sees a working model",
              A.mean([r["any_correct_pct"] for r in arms["p14_trained_max"]]) == 100.0)

        # The zero-variance case: every seed identical. This MUST NOT be
        # reported as no effect.
        t, note = A.paired_t([100.0] * 5, [0.0] * 5)
        check("5  a 100 pp effect with sd=0 is not reported as null",
              t == float("inf") and "sd=0" in note, "t=%s %s" % (t, note))

        shutil.rmtree(root)
        root = tempfile.mkdtemp(prefix="p14synth")

        # --- case 2: scattered, i.e. the critique refuted ---
        scenario(root, "scattered")
        arms = run_analyser(root)
        u = A.mean([r["unanimous_pct"] for r in arms["p14_holdout_max"]])
        check("6  a genuinely scattered arm reports ~0% unanimity", u == 0.0,
              "%.1f%%" % u)

        shutil.rmtree(root)
        root = tempfile.mkdtemp(prefix="p14synth")

        # --- case 3: the P6 trap. Silence is not consensus. ---
        scenario(root, "silent")
        arms = run_analyser(root)
        u = A.mean([r["unanimous_pct"] for r in arms["p14_holdout_max"]])
        sn = A.mean([r["send_none_pct"] for r in arms["p14_holdout_max"]])
        check("7  five silent modules are NOT counted as unanimous", u == 0.0,
              "%.1f%% unanimous" % u)
        check("8  and silence is reported as send_none=100%", sn == 100.0,
              "%.1f%%" % sn)

        failed = [n for n, ok, _ in results if not ok]
        print("\n%d/%d checks passed" % (len(results) - len(failed), len(results)))
        return 1 if failed else 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_analyse_p14():
    assert main() == 0, "see the printed report above"


if __name__ == "__main__":
    sys.exit(main())
