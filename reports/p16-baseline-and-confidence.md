# P16 — the per-object baseline, and why confidence cannot rescue it

**Analysis 2026-08-20. No new runs.** This re-reads P15's committed
`eval_stats.csv` files, so nothing here can have been tuned to the outcome —
the same discipline P8 used when it re-scored P7. Only the read-out changes.

Reproduce:

```bash
upstream/tbp.monty/.venv/bin/python tools/analyse_p16.py
```

## 1. The per-object baseline P15 demanded

P14 proposed subtracting one project-wide unanimity floor. P15 showed the floor
moves, so a single constant would be wrong in both directions. Here it is,
per object — **the unanimity a system reaches when it cannot possibly be
right**:

| object | unanimity (voting) | unanimity (no voting) | accuracy |
|---|---|---|---|
| `strawberry` | **100.00%** | 100.00% | 0.00% |
| `dice` | 95.00% | 75.00% | 0.00% |
| `banana` | 35.00% | 20.00% | 0.00% |
| `mug` | 20.00% | 35.00% | 0.00% |
| **`bowl`** (trained) | **100.00%** | — | **100.00%** |

## 2. The comparison that matters

> **Unanimity is 100.00% when the system is right, and 100.00% when it is
> wrong.**

`bowl` is trained and every module gets it right, unanimously. `strawberry` is
held out and every module gets it wrong, unanimously. **The two are identical at
the read-out.** Unanimity does not distinguish them, at all, in this substrate.

That is the strongest form of Nadi's critique available: not "consensus is
sometimes wrong", but **consensus is not a measurement of correctness**. The
number is the same in both states.

## 3. Can confidence rescue it? No.

The obvious repair for a system that agrees when wrong: trust the agreement only
when the modules are *confident*. Weight by evidence, filter out the uncertain
consensus. It is the first thing a reviewer would propose, so it is tested here,
and it is a real test because it can fail.

**It fails.** Mean `highest_evidence`, per seed, paired against the correct case:

| arm | mean evidence | vs. correct case | t(4) | state |
|---|---|---|---|---|
| `bowl` (trained) | 21.20 | — | — | **correct** |
| `mug` | 4.65 | −16.56 | −28.52 | 100% wrong |
| `banana` | 5.93 | −15.28 | −15.79 | 100% wrong |
| `dice` | 15.27 | −5.93 | −3.80 | 100% wrong |
| **`strawberry`** | **25.23** | **+4.02** | **+4.70** | **100% wrong** |

**The most confidently held answer in the entire sweep is a wrong one.**
`strawberry` carries *significantly more* evidence than the correct `bowl` case
(+4.02, t(4)=4.70) while being wrong in every episode and unanimous in every
episode.

So any confidence threshold that admits the correct case also admits
`strawberry`. **Evidence cannot filter false consensus here.** The rescue is not
merely weak; it is inverted for the worst case.

## 4. The constructive finding

The evidence ordering is not noise — it is orderly:

```
mug(4.6)  <  banana(5.9)  <  dice(15.3)  <  strawberry(25.2)
```

**Evidence tracks how close the unseen object is to something trained**, not
whether the answer is right. `mug` has a handle no trained object shares and
scores lowest; `strawberry` is nearly a `golf_ball` and scores highest.

That makes it a **usable signal for novelty detection and a misleading one for
correctness** — and those are opposite uses of the same number. A system reading
high evidence as "I am probably right" has it exactly backwards in the case that
matters most, because high evidence means *this looks like something I know*,
which is precisely the condition under which an unknown object is confidently
misidentified.

## 5. What this means for the project

1. **Unanimity must be reported against the per-object floor**, and the floor
   ranges from 20% to 100%. A project-wide constant cannot work.
2. **Confidence weighting is not the fix**, and P16 forecloses it with a
   measurement rather than an argument. This matters for H2's neighbourhood:
   the intuition that "weight by confidence" makes consensus more trustworthy
   is refuted here in the one condition where it could be checked.
3. **The three-way distinction the project now needs:** *agreement*,
   *confidence*, and *correctness* are three different things, and in this
   substrate the first two are uninformative about the third. Every previous
   experiment measured only agreement and read it as evidence about correctness.

## 6. Threats

- **One trained control object** (`bowl`). The correct case is a single point;
  `strawberry` beating it is significant across seeds but the comparison would
  be stronger with several trained objects.
- **4 episodes per run**, so the unanimity figures move in 25 pp steps. The
  100%/100% comparison is not affected by granularity — both are saturated.
- **`highest_evidence` is Monty's own confidence measure**, not a calibrated
  probability. The claim is about *this* signal, which is the one the vote
  mechanism would use.
- **Seed 42 fails on `dice`** (upstream `sensor_processing.py:444`); per-seed
  means are used so the shorter run is not over-weighted.

**Publication decision remains Nadi's and is not taken.**
