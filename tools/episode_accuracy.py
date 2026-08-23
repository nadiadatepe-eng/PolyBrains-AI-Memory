#!/usr/bin/env python3
"""Correct per-episode accuracy from Monty's eval_stats.csv.

WHY THIS EXISTS: eval_stats.csv has one row per learning module per episode.
Counting rows conflates "how many modules were right" with "was the system
right", and inflates the apparent sample size by the number of LMs. A 5-LM run
of 10 episodes yields 50 rows, which naive counting reports as 50 episodes.

The system-level verdict per episode is taken across LMs using the configured
match criterion (AnyLMsMatch), so an episode counts as correct if any LM
reached a correct terminal state.
"""
import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def episode_accuracy(path):
    rows = list(csv.DictReader(open(path)))
    if not rows:
        return None
    lm_rows = defaultdict(list)
    for r in rows:
        lm_rows[r['']].append(r)
    n_ep = min(len(v) for v in lm_rows.values())
    correct = 0
    for i in range(n_ep):
        verdicts = [lm_rows[k][i]['primary_performance'] for k in lm_rows]
        if any(v.startswith('correct') for v in verdicts):
            correct += 1
    return correct, n_ep, len(lm_rows)


def main(paths):
    print(f"{'run':46} {'eps':>5} {'LMs':>4} {'acc':>8}")
    print("-" * 68)
    accs = []
    for p in paths:
        p = Path(p)
        f = p / 'eval_stats.csv' if p.is_dir() else p
        if not f.exists():
            continue
        r = episode_accuracy(f)
        if not r:
            continue
        ok, n, nlm = r
        acc = 100 * ok / n
        accs.append(acc)
        print(f"{f.parent.name:46} {n:>5} {nlm:>4} {acc:>7.1f}%")
    if len(accs) > 1:
        print("-" * 68)
        print(f"{'mean':46} {'':>5} {'':>4} {statistics.mean(accs):>7.1f}%")
        print(f"{'stdev':46} {'':>5} {'':>4} {statistics.stdev(accs):>7.2f}pp")


if __name__ == '__main__':
    main(sys.argv[1:] or ['.'])
