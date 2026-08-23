#!/usr/bin/env python3
"""P7 analysis, applied mechanically against the pre-registered predictions.

Written to avoid post-hoc flattery: the noise floor, the comparisons and the
verdicts are computed by rule, not chosen after seeing the numbers.

Pre-registration (PREDICTIONS.md, committed 2f931cb, before these runs):
  P7a  consensus produces LOWER failure correlation than max
  P7b  consensus BEATS max on system accuracy
  control: if `mean` matches `consensus`, the effect is plain averaging,
           not agreement-weighting, and P7b does not support H2
"""
import csv
import glob
import statistics
from collections import defaultdict

B = '[local Monty results directory]'
ARMS = [
    ('max (upstream)', 'pow_p7_e1_ood_max_s*'),
    ('mean (control)', 'pow_p7_e1_ood_mean_s*'),
    ('consensus', 'pow_p7_e1_ood_consensus_s*'),
    ('no voting', 'pow_p7_e1_ood_novote_s*'),
]


def load(path):
    rows = list(csv.DictReader(open(path)))
    lm = defaultdict(list)
    for r in rows:
        lm[r['']].append(r)
    return lm, min(len(v) for v in lm.values())


def run_stats(path):
    """Per-run: system accuracy and failure correlation."""
    lm, n = load(path)
    ok = allfail = anyfail = 0
    for i in range(n):
        fails = [not lm[k][i]['primary_performance'].startswith('correct') for k in lm]
        if not all(fails):
            ok += 1
        if all(fails):
            allfail += 1
        if any(fails):
            anyfail += 1
    return 100 * ok / n, allfail, anyfail, n


def collect(pat):
    accs, af, yf, eps = [], 0, 0, 0
    for f in sorted(glob.glob(f'{B}/{pat}/eval_stats.csv')):
        a, x, y, n = run_stats(f)
        accs.append(a)
        af += x
        yf += y
        eps += n
    return accs, af, yf, eps


data = {lab: collect(pat) for lab, pat in ARMS}

print("=" * 74)
print("P7 -- POWERED RUN: 4 arms x 10 seeds x 50 episodes = 2000 episodes")
print("=" * 74)
print(f"\n{'arm':20} {'accuracy':>10} {'sd':>7} {'n runs':>8} {'episodes':>10}")
print("-" * 74)
for lab, _ in ARMS:
    accs, af, yf, eps = data[lab]
    print(f"{lab:20} {statistics.mean(accs):>9.2f}% "
          f"{statistics.stdev(accs):>6.2f} {len(accs):>8} {eps:>10}")

print(f"\n{'arm':20} {'any failed':>11} {'ALL failed':>11} {'correlation':>13}")
print("-" * 74)
for lab, _ in ARMS:
    _, af, yf, _ = data[lab]
    print(f"{lab:20} {yf:>11} {af:>11} {100*af/max(yf,1):>12.1f}%")

# ---- noise floor, computed by rule -------------------------------------
# NOTE: an earlier version of this script used sd/sqrt(n) as the threshold and
# declared P7b "SUPPORTED" at +0.80 pp. That was too lenient: the correct test
# for arms sharing seeds is a PAIRED t-test on per-seed differences, which
# gives t=1.08, not significant. The threshold below is retained only as a
# descriptive scale; the verdicts use the paired test.
pooled = statistics.stdev([a for lab, _ in ARMS for a in data[lab][0]])
within = statistics.mean([statistics.stdev(data[lab][0]) for lab, _ in ARMS])
floor = max(pooled, within) / (len(data['max (upstream)'][0]) ** 0.5)
print(f"\nNOISE FLOOR")
print(f"  pooled sd across all arms/seeds : {pooled:.2f} pp")
print(f"  mean within-arm sd              : {within:.2f} pp")
print(f"  standard error (sd/sqrt(n=10))  : {floor:.2f} pp  <- comparison threshold")

mx = statistics.mean(data['max (upstream)'][0])
mn = statistics.mean(data['mean (control)'][0])
cs = statistics.mean(data['consensus'][0])
nv = statistics.mean(data['no voting'][0])

print(f"\n{'='*74}\nPRE-REGISTERED VERDICTS\n{'='*74}")

