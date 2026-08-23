#!/usr/bin/env python3
"""P8b: is the unanimity result real, or is it circular?

THE WORRY. Unanimity rewards agreement. Voting manufactures agreement. So
"voting wins under unanimity" could be true by construction and say nothing
about accuracy -- exactly the same species of artefact as the AnyLMsMatch
objection it was written to answer. Swapping one biased criterion for the
opposite bias is not progress.

THE DISCRIMINATING TEST. Agreement alone cannot explain a gain in UNANIMOUS
CORRECTNESS, because agreeing on a wrong answer scores zero under `unanimous`.
So we separate the two things voting can do:

  lift    episodes where more modules are correct than without voting
  drag    episodes where voting makes previously-correct modules wrong,
          including total collapse (0 of 5 correct = correlated failure)

If voting only manufactured agreement we would see drag and collapse rising
with no gain in fully-correct episodes. If voting genuinely propagates correct
evidence, fully-correct episodes rise. Both can be true at once, and the
honest report is the net of the two, per arm.

Also reports mean modules-correct per episode, which is criterion-free: it
uses no threshold at all, so it cannot be biased toward either read-out.
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
CRIT_T = 2.262


def per_episode_correct(path):
    rows = list(csv.DictReader(open(path)))
    lm = defaultdict(list)
    for r in rows:
        lm[r['']].append(r)
    keys = list(lm)
    n = min(len(v) for v in lm.values())
    return [sum(1 for k in keys
                if lm[k][i]['primary_performance'].startswith('correct'))
            for i in range(n)], len(keys)


def by_seed(pat):
    out = {}
    for f in sorted(glob.glob(f'{B}/{pat}/eval_stats.csv')):
        seed = int(re.search(r'_s(\d+)/eval_stats', f).group(1))
        out[seed] = per_episode_correct(f)[0]
    return out


def paired_t(d):
    sd = statistics.stdev(d) if len(d) > 1 and len(set(d)) > 1 else 0.0
    return (statistics.mean(d), (statistics.mean(d) / (sd / len(d) ** 0.5)) if sd else 0.0)


def main():
    arms = {lab: by_seed(pat) for lab, pat in ARMS}

    print("=" * 78)
    print("P8b -- IS THE UNANIMITY RESULT CIRCULAR? lift vs drag, per arm")
    print("=" * 78)

    print("\nDistribution of modules-correct per episode, BY ARM (500 eps each):")
    print(f"\n{'arm':20}" + "".join(f"{k:>8}" for k in range(6)) + f"{'mean':>9}")
    print("-" * 78)
    for lab, _ in ARMS:
        allc = [c for seed in arms[lab].values() for c in seed]
        d = defaultdict(int)
        for c in allc:
            d[c] += 1
        row = f"{lab:20}" + "".join(f"{d[k]:>8}" for k in range(6))
        print(row + f"{statistics.mean(allc):>9.3f}")

    print("\n  'mean' is criterion-free: no threshold, so it cannot favour either")
    print("  read-out. If voting only manufactured agreement without helping, it")
    print("  would NOT raise this number.")

    nv = arms['no voting']
    seeds = sorted(nv)

    print(f"\n{'='*78}")
    print("MEAN MODULES CORRECT -- paired against no voting")
    print("=" * 78)
    for lab, _ in ARMS:
        if lab == 'no voting':
            continue
        d = [statistics.mean(arms[lab][s]) - statistics.mean(nv[s]) for s in seeds]
        m, t = paired_t(d)
        print(f"  {lab:20} {m:+.3f} modules/episode   t({len(d)-1}) = {t:6.2f}  "
              f"{'SIGNIFICANT' if abs(t) > CRIT_T else 'n.s.'}")

    print(f"\n{'='*78}")
    print("LIFT vs DRAG -- episode-by-episode, paired on seed AND episode index")
    print("=" * 78)
    print("\n(episodes are the same objects in the same order across arms, so a")
    print(" per-episode comparison against the no-voting arm is meaningful)\n")
    print(f"{'arm':20}{'lifted':>9}{'dragged':>9}{'net':>9}"
          f"{'collapse 5->0':>15}{'rescued 0->5':>14}")
    print("-" * 78)
    for lab, _ in ARMS:
        if lab == 'no voting':
            continue
        lift = drag = coll = resc = 0
        for s in seeds:
            a, b = arms[lab][s], nv[s]
            for x, y in zip(a, b):
                if x > y:
                    lift += 1
                elif x < y:
                    drag += 1
                if y == 5 and x == 0:
                    coll += 1
                if y == 0 and x == 5:
                    resc += 1
        print(f"{lab:20}{lift:>9}{drag:>9}{lift-drag:>+9}{coll:>15}{resc:>14}")

    print(f"\n{'='*78}")
    print("VERDICT")
    print("=" * 78)
    mx = arms['max (upstream)']
    d = [statistics.mean(mx[s]) - statistics.mean(nv[s]) for s in seeds]
    m, t = paired_t(d)
    if m > 0 and abs(t) > CRIT_T:
        print(f"  Voting raises mean modules-correct by {m:+.3f}/episode "
              f"(t={t:.2f}, significant),")
        print("  on a metric with NO threshold. The unanimity result is therefore")
        print("  NOT purely an artefact of rewarding agreement: voting is")
        print("  propagating correct evidence, not merely copying.")
    elif m <= 0:
        print(f"  Voting does NOT raise mean modules-correct ({m:+.3f}, t={t:.2f}).")
        print("  The unanimity advantage is then consistent with voting merely")
        print("  manufacturing agreement, and P8's flip is CIRCULAR -- it swaps")
        print("  one biased criterion for its mirror image.")
    else:
        print(f"  Inconclusive: {m:+.3f} modules/episode, t={t:.2f}, not significant.")
    print()


if __name__ == '__main__':
    main()
