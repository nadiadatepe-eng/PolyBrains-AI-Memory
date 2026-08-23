#!/usr/bin/env python3
"""P8: does the H1 refutation survive a unanimity criterion?

THE OBJECTION THIS TESTS. Every result so far scores an episode correct under
`AnyLMsMatch`: correct if ANY of the 5 modules reaches a correct terminal state.
That criterion rewards module INDEPENDENCE by construction -- 5 independent
modules get 5 lottery tickets, and voting (which makes modules agree) throws
tickets away. So "voting harms accuracy" might be a fact about the scoring rule
rather than about voting. This is the most obvious reviewer objection to P7.

WHAT THIS DOES. Re-scores the EXISTING P7 runs (40 runs x 50 episodes,
commit a88c029) under three read-outs. No new episodes are run, so nothing about
the runs can have been tuned to the outcome; only the criterion changes.

    any        >=1 of 5 modules correct  (upstream AnyLMsMatch, used so far)
    majority   >=3 of 5
    unanimous  all 5

Pre-registered in PREDICTIONS.md at commit 5e363dc, BEFORE any number below was
computed:
    P8a  under `unanimous`, the no-voting advantage SHRINKS
    P8b  under `unanimous`, voting BEATS no voting (sign of H1 effect flips)
    P8c  `majority` sits between the two, monotonically

Statistics: arms share seeds, so differences are tested with a PAIRED t-test.
This is the correction forced during P7, where an unpaired sd/sqrt(n) threshold
wrongly printed "SUPPORTED"; see tools/analyse_p7.py.
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
CRIT_T = 2.262  # t(9), two-tailed, alpha=0.05


def load(path):
    rows = list(csv.DictReader(open(path)))
    lm = defaultdict(list)
    for r in rows:
        lm[r['']].append(r)
    return lm, min(len(v) for v in lm.values())


def per_episode_correct(path):
    """Return list over episodes of how many LMs were correct, plus LM count."""
    lm, n = load(path)
    keys = list(lm)
    out = []
    for i in range(n):
        out.append(sum(1 for k in keys
                       if lm[k][i]['primary_performance'].startswith('correct')))
    return out, len(keys)


def accuracy(counts, n_lm, criterion):
    if criterion == 'any':
        need = 1
    elif criterion == 'majority':
        need = n_lm // 2 + 1
    elif criterion == 'unanimous':
        need = n_lm
    else:
        raise ValueError(criterion)
    return 100 * sum(1 for c in counts if c >= need) / len(counts)


def by_seed(pat, criterion):
    out = {}
    for f in sorted(glob.glob(f'{B}/{pat}/eval_stats.csv')):
        seed = int(re.search(r'_s(\d+)/eval_stats', f).group(1))
        counts, n_lm = per_episode_correct(f)
        out[seed] = accuracy(counts, n_lm, criterion)
    return out


def paired(a, b):
    """paired diff a - b over shared seeds -> (mean, t, n, wins, losses)"""
    seeds = sorted(set(a) & set(b))
    d = [a[s] - b[s] for s in seeds]
    sd = statistics.stdev(d) if len(d) > 1 and len(set(d)) > 1 else 0.0
    t = (statistics.mean(d) / (sd / len(d) ** 0.5)) if sd else 0.0
    return (statistics.mean(d), t, len(d),
            sum(1 for x in d if x > 0), sum(1 for x in d if x < 0))


def main():
    print("=" * 78)
    print("P8 -- UNANIMITY CRITERION: re-scoring P7's 2000 episodes, no new runs")
    print("=" * 78)

    # module-count distribution, to see whether unanimity has room to move
    counts_all, n_lm = [], None
    for _, pat in ARMS:
        for f in sorted(glob.glob(f'{B}/{pat}/eval_stats.csv')):
            c, n_lm = per_episode_correct(f)
            counts_all += c
    dist = defaultdict(int)
    for c in counts_all:
        dist[c] += 1
    print(f"\nHow many of {n_lm} modules are correct, per episode "
          f"({len(counts_all)} episodes, all arms):")
    for k in sorted(dist):
        print(f"  {k} correct : {dist[k]:>5}  ({100*dist[k]/len(counts_all):5.1f}%)")

    data = {}
    for crit in ('any', 'majority', 'unanimous'):
        data[crit] = {lab: by_seed(pat, crit) for lab, pat in ARMS}

    print(f"\n{'arm':20}" + "".join(f"{c:>14}" for c in
                                    ('any', 'majority', 'unanimous')))
    print("-" * 78)
    for lab, _ in ARMS:
        row = f"{lab:20}"
        for crit in ('any', 'majority', 'unanimous'):
            row += f"{statistics.mean(data[crit][lab].values()):>13.2f}%"
        print(row)

    print(f"\n{'='*78}\nPRE-REGISTERED VERDICTS (registered 5e363dc)\n{'='*78}")

    gaps = {}
    for crit in ('any', 'majority', 'unanimous'):
        nv = data[crit]['no voting']
        mx = data[crit]['max (upstream)']
        m, t, n, w, l = paired(nv, mx)
        gaps[crit] = m
        sig = 'SIGNIFICANT' if abs(t) > CRIT_T else 'n.s.'
        print(f"\n[{crit}] no voting - max = {m:+.2f} pp   "
              f"t({n-1}) = {t:.2f}  {sig}")
        print(f"         no-voting wins {w}, loses {l}, ties {n-w-l}")

    print(f"\n{'-'*78}")
    print(f"P8a: no-voting advantage shrinks under unanimity")
    print(f"  any {gaps['any']:+.2f} pp -> unanimous {gaps['unanimous']:+.2f} pp")
    print("  VERDICT:", "SUPPORTED" if gaps['unanimous'] < gaps['any']
          else "NOT SUPPORTED (advantage grew or held)")

    print(f"\nP8b: under unanimity, VOTING BEATS NO VOTING (sign flips)")
    nvu, mxu = data['unanimous']['no voting'], data['unanimous']['max (upstream)']
    m, t, n, w, l = paired(nvu, mxu)
    if m < 0 and abs(t) > CRIT_T:
        v = "SUPPORTED -- H1 refutation is criterion-dependent"
    elif m < 0:
        v = "directionally flipped but NOT significant"
    else:
        v = "NOT SUPPORTED -- no voting still wins under unanimity"
    print(f"  no voting - max = {m:+.2f} pp, t({n-1}) = {t:.2f}")
    print(f"  VERDICT: {v}")

    print(f"\nP8c: majority sits between any and unanimous, monotonically")
    mono = gaps['any'] >= gaps['majority'] >= gaps['unanimous']
    print(f"  {gaps['any']:+.2f} -> {gaps['majority']:+.2f} -> "
          f"{gaps['unanimous']:+.2f}")
    print("  VERDICT:", "SUPPORTED" if mono else "NOT SUPPORTED (non-monotonic)")

    print(f"\n{'-'*78}\nCONFOUND CHECK (pre-registered): floor effect?")
    for crit in ('any', 'majority', 'unanimous'):
        vals = [statistics.mean(data[crit][lab].values()) for lab, _ in ARMS]
        print(f"  {crit:10} range {min(vals):6.2f}% - {max(vals):6.2f}%  "
              f"spread {max(vals)-min(vals):5.2f} pp")
    print("  A spread that collapses to ~0 means the criterion compressed the")
    print("  arms, and the comparison is uninformative rather than negative.")

    print(f"\n{'='*78}\nSTANDING OF H1\n{'='*78}")
    if gaps['unanimous'] > 0:
        print("  H1 remains REFUTED under every criterion tested. The refutation")
        print("  SURVIVES its most obvious threat and is stronger than before.")
    else:
        print("  H1's refutation is CRITERION-DEPENDENT. It must be reported as")
        print("  relative to AnyLMsMatch, not as a general result.")
    print()


if __name__ == '__main__':
    main()