# P7b -- accuracy, PAIRED by seed (arms share seeds, so pairing is required)
import re as _re
def _by_seed(pat):
    out = {}
    for f in sorted(glob.glob(f'{B}/{pat}/eval_stats.csv')):
        m = _re.search(r'_s(\d+)/eval_stats', f)
        out[int(m.group(1))] = run_stats(f)[0]
    return out

_mx, _cs, _nv = (_by_seed(p) for p in
                 ('pow_p7_e1_ood_max_s*', 'pow_p7_e1_ood_consensus_s*',
                  'pow_p7_e1_ood_novote_s*'))
seeds = sorted(set(_mx) & set(_cs))
diffs = [_cs[s] - _mx[s] for s in seeds]
nd = len(diffs)
sd_d = statistics.stdev(diffs)
t = statistics.mean(diffs) / (sd_d / nd ** 0.5) if sd_d else 0.0
crit = 2.262  # t(9), two-tailed, 0.05
print(f"\nP7b: consensus beats max on accuracy  [PAIRED t-test, n={nd} seeds]")
print(f"  mean paired diff = {statistics.mean(diffs):+.2f} pp  (sd {sd_d:.2f})")
print(f"  t({nd-1}) = {t:.2f}   critical |t| = {crit}")
w = sum(1 for x in diffs if x > 0); l = sum(1 for x in diffs if x < 0)
print(f"  consensus wins {w}, loses {l}, ties {nd-w-l}")
if abs(t) <= crit:
    print("  VERDICT: NOT SIGNIFICANT -- P7b not supported")
elif t > 0:
    print("  VERDICT: SUPPORTED")
else:
    print("  VERDICT: REFUTED (consensus worse)")

dn = [_nv[s] - _mx[s] for s in sorted(set(_nv) & set(_mx))]
tn = statistics.mean(dn) / (statistics.stdev(dn) / len(dn) ** 0.5)
print(f"\n  no-voting vs max [paired]: {statistics.mean(dn):+.2f} pp, "
      f"t = {tn:.2f} -> {'SIGNIFICANT' if abs(tn) > crit else 'n.s.'}")
d = cs - mx

# control
dc = mn - mx
print(f"\n  control: mean - max = {dc:+.2f} pp")
if abs(dc) > floor and abs(dc) >= abs(d) * 0.5:
    print("  WARNING: plain averaging explains much of the gain."
          "\n           Agreement-weighting is NOT demonstrated.")
else:
    print("  control is flat -> the effect is agreement-weighting, not averaging")

# P7a -- correlation
_, af_mx, yf_mx, _ = data['max (upstream)']
_, af_cs, yf_cs, _ = data['consensus']
c_mx = 100 * af_mx / max(yf_mx, 1)
c_cs = 100 * af_cs / max(yf_cs, 1)
print(f"\nP7a: consensus lowers failure correlation")
print(f"  max       : {af_mx}/{yf_mx} = {c_mx:.1f}%")
print(f"  consensus : {af_cs}/{yf_cs} = {c_cs:.1f}%")
# two-proportion z-test
try:
    p1, n1 = af_mx / yf_mx, yf_mx
    p2, n2 = af_cs / yf_cs, yf_cs
    pp = (af_mx + af_cs) / (yf_mx + yf_cs)
    se = (pp * (1 - pp) * (1 / n1 + 1 / n2)) ** 0.5
    z = (p1 - p2) / se if se else 0
    print(f"  two-proportion z = {z:.2f}  ({'p<0.05' if abs(z) > 1.96 else 'n.s.'})")
    if c_cs < c_mx and abs(z) > 1.96:
        print("  VERDICT: SUPPORTED")
    elif c_cs < c_mx:
        print("  VERDICT: directionally consistent, NOT significant")
    else:
        print("  VERDICT: NOT supported")
except ZeroDivisionError:
    print("  VERDICT: undefined (no failures)")

# H1 standing
print(f"\nH1 (voting helps OOD): no-voting = {nv:.2f}% vs best voting arm "
      f"= {max(mx, mn, cs):.2f}%")
print("  VERDICT:", "still NOT supported" if nv >= max(mx, mn, cs) - floor
      else "revisit -- a voting arm now leads")
print()
