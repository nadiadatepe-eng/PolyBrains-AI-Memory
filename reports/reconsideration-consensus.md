# Reconsideration — consensus does not need to be true

**Written 2026-08-20 after Nadi's critique. Nothing has been re-run. No number
below is new; every one is lifted from a committed report. This document argues
that we mis-read numbers we already had.**

Status: **reconsideration proposed, not adopted.** `docs/plan.html` is
unchanged. H1 and H2 stand as written until Nadi decides.

---

## 1. The critique, in Nadi's words

> A consensus does not need to be true or false. Consensus can be reached on
> false premises. Our brain doesn't seek truth the same way an AI does — a
> brain can accept a false premise as truth, a silent agreement, if the
> conditions require it.

And the construction that makes it concrete:

> If I ask you a question with four alternatives and all of them are wrong —
> and not answering is not an option — then whatever you answer is wrong. The
> inspector evaluating you has two options: agree with you, or pick another
> wrong answer. The third inspector, seeing you both, has three choices; either
> way he is wrong, so finding the consensus and agreeing with one of you is the
> best option to avoid disagreement.

**This is not an objection to our results. It is an objection to what we think
they measure.**

---

## 2. Why it lands: the condition our design cannot produce

In every experiment in this project, the evaluated object is drawn from the set
the modules were pretrained on. `pb_indomain_5lm` trains on the objects that
`e1_ood_*` evaluates; the OOD manipulation is **rotation**, not identity. The
correct answer is therefore **always inside the hypothesis space**.

Nadi's scenario requires the opposite: the true answer *absent* from the
alternatives. **We built a world in which that cannot happen, and then measured
that consensus tracks truth reasonably well.**

That is close to circular. Not fraudulent — the rotation manipulation is a real
generalisation test — but the specific question "does agreement imply
correctness" was asked only under the one condition where the answer is
guaranteed to flatter it.

**Two of Nadi's three conditions already hold in our setup:**

| condition | present? | evidence |
|---|---|---|
| abstention is costly | **yes** | we track `send_none`%; P6 showed 88% silence destroys the mechanism |
| modules see each other | **yes** | `_combine_votes` transforms votes into the receiver's frame |
| truth absent from the options | **no** | every eval object is in the pretrained set |

Only the third is missing. It is also the cheapest to add (§5).

---

## 3. Our own data already shows the effect — we under-read it

### 3.1 P12: agreement rose, precision fell, and we bolded the wrong column

From `reports/p12-adaptive-weight.md`, unchanged:

| arm | unanimous | **unanimity precision** | confident-wrong |
|---|---|---|---|
| frozen | 36.50% | **97.49%** | 1.00% |
| ood | 48.00% | 95.99% | 2.00% |
| indomain | **58.00%** | **94.92%** | **3.00%** |

The arm with the most agreement has the **least reliable** agreement and the
most confident errors. We reported "+21.50 pp" as the headline and the
precision drop as a parenthesis with "not significant at n=5".

**Nadi's reading fits this table better than ours does.** Some of that
21.50 pp is agreement bought at the cost of correctness. We measured it,
printed it, and did not think about it.

### 3.2 P4: false consensus, already observed, already named too gently

From `reports/p4-voting-harms.md`:

```
 ep  LM0 LM1 LM2 LM3 LM4   target
  6   ok  ok  ok  ok  ok   dice   <- ALL FIVE CORRECT (before voting)
```

On `dice`, all five modules were independently correct and **all five failed
after talking to each other**. One module's wrong hypothesis propagated through
the vote and became unanimous.

| | all modules failed | correlation |
|---|---|---|
| voting ON | **2 episodes** | **29%** |
| voting OFF | 0 episodes | 0% |

We called this "correlated failure" — a statistics term that describes the
shape and hides the mechanism. **Nadi's framing names the mechanism: a false
premise became the group's truth because agreeing was the cheaper move.**

### 3.3 What still defends the theory, and how far

P8 and P12 anticipated the circularity objection and answered it with a
threshold-free metric: **mean modules correct per episode**, which agreement
alone cannot inflate.

| contrast | mean modules correct | t |
|---|---|---|
| `max` − no voting (P8) | **+0.564** | t(9)=15.11 |
| `indomain` − `frozen` (P12) | **+0.365** | t(4)=3.61 |

Voting does propagate genuinely correct evidence. P8 also reports **277
episodes lifted, 75 dragged, zero 5→0 collapses**.

**But this defence is weaker than we treated it.** A mean over modules cannot
separate:

- *more modules are independently right*, from
- *more modules were pulled to one answer, which happened to be right more
  often than chance.*

Both raise the mean. Only the first is what H1 claims. **The metric we used to
rule out the confound cannot actually distinguish it** — it only rules out the
crudest version, where agreement is on nothing in particular.

---

## 4. What is actually wrong with the theory

**Not that H1 is false.** Voting demonstrably moves accuracy, in both
directions, by tens of points.

