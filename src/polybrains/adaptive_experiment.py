"""H2's mechanism, wired so it actually runs.

## Why this file exists

`polybrains/weights.py` has held a complete, gated `AdaptiveVoteWeight` since
CP-4. `polybrains/learning_module.py` has held `record_episode_outcome` since
the same day. **Nothing ever called it outside the tests**, and every experiment
config sets `adaptive_weight: false`, so H2 — the hypothesis the venue decision
made load-bearing — was never once run. See the 2026-08-19 audit in
PREDICTIONS.md.

Turning the flag on alone would NOT have fixed it. w(t) only moves when
`record_episode_outcome` is called, so `adaptive_weight: true` without this file
produces a weight frozen at `w_init` for the whole run: an arm that completes
cleanly, prints plausible numbers, and tests nothing. That is this project's
fifth dead-arm shape, and it is registered here before the run rather than
discovered after.

## What H2 actually claims

*Weighting votes by a module's IN-DOMAIN confidence destroys the OOD advantage,
because one module confident on familiar input captures the consensus.*

So the experiment needs two weighting arms that differ in **what evidence moves
the weight**, not merely on/off:

    frozen      w(t) = w_init forever. Upstream. The control.
    ood         weight tracks OUT-of-domain correctness. The polymath design:
                being right on novel input earns influence.
    indomain    weight tracks IN-domain correctness -- H2's failure mode, the
                arm that should capture the consensus and hurt.

`AdaptiveVoteWeight.update(out_of_domain=...)` already implements the gate: it
ignores in-domain outcomes. The `indomain` arm inverts which episodes are passed
as `out_of_domain=True`, so the same frozen constants drive both arms and no new
free parameter enters.

## Contract

Upstream is read-only. This subclasses the experiment class and overrides
`post_episode` only, calling `super()` first so logging and counters are
untouched. Per-episode correctness is read from each LM's own terminal state,
the same source `eval_stats.csv` is written from.
"""

from __future__ import annotations

import logging
from typing import Literal

from tbp.monty.frameworks.experiments.object_recognition_experiments import (
    MontyObjectRecognitionExperiment,
)

logger = logging.getLogger(__name__)

WeightSource = Literal["frozen", "ood", "indomain"]


class AdaptiveWeightExperiment(MontyObjectRecognitionExperiment):
    """Feeds per-episode outcomes to each learning module's w(t).

    Args:
        weight_source: which episodes move the weight.
            ``"frozen"``   never (upstream control; w(t) stays at w_init).
            ``"ood"``      out-of-domain episodes only (polymath design).
            ``"indomain"`` in-domain episodes only (H2's failure mode).
        indomain_rotations: rotations counted as in-domain. Episodes at any
            other rotation are out-of-domain. Defaults to the training set
            used by `pb_indomain_5lm`.

    Attributes:
        weight_trace: ``(episode, lm_id, weight, score, was_correct)`` per
            episode per module. **Always report this.** A trace whose weights
            never leave ``w_init`` means the arm is dead, which is exactly how
            four earlier sweeps in this project produced plausible nulls.
    """

    #: The 5 rotations `pb_indomain_5lm` was actually pretrained on, read from
    #: configs/experiment/pb_pretrain_indomain.yaml lines 36-40. An earlier
    #: draft of this file guessed (0,180,0) here, which is NOT in the set --
    #: that would have mislabelled one rotation's episodes and silently
    #: corrupted the in-domain/OOD split the whole hypothesis rests on.
    #: Prefer passing `indomain_rotations` from the config over this default.
    DEFAULT_INDOMAIN = (
        (0, 0, 0), (0, 90, 0), (0, 270, 0), (90, 0, 0), (90, 180, 0),
    )

    def __init__(
        self,
        *args,
        weight_source: WeightSource = "frozen",
        indomain_rotations=None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.weight_source: WeightSource = weight_source
        self.indomain_rotations = {
            tuple(int(x) for x in r)
            for r in (indomain_rotations or self.DEFAULT_INDOMAIN)
        }
        self.weight_trace: list[tuple] = []
        self._episode_ix = 0

    # ------------------------------------------------------------------ #

    def _episode_is_indomain(self) -> bool:
        """True if this episode's rotation was in the pretraining set."""
        rot = getattr(self.env_interface, "primary_target", None)
        if isinstance(rot, dict):
            rot = rot.get("euler_rotation")
        if rot is None:
            return False
        try:
            key = tuple(int(round(float(x))) % 360 for x in rot)
        except (TypeError, ValueError):
            return False
        return key in self.indomain_rotations

    def _lm_was_correct(self, lm) -> bool:
        """Did this module identify the target? Same source as eval_stats."""
        target = getattr(self.env_interface, "primary_target", None)
        if isinstance(target, dict):
            target = target.get("object")
        try:
            mlh = lm.get_current_mlh()
            return bool(target) and mlh.get("graph_id") == target
        except Exception:  # noqa: BLE001 - a missing MLH is simply "not correct"
            return False

    def post_episode(self, steps) -> None:
        # READ BEFORE super(). `super().post_episode` ends by calling
        # `env_interface.post_episode()`, which ADVANCES `primary_target` to the
        # next episode -- upstream flags this itself at monty_experiment.py:584
        # ("move down here, otherwise env_interface.primary_target is already
        # changed"). Reading after super() therefore scores every module against
        # the WRONG episode's target. It did: a live smoke run had all 5 modules
        # marked incorrect while their MLH matched the target exactly, driving
        # w(t) down to 0.209 on pure artefact. The gate missed it because the
        # stub neutralised super(); test_adaptive_weight.py now asserts ordering.
        indomain = self._episode_is_indomain()
        outcomes = [
            (lm, self._lm_was_correct(lm))
            for lm in self.model.learning_modules
            if hasattr(lm, "record_episode_outcome")
        ]

        super().post_episode(steps)
        # `ood` learns from novel episodes; `indomain` learns from familiar
        # ones. AdaptiveVoteWeight.update() ignores anything passed as
        # out_of_domain=False, so this single flag selects the arm.
        # `frozen` records outcomes but never learns from them, so its trace is
        # written like every other arm's. Without this the frozen trace is EMPTY,
        # and "never moved" becomes indistinguishable from "never ran" -- the
        # ambiguity this project keeps getting caught by. AdaptiveVoteWeight is
        # constructed with frozen=not adaptive_weight, so passing True here still
        # cannot move a frozen weight.
        learn_from_this = (
            False if self.weight_source == "frozen"
            else ((not indomain) if self.weight_source == "ood" else indomain)
        )

        for lm, ok in outcomes:
            lm.record_episode_outcome(was_correct=ok, out_of_domain=learn_from_this)
            self.weight_trace.append(
                (
                    self._episode_ix,
                    getattr(lm, "learning_module_id", "?"),
                    float(getattr(lm, "effective_vote_weight", float("nan"))),
                    float(getattr(getattr(lm, "_w", None), "score", float("nan"))),
                    ok,
                )
            )
        self._episode_ix += 1
