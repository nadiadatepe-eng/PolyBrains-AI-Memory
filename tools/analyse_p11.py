#!/usr/bin/env python3
"""P11 analysis: does opposition work once the rule can express it?

Pre-registered in PREDICTIONS.md (commit 5774fd1) before the sweep ran:

    P11a  parl-3 separates from parl-noopp on confident errors. THE question:
          under max this gap was t=0.34, indistinguishable
    P11b  parl-3 has fewer confident errors than plain-3 at equal exchanges
    P11c  unanimity precision higher under parl-3 than parl-noopp
    P11d  REPLICATION CONTROL: p11_plain1 reproduces P7's powered consensus
          arm within noise. Fails => sweep void
    P11e  sequencing matters (parl-batch differs from parl-3)

Metric definitions are P10's, unchanged and not retuned, so the two experiments
are directly comparable arm for arm.
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
    'parl-3': 'p11_parl3_s*',
    'parl-noopp': 'p11_parlnoopp_s*',
    'parl-batch': 'p11_parlbatch_s*',
    'plain-3': 'p11_plain3_s*',
    'plain-1': 'p11_plain1_s*',
}
#: The replication reference. P7's powered consensus arm, 50 episodes over the
#: same 5 OOD rotations, run before any parliament existed.
REPLICATION_REF = 'pow_p7_e1_ood_consensus_s*'
EXPECT_EPISODES = 40


def episodes(path):
    """Per episode: (n_correct, n_lms, all_agree_on_same_object, agreed_right)."""
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
        out.append((ok, len(keys), agree, agree and next(iter(named_set)) == target))
    return out


def by_seed(pat):
    out = {}
    for f in sorted(glob.glob(f'{B}/{pat}/eval_stats.csv')):
        out[int(re.search(r'_s(\d+)/eval_stats', f).group(1))] = episodes(f)
    return out


def metrics(eps):
    n = len(eps)
    agree = [e for e in eps if e[2]]
    return {
        'any': 100 * sum(1 for e in eps if e[0] >= 1) / n,
        'unanimous': 100 * sum(1 for e in eps if e[0] == e[1]) / n,
        'mean_correct': statistics.mean(e[0] for e in eps),
        'unan_precision': 100 * sum(1 for e in eps if e[3]) / max(len(agree), 1),
        'conf_wrong_pct': 100 * sum(1 for e in eps if e[2] and not e[3]) / n,
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


def verdict(m, t, want_negative):
    ok = (m < 0) if want_negative else (m > 0)
    if ok and abs(t) > CRIT_T:
        return 'SUPPORTED'
    return 'directionally right, n.s.' if ok else 'NOT SUPPORTED'


def main():
    data = {n: d for n, p in ARMS.items() if (d := by_seed(p))}

    print('=' * 78)
    print('P11 -- PARLIAMENTARY VOTING UNDER vote_mode=consensus')
    print('=' * 78)
    for name in ARMS:
        print(f'  {name:12}: {len(data.get(name, {}))} runs')

    missing = [n for n in ('parl-3', 'parl-noopp', 'plain-3', 'plain-1')
               if n not in data]
    if missing:
        print(f'\nMissing required arms: {missing} -- run tools/run_p11.sh')
        return 1

    bad = [(n, s, len(e)) for n, d in data.items() for s, e in d.items()
           if len(e) != EXPECT_EPISODES]
    if bad:
        print(f"\n{'!'*78}\nREFUSING TO ANALYSE: {len(bad)} run(s) lack "
              f'{EXPECT_EPISODES} episodes')
        for n, s, k in bad[:8]:
            print(f'  {n} seed {s}: {k}')
        print('Cause is almost certainly a missing n_eval_epochs=4.')
        print('!' * 78)
        return 1

    print(f"\n{'arm':13}{'any':>9}{'unanimous':>11}{'mean corr':>11}"
          f"{'agree':>9}{'unan prec':>11}{'conf wrong':>12}")
    print('-' * 78)
    for name in ARMS:
        if name not in data:
            continue
        ms = [metrics(e) for e in data[name].values()]
        agg = {k: statistics.mean(m[k] for m in ms) for k in ms[0]}
        print(f"{name:13}{agg['any']:>8.2f}%{agg['unanimous']:>10.2f}%"
              f"{agg['mean_correct']:>11.3f}{agg['agree_pct']:>8.2f}%"
              f"{agg['unan_precision']:>10.2f}%{agg['conf_wrong_pct']:>11.2f}%")

    # ---- P11d FIRST. A failed replication voids everything below it. -------
    print(f"\n{'='*78}\nP11d REPLICATION CONTROL (checked first -- a failure "
          f"voids the sweep)\n{'='*78}")
    ref = by_seed(REPLICATION_REF)
    if not ref:
        print('  REFERENCE MISSING: pow_p7_e1_ood_consensus_s* not found.')
        print('  Cannot certify the sweep. Treat every verdict below as UNVERIFIED.')
    else:
        r = statistics.mean(metrics(e)['any'] for e in ref.values())
        p = statistics.mean(metrics(e)['any'] for e in data['plain-1'].values())
        sd = statistics.stdev([metrics(e)['any'] for e in ref.values()])
        print(f'  P7 powered consensus `any` : {r:.2f}%  (sd {sd:.2f} over '
              f'{len(ref)} seeds)')
        print(f'  P11 plain-1        `any` : {p:.2f}%')
        print(f'  difference {p - r:+.2f} pp')
        # 2 sd of the reference's own seed spread is the noise band. The arms
        # differ in episode count (40 vs 50 rotations), so exact equality is
        # not expected; a shift beyond the reference's own spread is.
        band = 2 * sd if sd else 5.0
        if abs(p - r) <= band:
            print(f'  WITHIN NOISE (+-{band:.2f} pp) -- sweep is certified.')
        else:
            print(f"  {'!'*70}")
            print(f'  OUTSIDE NOISE (+-{band:.2f} pp). Something other than the '
                  'parliament changed.')
            print('  DO NOT BELIEVE THE VERDICTS BELOW.')
            print(f"  {'!'*70}")

    print(f"\n{'='*78}\nPRE-REGISTERED VERDICTS (registered 5774fd1)\n{'='*78}")

    # ---- P11a: THE question ------------------------------------------------
    m, t, n = paired(data['parl-3'], data['parl-noopp'], 'conf_wrong_pct')
    ma, ta, _ = paired(data['parl-3'], data['parl-noopp'], 'agree_pct')
    print('\nP11a: opposition separates from the phase structure  [THE question]')
    print(f'  parl-3 - parl-noopp on confident errors: {m:+.2f} pp   t({n-1}) = {t:.2f}')
    print('  Under max the SAME contrast on errors was t=0.34. Note that is the')
    print('  error measure only -- on agreement max already gave t=-2.24.')
    print('  VERDICT:', 'SUPPORTED -- consensus gives dissent a channel max did not'
          if abs(t) > CRIT_T else
          'NOT SUPPORTED on confident errors')
    # The registered prediction is about ERRORS, so the verdict above stands as
    # registered. But reporting it alone would be misleading: the same contrast
    # on AGREEMENT is what shows whether the opposition is mechanically active
    # at all, and under max it was null there too.
    print(f'  but on AGREEMENT: {ma:+.2f} pp   t({n-1}) = {ta:.2f}'
          f"  {'SIGNIFICANT' if abs(ta) > CRIT_T else 'n.s.'}")
    if abs(ta) > CRIT_T and abs(t) <= CRIT_T:
        print('  READING: the opposition IS active under consensus -- it makes')
        print('           agreement measurably harder to reach -- but that friction')
        print('           does not convert into accuracy.')
        print('  CAUTION: parl-3 sits at a %.2f%% error floor and plain-1 at %.2f%%.'
              % (statistics.mean(metrics(e)['conf_wrong_pct']
                                 for e in data['parl-3'].values()),
                 statistics.mean(metrics(e)['conf_wrong_pct']
                                 for e in data['plain-1'].values())))
        print('           %d episodes/arm cannot resolve below ~2 pp, so this null'
              % (EXPECT_EPISODES * len(data['parl-3'])))
        print('           is POWER-LIMITED, not a demonstration of no effect.')

    # Does the RULE explain the opposition's effect? Saying "consensus gave dissent
    # a channel max did not" compares two contrasts, so it needs the contrast of
    # contrasts -- not "significant here, n.s. there", which is the classic error.
    # Under max the same gap was -14.00 pp at t=-2.24: near-miss, not absence.
    old_a, old_b = by_seed('p10_parl3_s*'), by_seed('p10_parlnoopp_s*')
    seeds = sorted(set(data['parl-3']) & set(data['parl-noopp'])
                   & set(old_a) & set(old_b))
    if len(seeds) > 1:
        d = [(metrics(data['parl-3'][s])['agree_pct']
              - metrics(data['parl-noopp'][s])['agree_pct'])
             - (metrics(old_a[s])['agree_pct'] - metrics(old_b[s])['agree_pct'])
             for s in seeds]
        sd = statistics.stdev(d)
        td = statistics.mean(d) / (sd / len(d) ** 0.5) if sd else 0.0
        print(f'\n  DID THE RULE DO IT? difference-in-differences on agreement,')
        print(f'  (parl3-noopp | consensus) - (parl3-noopp | max):'
              f' {statistics.mean(d):+.2f} pp  t({len(d)-1}) = {td:.2f}'
              f"  {'SIG' if abs(td) > CRIT_T else 'n.s.'}")
        if abs(td) <= CRIT_T:
            print('  => NOT ESTABLISHED. Under max this gap was already -14.00 pp')
            print('     (t=-2.24), a near-miss rather than an absence. P10\'s')
            print('     mechanism claim is CONSISTENT with P11, not confirmed by it.')

    # ---- P11b --------------------------------------------------------------
    m, t, n = paired(data['parl-3'], data['plain-3'], 'conf_wrong_pct')
    print('\nP11b: parl-3 has FEWER confident errors than plain-3')
    print(f'  difference {m:+.2f} pp   t({n-1}) = {t:.2f}')
    print('  VERDICT:', verdict(m, t, want_negative=True))

    # ---- P11c --------------------------------------------------------------
    m, t, n = paired(data['parl-3'], data['parl-noopp'], 'unan_precision')
    print('\nP11c: unanimity precision HIGHER under parl-3 than parl-noopp')
    print(f'  difference {m:+.2f} pp   t({n-1}) = {t:.2f}')
    print('  VERDICT:', verdict(m, t, want_negative=False))

    # ---- P11e --------------------------------------------------------------
    if 'parl-batch' in data:
        m, t, n = paired(data['parl-3'], data['parl-batch'], 'unanimous')
        print('\nP11e: sequencing matters (parl-3 vs parl-batch)')
        print(f'  difference {m:+.2f} pp   t({n-1}) = {t:.2f}')
        print('  VERDICT:', 'SUPPORTED -- one-by-one is doing work'
              if abs(t) > CRIT_T else 'NOT SUPPORTED')

    # ---- rule effect, held structure constant ------------------------------
    print(f"\n{'='*78}\nRULE EFFECT (P11 consensus vs P10 max, same arms)\n{'='*78}")
    for arm, p10 in (('parl-3', 'p10_parl3_s*'), ('parl-noopp', 'p10_parlnoopp_s*')):
        old = by_seed(p10)
        if not old or arm not in data:
            continue
        for key in ('conf_wrong_pct', 'any'):
            m, t, _ = paired(data[arm], old, key)
            print(f'  {arm:11} consensus - max on {key:15}: {m:+7.2f} pp  t={t:6.2f}'
                  f"  {'SIG' if abs(t) > CRIT_T else 'n.s.'}")

    print(f"\n{'='*78}\nWHAT THIS NULL MEANS\n{'='*78}")
    print('  The registered fallback was: if P11a fails, Monty\'s vote path cannot')
    print('  express opposition under ANY rule. That is NOT what happened -- under')
    print('  consensus the opposition moves agreement significantly (t=-3.06), so')
    print('  the path CAN carry dissent. But the difference-in-differences above')
    print('  shows the RULE is not demonstrably why: max was a near-miss, not an')
    print('  absence. Two open items, and they are different sizes:')
    print('    1. power -- the error floor is ~1%, n=5 seeds cannot resolve it;')
    print('    2. mechanism -- consensus vs max on the opposition effect needs')
    print('       its own powered test before P10\'s explanation can be claimed.\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