**The defect is that every metric in this project scores against a known
target.** Every question we ask is *did they converge on the true label*. A
system that only measures truth-tracking **cannot observe convergence that is
not about truth at all**. It sees "agreed and right" and "agreed and wrong" as
good and bad outcomes — never as *the same mechanism* with different luck.

So the missing thing is an axis, not a correction:

| what we measure | what we cannot currently measure |
|---|---|
| did they agree | *why* they agreed |
| were they right | whether a module abandoned its own evidence |
| how much they agreed | whether agreement was earned or deferred |

**H1's second clause is where this bites.** It says the advantage scales with
*disagreement*. But we only ever observe disagreement's **absence** — and
Nadi's `send_none` lesson is precisely that absence has two causes that look
identical in output: a module that dissents, and a module that was silenced or
deferred.

---

## 5. The experiment that would settle it

**E-null — the held-out target.**

Evaluate on an object that is **not in the pretrained set**. Every module must
answer; none can be right. Then measure unanimity.

- **Pre-registered prediction:** unanimity stays substantially above zero. If
  modules converge when correctness is impossible, then unanimity is confirmed
  to measure **coordination**, and every unanimity number in this project must
  be re-read with that constant subtracted.
- **What refutes Nadi's critique:** unanimity collapses to near zero. That
  would mean agreement in this substrate genuinely requires a correct
  attractor, and consensus here does track truth.

**Either outcome is publishable, and the second would strengthen the project
more than anything currently in it.**

### 5.1 The cost, checked rather than assumed

My first draft called this "low cost, no new pretraining". **That was wrong,
and checking it took two minutes.**

Verified 2026-08-20:

- `train_distinctobj_predefined.yaml` and `eval_distinctobj_random.yaml` carry
  the **identical 10-object list** — mug, bowl, potted_meat_can, spoon,
  strawberry, mustard_bottle, dice, golf_ball, c_lego_duplo, banana. This
  confirms §2: the target is always in the hypothesis space.
- **`~/tbp/data/mujoco/objects/ycb/` contains exactly those 10 objects and
  nothing else.** Upstream's `eval_77obj_random.yaml` references
  `master_chef_can`, `power_drill`, `padlock` and others that **are not on this
  machine**.

So E-null needs an asset download first. That is not free, and given the
HabitatSim situation the conversion path for a new YCB mesh into the MuJoCo
tree is **unverified** — it may be routine or it may be its own checkpoint.

**Two cheaper variants that need no new assets**, and should be considered
first:

- **Leave-one-out pretraining.** Pretrain on 9 objects, evaluate on the 10th.
  The held-out object is then genuinely outside the hypothesis space using only
  assets we have. Costs one pretraining run (47 s for 5 LMs, per CP-0), which
  is cheaper than a download of unknown difficulty.
- **Rotation so extreme it is effectively a new object.** Weaker, because the
  correct label technically remains available, so it does not cleanly implement
  Nadi's condition.

**Leave-one-out is the honest first choice.** It implements the condition
exactly and uses only what is on disk.

### 5.2 A second measurement, cheap and more diagnostic

**Deference rate.** Compare each module's pre-vote and post-vote state. Count
how often a module abandons a hypothesis that its *own* evidence favoured.

That separates the two readings §3.3 cannot: propagation of correct evidence
looks different from deference to the majority, even when both raise the mean.
The data to compute it may already exist in committed run directories — that is
worth checking before building anything.

---

## 6. What this would change in the plan

Proposed, **not applied**:

1. **Unanimity precision becomes a headline, never a side column.** Agreement
   and correctness are reported as a pair, always. A gain in one with a loss in
   the other is a finding, not a footnote.
2. **H1's second clause gets an honesty note**: we observe the absence of
   disagreement, and absence has two causes.
3. **A third hypothesis, H3**, stated to be losable:
   > *Voting raises agreement and raises correctness, and these are separable
   > effects. A mechanism that delivers the first without the second is the
   > failure mode, not a partial success.*
4. **P4's "correlated failure" is renamed** to what it is: false consensus.
5. **E-null, or the leave-one-out variant, runs before any further voting
   experiment**, including P13. Everything downstream inherits the
   interpretation it settles.

---

## 7. What this does NOT change

- No result is withdrawn. Every number stands.
- P8's central finding is untouched and arguably strengthened: **the sign of
  the voting effect is set by the scoring rule.** Nadi's critique is a
  statement about what scoring rules can see, which is the same argument one
  level deeper.
- H2's refutation stands. If anything the mechanism now has a better
  explanation: bounded weight prevented capture *because* it stopped any module
  buying the group's agreement.

---

## 8. The connection to the verifier

The same failure produces the same design rule in both projects. In
`~/PROPOSAL-polymath-verifier.md` §4.5: **frames must be blind to each other**,
because an inspector that reads previous verdicts inherits their frame.

Here it is measurable rather than argued: our modules *do* see each other via
`_combine_votes`, and P4 shows what that produces. **PolyBrains is the
experimental evidence for the verifier's blindness rule**, and E-null would make
that evidence direct rather than incidental.

---

**Nothing here is decided. `docs/plan.html`, `PREDICTIONS.md` and every report
are unchanged.**
