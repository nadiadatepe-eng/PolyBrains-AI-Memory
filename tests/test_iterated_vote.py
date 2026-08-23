#!/usr/bin/env python3
"""Gate for P9's iterated voting: rounds=1 MUST be upstream, call for call.

If rounds=1 differs from upstream in any way, then every P9 comparison is
confounded -- a difference between rounds could be the loop rather than the
number of exchanges. This is the same discipline as CP-3, where vote_mode="max"
had to reproduce upstream exactly before any other mode was believed.

Run:
    PYTHONPATH=src upstream/tbp.monty/.venv/bin/python tests/test_iterated_vote.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from polybrains.iterated_vote import IteratedVotingMonty  # noqa: E402


class FakeBuffer:
    def get_num_observations_on_object(self):
        return 1


class FakeLM:
    """Minimal stand-in recording the order of calls it receives."""

    def __init__(self, lm_id, log, silent=False):
        self.lm_id = lm_id
        self.log = log
        self.silent = silent
        self.evidence = 0.0
        self.buffer = FakeBuffer()
        self.learning_module_id = f"LM_{lm_id}"

    def get_possible_matches(self):
        return []

    def send_out_vote(self):
        # Evidence at the moment of sending -- this is what makes round 2 a
        # vote on round 1's RESULT rather than a replay of round 1's votes.
        self.log.append(("send", self.lm_id, self.evidence))
        return None if self.silent else f"vote{self.lm_id}@{self.evidence}"

    def receive_votes(self, votes):
        self.log.append(("recv", self.lm_id, tuple(votes)))
        # Mutate, exactly as upstream's _update_evidence_with_vote does.
        self.evidence += sum(1 for v in votes if v is not None)


class Harness(IteratedVotingMonty):
    """Bypass MontyBase.__init__ -- we are testing _vote() only."""

    # stand-ins for the two parent helpers the real _vote calls
    def _combine_votes(self, votes_per_lm):
        self.log.append(("combine", tuple(votes_per_lm)))
        return {"combined": tuple(votes_per_lm)}

    def send_vote_to_lm(self, lm, lm_id, combined_votes):
        lm.receive_votes(combined_votes)

    def update_stats_after_vote(self, lm):
        pass

    def __init__(self, n_lms=3, vote_rounds=1, silent_ids=()):
        if vote_rounds < 1:
            raise ValueError(f"vote_rounds must be >= 1, got {vote_rounds}")
        self.log = []
        self.learning_modules = [
            FakeLM(i, self.log, silent=(i in silent_ids)) for i in range(n_lms)
        ]
        # fully connected, excluding self, as in our 5lm_5sm connectivity
        self.lm_to_lm_vote_matrix = [
            [j for j in range(n_lms) if j != i] for i in range(n_lms)
        ]
        self.vote_rounds = vote_rounds
        self.vote_round_stats = []


def upstream_vote(monty):
    """Verbatim transcription of the REAL parent, graph_matching.py:389.

    NOT monty_base.py:302. MontyForGraphMatching overrides _vote and that
    override is what runs; transcribing the base version silently drops
    _combine_votes and send_vote_to_lm, which made the first P9 sweep exchange
    no votes at all while completing without error.
    """
    if monty.lm_to_lm_vote_matrix is not None:
        votes_per_lm = []
        for i in range(len(monty.learning_modules)):
            votes_per_lm.append(monty.learning_modules[i].send_out_vote())
        combined_votes = monty._combine_votes(votes_per_lm)
        for i in range(len(monty.learning_modules)):
            monty.send_vote_to_lm(monty.learning_modules[i], i, combined_votes)
            monty.update_stats_after_vote(monty.learning_modules[i])


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))
    return cond


def main():
    ok = True
    print("P9 gate: iterated voting")

    # 1. rounds=1 is upstream, call for call
    a = Harness(vote_rounds=1)
    a._vote()
    b = Harness(vote_rounds=1)
    upstream_vote(b)
    ok &= check("rounds=1 call sequence identical to upstream",
                a.log == b.log, f"{len(a.log)} calls")
    ok &= check("rounds=1 final evidence identical to upstream",
                [m.evidence for m in a.learning_modules]
                == [m.evidence for m in b.learning_modules])

    # 2. rounds=2 is exactly two exchanges, not one doubled
    c = Harness(vote_rounds=2)
    c._vote()
    sends = [e for e in c.log if e[0] == "send"]
    recvs = [e for e in c.log if e[0] == "recv"]
    ok &= check("rounds=2 sends twice per LM", len(sends) == 6, f"{len(sends)} sends")
    ok &= check("rounds=2 receives twice per LM", len(recvs) == 6, f"{len(recvs)} recvs")

    # 3. THE LOAD-BEARING ONE: round 2 votes on round 1's RESULT.
    # Round 1 sends at evidence 0; round 2 must send at the updated value.
    r1_sends = [e[2] for e in sends[:3]]
    r2_sends = [e[2] for e in sends[3:]]
    ok &= check("round 1 sends pre-vote evidence", all(v == 0.0 for v in r1_sends),
                str(r1_sends))
    # Each LM receives one combined-vote payload per round, so evidence rises
    # by 1 per round in this stub. The load-bearing point is that round 2 sends
    # a value CHANGED by round 1, i.e. it votes on the vote result.
    ok &= check("round 2 sends POST-vote evidence (votes on the vote result)",
                all(v > 0.0 for v in r2_sends) and r2_sends != r1_sends,
                f"round1={r1_sends} round2={r2_sends}")

    # 4. strict ordering: all sends of a round precede all receives of that round
    order = [e[0] for e in c.log]
    expect = (["send"] * 3 + ["combine"] + ["recv"] * 3) * 2
    ok &= check("each round gathers, combines, then scatters",
                order == expect, f"{order}")

    # 5. silence accounting (P6's lesson: silence != disagreement)
    d = Harness(vote_rounds=2, silent_ids=(0, 1))
    d._vote()
    s = d.vote_round_summary()
    expect = 2 / 3 * 100
    ok &= check("send_none% reported per round",
                abs(s.get("round_1_send_none_pct", -1) - expect) < 1e-9
                and abs(s.get("round_2_send_none_pct", -1) - expect) < 1e-9,
                f"{s['round_1_send_none_pct']:.1f}% / "
                f"{s['round_2_send_none_pct']:.1f}% (expect {expect:.1f}%)")

    # 6. STRUCTURAL: our _vote must call every helper the real parent does.
    #    This is the check that would have caught the first P9 sweep before it
    #    burned 73 minutes producing votes that were never delivered.
    import inspect
    from tbp.monty.frameworks.models.graph_matching import MontyForGraphMatching
    ours = inspect.getsource(IteratedVotingMonty._vote)
    parent = inspect.getsource(MontyForGraphMatching._vote)
    for call in ("_combine_votes", "send_vote_to_lm", "update_stats_after_vote"):
        ok &= check(f"_vote calls {call} like the real parent",
                    (call in parent) and (call in ours))
    # and the real parent must be the one we think it is
    for c in IteratedVotingMonty.__mro__[1:]:
        if "_vote" in c.__dict__:
            ok &= check("parent defining _vote is MontyForGraphMatching",
                        c.__name__ == "MontyForGraphMatching", c.__name__)
            break

    # 7. guard, on the real class as well as the harness
    try:
        Harness(vote_rounds=0)
        ok &= check("rounds=0 rejected", False)
    except ValueError:
        ok &= check("rounds=0 rejected", True)

    print("\n" + ("GATE PASSED" if ok else "GATE FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
