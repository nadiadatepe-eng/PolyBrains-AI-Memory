#!/usr/bin/env python3
"""Does P7's unbalanced rotation sampling change P7's or P8's conclusions?

FOUND 2026-08-19 while re-running P9. `Predefined.__call__` indexes rotations by
`epoch % len(rotations)`. P7's powered run used 5 epochs against 4 rotations, so
rotation [35 45 0] was sampled TWICE and the other three once:

    [35 45  0]   800 episodes   40%
    [325 45  0]  400 episodes   20%
    [ 35 315 0]  400 episodes   20%
    [325 315 0]  400 episodes   20%

Every P7 and P8 number is therefore a weighted average over OOD poses, weighted
2:1:1:1 rather than 1:1:1:1. Nobody chose that; it is an artefact of 5 epochs
against a 4-element list.

This script re-computes P8's headline comparisons on a BALANCED subset -- the
first 10 episodes of each rotation per run, i.e. dropping the duplicate pass of
[35 45 0] -- and reports whether any verdict moves.

The point is not to expect a change. It is that an unbalanced design must be
shown not to matter rather than assumed not to.
"""
import csv
import glob
import re
import statistics
from collections import defaultdict

B = '[local Monty results directory]'
ARMS = [
    ('max (upstream)', 'pow_p7_e1_ood_max_s*'),
    ('mean (control)', 'pow_p7_e1_ood_mean_s*'),
    ('consensus', 'pow_p7_e1_ood_consensus_s*'),
    ('no voting', 'pow_p7_e1_ood_novote_s*'),
]
CRIT_T = 2.262  # t(9)


def episodes(path):
    """Return [(rotation, n_correct_modules)] per episode, in file order."""
    rows = list(csv.DictReader(open(path)))
    lm = defaultdict(list)
    for r in rows:
        lm[r['']].append(r)
    keys = list(lm)
    n = min(len(v) for v in lm.values())
    out = []
    for i in range(n):
        rot = lm[keys[0]][i]['primary_target_rotation_euler']
        ok = sum(1 for k in keys
                 if lm[k][i]['primary_performance'].startswith('correct'))
        out.append((rot, ok))
    return out, len(keys)


def acc(eps, n_lm, criterion, balanced):
    need = {'any': 1, 'majority': n_lm // 2 + 1, 'unanimous': n_lm}[criterion]
    if balanced:
        seen = defaultdict(int)
        keep = []
        for rot, ok in eps:
            if seen[rot] < 10:      # one pass per rotation
                keep.append(ok)
            seen[rot] += 1
        eps_use = keep
    else:
        eps_use = [ok for _, ok in eps]
    return 100 * sum(1 for c in eps_use if c >= need) / len(eps_use)


def by_seed(pat, criterion, balanced):
    out = {}
    for f in sorted(glob.glob(f'{B}/{pat}/eval_stats.csv')):
        seed = int(re.search(r'_s(\d+)/eval_stats', f).group(1))
        eps, n_lm = episodes(f)
        out[seed] = acc(eps, n_lm, criterion, balanced)
    return out


def paired(a, b):
    seeds = sorted(set(a) & set(b))
    d = [a[s] - b[s] for s in seeds]
    sd = statistics.stdev(d) if len(d) > 1 and len(set(d)) > 1 else 0.0
    t = (statistics.mean(d) / (sd / len(d) ** 0.5)) if sd else 0.0
    return statistics.mean(d), t


def main():
    print("=" * 78)
    print("P7/P8 ROBUSTNESS: does the unbalanced rotation sampling matter?")
    print("=" * 78)

    # show the imbalance
    tot = defaultdict(int)
    for _, pat in ARMS:
        for f in glob.glob(f'{B}/{pat}/eval_stats.csv'):
            eps, _ = episodes(f)
            for rot, _ok in eps:
                tot[rot] += 1
    n = sum(tot.values())
    print("\nAs run (5 epochs over 4 rotations):")
    for k, v in sorted(tot.items()):
        print(f"  {k:18} {v:5} episodes  {100*v/n:4.1f}%")

    print(f"\n{'':20}{'AS RUN (2:1:1:1)':>22}{'BALANCED (1:1:1:1)':>22}")
    print("-" * 78)
    for crit in ('any', 'majority', 'unanimous'):
        print(f"[{crit}]")
        for lab, pat in ARMS:
            a = statistics.mean(by_seed(pat, crit, False).values())
            b = statistics.mean(by_seed(pat, crit, True).values())
            flag = "  <-- moves" if abs(a - b) > 1.0 else ""
            print(f"  {lab:18}{a:>21.2f}%{b:>21.2f}%{flag}")

    print(f"\n{'='*78}\nHEADLINE COMPARISONS: no voting - max\n{'='*78}")
    for crit in ('any', 'majority', 'unanimous'):
        ra = paired(by_seed('pow_p7_e1_ood_novote_s*', crit, False),
                    by_seed('pow_p7_e1_ood_max_s*', crit, False))
        rb = paired(by_seed('pow_p7_e1_ood_novote_s*', crit, True),
                    by_seed('pow_p7_e1_ood_max_s*', crit, True))
        sig_a = 'SIG' if abs(ra[1]) > CRIT_T else 'n.s.'
        sig_b = 'SIG' if abs(rb[1]) > CRIT_T else 'n.s.'
        same = (ra[0] > 0) == (rb[0] > 0) and sig_a == sig_b
        print(f"  [{crit:9}] as run {ra[0]:+7.2f} pp (t={ra[1]:6.2f} {sig_a:4})"
              f"   balanced {rb[0]:+7.2f} pp (t={rb[1]:6.2f} {sig_b:4})"
              f"   {'same verdict' if same else 'VERDICT CHANGES'}")

    print("\nIf every verdict is unchanged, P7 and P8 stand as reported and the")
    print("imbalance is a design flaw worth stating, not a correction to make.")
    print()


if __name__ == '__main__':
    main()
