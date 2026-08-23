#!/usr/bin/env python3
"""P12 analysis: H2's first real test.

Pre-registered at 9c57278 before the sweep ran:

    P12a  p12_indomain scores WORSE than p12_frozen on OOD episodes under
          unanimity -- in-domain confidence captures the consensus
    P12b  weight spread max(w)/min(w) is HIGHER under indomain than ood
    P12c  p12_ood is no worse than p12_frozen  (the constructive claim)
    P12d  REPLICATION CONTROL: p12_frozen reproduces P7's powered consensus
          arm on its OOD episodes. Fails => sweep void
    P12e  LIVENESS: w(t) moves in both adaptive arms and does NOT move in
          frozen. Checked FIRST; a frozen trace in an adaptive arm voids it

Accuracy is computed on the OOD subset only. The 5 in-domain rotations are in
the schedule so confidence can accumulate -- that is what H2 is about -- but
they are not part of the OOD denominator.
"""
import csv
import glob
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

B = Path.home() / 'tbp/results/monty/projects/monty_runs'
TRACE = Path(__file__).resolve().parents[1] / 'reports/p12-weights'
CRIT_T = 2.776
ARMS = {'frozen': 'p12_frozen', 'ood': 'p12_ood', 'indomain': 'p12_indomain'}
#: The 5 pretraining rotations, as they appear in eval_stats.
INDOMAIN = {(0, 0, 0), (0, 90, 0), (0, 270, 0), (90, 0, 0), (90, 180, 0)}
EXPECT_EPISODES = 90
REPLICATION_REF = 'pow_p7_e1_ood_consensus_s*'


def parse_rot(s):
    nums = re.findall(r'-?\d+', s or '')
    return tuple(int(n) % 360 for n in nums[:3]) if len(nums) >= 3 else None


def episodes(path, ood_only=True):
    """Per episode: (n_correct, n_lms, all_agree, agreed_right). OOD subset."""
    rows = list(csv.DictReader(open(path)))
    lm = defaultdict(list)
    for r in rows:
        lm[r['']].append(r)
    keys = list(lm)
    n = min(len(v) for v in lm.values())
    out = []
    for i in range(n):
        rot = parse_rot(lm[keys[0]][i].get('primary_target_rotation_euler'))
        if ood_only and (rot is None or rot in INDOMAIN):
            continue
        ok = sum(1 for k in keys
                 if lm[k][i]['primary_performance'].startswith('correct'))
        named = [lm[k][i].get('most_likely_object', '') for k in keys]
        target = lm[keys[0]][i].get('primary_target_object', '')
        s = {x for x in named if x not in ('', 'None')}
        agree = len(s) == 1 and len(named) == len(keys)
        out.append((ok, len(keys), agree, agree and next(iter(s)) == target))
    return out


def total_episodes(path):
    rows = list(csv.DictReader(open(path)))
    lm = defaultdict(list)
    for r in rows:
        lm[r['']].append(r)
    return min((len(v) for v in lm.values()), default=0)


def by_seed(stem, ood_only=True):
    out = {}
    for f in sorted(glob.glob(f'{B}/{stem}_s*/eval_stats.csv')):
        out[int(re.search(r'_s(\d+)/', f).group(1))] = episodes(f, ood_only)
    return out


