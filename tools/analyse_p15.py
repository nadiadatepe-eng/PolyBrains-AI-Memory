#!/usr/bin/env python3
"""Analyse P15: four held-out objects.

Pre-registered in `PREDICTIONS.md`. Follows `reports/p14-enull.md`.

Reuses `analyse_p14`'s per-run statistics rather than reimplementing them --
that code is validated against synthetic data with known answers by
`tests/test_analyse_p14.py`, and a second copy would be a second thing to
validate.

**The per-object breakdown is mandatory, not a nicety.** A mean over four
objects can hide one at 0% and three at 80%, and P15's whole purpose is to find
out whether P14 generalised or was a `dice`/`golf_ball` coincidence.
"""
from __future__ import annotations

import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import analyse_p14 as A  # noqa: E402

OBJECTS = ["dice", "banana", "mug", "strawberry"]


def arm_stats(name):
    return A.arm(name)


def main() -> int:
    print("P15 -- four held-out objects, pretrained on six\n")

    per_object = {}
    for obj in OBJECTS:
        mx = arm_stats("p15_%s_max" % obj)
        nv = arm_stats("p15_%s_novote" % obj)
        if not mx or not nv:
            print("MISSING runs for %s" % obj)
            return 1
        per_object[obj] = (mx, nv)

    ctrl = arm_stats("p15_trained_max")
    if not ctrl:
        print("MISSING the control arm")
        return 1

    # --- controls first, before any verdict is read ---
    print("--- CONTROLS ---")
    ok = True
    for obj, (mx, nv) in per_object.items():
        for label, rs in (("max", mx), ("novote", nv)):
            acc = A.mean([r["any_correct_pct"] for r in rs])
            good = acc == 0.0
            ok &= good
            if not good:
                print("C1 %s_%s accuracy is %.2f%% -- OBJECT LEAKED" % (obj, label, acc))
    print("C1 impossibility: every held-out arm is 0%% correct: %s"
          % ("PASS" if ok else "FAIL"))

    cacc = A.mean([r["any_correct_pct"] for r in ctrl])
    cgood = cacc >= 80.0
    ok &= cgood
    print("C2 replication: trained-object control %.2f%% (P14 was 100%%): %s"
          % (cacc, "PASS" if cgood else "FAIL -- MODEL BROKEN, SWEEP VOID"))

    sn = A.mean([r["send_none_pct"] for obj in OBJECTS
                 for r in per_object[obj][0]])
    sgood = sn < 50.0
    ok &= sgood
    print("C3 silence: send_none %.2f%%: %s" % (sn, "PASS" if sgood else "FAIL"))

    if not ok:
        print("\nCONTROLS FAILED -- no verdict reported.")
        return 1

    # --- the per-object table the pre-registration requires ---
    print("\n--- PER OBJECT (mandatory breakdown) ---")
    print("%-12s %10s %10s %8s   %s" %
          ("held out", "max unan", "novote", "gap", "attractor (max arm)"))
    means_max, means_nv = [], []
    attractors = {}
    for obj in OBJECTS:
        mx, nv = per_object[obj]
        m = A.mean([r["unanimous_pct"] for r in mx])
        n = A.mean([r["unanimous_pct"] for r in nv])
        means_max.append(m)
        means_nv.append(n)
        guesses = Counter(g for r in mx for g in r["guesses"])
        top, cnt = guesses.most_common(1)[0]
        attractors[obj] = (top, cnt, sum(guesses.values()))
        print("%-12s %9.2f%% %9.2f%% %+7.2f   %s (%d/%d)" %
              (obj, m, n, m - n, top, cnt, sum(guesses.values())))

    mean_max = A.mean(means_max)
    mean_nv = A.mean(means_nv)
    lowest = min(means_max)

    print("\n--- VERDICTS ---")

    # P15a: >=60% mean, and NO object below 25%.
    a_ok = mean_max >= 60.0 and lowest >= 25.0
    print("P15a unanimity high on EVERY held-out object: %s"
          % ("SUPPORTED" if a_ok else "NOT SUPPORTED"))
    print("     mean %.2f%% (bar 60%%), lowest object %.2f%% (bar 25%%)"
          % (mean_max, lowest))

    # P15b: do the four attractors DIFFER? This is the discriminating one.
    labels = [attractors[o][0] for o in OBJECTS]
    distinct = len(set(labels))
    print("P15b each object gets its own attractor: %s"
          % ("SUPPORTED -- shared perceptual prior" if distinct >= 3
             else "NOT SUPPORTED -- fixed architectural bias"))
    print("     %d distinct attractors across 4 objects: %s"
          % (distinct, dict(zip(OBJECTS, labels))))

    # P15c: does voting matter? P14 said barely.
    gap = mean_max - mean_nv
    c_ok = abs(gap) < 10.0
    print("P15c no-vote stays close to voting (P14 replication): %s"
          % ("SUPPORTED" if c_ok else "NOT SUPPORTED"))
    print("     max %.2f%% - novote %.2f%% = %+.2f pp (bar +/-10 pp)"
          % (mean_max, mean_nv, gap))

    t, note = A.paired_t(means_max, means_nv)
    print("     paired over the four objects: t=%.2f %s" % (t, note))

    return 0


if __name__ == "__main__":
    sys.exit(main())
