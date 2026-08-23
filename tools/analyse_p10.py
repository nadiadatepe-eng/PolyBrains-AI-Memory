#!/usr/bin/env python3
"""P10 analysis: does adversarial review beat plain repetition?

Pre-registered at 5b8d64f, before the mechanism was built:

    P10a  parl-3 produces FEWER high-confidence errors than plain-3
          (episodes where all 5 modules agree on the WRONG object)
    P10b  PRECISION of unanimity rises: of episodes reaching 5-of-5, the
          fraction correct is higher under parl-3, even if unanimity is
          reached less often
    P10c  parl-3 reaches unanimity LESS often than plain-3 (opposition is
          friction; if it does not slow convergence it is doing nothing)
    P10d  the parl-noopp control sits between. If parl-noopp MATCHES parl-3,
          the effect is the phase structure and NOT the opposition, and
          P10a/b do not support the idea
    P10e  module order within a phase matters (parl-batch differs from parl-3)

WHY THE CONTROLS ARE THE POINT. P9 showed any extra exchange raises agreement:
3 plain rounds took unanimity 43.50 -> 79.00%. So "parliament raises unanimity"
would be uninformative. The question is whether OPPOSITION buys something plain
repetition does not, at equal exchange count.

Nadi's success criterion was "the answers will be more genuine because of two
levels of confirmation". Operationalised as P10a + P10b: confident agreement
should become harder to reach, and what survives should be right more often.

Statistics: arms share seeds, so paired t-tests (the P7 correction). n=5 seeds,
so t(4) needs |t| > 2.776.
"""
import csv
import glob
import re
import statistics
import sys
from collections import defaultdict

B = '[local Monty results directory]'
CRIT_T = 2.776
ARMS = {
    'parl-3': 'p10_parl3_s*',
    'parl-noopp': 'p10_parlnoopp_s*',
    'parl-batch': 'p10_parlbatch_s*',
    'plain-3': 'p9_r3_s*',      # P9's equal-exchange control
    'plain-1': 'p9_r1_s*',      # single exchange, the baseline
}
EXPECT_EPISODES = 40


def episodes(path):
    """Per episode: (n_correct, n_lms, all_agree_on_same_object, agreed_right).

    `most_likely_object` lets us measure the thing that actually matters here:
    an episode where every module names the SAME object and that object is
    WRONG. Counting `n_correct == 0` instead would conflate confident consensus
    on a wrong answer with modules that merely all failed while disagreeing --
    opposite situations, and only the first is a "confident error".
    """
    rows = list(csv.DictReader(open(path)))
    lm = defaultdict(list)
    for r in rows:
        lm[r['']].append(r)
    keys = list(lm)
    n = min(len(v) for v in lm.values())
    out = []
    for i in range(n):
        ok = sum(1 for k in keys
                 if lm[k][i]['primary_performance'].startswith('correct'))
        named = [lm[k][i].get('most_likely_object', '') for k in keys]
        target = lm[keys[0]][i].get('primary_target_object', '')
        named_set = {x for x in named if x not in ('', 'None')}
        agree = len(named_set) == 1 and len(named) == len(keys)
        agreed_right = agree and next(iter(named_set)) == target
        out.append((ok, len(keys), agree, agreed_right))
    return out


def by_seed(pat):
    out = {}
    for f in sorted(glob.glob(f'{B}/{pat}/eval_stats.csv')):
        seed = int(re.search(r'_s(\d+)/eval_stats', f).group(1))
        out[seed] = episodes(f)
    return out


def metrics(eps):
    """Per-run metrics, including the two that encode 'more genuine'."""
    n = len(eps)
    unan = [e for e in eps if e[0] == e[1]]
    agree = [e for e in eps if e[2]]
    agree_right = [e for e in eps if e[3]]
    # A CONFIDENT ERROR: every module named the same object, and it was wrong.
    conf_wrong = [e for e in eps if e[2] and not e[3]]
    return {
        'any': 100 * sum(1 for e in eps if e[0] >= 1) / n,
        'unanimous': 100 * len(unan) / n,
        'mean_correct': statistics.mean(e[0] for e in eps),
        # Of the episodes where all modules named the SAME object, how many
        # named the right one. This is "quality of agreement".
        'unan_precision': 100 * len(agree_right) / max(len(agree), 1),
        'conf_wrong_pct': 100 * len(conf_wrong) / n,
        'agree_pct': 100 * len(agree) / n,
    }


def paired(a, b, key):
    seeds = sorted(set(a) & set(b))
    if not seeds:
        return 0.0, 0.0, 0
    d = [metrics(a[s])[key] - metrics(b[s])[key] for s in seeds]
    m = statistics.mean(d)
    sd = statistics.stdev(d) if len(d) > 1 and len(set(d)) > 1 else 0.0
    if sd:
        t = m / (sd / len(d) ** 0.5)
    elif abs(m) < 1e-9:
        t = 0.0            # no effect and no spread: genuinely nothing
    else:
        # ZERO VARIANCE WITH A REAL EFFECT. Every seed moved by the same
        # non-zero amount, so the effect is perfectly consistent -- the
        # STRONGEST possible evidence, not the weakest. Returning t=0 here
        # (the old behaviour) reported a -100 pp difference as "n.s.".
        # Caught by tests/test_analyse_p12.py, which feeds a known-true
        # scenario and asserts the verdict. float('inf') is the honest value
        # and every caller compares |t| against a threshold.
        t = float('inf') if m > 0 else float('-inf')
    return m, t, len(d)


