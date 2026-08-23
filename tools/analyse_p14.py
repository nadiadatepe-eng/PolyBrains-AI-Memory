#!/usr/bin/env python3
"""Analyse P14 (E-null): is unanimity about truth, or about coordination?

Pre-registered in `PREDICTIONS.md`. Reasoning in
`reports/reconsideration-consensus.md`.

**This analyser is validated against synthetic data with a known answer** by
`tests/test_analyse_p14.py`, because two of 2026-08-19's flaws lived in analysis
code, where no config audit would have found them. A zero-variance t-test once
reported a -100 pp effect as non-significant.

Reads `eval_stats.csv` per run: one row per (episode, LM). Unanimity is computed
over `most_likely_object` within an episode.
"""
from __future__ import annotations

import csv
import os
import statistics
import sys
from collections import defaultdict

RUNS = os.path.expanduser("~/tbp/results/monty/projects/monty_runs")
SEEDS = [42, 43, 44, 45, 46]
HELD_OUT = "dice"


def load(run):
    """-> list of episodes; each episode is a list of (guess, target, correct)."""
    path = os.path.join(RUNS, run, "eval_stats.csv")
    if not os.path.exists(path):
        return None
    rows = list(csv.DictReader(open(path)))
    if not rows:
        return None
    # Rows are written in (episode, lm) order, 5 LMs per episode. There is no
    # episode column, so group by position -- and assert the count divides,
    # because a partial episode would silently shift every group.
    if len(rows) % 5 != 0:
        print("  WARNING %s: %d rows, not a multiple of 5 -- partial episode"
              % (run, len(rows)))
    eps = []
    for i in range(0, len(rows) - 4, 5):
        chunk = rows[i:i + 5]
        eps.append([(r["most_likely_object"], r["primary_target_object"],
                     r["primary_performance"]) for r in chunk])
    return eps


def stats_for(run):
    eps = load(run)
    if eps is None:
        return None
    n = len(eps)
    if n == 0:
        return None
    unanimous = 0
    correct_any = 0
    silent = 0
    for ep in eps:
        guesses = [g for g, _t, _p in ep]
        # `no_match` / empty is silence, not a vote. Nadi's P6 lesson: silence
        # and agreement look identical in a count and are opposite facts.
        voiced = [g for g in guesses if g and g != "no_match"]
        silent += len(guesses) - len(voiced)
        if voiced and len(set(voiced)) == 1 and len(voiced) == len(guesses):
            unanimous += 1
        if any(p.startswith("correct") for _g, _t, p in ep):
            correct_any += 1
    return {
        "episodes": n,
        "unanimous_pct": 100.0 * unanimous / n,
        "any_correct_pct": 100.0 * correct_any / n,
        "send_none_pct": 100.0 * silent / (n * 5),
        "target": eps[0][0][1],
        "guesses": [g for ep in eps for g, _t, _p in ep],
    }


def arm(name):
    out = []
    for s in SEEDS:
        st = stats_for("%s_s%d" % (name, s))
        if st:
            out.append(st)
    return out


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def paired_t(a, b):
    """Paired t on per-seed differences. Zero variance is reported as such."""
    if len(a) != len(b) or len(a) < 2:
        return float("nan"), "n<2"
    d = [x - y for x, y in zip(a, b)]
    m = mean(d)
    sd = statistics.stdev(d)
    if sd == 0:
        # A -100 pp effect with sd=0 was once reported n.s. because the code
        # forced t=0. Every seed moving identically is the STRONGEST evidence.
        return float("inf") if m != 0 else 0.0, "sd=0 (identical across seeds)"
    return m / (sd / len(d) ** 0.5), ""


def main() -> int:
    print("P14 (E-null) -- held-out target: %s\n" % HELD_OUT)
    arms = {n: arm(n) for n in
            ("p14_holdout_max", "p14_holdout_novote", "p14_trained_max")}

    for n, rs in arms.items():
        if not rs:
            print("MISSING: %s has no runs" % n)
            return 1

    print("%-22s %6s %10s %10s %10s" %
          ("arm", "seeds", "unanimous", "any corr", "send_none"))
    for n, rs in arms.items():
        print("%-22s %6d %9.2f%% %9.2f%% %9.2f%%" % (
            n, len(rs), mean([r["unanimous_pct"] for r in rs]),
            mean([r["any_correct_pct"] for r in rs]),
            mean([r["send_none_pct"] for r in rs])))

    print("\n--- CONTROLS (checked before any verdict) ---")
    ok = True

    # C1: impossibility. If anything is correct on the held-out object, it
    # leaked into training and every number here is void.
    for n in ("p14_holdout_max", "p14_holdout_novote"):
        acc = mean([r["any_correct_pct"] for r in arms[n]])
        good = acc == 0.0
        ok &= good
        print("C1 %-20s accuracy on held-out target is 0%%: %s (%.2f%%)"
              % (n, "PASS" if good else "FAIL -- OBJECT LEAKED", acc))

    # C2: replication. A broken 9-object model fails everything, and its
    # unanimity would look like a finding.
    acc = mean([r["any_correct_pct"] for r in arms["p14_trained_max"]])
    good = acc >= 80.0
    ok &= good
    print("C2 trained-object control reproduces accuracy: %s (%.2f%%)"
          % ("PASS" if good else "FAIL -- MODEL IS BROKEN, SWEEP VOID", acc))

    # C3: silence must not explain agreement (P6).
    sn = mean([r["send_none_pct"] for r in arms["p14_holdout_max"]])
    good = sn < 50.0
    ok &= good
    print("C3 send_none%% does not explain the result: %s (%.2f%%)"
          % ("PASS" if good else "FAIL -- measuring absence", sn))

    if not ok:
        print("\nCONTROLS FAILED -- no verdict is reported.")
        return 1

    print("\n--- VERDICTS ---")
    mx = [r["unanimous_pct"] for r in arms["p14_holdout_max"]]
    nv = [r["unanimous_pct"] for r in arms["p14_holdout_novote"]]

    m = mean(mx)
    print("P14a unanimity >= 15%% on an impossible target: %s (%.2f%%)"
          % ("SUPPORTED" if m >= 15.0 else "NOT SUPPORTED", m))

    t, note = paired_t(mx, nv)
    diff = mean(mx) - mean(nv)
    print("P14b voting raises agreement on an impossible target: %s"
          % ("SUPPORTED" if diff > 0 else "NOT SUPPORTED"))
    print("     max %.2f%% - novote %.2f%% = %+.2f pp, t=%.2f %s"
          % (mean(mx), mean(nv), diff, t, note))

    # What did they converge ON? A single attractor is the strongest form of
    # the finding: not noise, but one wrong answer the group settles into.
    for n in ("p14_holdout_max", "p14_holdout_novote"):
        gs = [g for r in arms[n] for g in r["guesses"]]
        counts = defaultdict(int)
        for g in gs:
            counts[g] += 1
        top = sorted(counts.items(), key=lambda kv: -kv[1])[:3]
        print("     %-20s converged on: %s" % (n, top))

    return 0


if __name__ == "__main__":
    sys.exit(main())
