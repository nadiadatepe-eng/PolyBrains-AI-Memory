# Reasoning kernel and ontology engineering — project north star

## Status

This document defines an **expected future architecture**, not an implementation claim. The
observed implementation remains the memory core and measured benchmark policies documented in the
repository. The difference between expected and observed structure is the long-term roadmap.

## Purpose

PolyBrains-AI-Memory should grow into a small, model-independent reasoning kernel for agents that
can reason, act, learn from outcomes, and adapt without erasing provenance or disagreement. Models
may propose interpretations, hypotheses, ontologies, plans, and actions; the kernel governs what is
accepted, rejected, retained as contested, acted upon, revised, or left unknown.

The intended loop is:

```text
observe → retrieve → construct hypotheses → compare evidence → abstain or decide
        → act → record outcome → revise beliefs → adapt policy
```

The kernel is the epistemic and control boundary. A language or multimodal model is never the
authority merely because its output is fluent, confident, repeated, or semantically similar.

## Kernel contracts

- Keep relevance, confidence, agreement, authenticity, independence, and correctness separate.
- Preserve competing hypotheses, minority evidence, contradictions, silence, and abstentions.
- Require every promoted belief, ontology statement, decision, and policy change to retain its
  evidence chain, provenance, time, frame, and validation state.
- Treat actions as experiments whose outcomes can support, contradict, or leave hypotheses open.
- Revise through append-only, versioned records; never rewrite the evidence that motivated an old
  decision.
- Keep models, planners, tools, agent frameworks, ontology formats, and storage engines removable
  behind capability adapters.
- Allow human approval and explicit refusal at consequential trust, ontology, policy, and action
  boundaries.

## Model-assisted ontology engineering

Ontology engineering is a governed reasoning capability around the kernel. Model families may be
used when they measurably help, through capability-based adapters rather than model-specific logic:

| adapter capability | possible model family | contribution |
|---|---|---|
| language interpretation | LLM | propose concepts, relations, axioms, mappings, definitions, and competency questions |
| visual grounding | VLM | relate concepts to images, diagrams, objects, regions, and spatial evidence |
| concept-level representation | LCM | propose or compare concept structures when a suitable large-concept model exists |
| action semantics | LAM | propose actions, preconditions, effects, permissions, and failure outcomes |
| terminology completion | MLM | compare lexical variants or fill terminology gaps; “MLM” remains capability-defined because it may mean masked or multimodal language model |

The family names are provisional. The stable boundary is the capability contract and its evidence,
not a vendor, architecture, checkpoint, or acronym.

The expected ontology workflow is:

```text
source text / image / observation / existing schema
  → one or more model proposals
  → provenance-preserving extraction
  → conflict and alias detection without destructive merge
  → deterministic structural validation
  → competency-question tests
  → evidence or human promotion, rejection, contest, or abstention
  → immutable ontology version
```

An ontology version should eventually represent classes, instances, relations, constraints,
axioms, aliases, contested mappings, provenance, validation results, deprecations, and migrations.
OWL, RDF, SHACL, or another external format may be adapters; none belongs in the kernel until a
measured requirement justifies it.

## Expected ontology — generated design target

The statements below are expectations for the future reasoning-kernel domain. They are not facts
about the current repository.

expected [[Reasoning Kernel]] part of [[Agent Architecture]] [partOf]
expected [[Reasoning Kernel]] depends on [[Memory Core]] [dependsOn]
expected [[Reasoning Kernel]] depends on [[Evidence Governance]] [dependsOn]
expected [[Reasoning Kernel]] produces [[Decision]] [produces]
expected [[Decision]] depends on [[Hypothesis Set]] [dependsOn]
expected [[Hypothesis Set]] derived from [[Memory Core]] [derivedFrom]
expected [[Hypothesis]] related to [[Contradiction]] [relatedTo]
expected [[Evidence Governance]] validates [[Hypothesis Set]] [validates]
expected [[Decision]] produces [[Action]] [produces]
expected [[Action]] produces [[Outcome]] [produces]
expected [[Outcome]] validates [[Hypothesis]] [validates]
expected [[Outcome]] stores [[Provenance]] [stores]
expected [[Belief Revision]] derived from [[Outcome]] [derivedFrom]
expected [[Belief Revision]] stores [[Contradiction]] [stores]
expected [[Policy Adaptation]] derived from [[Belief Revision]] [derivedFrom]
expected [[Policy Adaptation]] depends on [[Evidence Governance]] [dependsOn]
expected [[Ontology Engineering]] part of [[Reasoning Capability]] [partOf]
expected [[Ontology Engineering]] depends on [[Evidence Governance]] [dependsOn]
expected [[Ontology Proposal]] derived from [[Source Evidence]] [derivedFrom]
expected [[Ontology Proposal]] stores [[Provenance]] [stores]
expected [[LLM Adapter]] produces [[Ontology Proposal]] [produces]
expected [[VLM Adapter]] produces [[Visual Grounding]] [produces]
expected [[Visual Grounding]] derived from [[Source Evidence]] [derivedFrom]
expected [[LCM Adapter]] produces [[Concept Structure]] [produces]
expected [[Concept Structure]] derived from [[Source Evidence]] [derivedFrom]
expected [[LAM Adapter]] produces [[Action Schema]] [produces]
expected [[Action Schema]] depends on [[Ontology Version]] [dependsOn]
expected [[MLM Adapter]] produces [[Terminology Mapping]] [produces]
expected [[Terminology Mapping]] related to [[Ontology Proposal]] [relatedTo]
expected [[Model Adapter]] depends on [[Capability Contract]] [dependsOn]
expected [[Capability Contract]] validates [[Model Adapter]] [validates]
expected [[Ontology Validator]] validates [[Ontology Proposal]] [validates]
expected [[Ontology Validator]] validates [[Concept Structure]] [validates]
expected [[Competency Question]] validates [[Ontology Version]] [validates]
expected [[Ontology Version]] stores [[Provenance]] [stores]
expected [[Ontology Version]] stores [[Contradiction]] [stores]
expected [[Human Review]] validates [[Ontology Promotion]] [validates]
expected [[Human Review]] depends on [[Competency Question]] [dependsOn]
expected [[Ontology Promotion]] produces [[Ontology Version]] [produces]

