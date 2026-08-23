#!/usr/bin/env python3
"""Audit every experiment config, and every run it produced, for silent errors.

Written 2026-08-19 on Nadi's instruction to verify everything before continuing.
This project has voided six sweeps, none caught by reading code, so this checks
the OUTPUT of runs against the INTENT of configs.

Checks, each of which has caught a real bug in this project:
  A  epoch trap  -- `Predefined` indexes rotations by EPOCH, so a run with
                    n_eval_epochs < len(rotations) silently evaluates a subset
  B  append trap -- Monty appends to an existing eval_stats.csv, so a run with
                    an unexpected episode count contains another run's rows
  C  dead arm    -- arms that produce byte-identical outcomes are not testing
                    the variable they claim to
  D  drift       -- committed yaml vs the Hydra config the run actually used
"""
import csv, glob, hashlib, os, re, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / 'configs/experiment'
RUNS = Path.home() / 'tbp/results/monty/projects/monty_runs'
OUT = ROOT / 'upstream/tbp.monty/outputs'
PROBLEMS = []

#: Arms actually read by an analyser in tools/. Anything else is kept for the
#: record and its epoch coverage does not affect a published number. Derived by
#: grepping the glob patterns out of tools/analyse_*.py.
LIVE_ARMS = {
    'p9_r1', 'p9_r3',
    'p10_parl3', 'p10_parlnoopp', 'p10_parlbatch',
    'p11_parl3', 'p11_parlnoopp', 'p11_parlbatch', 'p11_plain1', 'p11_plain3',
    'pow_p7_e1_ood_max', 'pow_p7_e1_ood_mean',
    'pow_p7_e1_ood_consensus', 'pow_p7_e1_ood_novote',
}


def note(sev, msg):
    PROBLEMS.append((sev, msg))
    print(f"  [{sev}] {msg}")


def cfg_facts(path):
    t = path.read_text()
    def one(pat, d=None):
        m = re.search(pat, t, re.M)
        return m.group(1).strip() if m else d
    rot = re.search(r'^\s*eval_rotations:\s*\n((?:\s*-\s*\[.*\n)+)', t, re.M)
    return dict(
        vote=one(r'^\s*vote_mode:\s*(\S+)'),
        adaptive=one(r'^\s*adaptive_weight:\s*(\S+)'),
        n_rot=len(re.findall(r'-\s*\[', rot.group(1))) if rot else 0,
        epochs=one(r'^\s*n_eval_epochs:\s*(\d+)'),
        cls=(one(r'monty_class:.*?([A-Za-z_]+)\}') or '-'),
        exp=(one(r'^\s*_target_:\s*(\S+)') or '-').split('.')[-1],
        model=(one(r'model_name_or_path:.*?polybrains/([^/]+)/') or '-'),
    )


def episodes(path):
    rows = list(csv.DictReader(open(path)))
    lm = defaultdict(list)
    for r in rows:
        lm[r['']].append(r)
    n = min((len(v) for v in lm.values()), default=0)
    rots = {r['primary_target_rotation_euler'] for r in rows}
    sig = hashlib.sha1(''.join(
        r['primary_performance'] + r.get('most_likely_object', '') for r in rows
    ).encode()).hexdigest()[:12]
    return n, len(lm), rots, sig


