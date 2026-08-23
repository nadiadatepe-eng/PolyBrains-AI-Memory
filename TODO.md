# PolyBrains-AI-Memory — TODO

## CP-M0 · Memory research contract

- [x] Import the complete committed PolyBrains record at `fb8071d` without its Git metadata,
      ignored upstream checkout, virtual environment, caches, or run outputs.
- [x] Separate ownership and working tree from `[source PolyBrains checkout]`.
- [x] Record explicit external memory, independent reference frames, provenance, disagreement,
      abstention, and conservative shared consolidation as the new scope.
- [ ] Write a falsifiable proposal before changing inherited source or running experiments.
- [ ] Define the smallest control that separates private retrieval, claim exchange, and shared
      consolidation.

Everything below this point is the imported PolyBrains checkpoint ledger. It is historical
evidence, not a claim that its hypotheses automatically transfer to agent memory.

---

## Imported PolyBrains ledger

Thousand Brains Theory as substrate, polymath properties as specification.
Evidence is a commit sha or a measured number. Blocked work is written down with its reason.

Plan: `docs/plan.html` (open in a browser)

---

## CP-0 · Ground truth on the machine — **DONE** `d22d5b9`

- [x] Clone `tbp.monty`, pin sha `0c81b1f2537eb08bb906859cc69d2b5caf55b6fd` (v0.46.0)
- [x] Isolated env — Python 3.12.3, uv venv, CPU torch 2.13.0, MuJoCo 3.11.0
- [x] YCB dataset — 10 objects, 64 MB, `tools/fetch_ycb.sh`
- [x] Test suites — 590 passed, 1 benign hypothesis timing failure, 30 skipped
- [x] Pretrain 5 LMs — **47.4 s**, 1.17 GB RSS, exit 0
- [x] Eval 5 LMs voting, 50 episodes — **57.7 s**, 1.30 GB RSS, exit 0

**Gate met.** Report: `reports/cp0-feasibility.md`

Findings that changed the plan:
- Compute risk **high → low**. Runs are ~1 min, not hours.
- Python 3.8 risk **dead**. 3.12 works fine.
- **New top risk: HabitatSim is unavailable on Linux** (PyPI wheel is macOS arm64, cp310).
  Committed to MuJoCo. Skips 17 integration tests including `evidence_lm_test.py`.
- MuJoCo object placement needs re-tuning; `rotations_all` puts objects out of view.
- The 60% accuracy from this run is a **liveness check, not a baseline** (trained on 1
  rotation, evaluated on random rotations).

## CP-1 · Read the vote path properly — **DONE**

- [x] Line-by-line notes on `_vote`, `send_out_vote`, `receive_votes`,
      `_update_evidence_with_vote` against the pinned sha
- [x] All three §3 findings **confirmed**, by reading and by executable probe
      (`tests/cp1_probe_vote_path.py`, exit 0)
- [x] `lm_to_lm_vote_matrix` mapped — assigned once at `monty_base.py:99`, never mutated,
      all-to-all for our 5-LM config
- [x] Novelty check across all TBP repos, issues, PRs and `docs/future-work/`

**Gate met.** Report: `reports/vote-path.md`

Findings:
- **(a)** `np.ma.max` at `learning_module.py:938`. Stronger than claimed: the variable is
  named `distance_weighted_vote_evidence` but the weighting is commented out at line 940 and
  upstream's own comment says "Currently unweighted". Probe: 0.95/0.42/0.40 → **0.95**, and
  removing the two agreeing modules gives **the same 0.95**.
- **(b)** Confirmed for the vote path, with two corrections. An `np.std` exists at `:1159`
  but is *within*-LM across object hypotheses. And `AnyLMsMatch` (`count: 3` in our config)
  **is** a cross-module agreement mechanism — but a terminal condition that stops the
  episode, not a vote input. The paper must state this.
- **(c)** Confirmed exactly. `vote_weight` assigned only at `:285`, read at `:951`/`:960`,
  no other assignment in any method.
- **Wrong file in the plan:** our experiments use `evidence_matching/model.py`, not
  `graph_matching.py`. Corrected in §3.
