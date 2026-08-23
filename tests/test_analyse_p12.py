#!/usr/bin/env python3
"""Validate analyse_p12.py against synthetic data with a KNOWN answer.

The analyser has never run on real P12 data. Every earlier voided sweep in this
project produced plausible numbers from a broken pipeline, so the analyser is
checked here the same way a mechanism is: by feeding it inputs whose correct
verdict is known in advance and asserting it reports them.

Three scenarios:
  1. H2 TRUE   -- indomain genuinely worse than frozen. Analyser must say
                  P12a SUPPORTED.
  2. H2 FALSE  -- all arms identical. Analyser must NOT say SUPPORTED.
  3. DEAD ARM  -- an adaptive arm whose weights never move. Analyser must
                  flag the liveness problem BEFORE reporting accuracy.

Run:
    PYTHONPATH=src upstream/tbp.monty/.venv/bin/python tests/test_analyse_p12.py
"""
import csv
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAIL = []

#: Must match analyse_p12.INDOMAIN and the pretraining set.
INDOMAIN = ['[0 0 0]', '[0 90 0]', '[0 270 0]', '[90 0 0]', '[90 180 0]']
OOD = ['[ 35 45 0]', '[325 45 0]', '[ 35 315 0]', '[325 315 0]']
OBJECTS = ['mug', 'bowl', 'can', 'box', 'ball',
           'fork', 'jug', 'lid', 'pen', 'cup']
HEADER = ['', 'primary_performance', 'most_likely_object',
          'primary_target_object', 'primary_target_rotation_euler']


def write_run(base, run, ood_correct_lms, n_lm=5):
    """One synthetic run: 90 episodes (10 objects x 9 rotations).

    `ood_correct_lms` is how many of the 5 modules are correct on OOD
    episodes -- the single knob that makes an arm better or worse.
    """
    d = base / run
    d.mkdir(parents=True, exist_ok=True)
    rows = []
    for rot in INDOMAIN + OOD:
        for obj in OBJECTS:
            n_ok = n_lm if rot in INDOMAIN else ood_correct_lms
            for i in range(n_lm):
                ok = i < n_ok
                rows.append({
                    '': f'LM_{i}',
                    'primary_performance': 'correct' if ok else 'confused',
                    'most_likely_object': obj if ok else 'WRONG',
                    'primary_target_object': obj,
                    'primary_target_rotation_euler': rot,
                })
    with open(d / 'eval_stats.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)


def write_trace(tdir, run, moved):
    """Weight trace. `moved` False means the arm is dead."""
    with open(tdir / f'{run}.tsv', 'w', newline='') as fh:
        w = csv.writer(fh, delimiter='\t')
        w.writerow(['episode', 'lm', 'weight', 'score', 'was_correct'])
        for ep in range(3):
            for i in range(5):
                weight = 1.0 if not moved else (1.0 + 0.1 * i)
                w.writerow([ep, f'learning_module_{i}', weight, 0.5, True])


def run_analyser(runs_dir, trace_dir):
    """Run the real analyser with its paths pointed at synthetic data."""
    src = (ROOT / 'tools/analyse_p12.py').read_text()
    src = src.replace(
        "B = Path.home() / 'tbp/results/monty/projects/monty_runs'",
        f"B = Path({str(runs_dir)!r})")
    src = src.replace(
        "TRACE = Path(__file__).resolve().parents[1] / 'reports/p12-weights'",
        f"TRACE = Path({str(trace_dir)!r})")
    tmp = trace_dir.parent / '_analyse_under_test.py'
    tmp.write_text(src)
    r = subprocess.run([sys.executable, str(tmp)], capture_output=True, text=True)
    return r.stdout + r.stderr


def check(cond, msg):
    print(f"  [{'PASS' if cond else 'FAIL'}] {msg}")
    if not cond:
        FAIL.append(msg)


def scenario(name, indomain_ok, ood_ok, frozen_ok, moved=True):
    tmp = Path(tempfile.mkdtemp(prefix=f'p12val_{name}_'))
    runs, traces = tmp / 'runs', tmp / 'traces'
    traces.mkdir(parents=True)
    for seed in (42, 43, 44, 45, 46):
        write_run(runs, f'p12_frozen_s{seed}', frozen_ok)
        write_run(runs, f'p12_ood_s{seed}', ood_ok)
        write_run(runs, f'p12_indomain_s{seed}', indomain_ok)
        write_trace(traces, f'p12_frozen_s{seed}', False)
        write_trace(traces, f'p12_ood_s{seed}', moved)
        write_trace(traces, f'p12_indomain_s{seed}', moved)
    out = run_analyser(runs, traces)
    shutil.rmtree(tmp, ignore_errors=True)
    return out


def main():
    print('=' * 70)
    print('VALIDATING analyse_p12.py AGAINST KNOWN ANSWERS')
    print('=' * 70)

    print('\nScenario 1 — H2 is TRUE (indomain 1/5 correct, frozen 5/5)')
    out = scenario('h2true', indomain_ok=1, ood_ok=5, frozen_ok=5)
    seg = out.split('P12a')[1].split('P12b')[0] if 'P12a' in out else ''
    check('SUPPORTED' in seg and 'NOT SUPPORTED' not in seg,
          'reports P12a SUPPORTED when indomain really is worse')
    check('90 episodes' not in out, 'no episode-count refusal on valid data')

    print('\nScenario 2 — H2 is FALSE (all arms identical)')
    out = scenario('h2false', indomain_ok=5, ood_ok=5, frozen_ok=5)
    seg = out.split('P12a')[1].split('P12b')[0] if 'P12a' in out else ''
    check('SUPPORTED' not in seg or 'NOT SUPPORTED' in seg,
          'does NOT report P12a SUPPORTED when arms are identical')

    print('\nScenario 3 — DEAD ARM (adaptive weights never move)')
    out = scenario('dead', indomain_ok=1, ood_ok=5, frozen_ok=5, moved=False)
    check('LIVENESS PROBLEM' in out,
          'flags the liveness problem when an adaptive arm is frozen')
    check(out.index('LIVENESS') < out.index('P12a') if 'P12a' in out else True,
          'reports liveness BEFORE the accuracy verdicts')

    print()
    if FAIL:
        print(f'VALIDATION FAILED: {len(FAIL)} check(s)')
        for f in FAIL:
            print(f'  - {f}')
        return 1
    print('ANALYSER VALIDATED')
    return 0


if __name__ == '__main__':
    sys.exit(main())