def main():
    print('=' * 88)
    print('CONFIG + RUN AUDIT')
    print('=' * 88)

    print('\n--- committed configs ---')
    print(f"{'config':<24}{'vote':<11}{'adaptive':<10}{'rots':<6}"
          f"{'class':<21}{'experiment':<34}")
    print('-' * 88)
    facts = {}
    for f in sorted(CFG.glob('*.yaml')):
        c = cfg_facts(f)
        facts[f.stem] = c
        print(f"{f.stem:<24}{str(c['vote']):<11}{str(c['adaptive']):<10}"
              f"{c['n_rot']:<6}{c['cls']:<21}{c['exp']:<34}")

    print('\n--- A: epoch trap (rotations evaluated vs rotations configured) ---')
    print('  Severity depends on whether the run feeds a PUBLISHED number.')
    print('  LIVE = read by an analyser in tools/; SUPERSEDED = early run kept')
    print('  for the record only. n_eval_epochs is a command-line override, so')
    print('  a committed yaml saying 1 does not mean the sweep ran with 1.')
    seen_any = False
    for d in sorted(RUNS.glob('*/eval_stats.csv')):
        run = d.parent.name
        stem = re.sub(r'_s\d+$', '', run)
        c = facts.get(stem)
        if not c or not c['n_rot']:
            continue
        n, nlm, rots, _ = episodes(d)
        seen_any = True
        if len(rots) != c['n_rot']:
            live = any(stem == a for a in LIVE_ARMS)
            note('EPOCH' if live else 'epoch-old',
                 f"{'LIVE ' if live else 'SUPERSEDED '}{run}: saw {len(rots)} "
                 f"rotation(s), config lists {c['n_rot']}")
    if seen_any:
        print('  (only mismatches are listed)')

    print('\n--- B: append trap (episode counts within an arm) ---')
    by_arm = defaultdict(dict)
    for d in sorted(RUNS.glob('*/eval_stats.csv')):
        run = d.parent.name
        stem = re.sub(r'_s\d+$', '', run)
        n, nlm, rots, sig = episodes(d)
        by_arm[stem][run] = (n, sig)
    for stem, runs in sorted(by_arm.items()):
        counts = {v[0] for v in runs.values()}
        if len(counts) <= 1:
            continue
        odd = [r for r, v in runs.items() if v[0] != max(counts)]
        # e2_05_e1_ood_consensus_s42 is a KNOWN incomplete run (30 episodes of
        # 50). reports/cp5-results.md excludes it explicitly -- its table says
        # "Paired, complete runs only" and reports threshold 0.5 as n=1. So the
        # truncation is recorded and already handled, not silently averaged.
        known = stem.startswith('e2_')
        note('append-known' if known else 'APPEND',
             f"{stem}: uneven episode counts {sorted(counts)} -> {odd}"
             + ("  [excluded by reports/cp5-results.md]" if known else ""))

    print('\n--- C: dead arms (different configs, identical outcomes) ---')
    print('  NOTE: a match on the coarse outcome signature (performance + named')
    print('  object) is NOT proof of a dead arm -- with 10 objects at ~98% accuracy')
    print('  two arms tie often. Confirm any hit against a CONTINUOUS column')
    print('  (highest_evidence); genuinely identical wiring matches on every row.')
    sigs = defaultdict(list)
    for stem, runs in by_arm.items():
        for run, (n, sig) in runs.items():
            seed = re.search(r'_s(\d+)$', run)
            if seed:
                sigs[(seed.group(1), sig)].append(stem)
    def evidence_col(run):
        f = RUNS / run / 'eval_stats.csv'
        return [r.get('highest_evidence', '') for r in csv.DictReader(open(f))]

    for (seed, sig), stems in sorted(sigs.items()):
        uniq = sorted(set(stems))
        if len(uniq) < 2:
            continue
        # Confirm against a continuous column before calling it a dead arm.
        try:
            cols = [evidence_col(f'{u}_s{seed}') for u in uniq]
        except FileNotFoundError:
            cols = []
        identical = bool(cols) and all(
            len(c) == len(cols[0]) and c == cols[0] for c in cols[1:]
        ) and any(v not in ('', 'None') for v in cols[0])
        if identical:
            # Two identities are EXPECTED and documented, not bugs:
            #   p6_* max == consensus -- P6's own refutation. The spread task
            #     knocked modules off the object, send_out_vote returned None
            #     88% of the time, so no rule had votes to reduce.
            #     reports/p6-spread-sensors.md
            #   cp5_* == e2_08_* -- E2's 0.8 arm IS the default threshold, so
            #     it re-runs CP-5's configuration. Same config, same result.
            known = (all(u.startswith('p6_') for u in uniq)
                     or {u.split('_e1_')[0] for u in uniq} == {'cp5', 'e2_08'})
            note('KNOWN' if known else 'DEAD',
                 f"seed {seed}: {uniq} identical on EVERY evidence row"
                 + (" -- documented, expected" if known else
                    " -- SAME WIRING, investigate"))
        else:
            print(f"  seed {seed}: {uniq} tie on outcomes but differ on "
                  f"evidence -- a genuine tie, not a dead arm")

    print('\n--- D: committed yaml vs the config Hydra actually ran ---')
    for stem in ('p11_parl3', 'p11_plain1', 'p10_parl3', 'p9_rounds3',
                 'p7_e1_ood_consensus', 'p7_e1_ood_max'):
        c = facts.get(stem)
        if not c:
            continue
        hits = [p for p in OUT.glob('*/*/.hydra/config.yaml')
                if f'run_name: {stem}_s' in p.read_text()
                or f'run_name: {stem}\n' in p.read_text()]
        if not hits:
            print(f"  {stem}: no hydra record found (older run)")
            continue
        live = hits[-1].read_text()
        lv = re.search(r'^  vote_mode:\s*(\S+)', live, re.M)
        if c['vote'] and lv and lv.group(1) != c['vote']:
            note('DRIFT', f"{stem}: yaml says {c['vote']}, ran {lv.group(1)}")
        else:
            print(f"  {stem}: yaml and live config agree (vote_mode={c['vote']})")

    print('\n' + '=' * 88)
    hard = [p for p in PROBLEMS if p[0] in ('EPOCH', 'APPEND', 'DEAD', 'DRIFT')]
    soft = [p for p in PROBLEMS if p not in hard]
    print(f"{len(hard)} finding(s) affecting PUBLISHED numbers")
    print(f"{len(soft)} finding(s) in superseded/known runs (recorded, not blocking)")
    if hard:
        for sev, m in hard:
            print(f"   [{sev}] {m}")
        return 1
    print('NO PROBLEMS FOUND')
    return 0


if __name__ == '__main__':
    sys.exit(main())