- **Novelty holds but is not virgin:** `np.ma.max` has 0 hits ever; consensus voting rule 0.
  But `docs/future-work/voting-improvements/` has five planned items. Two matter:
  *Clean up and Simplify Voting* (knows votes can "spuriously align", proposes orientation
  pre-filtering, does not touch the max) and *Outline How to Apply Attention* (TBP-owned,
  scoping, "emphasize the representations in certain LMs over others" — adjacent to our
  w(t)). Both must be cited.

## CP-2 · Rival theories written down — **DONE**

- [x] Gentner structure-mapping (1983): predictions for E1–E3
- [x] Ensemble-diversity literature, both the supporting and the failing side
- [x] Explicit statement of where the accounts diverge measurably

**Gate met.** Report: `reports/rivals.md`. Sources cached in `reports/sources/`.

- **E3 forks structure-mapping against H1.** Systematicity says a near-clone module transfers
  as well as a diverse one provided it holds the same relational structure — diversity per se
  is not its mechanism. H1 says clones buy nothing. If clones do as well, **H1's second clause
  is false**.
- **E2 forks the ensemble account against H2.** Ensemble theory says little about
  confidence-weighted aggregation under a max-reduction it never uses.
- **The uncomfortable finding:** Rubinstein et al. (arXiv:2409.16797) already "encourage the
  ensemble members to disagree" and report "large benefits" for OOD. H1 risks rediscovering a
  known ML result on a new substrate. Ortega et al. (PMLR v151) derive the diversity vs
  individual-performance trade-off — the strongest reason to expect H1 to fail. Both are in
  the plan rather than omitted.
- **We do not claim to refute structure-mapping.** A reference frame may be the cortical
  mechanism for what Gentner described computationally. Stated limitation: his relations hold
  between propositions, ours vote on 3D poses.

## CP-3 · Consensus rule + dissent signal — **DONE** `ed65634`

