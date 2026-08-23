# CP-2 — Rival accounts

**Date:** 2026-08-18 · sources cached in `reports/sources/` before the line outage
**Gate:** name at least one experiment where structure-mapping and Thousand Brains Theory
predict *different* outcomes. If none can be found, say so, because that weakens the paper.

**Gate met.** E3 (the clone control) separates them, and E2 separates our account from the
ensemble-diversity literature. Details below, including the case where we would be wrong.

---

## 1. Why this section exists

The failure mode named in `docs/plan.html` §1 is a paper that maps cognitive-science
vocabulary onto a neuroscience theory and stops. A subtler version is a paper that reads only
its own tradition and therefore agrees with itself. Two literatures make claims about our
experiments and neither is Numenta's.

---

## 2. Gentner's structure-mapping theory

Gentner 1983, *Structure-Mapping: A Theoretical Framework for Analogy*, Cognitive Science
7:155-170. This is the established formal account of "translate ideas from one field into
another" — one of Nadi's thirteen polymath properties — and it predates the reference-frame
account by three decades.

### What it claims

Analogy maps **relations between objects**, not attributes of objects. From the paper:

> Relations between objects, rather than attributes of objects, are mapped from base to
> target.

And the selection rule, which is the load-bearing part:

> **(The Systematicity Principle)** A predicate that belongs to a mappable system of mutually
> interconnecting relationships is more likely to be imported into the target than is an
> isolated predicate.

The worked example is Rutherford's atom-as-solar-system: `MORE MASSIVE THAN` transfers but
`HOTTER THAN` does not, because only the former participates in the central-force system.
Crucially, Gentner insists the rules are **syntactic**:

> the rules depend only on syntactic properties of the knowledge representation, and not on
> the specific content of the domains

### What it predicts for our experiments

Structure-mapping is a theory of *transfer between representations*, not of *voting among
them*. Mapped onto our setup, an LM's object graph is a relational structure, and a vote is
an attempt to align two such structures.

| Experiment | Structure-mapping predicts | TBT / our H1 predicts |
|---|---|---|
| **E1** multi-frame vs single-frame OOD | Advantage, but from **relational depth** — modules holding richer interconnected structure transfer better. Number of frames is incidental. | Advantage from **disagreement** between complete models in different reference frames. |
| **E2** confidence weighting | **No strong prediction.** Systematicity is about which predicates map, not how confident voters are weighted. Largely silent. | Confidence weighting destroys the advantage by letting one module capture consensus. |
| **E3** diverse vs near-clone modules | **Clones should transfer as well as diverse modules**, provided each holds the same systematic relational structure. Diversity per se is not the mechanism; systematicity is. | **Clones should buy nothing.** The advantage tracks disagreement. |

### The divergence, stated plainly

**E3 is the experiment that separates the two theories.**

- If near-clone modules transfer as well as diverse ones, and both beat single-frame, the
  result favours a *systematicity* account: what matters is the richness of each module's
  relational structure, not that modules differ. **H1's second clause is false.**
- If clones buy nothing while diverse modules help, disagreement is doing the work and
  systematicity alone cannot explain it.

This is a real fork, and we are not confident which way it goes. Recording that now, before
the run, is the point of pre-registration.

### Where the theories are genuinely compatible

Both say analogy is structural rather than surface. Hawkins' reference frame is a candidate
*mechanism* for what Gentner describes at the computational level: applying a frame learned
in domain A to input from domain B is structural alignment implemented in cortex. **We should
not claim to refute structure-mapping.** The honest position is that TBT proposes a substrate
for it, and that our H1 adds a claim about *disagreement* which structure-mapping does not
make.

### The caveat that limits us

Gentner's theory is about **relational structure between propositions**. Monty's LMs vote on
**locations and poses in 3D space**. Whether a pose hypothesis constitutes a "relation" in
Gentner's sense is arguable, and a reviewer may say the mapping is loose. We should state
this limitation ourselves rather than have it pointed out.

