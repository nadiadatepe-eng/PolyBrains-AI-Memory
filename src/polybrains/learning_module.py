"""Drop-in learning module that routes the vote reduction through PolyBrains.

Design constraint from `AGENTS.md`: upstream is read-only. So rather than
patching `learning_module.py`, this subclasses `EvidenceGraphLM` and overrides
exactly one method, `_update_evidence_with_vote`.

The override is a transcription of upstream's method at the pinned sha
(`0c81b1f`, learning_module.py:902-963) with two changes and nothing else:

  * line 938's `np.ma.max` becomes `reduce_votes(..., mode=self.vote_mode)`;
  * the D-index of each neighbourhood is recorded on `self.last_dissent`.

With ``vote_mode="max"`` the behaviour is upstream's, which is what makes the
comparison honest: the baseline arm runs through the same code as the
experimental arms.
"""

from __future__ import annotations

import numpy as np
from scipy.spatial import KDTree

from tbp.monty.frameworks.models.evidence_matching.learning_module import (
    EvidenceGraphLM,
)

from polybrains.consensus import (
    CONSENSUS_TAU,
    VoteMode,
    capture_rate,
    dissent_index,
    reduce_votes,
)
from polybrains.weights import AdaptiveVoteWeight


class ConsensusEvidenceGraphLM(EvidenceGraphLM):
    """EvidenceGraphLM with a configurable vote reduction and a dissent signal.

    Args:
        vote_mode: ``"max"`` (upstream), ``"mean"``, or ``"consensus"``.
        consensus_tau: agreement scale, frozen at CP-3.
        record_dissent: keep per-step D-index and capture-rate history.
        adaptive_weight: if True, ``vote_weight`` becomes w(t), updated from
            this module's out-of-domain track record via
            :meth:`record_episode_outcome`. If False the upstream constant is
            used, which is the ablation arm.
    """

    def __init__(
        self,
        *args,
        vote_mode: VoteMode = "max",
        consensus_tau: float = CONSENSUS_TAU,
        record_dissent: bool = True,
        adaptive_weight: bool = False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.vote_mode: VoteMode = vote_mode
        self.consensus_tau = consensus_tau
        self.record_dissent = record_dissent
        self.dissent_history: list[float] = []
        self.capture_history: list[float] = []
        self.last_dissent: float | None = None
        self.adaptive_weight = adaptive_weight
        # w_init mirrors upstream's configured constant so that the frozen
        # ablation is exactly upstream.
        self._w = AdaptiveVoteWeight(
            w_init=float(getattr(self, "vote_weight", 1.0)),
            frozen=not adaptive_weight,
        )

    @property
    def effective_vote_weight(self) -> float:
        """The weight actually applied to incoming votes this step."""
        return self._w.weight if self.adaptive_weight else self.vote_weight

    def record_episode_outcome(
        self, was_correct: bool, out_of_domain: bool = True
    ) -> float:
        """Feed one episode's outcome to w(t).

        In-domain outcomes deliberately do not move the weight; see
        `polybrains.weights` and H2.
        """
        return self._w.update(was_correct=was_correct, out_of_domain=out_of_domain)

    # -- transcribed from upstream 0c81b1f, learning_module.py:902 ------------
    def _update_evidence_with_vote(self, votes: list, graph_id) -> None:
        """Use incoming votes to update all hypotheses.

        Differs from upstream only in the reduction step and the dissent
        recording; everything else is upstream's code.
        """
        graph_location_vote = np.zeros((len(votes), 3))
        vote_evidences = np.zeros(len(votes))
        for n, vote in enumerate(votes):
            graph_location_vote[n] = vote.location
            vote_evidences[n] = vote.confidence

        vote_location_tree = KDTree(graph_location_vote, leafsize=40)
        vote_nn = 3
        if graph_location_vote.shape[0] < vote_nn:
            vote_nn = graph_location_vote.shape[0]
        graph_hyps = self._hypotheses[graph_id]
        (radius_node_dists, radius_node_ids) = vote_location_tree.query(
            graph_hyps.locations, k=vote_nn, p=2, workers=1
        )
        if vote_nn == 1:
            radius_node_dists = np.expand_dims(radius_node_dists, axis=1)
            radius_node_ids = np.expand_dims(radius_node_ids, axis=1)
        radius_evidences = vote_evidences[radius_node_ids]
        node_distance_weights = self._get_node_distance_weights(radius_node_dists)
        too_far_away = node_distance_weights <= 0
        all_radius_evidence = np.ma.array(radius_evidences, mask=too_far_away)

        # ---- the one substantive change -----------------------------------
        distance_weighted_vote_evidence = reduce_votes(
            all_radius_evidence,
            mode=self.vote_mode,
            tau=self.consensus_tau,
        )

        if self.record_dissent:
            d = dissent_index(all_radius_evidence)
            self.last_dissent = float(np.mean(d)) if d.size else 0.0
            self.dissent_history.append(self.last_dissent)
            self.capture_history.append(
                capture_rate(all_radius_evidence, distance_weighted_vote_evidence)
            )
        # -------------------------------------------------------------------

        # `effective_vote_weight` is upstream's constant unless adaptive_weight
        # is on, in which case it is w(t). With adaptive_weight=False this is
        # `self.vote_weight` exactly, preserving upstream behaviour.
        vw = self.effective_vote_weight

        if self.past_weight + self.present_weight == 1:
            graph_hyps.evidence = np.ma.average(
                [graph_hyps.evidence, distance_weighted_vote_evidence],
                weights=[1, vw],
                axis=0,
            )
        else:
            graph_hyps.evidence = np.ma.sum(
                [
                    graph_hyps.evidence,
                    distance_weighted_vote_evidence * vw,
                ],
                axis=0,
            )

    # -- reporting -----------------------------------------------------------
    def dissent_summary(self) -> dict:
        """Aggregate D-index and capture rate over the episode so far."""
        if not self.dissent_history:
            return {"n_steps": 0}
        caps = [c for c in self.capture_history if not np.isnan(c)]
        return {
            "n_steps": len(self.dissent_history),
            "mean_dissent": float(np.mean(self.dissent_history)),
            "max_dissent": float(np.max(self.dissent_history)),
            "mean_capture_rate": float(np.mean(caps)) if caps else float("nan"),
            "vote_mode": self.vote_mode,
        }

    def reset_dissent(self) -> None:
        self.dissent_history.clear()
        self.capture_history.clear()
        self.last_dissent = None
