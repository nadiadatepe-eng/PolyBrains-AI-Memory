#!/usr/bin/env python3
"""P16: the per-object unanimity baseline, and whether confidence can save it.

Follows `reports/p15-four-holdout.md`, which showed the unanimity floor moves
between 20% and 100% depending on the held-out object, so a single project-wide
baseline would be wrong in both directions.

**No new runs.** This re-reads P15's committed `eval_stats.csv` files, so
nothing here can have been tuned to the outcome. Only the read-out changes --
the same discipline P8 used when it re-scored P7.

Two questions:

1. **The baseline.** For each object, what is the unanimity a system reaches
   when it CANNOT be right? That number must be subtracted before any unanimity
   figure is read as agreement-about-truth.

2. **Can confidence separate them?** The obvious rescue for a system that agrees
   when wrong is to weight by evidence: trust unanimity only when the modules
   are confident. This tests whether that works, and it is a real test because
   it can fail.
"""
from __future__ import annotations

import csv
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import analyse_p14 as A  # noqa: E402

RUNS = os.path.expanduser("~/tbp/results/monty/projects/monty_runs")
SEEDS = [42, 43, 44, 45, 46]
HELD_OUT = ["dice", "banana", "mug", "strawberry"]
CONTROL = "bowl"


def evidence_per_seed(prefix):
    """Mean `highest_evidence` per seed. Per-seed, because a pooled mean over
    episodes would weight a seed with more episodes more heavily -- and seed 42
    has 3 episodes on `dice` where the others have 4."""
    out = []
    for s in SEEDS:
        p = os.path.join(RUNS, "%s_s%d" % (prefix, s), "eval_stats.csv")
        if not os.path.exists(p):
            continue
        vals = []
        for r in csv.DictReader(open(p)):
            try:
                vals.append(float(r["highest_evidence"]))
            except (ValueError, KeyError):
                pass
        if vals:
            out.append(statistics.mean(vals))
    return out


def paired_t(a, b):
    if len(a) != len(b) or len(a) < 2:
        return float("nan"), "n<2"
    d = [x - y for x, y in zip(a, b)]
    m = statistics.mean(d)
    sd = statistics.stdev(d)
    if sd == 0:
        return (float("inf") if m else 0.0), "sd=0"
    return m / (sd / len(d) ** 0.5), ""


def main() -> int:
    print("P16 -- per-object baseline and the confidence rescue")
    print("Re-reads P15 data. No new runs.\n")

    print("--- 1. THE PER-OBJECT UNANIMITY BASELINE ---")
    print("Unanimity reached when the correct answer is NOT AVAILABLE.\n")
    print("%-12s %12s %12s   %s" %
          ("object", "unan (max)", "unan(novote)", "read any unanimity here as"))
    floors = {}
    for obj in HELD_OUT:
        mx = A.arm("p15_%s_max" % obj)
        u = A.mean([r["unanimous_pct"] for r in mx])
        n = A.mean([r["unanimous_pct"] for r in A.arm("p15_%s_novote" % obj)])
        floors[obj] = u
        print("%-12s %11.2f%% %11.2f%%   %s" % (
            obj, u, n,
            "%.0f pp of it is NOT evidence of truth" % u))

    ctrl = A.arm("p15_trained_max")
    cu = A.mean([r["unanimous_pct"] for r in ctrl])
    ca = A.mean([r["any_correct_pct"] for r in ctrl])
    print("\n%-12s %11.2f%%  (accuracy %.2f%%)  <- the CORRECT case"
          % (CONTROL, cu, ca))

    print("\n**The comparison that matters**: unanimity is %.2f%% when the "
          "system is RIGHT\n   and %.2f%% when it is WRONG (strawberry)."
          % (cu, floors["strawberry"]))
    same = abs(cu - floors["strawberry"]) < 0.01
    print("   %s" % ("IDENTICAL -- unanimity cannot distinguish them at all."
                     if same else "They differ, so unanimity carries some signal."))

    print("\n--- 2. CAN CONFIDENCE SEPARATE TRUE FROM FALSE CONSENSUS? ---")
    print("The obvious rescue: trust unanimity only when evidence is high.\n")
    ev_ctrl = evidence_per_seed("p15_trained_max")
    print("%-26s %6s %10s   %s" % ("arm", "seeds", "mean ev", "state"))
    print("%-26s %6d %10.2f   %s"
          % ("%s (TRAINED, correct)" % CONTROL, len(ev_ctrl),
             statistics.mean(ev_ctrl), "correct"))
    rows = []
    for obj in HELD_OUT:
        e = evidence_per_seed("p15_%s_max" % obj)
        rows.append((obj, e))
        print("%-26s %6d %10.2f   %s"
              % ("%s (held out)" % obj, len(e), statistics.mean(e),
                 "100%% WRONG, %.0f%% unanimous" % floors[obj]))

    print("\nPaired against the correct case, per seed:")
    broken = False
    for obj, e in rows:
        if len(e) != len(ev_ctrl):
            print("  %-12s n=%d vs %d, skipped" % (obj, len(e), len(ev_ctrl)))
            continue
        t, note = paired_t(e, ev_ctrl)
        diff = statistics.mean(e) - statistics.mean(ev_ctrl)
        flag = ""
        if diff > 0 and abs(t) > 2.0:
            flag = "  <-- WRONG answer held MORE confidently than a correct one"
            broken = True
        print("  %-12s %+7.2f  t=%.2f %s%s" % (obj, diff, t, note, flag))

    print("\n--- VERDICT ---")
    if broken:
        print("**The confidence rescue FAILS.**")
        print("At least one held-out object carries HIGHER evidence than the")
        print("trained control while being 100% wrong. A confidence threshold")
        print("that admits the correct case also admits that one, so evidence")
        print("cannot be used to filter false consensus in this substrate.")
    else:
        print("Confidence separates the cases: a threshold could filter false")
        print("consensus. Report the threshold and its error rates.")

    print("\n**But note the ordering**, which is the constructive finding:")
    order = sorted([(statistics.mean(e), o) for o, e in rows])
    print("   %s" % " < ".join("%s(%.1f)" % (o, v) for v, o in order))
    print("   Evidence tracks how CLOSE the unseen object is to a trained one,")
    print("   not whether the answer is right. That is a usable signal for")
    print("   novelty detection -- and a misleading one for correctness.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