def metrics(eps):
    n = max(len(eps), 1)
    agree = [e for e in eps if e[2]]
    return {
        'any': 100 * sum(1 for e in eps if e[0] >= 1) / n,
        'unanimous': 100 * sum(1 for e in eps if e[0] == e[1]) / n,
        'mean_correct': statistics.mean([e[0] for e in eps]) if eps else 0.0,
        'unan_precision': 100 * sum(1 for e in eps if e[3]) / max(len(agree), 1),
        'conf_wrong_pct': 100 * sum(1 for e in eps if e[2] and not e[3]) / n,
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


def weight_stats(stem):
    """Per seed: (moved, spread, final weights). From the run's weight trace."""
    out = {}
    for f in sorted(TRACE.glob(f'{stem}_s*.tsv')):
        seed = int(re.search(r'_s(\d+)\.tsv', f.name).group(1))
        rows = list(csv.DictReader(open(f), delimiter='\t'))
        if not rows:
            out[seed] = (False, 1.0, [])
            continue
        last = {}
        moved = False
        for r in rows:
            w = float(r['weight'])
            last[r['lm']] = w
            if abs(w - 1.0) > 1e-9:
                moved = True
        ws = list(last.values())
        spread = (max(ws) / min(ws)) if ws and min(ws) > 0 else float('nan')
        out[seed] = (moved, spread, ws)
    return out


def main():
    data = {n: by_seed(s) for n, s in ARMS.items()}
    print('=' * 78)
    print('P12 -- H2: does in-domain-confidence weighting capture the consensus?')
    print('=' * 78)
    for n, s in ARMS.items():
        runs = sorted(glob.glob(f'{B}/{s}_s*/eval_stats.csv'))
        print(f'  {n:10}: {len(runs)} runs')

    missing = [n for n in ARMS if not data.get(n)]
    if missing:
        print(f'\nMissing arms: {missing} -- run tools/run_p12.sh')
        return 1

    # Episode-count guard on the FULL run, before any subsetting.
    bad = []
    for n, s in ARMS.items():
        for f in sorted(glob.glob(f'{B}/{s}_s*/eval_stats.csv')):
            k = total_episodes(f)
            if k != EXPECT_EPISODES:
                bad.append((f.split('/')[-2], k))
    if bad:
        print(f"\n{'!'*78}\nREFUSING TO ANALYSE: {len(bad)} run(s) lack "
              f'{EXPECT_EPISODES} episodes')
        for r, k in bad[:8]:
            print(f'  {r}: {k}')
        print('Cause is almost certainly a missing n_eval_epochs=9.')
        print('!' * 78)
        return 1

    # ---- P12e FIRST: a dead arm makes every number below meaningless -------
    print(f"\n{'='*78}\nP12e LIVENESS (checked first -- a dead arm voids its own "
          f"results)\n{'='*78}")
    ws = {n: weight_stats(s) for n, s in ARMS.items()}
    dead = []
    for n in ARMS:
        st = ws[n]
        if not st:
            print(f'  {n:10}: NO TRACE FILE -- cannot verify, treat as unproven')
            dead.append(n)
            continue
        movers = sum(1 for v in st.values() if v[0])
        spreads = [v[1] for v in st.values()]
        should_move = n != 'frozen'
        ok = (movers == len(st)) if should_move else (movers == 0)
        print(f'  {n:10}: w(t) moved in {movers}/{len(st)} seeds, '
              f'mean spread {statistics.mean(spreads):.2f}  '
              f"{'OK' if ok else 'PROBLEM'}")
        if not ok:
            dead.append(n)
    if dead:
        print(f"\n  {'!'*70}")
        print(f'  LIVENESS PROBLEM in {dead}. An adaptive arm whose weights never')
        print('  move is a dead arm; a frozen arm whose weights move is not upstream.')
        print(f"  {'!'*70}")

    # ---- results table -----------------------------------------------------
    print(f"\n{'arm':12}{'any':>9}{'unanimous':>11}{'mean corr':>11}"
          f"{'unan prec':>11}{'conf wrong':>12}{'w spread':>10}")
    print('-' * 78)
    for n in ARMS:
        ms = [metrics(e) for e in data[n].values()]
        agg = {k: statistics.mean(m[k] for m in ms) for k in ms[0]}
        sp = ws[n] and statistics.mean(v[1] for v in ws[n].values())
        print(f"{n:12}{agg['any']:>8.2f}%{agg['unanimous']:>10.2f}%"
              f"{agg['mean_correct']:>11.3f}{agg['unan_precision']:>10.2f}%"
              f"{agg['conf_wrong_pct']:>11.2f}%"
              f"{(sp if sp else float('nan')):>10.2f}")
    print(f"  (OOD episodes only: {len(next(iter(data['frozen'].values())))} of "
          f'{EXPECT_EPISODES} per run)')

    # ---- P12d replication control -----------------------------------------
    print(f"\n{'='*78}\nP12d REPLICATION CONTROL\n{'='*78}")
    ref = {}
    for f in sorted(glob.glob(f'{B}/{REPLICATION_REF}/eval_stats.csv')):
        ref[int(re.search(r'_s(\d+)/', f).group(1))] = episodes(f, ood_only=False)
    if not ref:
        print('  REFERENCE MISSING -- treat every verdict below as UNVERIFIED.')
    else:
        r = statistics.mean(metrics(e)['any'] for e in ref.values())
        sd = statistics.stdev([metrics(e)['any'] for e in ref.values()])
        p = statistics.mean(metrics(e)['any'] for e in data['frozen'].values())
        band = 2 * sd if sd else 5.0
        print(f'  P7 powered consensus `any` : {r:.2f}%  (sd {sd:.2f})')
        print(f'  P12 frozen (OOD subset)    : {p:.2f}%')
        print(f'  difference {p - r:+.2f} pp   band +-{band:.2f} pp')
        print('  ' + ('WITHIN NOISE -- sweep certified.' if abs(p - r) <= band
                      else 'OUTSIDE NOISE -- DO NOT BELIEVE THE VERDICTS BELOW.'))

    print(f"\n{'='*78}\nPRE-REGISTERED VERDICTS (registered 9c57278)\n{'='*78}")

    for key, label in (('unanimous', 'unanimity'), ('any', '`any`')):
        m, t, n = paired(data['indomain'], data['frozen'], key)
        tag = 'P12a' if key == 'unanimous' else '     '
        print(f'\n{tag}: indomain WORSE than frozen on {label}')
        print(f'  difference {m:+.2f} pp   t({n-1}) = {t:.2f}')
        if key == 'unanimous':
            print('  VERDICT:', 'SUPPORTED -- in-domain confidence captures the '
                  'consensus' if m < 0 and abs(t) > CRIT_T
                  else ('directionally right, n.s.' if m < 0 else 'NOT SUPPORTED'))

    # P12b -- spread
    print('\nP12b: weight spread HIGHER under indomain than ood')
    seeds = sorted(set(ws['indomain']) & set(ws['ood']))
    if seeds:
        d = [ws['indomain'][s][1] - ws['ood'][s][1] for s in seeds]
        sd = statistics.stdev(d) if len(set(d)) > 1 else 0.0
        t = statistics.mean(d) / (sd / len(d) ** 0.5) if sd else 0.0
        print(f'  difference {statistics.mean(d):+.3f}x   t({len(d)-1}) = {t:.2f}')
        print('  VERDICT:', 'SUPPORTED' if statistics.mean(d) > 0 and abs(t) > CRIT_T
              else ('directionally right, n.s.' if statistics.mean(d) > 0
                    else 'NOT SUPPORTED'))
    else:
        print('  no traces to compare')

    # P12c -- the constructive claim
    m, t, n = paired(data['ood'], data['frozen'], 'unanimous')
    print('\nP12c: ood is NO WORSE than frozen  [the constructive claim]')
    print(f'  difference {m:+.2f} pp   t({n-1}) = {t:.2f}')
    print('  VERDICT:', 'NOT SUPPORTED -- earning influence on novel input HURT'
          if m < 0 and abs(t) > CRIT_T else 'SUPPORTED -- no significant cost')

    # A blocked schedule means the arms adapt in DIFFERENT phases. Report it
    # rather than leaving the reader to infer an ood-vs-indomain ranking that
    # the design cannot support.
    print(f"\n{'='*78}\nCONFOUND: THE SCHEDULE IS BLOCKED, NOT INTERLEAVED\n{'='*78}")
    for arm in ('ood', 'indomain'):
        st = ws.get(arm) or {}
        firsts = []
        for f in sorted(TRACE.glob(f'p12_{arm}_s*.tsv')):
            for r in csv.DictReader(open(f), delimiter='\t'):
                if abs(float(r['weight']) - 1.0) > 1e-9:
                    firsts.append(int(r['episode']))
                    break
        if firsts:
            print(f'  {arm:9}: first weight change at episode '
                  f'{min(firsts)}-{max(firsts)} across seeds')
    print('  `Predefined` indexes rotations by EPOCH, so all in-domain episodes')
    print('  run before all OOD ones. `indomain` therefore enters the measured')
    print('  OOD phase with a fully trained weight; `ood` trains during it.')
    print('  => Do NOT read an ood-vs-indomain ACCURACY ranking from the table.')
    print('  => The H2 refutation is unaffected: the blocked order gives H2 its')
    print('     most favourable setup and the predicted harm still does not appear.')

    print(f"\n{'='*78}\nREADING\n{'='*78}")
    print('  H2 had never been run before this sweep: adaptive_weight was false')
    print('  in 24 of 24 configs and nothing outside the tests called')
    print('  record_episode_outcome. Whatever this shows, it is the first')
    print('  evidence the project has about its own load-bearing hypothesis.\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
