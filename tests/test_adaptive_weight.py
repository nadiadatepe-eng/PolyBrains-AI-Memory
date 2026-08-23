#!/usr/bin/env python3
"""Gate for P12's adaptive-weight mechanism.

H2 was never run: `adaptive_weight` is false in 24 of 24 configs, and
`record_episode_outcome` is called nowhere outside tests. So the FIRST thing
this gate asserts is the thing that was false for a month -- that outcomes
actually reach w(t) during an episode loop.

Asserts:
  * frozen arm reproduces upstream: w(t) never moves, whatever the outcomes
  * ood arm learns from OOD episodes and IGNORES in-domain ones
  * indomain arm does the exact opposite -- this is H2's failure mode and the
    whole experiment is void if the two arms behave alike
  * a persistently-wrong module loses weight but is NEVER silenced (w_min > 0)
    and can climb back, which is the polymath invariant from CP-4
  * post_episode calls super() so upstream logging/counters still run
  * the weight trace is populated, because a dead arm and a null look identical

Run:
    PYTHONPATH=src upstream/tbp.monty/.venv/bin/python tests/test_adaptive_weight.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from polybrains.weights import W_MAX, W_MIN, AdaptiveVoteWeight  # noqa: E402

FAIL = []


def check(cond, msg):
    print(f"  [{'PASS' if cond else 'FAIL'}] {msg}")
    if not cond:
        FAIL.append(msg)


class FakeLM:
    """Minimal stand-in exposing the two attributes the experiment touches."""

    def __init__(self, lm_id, correct):
        self.learning_module_id = f"LM_{lm_id}"
        self._correct = correct
        self._w = AdaptiveVoteWeight(w_init=1.0)

    @property
    def effective_vote_weight(self):
        return self._w.weight

    def record_episode_outcome(self, was_correct, out_of_domain=True):
        return self._w.update(was_correct=was_correct, out_of_domain=out_of_domain)

    def get_current_mlh(self):
        return {"graph_id": "mug" if self._correct else "bowl"}


def test_frozen_is_upstream():
    print("\nfrozen arm reproduces upstream")
    w = AdaptiveVoteWeight(w_init=1.0, frozen=True)
    for _ in range(50):
        w.update(was_correct=False)
    check(w.weight == 1.0, "50 wrong episodes leave a frozen weight at w_init")
    check(len(w.history) == 51, "history still records, so silence is visible")


def test_ood_and_indomain_are_opposites():
    print("\nood and indomain arms are genuine opposites")
    # Same outcomes, different gate. If these two agree, the experiment is void.
    ood = AdaptiveVoteWeight(w_init=1.0)
    ind = AdaptiveVoteWeight(w_init=1.0)
    for _ in range(30):
        ood.update(was_correct=False, out_of_domain=True)   # learns
        ind.update(was_correct=False, out_of_domain=False)  # ignores
    check(ood.weight < 1.0, f"ood arm moved on OOD outcomes (w={ood.weight:.3f})")
    check(ind.weight == 1.0, "indomain arm ignored those same OOD outcomes")
    check(ood.weight != ind.weight, "the two arms are distinguishable")


def test_never_silenced_and_can_recover():
    print("\npolymath invariants (frozen at CP-4)")
    w = AdaptiveVoteWeight(w_init=1.0)
    for _ in range(500):
        w.update(was_correct=False)
    check(w.weight >= W_MIN > 0, f"never silenced: w={w.weight:.3f} >= {W_MIN}")
    floor = w.weight
    for _ in range(500):
        w.update(was_correct=True)
    check(w.weight > floor, f"recovers from the floor: {floor:.3f} -> {w.weight:.3f}")
    check(w.weight <= W_MAX, f"never exceeds the ceiling {W_MAX}")


def test_indomain_set_matches_pretraining():
    """The in-domain set must equal what the model was pretrained on.

    A draft of adaptive_experiment.py guessed (0,180,0), which is not in the
    set. That single wrong tuple would mislabel one rotation's episodes and
    corrupt the in-domain/OOD split the entire hypothesis rests on -- while
    every run completed cleanly.
    """
    print("\nin-domain rotations match the pretraining config")
    import re

    from polybrains.adaptive_experiment import AdaptiveWeightExperiment as E

    txt = (Path(__file__).resolve().parents[1]
           / "configs/experiment/pb_pretrain_indomain.yaml").read_text()
    block = txt.split("rotations:")[1]
    rots = set()
    for line in block.splitlines():
        m = re.match(r"\s*-\s*\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]", line)
        if m:
            rots.add(tuple(int(g) for g in m.groups()))
        elif rots:
            break
    check(len(rots) == 5, f"parsed 5 pretraining rotations ({len(rots)})")
    check(set(E.DEFAULT_INDOMAIN) == rots,
          f"code default == pretraining set  code={sorted(E.DEFAULT_INDOMAIN)}"
          f" yaml={sorted(rots)}")


def test_frozen_arm_still_writes_a_trace():
    """The frozen arm must write a trace, not an empty file.

    An empty trace makes "w(t) never moved" indistinguishable from "the arm
    never ran" -- the exact ambiguity that has voided sweeps here. The first
    P12 launch produced a header-only frozen trace for this reason.
    """
    print("\nfrozen arm still writes a trace (so absence != stillness)")
    from polybrains.adaptive_experiment import AdaptiveWeightExperiment as E
    import polybrains.adaptive_experiment as mod

    class FrozenProbe(E):
        def __init__(self):
            self.weight_source = "frozen"
            self.indomain_rotations = {(0, 0, 0)}
            self.weight_trace = []
            self._episode_ix = 0
            self.env_interface = type(
                "EI", (), {"primary_target":
                           {"object": "mug", "euler_rotation": [35, 45, 0]}}
            )()
            lms = [FakeLM(0, True), FakeLM(1, False)]
            for lm in lms:                    # frozen weights, as the config sets
                lm._w.frozen = True
            self.model = type("M", (), {"learning_modules": lms})()

    f = FrozenProbe()
    orig = mod.MontyObjectRecognitionExperiment.post_episode
    mod.MontyObjectRecognitionExperiment.post_episode = lambda self, steps: None
    try:
        f.post_episode(10)
    finally:
        mod.MontyObjectRecognitionExperiment.post_episode = orig

    check(len(f.weight_trace) == 2,
          f"frozen arm wrote {len(f.weight_trace)} trace rows (want 2, not 0)")
    check(all(t[2] == 1.0 for t in f.weight_trace),
          "and its weights did NOT move, which is what frozen means")


def test_experiment_wiring():
    print("\nthe experiment actually feeds outcomes to w(t)  [THE dead-arm check]")
    from polybrains.adaptive_experiment import AdaptiveWeightExperiment as E

    # Drive the REAL post_episode. It uses zero-arg super(), which needs a
    # genuine instance of the class, so subclass it and neutralise only
    # __init__ and the upstream parent call. Do NOT reimplement the method --
    # transcribing it would test the copy rather than the code, which is
    # exactly the P9 bug.
    class Probe(E):
        def __init__(self):  # noqa: D107 - bypass the heavy upstream __init__
            self.weight_source = "ood"
            self.indomain_rotations = {(0, 0, 0)}
            self.weight_trace = []
            self._episode_ix = 0
            self.called_super = False
            self.env_interface = type(
                "EI", (), {"primary_target":
                           {"object": "mug", "euler_rotation": [35, 45, 0]}}
            )()
            self.model = type(
                "M", (), {"learning_modules": [FakeLM(0, True), FakeLM(1, False)]}
            )()

    s = Probe()
    check(s._episode_is_indomain() is False, "oblique rotation read as OOD")
    s.env_interface.primary_target["euler_rotation"] = [0, 0, 0]
    check(s._episode_is_indomain() is True, "trained rotation read as in-domain")

    # super().post_episode must be called: skipping it breaks upstream logging.
    import polybrains.adaptive_experiment as mod

    orig = mod.MontyObjectRecognitionExperiment.post_episode
    mod.MontyObjectRecognitionExperiment.post_episode = (
        lambda self, steps: setattr(self, "called_super", True)
    )
    try:
        s.env_interface.primary_target["euler_rotation"] = [35, 45, 0]
        s.post_episode(10)
    finally:
        mod.MontyObjectRecognitionExperiment.post_episode = orig

    check(s.called_super, "super().post_episode() ran, so logging is intact")

    # ORDERING. super().post_episode() ends by calling env_interface.post_episode(),
    # which ADVANCES primary_target to the next episode (upstream flags this at
    # monty_experiment.py:584). Reading the target after super() scores every
    # module against the WRONG episode. A live smoke run did exactly that: all 5
    # modules marked incorrect while their MLH matched the target, dragging w(t)
    # to 0.209 on pure artefact. Simulate the advance and assert we read before it.
    class Ordering(Probe):
        def __init__(self):
            super().__init__()
            self.read_before_advance = None

    o = Ordering()
    o.model.learning_modules = [FakeLM(0, True), FakeLM(1, True)]  # both CORRECT

    def advancing_super(self, steps):
        # what upstream really does at the end of post_episode
        self.env_interface.primary_target = {
            "object": "SOMETHING_ELSE", "euler_rotation": [0, 0, 0]
        }

    orig2 = mod.MontyObjectRecognitionExperiment.post_episode
    mod.MontyObjectRecognitionExperiment.post_episode = advancing_super
    try:
        o.post_episode(10)
    finally:
        mod.MontyObjectRecognitionExperiment.post_episode = orig2

    correct_flags = [t[4] for t in o.weight_trace]
    check(all(correct_flags),
          f"targets read BEFORE super() advances them: correct={correct_flags} "
          "(all-False here means the ordering bug is back)")
    check(all(t[2] > 1.0 for t in o.weight_trace),
          "correct modules gained weight, so the outcome reached w(t) intact")
    check(len(s.weight_trace) == 2, f"trace populated for both LMs ({len(s.weight_trace)})")
    ws = [t[2] for t in s.weight_trace]
    check(any(w != 1.0 for w in ws), f"w(t) MOVED during the episode loop: {ws}")
    check(ws[0] > ws[1], "the correct module ends louder than the wrong one")


def main():
    print("=" * 70)
    print("P12 GATE -- adaptive vote weight (H2), the arm that was never run")
    print("=" * 70)
    test_frozen_is_upstream()
    test_ood_and_indomain_are_opposites()
    test_never_silenced_and_can_recover()
    test_indomain_set_matches_pretraining()
    test_frozen_arm_still_writes_a_trace()
    test_experiment_wiring()
    print()
    if FAIL:
        print(f"GATE FAILED: {len(FAIL)} check(s)")
        for f in FAIL:
            print(f"  - {f}")
        return 1
    print("GATE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
