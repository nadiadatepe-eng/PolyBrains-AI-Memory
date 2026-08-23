"""Adaptive vote weight: w(t) driven by out-of-domain track record.

Monty's `vote_weight` is a constant set in `__init__` and never updated
(confirmed at the pinned sha, `reports/vote-path.md` finding (c)). There is no
mechanism by which a module that is repeatedly wrong outside its training
distribution becomes quieter, nor one by which a module reliably right on novel
input becomes louder.

This module supplies that mechanism. Two design constraints come straight from
the polymath specification and are enforced by tests:

  * **A module can never be silenced permanently.** `w_min > 0` is a hard
    floor. "Become a beginner without losing intellectual confidence" requires
    that a module which has been wrong can still be heard, and can recover.
  * **Recovery must be possible from the floor.** A module at `w_min` that
    starts being right must climb back. A one-way ratchet would encode exactly
    the entrenchment the project is trying to study.

Nothing here is claimed to improve accuracy. CP-4's gate is only that w(t)
demonstrably moves in the right direction on a task with a known-unreliable
module, and that the two invariants above hold.

Constants frozen at CP-4, 2026-08-18, before any accuracy comparison.
"""

from __future__ import annotations

import numpy as np

#: Hard floor. A module at this weight still contributes. Frozen.
W_MIN = 0.1
#: Ceiling, to stop any module dominating outright. Frozen.
W_MAX = 2.0
#: Exponential-moving-average horizon for the track record. Frozen.
EMA_ALPHA = 0.1


class AdaptiveVoteWeight:
    """Per-module vote weight updated from out-of-domain correctness.

    The weight tracks an exponential moving average of whether this module's
    vote agreed with the eventual outcome, evaluated *only* on out-of-domain
    episodes. In-domain performance deliberately does not raise the weight:
    that is the H2 failure mode, where a module confident on familiar input
    captures the consensus.

    Args:
        w_init: starting weight. 1.0 reproduces upstream's default.
        alpha: EMA rate. Higher adapts faster and is noisier.
        w_min: hard floor, must be > 0 so no module is ever silenced.
        w_max: ceiling.
        frozen: if True the weight never moves. This is the ablation arm, and
            it must reproduce upstream exactly.
    """

    def __init__(
        self,
        w_init: float = 1.0,
        alpha: float = EMA_ALPHA,
        w_min: float = W_MIN,
        w_max: float = W_MAX,
        frozen: bool = False,
    ):
        if not (0 < w_min <= w_init <= w_max):
            raise ValueError(
                f"require 0 < w_min <= w_init <= w_max, got "
                f"{w_min}, {w_init}, {w_max}"
            )
        self.w_init = float(w_init)
        self.alpha = float(alpha)
        self.w_min = float(w_min)
        self.w_max = float(w_max)
        self.frozen = bool(frozen)

        self._w = float(w_init)
        #: EMA of out-of-domain correctness in [0, 1]; starts neutral.
        self._score = 0.5
        self.history: list[float] = [self._w]
        self.n_updates = 0

    @property
    def weight(self) -> float:
        return self._w

    @property
    def score(self) -> float:
        """Current out-of-domain track record, in [0, 1]."""
        return self._score

    def update(self, was_correct: bool, out_of_domain: bool = True) -> float:
        """Record one episode outcome and return the new weight.

        Args:
            was_correct: did this module's vote agree with the outcome?
            out_of_domain: only OOD episodes move the weight. In-domain
                outcomes are recorded in `n_updates` but change nothing, which
                is the point: in-domain confidence must not buy influence.

        Returns:
            The updated weight.
        """
        self.n_updates += 1
        if self.frozen or not out_of_domain:
            self.history.append(self._w)
            return self._w

        target = 1.0 if was_correct else 0.0
        self._score = (1 - self.alpha) * self._score + self.alpha * target

        # Map score in [0,1] to weight in [w_min, w_max], with score 0.5
        # mapping to w_init so a neutral record reproduces upstream.
        if self._score >= 0.5:
            frac = (self._score - 0.5) / 0.5
            w = self.w_init + frac * (self.w_max - self.w_init)
        else:
            frac = (0.5 - self._score) / 0.5
            w = self.w_init - frac * (self.w_init - self.w_min)

        self._w = float(np.clip(w, self.w_min, self.w_max))
        self.history.append(self._w)
        return self._w

    def reset(self) -> None:
        self._w = self.w_init
        self._score = 0.5
        self.history = [self._w]
        self.n_updates = 0

    def __repr__(self) -> str:
        return (
            f"AdaptiveVoteWeight(w={self._w:.3f}, score={self._score:.3f}, "
            f"n={self.n_updates}, frozen={self.frozen})"
        )
