# CP-1 — The vote path, read against the pinned sha

**Date:** 2026-08-18
**Sha:** `0c81b1f2537eb08bb906859cc69d2b5caf55b6fd` (v0.46.0), working tree clean
**Gate:** confirm or refute the three §3 findings, which were read from `main` *before*
pinning and were therefore unverified.

**Verdict: all three confirmed**, by reading and by an executable probe
(`tests/cp1_probe_vote_path.py`, exit 0). Two corrections and one significant novelty
finding are recorded below.

---

## The vote path as it actually runs

There are **two** vote implementations. The plan named only one.

| Class | File | Used by |
|---|---|---|
| `MontyForGraphMatching` | `models/graph_matching.py` | displacement/feature-matching LMs |
| **`MontyForEvidenceGraphMatching`** | **`models/evidence_matching/model.py`** | **evidence LMs — our experiments** |

Our 5-LM configs use `evidence_5lm_nn10_dod003` → `EvidenceGraphLM`, so
`evidence_matching/model.py::_combine_votes` is the path that matters. It is the shorter of
the two and does **not** tally per-object positive/negative counts the way
`graph_matching.py` does; it transforms votes into the receiving LM's frame and concatenates
them.

Per step:

1. `monty_base.py:302` `_vote()` — gathers `send_out_vote()` from each LM, routes by
   `lm_to_lm_vote_matrix`.
2. `learning_module.py:403` `send_out_vote()` — emits hypotheses whose *scaled* evidence
   exceeds `vote_evidence_threshold` (default `0.8`), each a `Message` with `location`,
   `pose_vectors`, `confidence`.
3. `evidence_matching/model.py:38` `_combine_votes()` — transforms each sender's votes by the
   sensor displacement between sender and receiver ("if I am here, you should be there"),
   then **`.extend()`s them into one flat list per object**.
4. `learning_module.py:357` `receive_votes()` → `:902` `_update_evidence_with_vote()` —
   KD-tree over vote locations, `k=3` nearest per hypothesis, reduce, blend into own evidence.

---

## Finding (a) — the aggregation is a max, not a consensus · **CONFIRMED**

`learning_module.py:938`

```python
# Get the highest vote in the radius. Currently unweighted but using
# np.ma.average and the node_distance_weights also works reasonably well.
distance_weighted_vote_evidence = np.ma.max(
    all_radius_evidence,
    # weights=node_distance_weights,
    axis=1,
)
```

Stronger than the plan claimed. The variable is named `distance_weighted_vote_evidence` but
the weighting is **commented out** on line 940, and upstream's own comment on line 936 admits
it: "Currently unweighted". The name no longer describes the behaviour.

Probe result, three peers at 0.95 / 0.42 / 0.40:

| | |
|---|---|
| `np.ma.max` reduction | **0.95** (the loudest) |
| mean would be | 0.590 |
| result with the two agreeing modules removed | **0.95, identical** |

**Two modules agreeing with each other change the outcome by exactly zero.** This is the
computational form of H2's failure, present in the default configuration.

## Finding (b) — disagreement is never represented · **CONFIRMED, with a correction**

No `np.var`, `np.std`, `entropy`, or any dispersion statistic appears in either
`_combine_votes` or `_update_evidence_with_vote`. Votes are concatenated and reduced; the
spread of the group is never computed, never stored, never transmitted.

**Correction 1 — there is an `np.std`, but not where it matters.**
`learning_module.py:1159` computes `std_ge = np.std(graph_evidences)`. This is the spread
**across object hypotheses inside a single LM**, used to threshold possible matches. It is
not across LMs and says nothing about whether peers agree. The plan should not claim Monty
computes *no* variance anywhere; it computes the wrong one for our purposes.

**Correction 2 — there IS a cross-module agreement mechanism, and the plan missed it.**
`graph_matching.py:157` onward, plus `experiment/match_criteria.py`:

```python
class AnyLMsMatch(MatchCriterion):
    """Satisfied once any `count` of learning modules have reached "match"."""
```