---

## 3. The ensemble-diversity literature

This is the more dangerous rival, because if H1 holds it may be rediscovering something ML
already knows.

### The supporting side

Rubinstein, Teney, Scimeca & Oh, *Scalable Ensemble Diversification for OOD Generalization
and Detection* (arXiv:2409.16797). Their method:

> SED identifies hard training samples on the fly and **encourages the ensemble members to
> disagree** on these.

And their result:

> for OOD generalization, we observe large benefits from the diversification in multiple
> settings

**This is uncomfortably close to H1.** Deliberately induced disagreement, measured OOD
benefit. If we find that multi-frame voting helps OOD and the advantage tracks disagreement,
a reviewer can reasonably say: known result, new substrate.

### The failing side

Ortega, Cabañas & Masegosa, *Diversity and Generalization in Neural Network Ensembles*
(PMLR v151). They derive:

> the exact trade-off that exists between this diversity measure, the performance of the
> individual predictors and the generalization error of the ensemble

The trade-off is the point. **Diversity is not free.** Members made more diverse are usually
made individually worse, and the ensemble improves only while the diversity gain outruns the
individual loss. Their P2B-Ensemble beats a plain ensemble on some architectures and not
uniformly.

So the honest state of the field: diversity *sometimes* helps OOD, with a known trade-off
against individual member quality, and no general guarantee.

### What we can claim that they cannot

Three structural differences, each of which must be *measurable* or it is not a difference:

1. **Ensemble members share one input representation and vote on labels.** TBT modules hold
   complete models in **different reference frames** and vote on **poses and locations**. The
   vote carries geometry, not a class score.
2. **Ensemble diversity is induced during training** by an explicit objective. Our modules
   are diverse because they occupy different sensory positions; diversity is a consequence of
   embodiment, not a loss term.
3. **The ensemble literature aggregates by averaging or majority vote.** Monty's default is
   `np.ma.max` — winner-take-all, verified at CP-1. **No ensemble paper we found defends a
   max-reduction over member outputs.** That is the specific thing we change.

**E2 is the experiment that separates us from the ensemble account.** Ensemble theory has
little to say about whether confidence-weighting the aggregation destroys OOD transfer,
because ensembles rarely use a max in the first place. If H2 holds, it is a claim about
*aggregation rules under adversarial confidence*, which is our own ground.

### Where this leaves H1

**If H1 holds and the ensemble explanation fits, we say so.** The plan's §8 already commits
to this: "If the advantage tracks count rather than disagreement, we report ensembling and
stop claiming novelty." CP-2 sharpens it — even if the advantage *does* track disagreement,
we must argue that reference frames and pose-voting make it more than ensembling, and if we
cannot measure that difference, the claim is weak.

---

## 4. Summary for the paper

| Question | Structure-mapping | Ensemble diversity | TBT + H1/H2 |
|---|---|---|---|
| Why does multi-frame help OOD? | relational depth (systematicity) | decorrelated errors | disagreement between complete models |
| Do clones help? (**E3**) | **yes**, if systematic | no | **no** |
| Does confidence weighting hurt? (**E2**) | silent | mostly silent | **yes** |
| What is aggregated? | predicates | labels/logits | poses and locations |

**Two experiments do real discriminative work.** E3 forks structure-mapping against H1; E2
forks the ensemble account against H2. That satisfies the CP-2 gate.

## 5. What would make this section dishonest

- Presenting structure-mapping as refuted. It is not; it may be the computational-level
  description of what TBT implements.
- Omitting Ortega's trade-off, which is the strongest reason to expect H1 to fail.
- Claiming ensembles and TBT modules are simply different without measuring how.

## Sources

Cached locally in `reports/sources/` (gitignored, re-fetchable):
`gentner1983.pdf`, `gentner_structure_mapping_similarity.pdf`,
`ensemble_diversification.pdf` (arXiv:2409.16797),
`ortega_diversity_generalization.pdf` (PMLR v151).