def main():
    data = {}
    for name, pat in ARMS.items():
        d = by_seed(pat)
        if d:
            data[name] = d

    print("=" * 78)
    print("P10 -- PARLIAMENTARY VOTING: does opposition beat plain repetition?")
    print("=" * 78)
    for name in ARMS:
        print(f"  {name:12}: {len(data.get(name, {}))} runs")

    missing = [n for n in ('parl-3', 'parl-noopp', 'plain-3') if n not in data]
    if missing:
        print(f"\nMissing required arms: {missing} -- run tools/run_p10.sh")
        return 1

    # GUARD: truncated runs are not comparable (three sweeps voided for this)
    bad = [(n, s, len(e)) for n, d in data.items() for s, e in d.items()
           if len(e) != EXPECT_EPISODES]
    if bad:
        print(f"\n{'!'*78}\nREFUSING TO ANALYSE: {len(bad)} run(s) lack "
              f"{EXPECT_EPISODES} episodes")
        for n, s, k in bad[:8]:
            print(f"  {n} seed {s}: {k}")
        print("Cause is almost certainly a missing n_eval_epochs=4.")
        print('!' * 78)
        return 1

    print(f"\n{'arm':13}{'any':>9}{'unanimous':>11}{'mean corr':>11}"
          f"{'unan prec':>11}{'conf wrong':>12}")
    print("-" * 78)
    for name in ARMS:
        if name not in data:
            continue
        ms = [metrics(e) for e in data[name].values()]
        agg = {k: statistics.mean(m[k] for m in ms) for k in ms[0]}
        print(f"{name:13}{agg['any']:>8.2f}%{agg['unanimous']:>10.2f}%"
              f"{agg['mean_correct']:>11.3f}{agg['unan_precision']:>10.2f}%"
              f"{agg['conf_wrong_pct']:>11.2f}%")

    print(f"\n{'='*78}\nPRE-REGISTERED VERDICTS (registered 5b8d64f)\n{'='*78}")

    # P10a -- fewer confidently-wrong episodes
    m, t, n = paired(data['parl-3'], data['plain-3'], 'conf_wrong_pct')
    print(f"\nP10a: parl-3 has FEWER confidently-wrong episodes than plain-3")
    print(f"  difference {m:+.2f} pp   t({n-1}) = {t:.2f}")
    print("  VERDICT:", "SUPPORTED" if m < 0 and abs(t) > CRIT_T
          else ("directionally right, n.s." if m < 0 else "NOT SUPPORTED"))

    # P10b -- precision of unanimity
    m, t, n = paired(data['parl-3'], data['plain-3'], 'unan_precision')
    print(f"\nP10b: precision of unanimity is HIGHER under parl-3  [the sharp one]")
    print(f"  difference {m:+.2f} pp   t({n-1}) = {t:.2f}")
    print("  VERDICT:", "SUPPORTED -- two-level confirmation trades quantity "
          "of agreement for quality" if m > 0 and abs(t) > CRIT_T
          else ("directionally right, n.s." if m > 0 else "NOT SUPPORTED"))

    # P10c -- opposition is friction
    m, t, n = paired(data['parl-3'], data['plain-3'], 'unanimous')
    print(f"\nP10c: parl-3 reaches unanimity LESS often than plain-3")
    print(f"  difference {m:+.2f} pp   t({n-1}) = {t:.2f}")
    print("  VERDICT:", "SUPPORTED" if m < 0 else
          "NOT SUPPORTED -- opposition did not slow convergence")

    # P10d -- the control that decides whether any of this is about OPPOSITION
    print(f"\nP10d: parl-noopp control -- structure vs opposition")
    for key in ('conf_wrong_pct', 'unan_precision', 'unanimous'):
        m1, t1, _ = paired(data['parl-3'], data['parl-noopp'], key)
        print(f"  parl-3 - parl-noopp on {key:16}: {m1:+7.2f} pp  t={t1:6.2f}"
              f"  {'SIG' if abs(t1) > CRIT_T else 'n.s.'}")
    m1, t1, _ = paired(data['parl-3'], data['parl-noopp'], 'unan_precision')
    if abs(t1) <= CRIT_T:
        print("  READING: opposition adds nothing over the phase structure alone.")
        print("           P10a/b, if positive, are about SEQUENCING not dissent.")
    else:
        print("  READING: opposition has an effect beyond the phase structure.")

    # P10e -- does order matter
    if 'parl-batch' in data:
        m, t, n = paired(data['parl-3'], data['parl-batch'], 'unanimous')
        print(f"\nP10e: sequential ordering matters (parl-3 vs parl-batch)")
        print(f"  difference {m:+.2f} pp   t({n-1}) = {t:.2f}")
        print("  VERDICT:", "SUPPORTED -- one-by-one is doing work"
              if abs(t) > CRIT_T
              else "NOT SUPPORTED -- 'one by one' changes nothing measurable")

    print(f"\n{'='*78}\nTHE MECHANISM QUESTION\n{'='*78}")
    print("  The reduction is np.ma.max: the loudest vote wins outright, so max")
    print("  cannot represent opposition, only volume. If every verdict above is")
    print("  null, the finding is about the AGGREGATION RULE -- that Monty's vote")
    print("  path structurally cannot express dissent -- not about parliaments.")
    print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
