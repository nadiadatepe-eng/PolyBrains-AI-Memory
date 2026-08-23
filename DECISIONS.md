# PolyBrains-AI-Memory — Decisions

Reasoning behind choices, including what was rejected. Not a diary; entries are here because
they constrain future work.

---

## 2026-08-23 · Independent memory project, not a shared working tree

PolyBrains-AI-Memory begins from PolyBrains commit `fb8071d` but is a separate project. Claude's
work in `[source PolyBrains checkout]` and Codex's work here must not overwrite or silently synchronize
one another.

The inherited finding that agreement, confidence, and correctness differ becomes a design
constraint, not proof of a new memory hypothesis. The new contribution surface is explicit
external memory with independent private stores, provenance-preserving claim exchange, and
conservative shared consolidation. A falsifiable proposal must precede implementation.

---

## 2026-08-18 · Project framing

**Thousand Brains Theory is the substrate, the polymath properties are the specification.**

The alternative framings were rejected:

- *Polymathy as illustration of TBT* — unfalsifiable. Maps vocabulary onto a theory and
  stops. This is the dominant failure mode of the genre and reviewers recognise it.
- *TBT as explanation of polymathy* — same problem in the other direction, and it would
  require psychological evidence we do not have.

What survives: TBT gives a working system with modules, reference frames and a vote. The
polymath list gives requirements Hawkins never specified. The contribution is the gap between
them, not the resemblance.

## 2026-08-18 · One falsifiable claim, not a mapping

The paper commits to H1 and H2 (see `docs/plan.html` §1). H1's second clause — that the OOD
advantage scales with module **disagreement**, not module **count** — is what makes it
losable, and E3's clone control is designed to kill it.

The seven polymath properties that TBT already explains (§4.1) are fenced off as motivation.
Writing them up as findings would be the failure mode above.

## 2026-08-18 · Read the source before believing the docs

The three findings in §3 came from reading `monty_base.py` and
`evidence_matching/learning_module.py` directly, not from documentation. The doc URLs we
tried (`docs.thousandbrains.org/docs/voting`) 404'd. This is why CP-1 re-reads everything
against the pinned sha rather than trusting the first pass.

## 2026-08-18 · Four decisions from Nadi

| Question | Decision | Consequence |
|---|---|---|
| Venue | Journal | CP-2 (rival theories) is mandatory, not optional. Both H1 and H2 needed. |
| Upstream | Keep in our layer until the paper is out | No CLA yet. Offer the dissent instrumentation upstream afterwards. |
| Scope | All six §4.2 properties, weight on H2 | H2 is the one that survives if time runs out. |
| Compute | No external compute; scale down instead | Also: determine empirically what hardware *would* be needed, as a reportable result. |

## 2026-08-18 · CP-0: committed to MuJoCo, not HabitatSim

**Not a preference. HabitatSim cannot be installed on this platform.** The PyPI wheel is
`macosx_13_0_arm64` and cp310 only; on Linux it is conda-only, and the account boundary rules
discourage a conda install here.

Consequences accepted:

1. **17 integration tests skip, including `evidence_lm_test.py`** — the test for the exact
   module we intend to modify. Mitigation is now a CP-3 requirement: write our own MuJoCo
   vote-path integration test *before* touching the module.
2. **Upstream's published benchmark table is Habitat-based.** We cannot compare our absolute
   numbers to it. All comparisons must be internal: our arms against each other, same
   simulator, same seeds. This is a real loss of an external reference point and it goes in
   the paper.
3. **Object placement needs re-tuning.** The habitat-tuned `rotations_all` set puts objects
   outside the MuJoCo camera's view.

Rejected alternative: build HabitatSim from source. Cost is high, and the MuJoCo path is
supported upstream with 18 of 63 configs already ported, including the 5-LM voting one.

## 2026-08-18 · CP-0's accuracy number is not a baseline

The 60% (30/50) from the first voting eval is a **pipeline liveness check**. The model was
pretrained on a single rotation `[[0,0,0]]` to get past the placement bug, then evaluated on
random rotations. Upstream reports 99% for the equivalent Habitat experiment.

Recorded here explicitly because a 60% figure in a results directory will otherwise be
mistaken for a finding later. A real baseline requires the CP-5 placement fix and full
pretraining.

## 2026-08-18 · YCB fetched directly from S3

`habitat_sim.utils.datasets_download` is the documented path and is unavailable to us.
MuJoCo needs only `textured.obj` + `texture_map.png` per object, both present in the official
Berkeley meshes on the YCB S3 bucket. 10 objects, 64 MB, 14 s.

One trap worth remembering: the tarballs contain macOS AppleDouble `._` resource-fork files
that sort before the real ones. Copying them yields
`ValueError: incorrect PNG signature, it's no PNG or corrupted` from MuJoCo's compiler.
`tools/fetch_ycb.sh` filters them with `! -name "._*"`.

## 2026-08-18 · CP-1: the max reduction is worse than we described, and the name lies

`learning_module.py:938` reduces incoming votes with `np.ma.max`. The variable receiving it
is named `distance_weighted_vote_evidence`, but line 940 has the weighting **commented out**,
and upstream's own comment at 936 reads "Currently unweighted". The name describes an
intention, not the behaviour.

This matters for the paper's framing. H2 is not a hypothetical failure mode we introduce to
test; it is the default configuration's actual behaviour. Probe: three peers at 0.95, 0.42,
0.40 reduce to 0.95, and deleting the two agreeing peers leaves the result identical.

## 2026-08-18 · CP-1: two things the plan got wrong

**Wrong file.** The plan's §3 described `graph_matching.py`. Our configs use
`evidence_5lm_nn10_dod003` → `EvidenceGraphLM` → `evidence_matching/model.py`, which has a
*different* `_combine_votes` that concatenates rather than tallying. Corrected.

**Overclaimed absence.** "Disagreement is never represented" was too strong in two ways:

1. `np.std` exists at `learning_module.py:1159` — but across object hypotheses *within* one
   LM, not across LMs.
2. `AnyLMsMatch` in `experiment/match_criteria.py` **is** a cross-module agreement
   mechanism, and our config sets `count: 3` of 5. But it is a terminal condition that ends
   the episode: a binary count of terminal states, never fed back into the vote, measuring no
   dispersion.

Both are now stated in the plan. A reviewer who knows Monty would have caught the second and
the paper would have lost credibility on its central claim.

## 2026-08-18 · CP-1: novelty is open but not virgin, and we will say so

`np.ma.max` has **never** been mentioned in any TBP issue or PR. Neither has a consensus
voting rule. But `docs/future-work/voting-improvements/` contains five planned items, and
pretending the vote rule is unexamined would be false and trivially checkable.

Two we must cite:

- **Clean up and Simplify Voting** — upstream already knows votes can "spuriously align" and
  give "incorrectly positive evidence". They propose orientation pre-filtering for speed and
  precision. They do not propose replacing the max or measuring dispersion.
- **Outline How to Apply Attention** — TBP-owned, at scoping. Proposes to "emphasize the
  representations in certain LMs over others" via lateral competition. **Adjacent to our
  adaptive w(t).** Theory only for now. Re-check before CP-4; if they ship first, build on it.

The distinction we claim: nobody has proposed *measuring disagreement across modules and
feeding it back into the aggregation*. That stays our contribution.
