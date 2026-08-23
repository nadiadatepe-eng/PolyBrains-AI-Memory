#!/usr/bin/env python3
"""Cross-check P8's headline numbers in a second engine (DuckDB).

WHY. P8 overturned this project's central finding on the strength of one Python
script. A transcription or grouping error in that script would look exactly like
a discovery. This recomputes the same quantities with a completely different
implementation -- SQL over the raw CSVs, no shared code with tools/analyse_p8.py
-- so agreement is evidence and disagreement is a bug found before publication.

GOTCHA worth keeping: the episode index must come from PHYSICAL FILE ORDER.
eval_stats.csv has one row per learning module per episode with no episode-id
column, so episodes are identified positionally. A first version used
`row_number() OVER (PARTITION BY lm ORDER BY 1)`, where `ORDER BY 1` is a
constant, leaving row order unspecified: modules were paired against the wrong
episodes and unanimity read 39.4% instead of 41.0%. With `ORDER BY rid` (a
stable file-order row id) the two engines agree exactly.

Run:
    upstream/tbp.monty/.venv/bin/python tools/crosscheck_p8_duckdb.py
"""
import glob
import re
import statistics
import sys

import duckdb

B = '[local Monty results directory]'
ARMS = ['max', 'mean', 'consensus', 'novote']


def per_seed(arm):
    """unanimous%, majority%, any%, mean-correct per seed, via SQL."""
    out = {}
    for f in sorted(glob.glob(f'{B}/pow_p7_e1_ood_{arm}_s*/eval_stats.csv')):
        seed = int(re.search(r"_s(\d+)/eval_stats", f).group(1))
        q = f"""
        WITH raw AS (
          SELECT *, row_number() OVER () AS rid
          FROM read_csv_auto('{f}', header=true)
        ), ep AS (
          SELECT column00 AS lm,
                 row_number() OVER (PARTITION BY column00 ORDER BY rid) AS ix,
                 CASE WHEN starts_with(primary_performance,'correct')
                      THEN 1 ELSE 0 END AS ok
          FROM raw
        ), agg AS (SELECT ix, SUM(ok) AS n FROM ep GROUP BY ix)
        SELECT 100*AVG(CASE WHEN n>=1 THEN 1 ELSE 0 END),
               100*AVG(CASE WHEN n>=3 THEN 1 ELSE 0 END),
               100*AVG(CASE WHEN n>=5 THEN 1 ELSE 0 END),
               AVG(n), COUNT(*)
        FROM agg
        """
        out[seed] = duckdb.sql(q).fetchone()
    return out


def paired(a, b, ix):
    seeds = sorted(set(a) & set(b))
    d = [a[s][ix] - b[s][ix] for s in seeds]
    sd = statistics.stdev(d) if len(d) > 1 and len(set(d)) > 1 else 0.0
    t = (statistics.mean(d) / (sd / len(d) ** 0.5)) if sd else 0.0
    return statistics.mean(d), t


def main():
    data = {a: per_seed(a) for a in ARMS}
    if not all(data.values()):
        print("P7 run data not found")
        return 1

    print("=" * 74)
    print("P8 CROSS-CHECK IN DUCKDB -- independent of tools/analyse_p8.py")
    print("=" * 74)
    print(f"\n{'arm':12}{'any':>10}{'majority':>11}{'unanimous':>12}"
          f"{'mean corr':>11}{'episodes':>10}")
    print("-" * 74)
    for a in ARMS:
        v = data[a]
        cols = [statistics.mean(x[i] for x in v.values()) for i in range(4)]
        eps = sum(x[4] for x in v.values())
        print(f"{a:12}{cols[0]:>9.2f}%{cols[1]:>10.2f}%{cols[2]:>11.2f}%"
              f"{cols[3]:>11.3f}{eps:>10}")

    print(f"\n{'-'*74}\nno voting - max, paired over 10 seeds")
    expect = {'any': +2.80, 'majority': +0.20, 'unanimous': -30.20}
    ok = True
    for name, ix in (('any', 0), ('majority', 1), ('unanimous', 2)):
        m, t = paired(data['novote'], data['max'], ix)
        e = expect[name]
        agree = abs(m - e) < 0.01
        ok &= agree
        print(f"  {name:10} {m:+7.2f} pp  t={t:7.2f}   "
              f"analyse_p8.py said {e:+.2f}   "
              f"{'MATCH' if agree else 'MISMATCH'}")

    m, t = paired(data['max'], data['novote'], 3)
    agree = abs(m - 0.564) < 0.001
    ok &= agree
    print(f"  {'mean corr':10} {m:+7.3f}     t={t:7.2f}   "
          f"analyse_p8_circularity.py said +0.564   "
          f"{'MATCH' if agree else 'MISMATCH'}")

    print(f"\n{'='*74}")
    print("P8 REPRODUCES IN A SECOND ENGINE" if ok
          else "DISAGREEMENT -- investigate before trusting either")
    print("=" * 74)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