POLE+O typing for this target: people and agent/model actors are **Person**; persistent records,
schemas, adapters, and versions are **Object**; repositories and stores are **Location**; runs,
actions, outcomes, revisions, validations, and promotions are **Event**; reasoning, provenance,
ontology, belief, trust, and policy terms are **Ontology** concepts.

## Expected axioms and falsifiers

1. A promoted belief or ontology statement must retain evidence or an explicit human decision.
   **Falsifier:** one promoted statement with neither.
2. An action outcome may revise a hypothesis but may not delete its prior evidence.
   **Falsifier:** revision makes the earlier evidence unrecoverable.
3. Authentication establishes authorship, not correctness.
   **Falsifier:** a valid signature is used as the sole correctness condition.
4. Conflicting ontology proposals remain independently inspectable until an explicit promotion.
   **Falsifier:** deduplication destructively merges a contested pair.
5. A model adapter can be removed without changing kernel record or validation semantics.
   **Falsifier:** removing one model changes the meaning of stored kernel state.
6. Policy adaptation is versioned and outcome-backed.
   **Falsifier:** a policy changes silently or solely from model confidence/agreement.

## Observed ontology — extracted from the current project

observed [[Memory Record]] stores [[Provenance]] [stores]

> “Require identity, owning agent and frame, source, event time, write time, confidence, lifecycle state, and links to supporting, contradicting, and superseded records.” — `TODO.md`, CP-M1

observed [[Private Episodic Store]] stores [[Memory Record]] [stores]

> “Give each agent/frame an independent append-only episodic store.” — `TODO.md`, CP-M2

observed [[Claim Exchange]] validates [[Signed Claim]] [validates]

> “Exchange signed claims and evidence references rather than exposing private stores.” — `TODO.md`, CP-M6

observed [[Conservative Consolidation]] depends on [[Verified Outcome]] [dependsOn]

> “Compare no consolidation, naive agreement/confidence consolidation, and conservative provenance/outcome consolidation.” — `TODO.md`, CP-M3

observed [[CP-C2 Replication]] validates [[Outcome Provenance Rule]] [validates]

> “The outcome/provenance rule passed the registered replication gate on seeds 11, 23, and 37.” — `reports/cp-c2-replication.md`

observed [[Memory Core]] opposes [[Model Dependency]] [opposes]

> “The core and its gate use only the Python standard library.” — `README.md`

observed [[Outcome Provenance Rule]] opposes [[Core API Integration]] [opposes]

> “The measured rule stays outside the core API.” — `README.md`

Extraction precision: **7/7 statements hand-checked** against the named source sentence and active
code where the sentence names a mechanism rather than its validation behavior.

## Gap: what the project does not yet declare

Scope: the complete active repository as of 2026-08-26, excluding preserved upstream reports as
implementation evidence.

- No kernel-level hypothesis, belief, decision, action, outcome, or policy-version record exists.
- No observe–decide–act–revise execution loop exists.
- No capability adapter contract for LLM, VLM, LCM, LAM, or MLM models exists.
- No ontology proposal, axiom, competency-question, validation, promotion, migration, or contested
  alias mechanism exists.
- No model-assisted ontology experiment has been pre-registered or measured.

These are planned absences, not defects. Evidence trust, belief revision, and action/outcome gates
must precede ontology promotion or model-directed adaptation.

## Long-term sequence

1. Finish evidence authenticity and independence (v0.4).
2. Add explicit hypothesis construction and comparison.
3. Test decision and abstention under uncertainty.
4. Add bounded action proposals and outcome records.
5. Test append-only belief revision and policy adaptation.
6. Define capability adapters and run the first model-assisted ontology experiment.
7. Add governed multi-agent reasoning without consensus-as-truth.

Every phase begins with a falsifiable proposal and the smallest control that can defeat it. The
reasoning kernel is earned by these measured contracts; it is not declared complete by assembling
features.
