#!/usr/bin/env python3
"""Gate for P13's near-copy arms.

Asserts the things that would silently invalidate the experiment:

  * the `sep001` arm is byte-identical to upstream's stock environment, so it
    is a true replication control and any difference between arms comes from
    the separation and not from the generator
  * each arm's four patch offsets are exactly the intended value, and patch_0,
    the view_finder and the agent position are NOT touched
  * the arms are distinguishable from each other (a generator that silently
    wrote the same offsets everywhere would produce four identical arms, which
    is this project's recurring failure)
  * every arm still declares 5 sensor modules and 5 LMs -- the point of the
    experiment is that the COUNT is held fixed while disagreement varies
  * the experiment configs differ from p7_e1_ood_max in exactly one key

Run:
    PYTHONPATH=src upstream/tbp.monty/.venv/bin/python tests/test_p13_configs.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / 'configs/environment'
EXP = ROOT / 'configs/experiment'
STOCK = (ROOT / 'upstream/tbp.monty/src/tbp/monty/conf/environment'
         / 'mujoco_dist_agent_sensors5.yaml')
ARMS = {'p13_sep000': 0.0, 'p13_sep0025': 0.0025,
        'p13_sep001': 0.01, 'p13_sep004': 0.04}
FAIL = []


def check(cond, msg):
    print(f"  [{'PASS' if cond else 'FAIL'}] {msg}")
    if not cond:
        FAIL.append(msg)


def body(text):
    """The config below our header, for comparison against stock."""
    return text[text.index('env_init_args:'):]


def offsets(text):
    """Every scalar inside a `position:` list, in order."""
    out = []
    for m in re.finditer(r'\n          position:\n((?:\s+- -?\d*\.?\d+\n){3})',
                         text):
        out.append(tuple(float(x) for x in re.findall(r'-?\d*\.?\d+',
                                                      m.group(1))))
    return out


def main():
    print('=' * 72)
    print('P13 GATE -- near-copy arms for H1 clause 2')
    print('=' * 72)

    stock = STOCK.read_text()
    stock_off = offsets(stock)

    print('\nthe stock environment is what we think it is')
    check(len(stock_off) == 6,
          f'stock declares 6 sensor positions (5 patches + view_finder), got '
          f'{len(stock_off)}')
    check(stock_off[0] == (0.0, 0.0, 0.0), 'patch_0 sits at the origin')
    nonzero = {v for p in stock_off for v in p if v}
    check(nonzero <= {0.01, -0.01, 1.5, 0.2},
          f'stock offsets are +-0.01 (plus the agent pose), got {sorted(nonzero)}')

    print('\nsep001 is a TRUE replication control')
    s001 = body((ENV / 'p13_sep001.yaml').read_text())
    check(s001 == body(stock),
          'p13_sep001 body is byte-identical to upstream stock')

    print('\neach arm has exactly the intended separation')
    for name, sep in ARMS.items():
        off = offsets((ENV / f'{name}.yaml').read_text())
        check(len(off) == 6, f'{name}: 6 sensor positions')
        check(off[0] == (0.0, 0.0, 0.0), f'{name}: patch_0 untouched at origin')
        patch_vals = {abs(v) for p in off[1:5] for v in p if v}
        want = {sep} if sep else set()
        check(patch_vals == want,
              f'{name}: patch offsets are {sorted(patch_vals) or "[all zero]"}, '
              f'want {sorted(want) or "[all zero]"}')
        # the view_finder keeps zoom 1.0 at the origin; the agent pose is
        # outside the patch blocks and must survive untouched
        check('- 1.5' in (ENV / f'{name}.yaml').read_text(),
              f'{name}: agent position preserved')

    print('\narms are distinguishable from one another')
    sigs = {n: offsets((ENV / f'{n}.yaml').read_text())[1:5] for n in ARMS}
    uniq = {tuple(v) for v in sigs.values()}
    check(len(uniq) == len(ARMS),
          f'{len(uniq)} distinct offset patterns across {len(ARMS)} arms')

    print('\nmodule COUNT is held fixed (the whole point of the design)')
    for name in ARMS:
        t = (ENV / f'{name}.yaml').read_text()
        n_patch = len(re.findall(r'\n        patch_\d:', t))
        check(n_patch == 5, f'{name}: 5 sensor patches declared, got {n_patch}')
        e = (EXP / f'{name}.yaml').read_text()
        check('polybrains_5lm' in e, f'{name}: still uses the 5-LM module set')
        check('5lm_5sm' in e, f'{name}: still uses 5lm_5sm connectivity')

    print('\nexperiment configs differ from p7_e1_ood_max in ONE key')
    base = (EXP / 'p7_e1_ood_max.yaml').read_text()
    base_lines = [ln for ln in base.splitlines()
                  if not ln.startswith('#') and ln.strip()]
    for name in ARMS:
        arm = (EXP / f'{name}.yaml').read_text()
        arm_lines = [ln for ln in arm.splitlines()
                     if not ln.startswith('#') and ln.strip()]
        diff = [a for a, b in zip(base_lines, arm_lines) if a != b]
        check(len(diff) == 2 and len(base_lines) == len(arm_lines),
              f'{name}: differs from p7 in {len(diff)} lines (environment + '
              f'run_name), same length')

    print('\nthe reused model exists (arms must NOT need new pretraining)')
    model = (Path.home() / 'tbp/results/monty/pretrained_models/polybrains'
             / 'pb_indomain_5lm/pretrained')
    check(model.is_dir(), f'pb_indomain_5lm present at {model}')

    print()
    if FAIL:
        print(f'GATE FAILED: {len(FAIL)} check(s)')
        for f in FAIL:
            print(f'  - {f}')
        return 1
    print('GATE PASSED')
    return 0


if __name__ == '__main__':
    sys.exit(main())
