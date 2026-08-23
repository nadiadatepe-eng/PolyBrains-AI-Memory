#!/usr/bin/env python3
"""P9 analysis: does voting on an already-voted result help?

Applied mechanically against the predictions registered at 0d9b386, before the
mechanism was built:

    P9a  accuracy under UNANIMITY rises from rounds=1 to rounds=2
    P9b  the gain SATURATES: round 2->3 adds less than round 1->2
    P9c  agreement rises monotonically with rounds
    P9d  under AnyLMsMatch, iteration is WORSE and worsens with each round,
         because np.ma.max lets a confident error compound

Reported under all three criteria from P8, because P8's whole lesson is that a
single criterion can set the sign of the result. Reporting iterated voting under
only one read-out would repeat the mistake P8 exists to correct.

Statistics: arms share seeds, so paired t-tests throughout (the P7 correction).
"""
import csv
import glob
import re
import statistics
import sys
from collections import defaultdict

B = '[local Monty results directory]'
ARMS = [(r, f'p9_r{r}_s*') for r in (1, 2, 3)]
CRIT_T = 2.776  # t(4), two-tailed, alpha=0.05 -- 5 seeds


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


def accuracy(counts, n_lm, criterion):
    need = {'any': 1, 'majority': n_lm // 2 + 1, 'unanimous': n_lm}[criterion]
    return 100 * sum(1 for c in counts if c >= need) / len(counts)


def by_seed(pat, criterion=None):
    """criterion=None returns raw per-episode counts."""
    out = {}
    for f in sorted(glob.glob(f'{B}/{pat}/eval_stats.csv')):
        seed = int(re.search(r'_s(\d+)/eval_stats', f).group(1))
        counts, n_lm = per_episode_correct(f)
        out[seed] = counts if criterion is None else accuracy(counts, n_lm, criterion)
    return out


def paired(a, b):
    seeds = sorted(set(a) & set(b))
    if not seeds:
        return 0.0, 0.0, 0
    d = [a[s] - b[s] for s in seeds]
    sd = statistics.stdev(d) if len(d) > 1 and len(set(d)) > 1 else 0.0
    t = (statistics.mean(d) / (sd / len(d) ** 0.5)) if sd else 0.0
    return statistics.mean(d), t, len(d)


def main():
    have = {r: sorted(glob.glob(f'{B}/{pat}/eval_stats.csv')) for r, pat in ARMS}
    print("=" * 78)
    print("P9 -- ITERATED VOTING: vote, then vote on the result of that vote")
    print("=" * 78)
    for r, fs in have.items():
        print(f"  rounds={r}: {len(fs)} runs")
    if not all(have.values()):
        print("\nSweep incomplete -- rerun tools/run_p9.sh")
        return 1

    # GUARD, added after the first P9 sweep was voided. `Predefined` indexes
    # rotations by EPOCH, so n_eval_epochs=1 silently evaluates only the FIRST
    # of the four OOD rotations: 10 episodes and one OOD condition. It fails
    # silently -- the run completes and the analysis prints clean numbers.
    #
    # EXPECTED here is 40 = 10 objects x 4 rotations, one pass each. Note that
    # P7 has 50 because it ran FIVE epochs against a four-rotation list, so it
    # sampled [35 45 0] twice: a 2:1:1:1 weighting nobody chose. P9 at 4 epochs
    # is the balanced design. tools/check_rotation_balance.py shows every P7/P8
    # verdict survives rebalancing, so the two are still comparable in sign and
    # significance -- but absolute accuracies differ slightly by construction.
    EXPECT = 40
    bad = []
    for r, pat in ARMS:
        for f in sorted(glob.glob(f'{B}/{pat}/eval_stats.csv')):
            counts, _ = per_episode_correct(f)
            if len(counts) != EXPECT:
                bad.append((f.split('/')[-2], len(counts)))
    if bad:
        print(f"\n{'!'*78}\nREFUSING TO ANALYSE: {len(bad)} run(s) lack {EXPECT} episodes")
        for name, n in bad[:8]:
            print(f"  {name}: {n} episodes")
        print("10 episodes means n_eval_epochs was 1: only 1 of 4 OOD rotations.")
        print("Re-run tools/run_p9.sh.")
        print('!' * 78)
        return 1

    # --- accuracy under all three criteria -------------------------------
    data = {c: {r: by_seed(p, c) for r, p in ARMS}
            for c in ('any', 'majority', 'unanimous')}

    print(f"\n{'rounds':>8}" + "".join(f"{c:>14}" for c in
                                       ('any', 'majority', 'unanimous')))
    print("-" * 78)
    for r, _ in ARMS:
        row = f"{r:>8}"
        for c in ('any', 'majority', 'unanimous'):
            row += f"{statistics.mean(data[c][r].values()):>13.2f}%"
        print(row)

    # --- replication control ---------------------------------------------
    print(f"\n{'='*78}\nCONTROL: rounds=1 must reproduce P7's max arm\n{'='*78}")
    p7 = {}
    for f in sorted(glob.glob(f'{B}/pow_p7_e1_ood_max_s*/eval_stats.csv')):
        seed = int(re.search(r'_s(\d+)/eval_stats', f).group(1))
        counts, n_lm = per_episode_correct(f)
        p7[seed] = accuracy(counts, n_lm, 'any')
    shared = sorted(set(p7) & set(data['any'][1]))
    if shared:
        m, t, n = paired(data['any'][1], {k: p7[k] for k in shared})
        print(f"  rounds=1 vs P7 max, {n} shared seeds: {m:+.2f} pp, t={t:.2f}")
        print("  " + ("OK -- replication holds (within noise)" if abs(m) < 0.5 and abs(t) < 2.776
                      else "WARNING: rounds=1 does NOT reproduce P7. "
                           "The loop changed something other than round count; "
                           "every comparison below is confounded."))
    else:
        print("  no shared seeds with P7 -- cannot check replication")

    # --- pre-registered verdicts -----------------------------------------
    print(f"\n{'='*78}\nPRE-REGISTERED VERDICTS (registered 0d9b386)\n{'='*78}")

    u = data['unanimous']
    d12, t12, n12 = paired(u[2], u[1])
    d23, t23, _ = paired(u[3], u[2])
    print(f"\nP9a: accuracy under unanimity rises from rounds 1 to 2")
    print(f"  {statistics.mean(u[1].values()):.2f}% -> "
          f"{statistics.mean(u[2].values()):.2f}%  "
          f"({d12:+.2f} pp, t({n12-1})={t12:.2f})")
    print("  VERDICT:", "SUPPORTED" if d12 > 0 and abs(t12) > CRIT_T
          else ("directionally right, n.s." if d12 > 0 else "NOT SUPPORTED"))

    print(f"\nP9b: the gain saturates (2->3 adds less than 1->2)")
    print(f"  1->2 {d12:+.2f} pp   2->3 {d23:+.2f} pp")
    print("  VERDICT:", "SUPPORTED" if abs(d23) < abs(d12)
          else "NOT SUPPORTED (gain did not shrink)")

    print(f"\nP9c: agreement rises monotonically with rounds")
    means = []
    for r, p in ARMS:
        raw = by_seed(p)
        means.append(statistics.mean(
            [statistics.mean(v) for v in raw.values()]))
        five = sum(1 for v in raw.values() for c in v if c == 5)
        tot = sum(len(v) for v in raw.values())
        print(f"  rounds={r}: mean modules correct {means[-1]:.3f}   "
              f"5-of-5 in {five}/{tot} ({100*five/tot:.1f}%)")
    mono = means[0] <= means[1] <= means[2]
    print("  VERDICT:", "SUPPORTED" if mono else "NOT SUPPORTED (non-monotonic)")

    print(f"\nP9d: under AnyLMsMatch iteration is worse, and worsens per round")
    a = data['any']
    a12, ta12, _ = paired(a[2], a[1])
    a23, ta23, _ = paired(a[3], a[2])
    print(f"  rounds 1->2 {a12:+.2f} pp (t={ta12:.2f})   "
          f"2->3 {a23:+.2f} pp (t={ta23:.2f})")
    worse = a12 < 0 and a23 < 0
    print("  VERDICT:", "SUPPORTED -- confident errors compound" if worse
          else ("partially: first step worse only" if a12 < 0
                else "NOT SUPPORTED -- iteration does not hurt under `any`"))

    # --- the falsifier ----------------------------------------------------
    print(f"\n{'='*78}\nFALSIFIER CHECK (pre-registered)\n{'='*78}")
    spread = [statistics.mean(data[c][r].values())
              for c in ('any', 'majority', 'unanimous') for r, _ in ARMS]
    flat = max(spread) - min(spread) < 1.0
    print(f"  accuracy flat across every criterion and round? "
          f"{'YES -- vote is at a fixed point after one round' if flat else 'no'}")
    print("  NOTE: send_none% per round is recorded by "
          "IteratedVotingMonty.vote_round_summary().")
    print("  P6's rule: if silence CLIMBS with rounds, modules are dropping out,")
    print("  not converging, and any accuracy change is that instead.")
    print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