- [x] **Our own MuJoCo-runnable vote-path tests** (upstream's is Habitat-gated) — 10 characterization tests
- [x] `ConsensusVoteMixin` → shipped as `ConsensusEvidenceGraphLM`, one overridden method, upstream untouched
- [x] D-index emitted per step; **definition frozen before any accuracy was observed**, guarded by `test_tau_is_frozen`
- [x] Capture rate instrumented; 1.0 under stock `max` as predicted

**Gate met.** 62 PolyBrains tests pass. Upstream still 590 passed / 1 benign failure.
Report: `reports/cp3-consensus.md`

Key result (no accuracy claim, only mechanism):

| Neighbourhood | `max` | `consensus` | D-index |
|---|---|---|---|
| 0.95 / 0.42 / 0.40 (one loud voice) | **0.95** | **0.527** | 0.255 |
| 0.90 / 0.88 / 0.89 (real agreement) | 0.90 | 0.890 | 0.008 |

Capture rate 1.0 → 0.0 on the contested case.

**Behaviour-preserving proof:** `max` mode is bit-identical to upstream, verified on the
reduction in isolation (12 mask/k combos) *and* by driving the real
`_update_evidence_with_vote` on both classes across 20 seed/vote combos. Any later accuracy
difference is therefore attributable to the rule, not the refactor.

## CP-4 · Adaptive vote weight — **DONE**

- [x] `vote_weight` scalar → w(t) from per-module OOD track record
- [x] Guard against runaway: hard floor `W_MIN=0.1`, a module is **never** silenced
- [x] Recovery from the floor proven — no one-way ratchet
- [x] Ablation config with w(t) frozen, reproducing upstream's constant exactly

**Gate met.** 77 tests pass. Report: `reports/cp4-adaptive-weight.md` ·
Log: `reports/cp4-weight-log.txt`

| Module (200 episodes) | final w |
|---|---|
| reliable OOD (90% right) | **1.9992** |
| mediocre (50%) | 1.0255 |
| unreliable (20% right) | **0.1946** |
| frozen ablation | **1.0000** |

Recovery: 200 failures → 0.1000 (floor, never 0) · 1 success → 0.2800 (not instant) ·
200 successes → 2.0000 (past start).

**The H2 clause is enforced in the mechanism:** 100 in-domain successes leave w at 1.0000.
In-domain confidence buys no influence, so that capture route cannot arise at all.

Constants frozen before any accuracy comparison: `W_MIN=0.1`, `W_MAX=2.0`, `EMA_ALPHA=0.1`.

## CP-5 · E0–E3 with pre-registration — **RUN, results in**

- [x] **Fix MuJoCo object placement** — probed all 14 rotations, 9 usable, two distinct bugs
- [x] Full pretraining, real baseline established
- [x] Noise floor: 5 seeds per arm
- [x] `PREDICTIONS.md` committed before each run
- [x] E0 replication, E1/E2 vote-rule arms, **P4 clean H1 test**, **P6 disagreement task**

**Reports:** `cp5-corrected.md` · `p4-voting-harms.md` · `p6-spread-sensors.md`

### The headline: H1 is NOT supported

| arm | in-domain | OOD | drop |
|---|---|---|---|
| voting ON (upstream) | 100.0% | 96.0% | **−4.0 pp** |
| voting OFF | 100.0% | **100.0%** | 0.0 pp |

Voting **cost** 4.0 pp. Mechanism: it did not reduce module failures (7 vs 8 across 50
episodes), it made them **correlated** — 2 all-module failures vs **0** without voting.
`AnyLMsMatch` survives independent failures, not correlated ones. This is what CP-1's
`np.ma.max` finding predicts: one confident error captures the consensus.

### Two errors I made and caught

1. **Counted LM-rows as episodes.** `eval_stats.csv` is one row per module per episode, so
   5-LM runs looked 5x larger than they were. Fixed: `tools/episode_accuracy.py`. The
   vote-rule null got *stronger* — all three rules now exactly identical.
2. **P6 "fix" backfired.** Spreading sensors 8x produced identical results across all three
   arms, which is impossible for three different rules. Instrumented the vote path:
   `send_out_vote` returned `None` **88%** of the time (vs 63% stock) and only 22% of receipts
   changed evidence (vs 92%). Spreading knocked modules **off the object** rather than making
   them disagree. **Disagreement and absence look identical in output stats and are opposite
   at the mechanism.** Tool: `tools/vote_spy.py`.

### Status

- **H1: not supported.** Voting harmed OOD accuracy on the one task with a verified-live vote path.
- **H2: still untested.** No task yet built gives genuine disagreement among modules that are
  all actually voting. **This is now the central obstacle.**
- **P7 registered:** inject sensory noise into 2 of 5 modules while keeping every patch on the
  object. Mandatory check: report `send_none`% alongside any accuracy number.

## CP-6 · Dissent-driven routing — stretch, cuttable

## CP-7 · Disagreement-driven action — stretch, cuttable

## CP-8 · Write-up — core

- [ ] Motivation section labels the polymath mapping as motivation, not finding
- [ ] Negative and null results in the body, not an appendix
- [ ] Rival-theory section kept intact even if unflattering
- [ ] Every number reproducible from the pinned sha, configs and run directories

---

## Decisions taken 2026-08-18

| Question | Decision |
|---|---|
| Venue | **Journal.** H1, H2 and the rival analysis all in scope. |
| Upstream posture | Keep instrumentation in our own layer **until the paper is out**, then offer upstream. |
| Polymath scope | Attempt all six §4.2 properties, **weight on H2** (manipulation resistance). |
| Compute | No external compute. Scale down instead; determine empirically what hardware would be needed. |

## P7 · H2's real test — **RUN, 2000 episodes** `a88c029`

Noise on modules 3+4 only, patch positions unchanged so every module stays on the object.
Vote path verified live before use (`send_none` 60% vs stock 63%, vs P6's broken 88%).

| arm | accuracy | failure correlation |
|---|---|---|
| `max` (upstream) | 97.00% | 5.1% |
| `mean` (control) | 97.40% | 4.3% |
| `consensus` (ours) | 97.80% | 3.7% |
| **no voting** | **99.80%** | **0.2%** |

- **H1 REFUTED, significantly:** no voting beats `max` by **+2.80 pp, paired t(9)=4.58, p<0.05**
- **H2 not supported:** P7b +0.80 pp (t=1.08 n.s.), P7a 5.1→3.7% (z=0.84 n.s.)
- Control behaved: `mean` gained only +0.40 pp
- **Analysis error caught:** first script used sd/√n and printed "SUPPORTED"; arms share seeds
  so a paired t-test is required. Fixed, mistake recorded in `tools/analyse_p7.py`.

Report: `reports/p7-powered.md`

## P8 · Unanimity criterion — **RUN 2026-08-19** `31d0c04`

Re-scored P7's 2000 episodes under three read-outs. No new episodes.

| criterion | no voting − max | t(9) | verdict |
|---|---|---|---|
| `any` (AnyLMsMatch) | +2.80 pp | 4.58 | voting harms |
| `majority` | +0.20 pp | 0.13 | n.s. |
| `unanimous` | **−30.20 pp** | **−14.40** | **voting helps** |

- All three pre-registered predictions supported; monotonic across criteria
- **H1 refutation WITHDRAWN as a general result** — the sign is set by the scoring rule
- Not circular: voting gains **+0.564 modules/episode (t=15.11)** on a threshold-free
  metric, lifting 277 episodes, dragging 75, zero 5→0 collapses
- Corrects P7's one-sided "correlated failure" claim: the 1→15 tail was reported without
  the 261 episodes moved up
- H2 unaffected, still not supported (`consensus` 40.20% vs `max` 41.00%)

Report: `reports/p8-unanimity.md`

## P9 · Iterated voting — **RUN 2026-08-19** `2bf94d7`

Nadi's question: vote, then vote on the result of that vote. 600 episodes.

| rounds | `any` | `unanimous` | mean correct |
|---|---|---|---|
| 1 | 96.50% | 43.50% | 4.050 |
| 2 | 94.50% | 66.00% | 4.335 |
| 3 | 90.50% | **79.00%** | 4.340 |

- All four pre-registered predictions supported
- **Iteration buys agreement and pays in independence**: three rounds turn a 6 pp
  loss under `any` into **+35.50 pp under unanimity**
- Liveness verified: evidence moves, `send_none` flat at 53.8% across rounds
- **Two sweeps voided first**, both caught by the replication control, not inspection

Report: `reports/p9-iterated.md`

## Tooling reviewed 2026-08-19 `e219a02`

- ArjanCodes `2026/libraries`: adopt **msgspec** (tvfeed error contract) and
  **duckdb** (eval_stats analysis); **complexipy** cheap; pint/whenever conditional
- **NVIDIA PhysicsNeMo: assessed and rejected** — right library, wrong domain
- `tools/crosscheck_p8_duckdb.py`: **P8 reproduces exactly in a second engine**
- Report: `reports/tooling-review-2026-08-19.md`

## P10 · Parliamentary voting — **RUN 2026-08-19** `9da7bee`

Nadi's design: propose (LMs 0,1,2) → oppose (3) → oppose (4), devil's advocate
argues its runner-up, one by one. 600 episodes.

| arm | `any` | agree | **confident errors** |
|---|---|---|---|
| plain-3 | 90.50% | 87.00% | **8.00%** |
| **parl-3** | 96.50% | 38.50% | **2.50%** |
| parl-noopp | 96.50% | 52.50% | 2.00% |

- **The structure works**: −5.50 pp confident errors vs equal-exchange plain
  iteration (t=−3.77), while keeping `any` at 96.50% instead of 90.50%
- **The opposition does not**: `parl-noopp` matches `parl-3` on every measure
- Cause: `np.ma.max` has no channel for dissent, and "one by one" made every
  phase single-speaker (≤1 arguer per exchange over 2180 live events)

Report: `reports/p10-parliament.md`

## P11 — the parliament under `consensus` (2026-08-19, `b4da4ce`)

1000 episodes, 5 arms x 5 seeds x 40. **P11d replication control passed**
(`plain-1` 97.50% vs P7 powered consensus 97.80%), so the sweep is certified.

| arm | `any` | agree | conf wrong |
|---|---|---|---|
| plain-1 | 97.50% | 40.50% | 1.50% |
| plain-3 | 91.50% | 85.00% | 8.00% |
| parl-3 | 98.50% | 37.50% | 1.00% |
| parl-noopp | 97.00% | 55.50% | 2.50% |
| parl-batch | 98.50% | 28.50% | 1.00% |

- **Opposition is active under consensus**: `parl-3` − `parl-noopp` on **agreement
  is −18.00 pp, t(4)=−3.06**. But **the rule's role is NOT established** — under max
  the same gap was already −14.00 pp (t=−2.24, near-miss), and the
  difference-in-differences is **−4.00 pp, t(4)=−0.60, n.s.** P10's mechanism claim
  is consistent with P11, not confirmed by it. See the correction in `PREDICTIONS.md`.
- **It still does not pay.** That 18 pp of friction buys 1.5 pp of confident errors
  (t=−1.50) and 1.5 pp of `any` (t=0.88). **P11a NOT SUPPORTED, but power-limited**:
  `parl-3` sits at a 1.00% error floor, `plain-1` at 1.50%, and 200 episodes/arm
  cannot resolve below ~2 pp.
- **P11b SUPPORTED** — −7.00 pp vs `plain-3`, t=−3.50. P10a replicates under a new rule.
- **Third confirmation the rule barely matters**: consensus − max, structure fixed,
  n.s. everywhere (max |t| = 1.63).

Report: `reports/p11-consensus-parliament.md`

## P12 — H2's first real test (2026-08-19, `61ddc4d`)

1350 episodes, 3 arms x 5 seeds x 90. Certified by P12d; **P12e liveness verified
live** (w(t) moved 5/5 seeds in both adaptive arms, 0/5 frozen, tracking per-module
OOD accuracy).

| arm | `any` | unanimous | mean corr | conf wrong | w spread |
|---|---|---|---|---|---|
| frozen | 99.00% | 36.50% | 3.960 | 1.00% | 1.00 |
| ood | 97.00% | 48.00% | 4.085 | 2.00% | 1.56 |
| indomain | 97.00% | **58.00%** | **4.325** | 3.00% | 1.49 |

- **H2 REFUTED, sign inverted.** `indomain` was predicted worse than `frozen` under
  unanimity; it is **+21.50 pp better** (t=5.00). No capture signature (P12b spread
  −0.067x, n.s.). Not an agreement artefact: **+0.365 modules/episode, t=3.61** on
  the threshold-free metric.
- **Why:** the weight is bounded (0.1–2.0) with an EMA, so nothing can run away.
  **The polymath "never silence a module" invariant, frozen at CP-4 before any
  accuracy was seen, is what blocks H2's failure mode.**
- **Recurrence worth testing:** both weighting arms trade 2 pp of `any` for large
  unanimity gains — the same trade P9 found for iterated voting, via a different
  mechanism.

Report: `reports/p12-adaptive-weight.md`

## NEXT SESSION — more testing before any publication decision

- [ ] **P13 / H1 clause 2 — built, gated, pre-registered (`7fb5c07`), NOT run.**
      Near-copy control: 4 arms varying patch separation, module count held at 5,
      reusing `pb_indomain_5lm`. **Blocked on one config fix**: `p13_sep004` measured
      **83.2% `send_none`** on a pre-sweep smoke test, which is P6's failure mode
      (0.08 gave 88%). Replace with 0.02, smoke-test, keep only if silence stays near
      stock. `sep000` 38.4% and `sep001` 60.3% are healthy.
      The COUNT term remains a separate, larger job: 3-LM and 7-LM need new
      connectivity, sensor and motor configs AND their own pretraining runs.
- [ ] **The `any`-for-unanimity trade appears in two unrelated mechanisms** (P9
      iteration, P12 weighting). Is it a general property of anything that increases
      module coupling?
- [ ] **Power the P11a contrast.** −1.50 pp at t=−1.50 on a 1% error floor.
      Needs several times 200 episodes/arm, or a harder task that lifts the floor.
- [ ] **Power the rule contrast (`consensus` vs `max` on the opposition effect).**
      The difference-in-differences is −4.00 pp at t=−0.60 with per-seed values
      spanning −27.5 to +12.5. Until this is powered, P10's mechanism explanation
      stays a hypothesis. Both arms already exist, so this is seeds only.

- [ ] **Why are all three vote rules identical?** They stay within 1.6 pp under every
      criterion while voting-vs-no-voting moves 30 pp. Whether you vote matters enormously;
      which rule you use barely matters. This is now the sharpest open question.
- [ ] Justify the criterion rather than pick one — the paper's claim now depends on it
- [ ] Get off the ceiling: all arms sit at 97–99.8%, compressing effects into a 3 pp band
- [ ] Multi-object episodes — Monty's voting is aimed at ambiguous scenes, which this is not
- [ ] Replicate the threshold effect (P1) with correct per-episode counting

**Publication decision is Nadi's and has not been taken.**