Our 5-LM config sets `count: 3`. So Monty **does** ask "have at least 3 of 5 modules
converged?" — but this is a **terminal condition** that stops the episode. It does not feed
back into the vote, does not modulate evidence, and is a binary count of terminal states
rather than a measure of dispersion. The distinction is real but it must be stated in the
paper, because a reviewer who knows Monty will otherwise catch it.

## Finding (c) — `vote_weight` is a static scalar · **CONFIRMED exactly**

Every occurrence in the entire `src/` tree:

| Line | Role |
|---|---|
| `learning_module.py:163` | docstring |
| `:245` | default `vote_weight=1` |
| `:285` | `self.vote_weight = vote_weight` — **the only assignment** |
| `:951` | read, as `weights=[1, self.vote_weight]` |
| `:960` | read, multiplied into the evidence sum |

The probe enumerated every method of `EvidenceGraphLM` and found assignment in `__init__`
only. No mechanism exists by which a module repeatedly wrong out of domain becomes quieter.

`lm_to_lm_vote_matrix` is likewise assigned once (`monty_base.py:99`) and never mutated. Our
5-LM config is all-to-all (`conf/monty/connectivity/5lm_5sm.yaml`).

---

## Novelty check — the important part

Searched all TBP repos, issues, PRs, and the `docs/future-work/` tree.

| Query | Hits |
|---|---|
| `np.ma.max` | **0** |
| `vote_weight` | 1 — a spelling fix (#728, closed) |
| `disagreement` | 1 — PR #358, see below |
| consensus voting rule | **0** |

**`docs/future-work/voting-improvements/` exists with five planned items.** Read all five.
This is the honest comparison:

| Upstream item | Status | Overlaps us? |
|---|---|---|
| Generalize Voting to Associative Connections (PR #358, #359) | open, needs discussion | **No.** Solves object-**ID alignment** across LMs in unsupervised settings — how LM-A's "object_1" maps to LM-B's "object_3". Orthogonal to the aggregation rule. |
| Clean up and Simplify Voting | open | **Partial, and it matters.** Proposes filtering votes by orientation agreement *before* the KD-tree, for speed. Notes that votes can "spuriously align" and give "incorrectly positive evidence". They are aware of a *precision* problem in voting. They do **not** propose replacing the max reduction or measuring dispersion. |
| Vote on State | open | No. Object state as a sub-ID. |
| Outline How to Apply Attention | scoping, TBP-owned | **Watch this one.** "Emphasize the representations in certain LMs over others… top-down feedback and lateral competition." That is adjacent to our adaptive w(t). Currently theory/RFC only, no implementation, no dissent signal. |
| CMP displacements vs locations | open | No. |

**Assessment: the contribution is still open, but it is not in virgin territory.** Upstream
knows voting needs work and has an attention item that could collide with CP-4. What nobody
has proposed is: measuring *disagreement across modules* and feeding it back into the
aggregation. The `np.ma.max` reduction has never been raised at all.

**Consequence for the paper:** we must cite `clean-up-and-simplify-voting.md` and the
attention item, and state plainly what we add beyond them. Claiming the vote rule is
unexamined would be false and checkable.

---

## Corrections owed to `docs/plan.html`

1. §3 must name **`evidence_matching/model.py`** as the path our experiments use. The plan
   currently describes `graph_matching.py`, which our configs do not exercise.
2. §3 finding (b) must be narrowed: dispersion is absent **from the vote path**, not from the
   codebase. `np.std` exists at `learning_module.py:1159`, within-LM.
3. §3 must acknowledge `AnyLMsMatch` as an existing cross-module agreement mechanism, and
   distinguish it: terminal condition, not vote input.
4. §8 must add a risk: upstream's planned attention work could overlap CP-4.
5. §9 must cite the five `future-work/voting-improvements` items.

## Reproduce

```bash
cd ~/PolyBrains/upstream/tbp.monty
.venv/bin/python ~/PolyBrains/tests/cp1_probe_vote_path.py   # exit 0 = all three confirmed
```
