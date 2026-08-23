#!/usr/bin/env python3
"""Why did rounds 2 and 3 change nothing? Instrument the live vote path.

P9 produced byte-identical eval_stats across rounds=1/2/3 except the `time`
column. Two very different explanations, and they demand opposite responses:

  (A) DEAD ROUNDS -- rounds 2+ never happen. `send_out_vote` returns None
      unless `buffer.get_last_obs_processed()` is True, a flag set once per
      SENSORY step (graph_matching.py:914). If it is False during extra rounds,
      every module abstains and the loop burns time doing nothing. Then P9 has
      NOT tested iterated voting at all, and any parliamentary scheme built on
      the same insertion point would fail the same way.

  (B) FIXED POINT -- rounds 2+ run, votes are exchanged, but evidence has
      already converged so the updates are no-ops. Then iteration genuinely
      adds nothing here and the null is real.

This distinguishes them by counting, per round: modules that voted, modules
that abstained, and -- the load-bearing measure -- how much evidence actually
CHANGED as a result of receiving votes.

This is P6's lesson applied before drawing a conclusion, not after: silence and
disagreement look identical in output statistics and are opposite at the
mechanism.

Run:
    cd upstream/tbp.monty && PYTHONPATH=~/PolyBrains/src .venv/bin/python \
        ~/PolyBrains/tests/probe_p9_dead_rounds.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "PolyBrains" / "src"))

import numpy as np  # noqa: E402

TRACE = {"rounds": [], "evidence_deltas": []}


def patch(monty_cls):
    """Measure evidence movement by wrapping send_vote_to_lm on the REAL path.

    An earlier version of this probe REIMPLEMENTED _vote and called
    lm.receive_votes() directly -- reproducing the very bug it was meant to
    detect (skipping _combine_votes), and so reporting 0.0000 delta for every
    round including round 1. Wrap, never reimplement.
    """
    orig_send = monty_cls.send_vote_to_lm
    orig_vote = monty_cls._vote

    def snap(lm):
        h = getattr(lm, "_hypotheses", None)
        if not isinstance(h, dict):
            return None
        out = {}
        for gid, hyp in h.items():
            ev = getattr(hyp, "evidence", None)
            if ev is not None:
                out[gid] = np.array(ev, copy=True)
        return out

    def traced_send(self, lm, lm_id, combined_votes):
        before = snap(lm)
        orig_send(self, lm, lm_id, combined_votes)
        after = snap(lm)
        d = 0.0
        if before and after:
            for gid, ev in after.items():
                b = before.get(gid)
                if b is not None and b.shape == np.shape(ev):
                    d += float(np.abs(np.asarray(ev) - b).sum())
        TRACE["evidence_deltas"].append((self._probe_round, d))

    def traced_vote(self):
        # Run one phase at a time so each phase is attributable.
        all_phases = self.phases
        for ix, ids in enumerate(all_phases):
            self._probe_round = ix
            self.phases = [ids]
            saved_opp = self.opposing_phases
            self.opposing_phases = [0] if ix in saved_opp else []
            try:
                orig_vote(self)
            finally:
                self.phases = all_phases
                self.opposing_phases = saved_opp
            TRACE["rounds"].append((ix, len(ids), 0))

    monty_cls.send_vote_to_lm = traced_send
    monty_cls._vote = traced_vote
    monty_cls._probe_round = 0


ARM = os.environ.get("PB_PROBE_ARM", "p10_parl3")


def main():
    from tbp.monty.hydra import register_resolvers
    from hydra import compose, initialize_config_dir
    from polybrains.parliament import ParliamentaryMonty

    register_resolvers()
    patch(ParliamentaryMonty)

    with initialize_config_dir(
        config_dir=str(Path.home() / "PolyBrains" / "configs"), version_base=None
    ):
        cfg = compose(
            config_name="experiment",
            overrides=[
                f"experiment={ARM}",
                "++experiment.config.seed=42",
                "++experiment.config.n_eval_epochs=1",
                "++experiment.config.logging.wandb_id=p10probe",
                f"++experiment.config.logging.run_name={ARM}_liveprobe",
            ],
        )

    from tbp.monty.hydra import instantiate_experiment

    exp = instantiate_experiment(cfg.experiment)
    with exp:
        # evaluate() sets experiment_mode and wires env_interface; calling
        # run_epoch() directly leaves env_interface None.
        exp.evaluate()

    rounds = TRACE["rounds"]
    deltas = TRACE["evidence_deltas"]
    print("\n" + "=" * 78)
    print("P9 DEAD-ROUND PROBE -- did rounds 2 and 3 actually do anything?")
    print("=" * 78)
    if not rounds:
        print("  no vote calls recorded at all")
        return 1

    n_r = max(r[0] for r in rounds) + 1
    print(f"\n{'round':>7}{'steps':>9}{'voted':>10}{'silent':>9}"
          f"{'send_none%':>12}{'deliveries':>12}{'total |delta|':>16}")
    print("-" * 78)
    per_round = {}
    for r in range(n_r):
        rows = [x for x in rounds if x[0] == r]
        voted = sum(x[1] for x in rows)
        silent = sum(x[2] for x in rows)
        ds = [d for rr, d in deltas if rr == r]
        tot = voted + silent
        per_round[r] = sum(ds)
        print(f"{r+1:>7}{len(rows):>9}{voted:>10}{silent:>9}"
              f"{100*silent/max(tot,1):>11.1f}%{len(ds):>12}{sum(ds):>16.4f}")

    d1 = per_round.get(0, 0.0)
    dr = sum(v for k, v in per_round.items() if k > 0)
    print(f"\n{'='*78}\nDIAGNOSIS\n{'='*78}")
    print(f"  round 1 evidence change : {d1:.4f}")
    print(f"  rounds 2+ change        : {dr:.4f}")
    if d1 == 0:
        print("\n  BROKEN: even round 1 moves no evidence. Votes are not being")
        print("  delivered at all -- the vote path itself is dead, not the loop.")
    elif dr == 0:
        print("\n  (A) DEAD ROUNDS: round 1 works, rounds 2+ move nothing.")
        print("      Iterated voting is a no-op at this insertion point.")
    elif dr < d1 * 0.01:
        print(f"\n  (B) FIXED POINT: rounds 2+ move {100*dr/d1:.2f}% of round 1.")
        print("      Iteration saturates almost immediately.")
    else:
        print(f"\n  (C) LIVE: rounds 2+ move {100*dr/d1:.1f}% of round 1's evidence.")
        print("      Iterated voting is doing real work; any null in the accuracy")
        print("      numbers is a real result, not a dead mechanism.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
