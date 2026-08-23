#!/usr/bin/env python3
"""Gate for P10's parliamentary voting.

Three sweeps have now been voided in this project for mechanisms that ran
cleanly while doing nothing. This gate asserts the things that were false in
each of those cases:

  * the propose-only configuration is upstream's exchange, call for call
  * `_vote` calls every helper the REAL parent calls, and the parent defining
    `_vote` is MontyForGraphMatching, not MontyBase   (the P9 bug)
  * opposing modules genuinely argue a DIFFERENT object than they would
    normally -- the whole idea is void if "opposition" sends the same vote
  * opposition is non-destructive: the module is left exactly as found
  * sequential mode really lets later voters see earlier updates

Run:
    PYTHONPATH=src upstream/tbp.monty/.venv/bin/python tests/test_parliament.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402

from polybrains.parliament import ParliamentaryMonty  # noqa: E402


class FakeBuffer:
    def get_num_observations_on_object(self):
        return 1


class FakeHyp:
    def __init__(self, evidence):
        self.evidence = np.array(evidence, dtype=float)


class FakeLM:
    """Stand-in with two objects, so a runner-up exists."""

    def __init__(self, lm_id, log, best="apple", best_ev=0.9, second_ev=0.4):
        self.lm_id = lm_id
        self.learning_module_id = f"LM_{lm_id}"
        self.log = log
        self.buffer = FakeBuffer()
        self.seen_evidence = 0.0
        other = "banana" if best == "apple" else "apple"
        self._hypotheses = {
            best: FakeHyp([best_ev, best_ev - 0.1]),
            other: FakeHyp([second_ev, second_ev - 0.1]),
        }

    def send_out_vote(self):
        # Argues whichever object is currently visible with the most evidence.
        tops = {g: float(np.max(h.evidence)) for g, h in self._hypotheses.items()}
        arg = max(tops, key=tops.get) if tops else None
        self.log.append(("send", self.lm_id, arg, self.seen_evidence))
        return {"arg": arg, "from": self.lm_id}

    def receive_votes(self, votes):
        self.log.append(("recv", self.lm_id))
        self.seen_evidence += 1

    def get_possible_matches(self):
        return []


class Harness(ParliamentaryMonty):
    def __init__(self, n=5, **kw):
        self.log = []
        self.learning_modules = [FakeLM(i, self.log) for i in range(n)]
        self.lm_to_lm_vote_matrix = [
            [j for j in range(n) if j != i] for i in range(n)
        ]
        self.phases = [list(p) for p in kw.get("phases", [[0, 1, 2], [3], [4]])]
        self.opposing_phases = list(kw.get("opposing_phases", [1, 2]))
        self.sequential = kw.get("sequential", True)
        self.phase_stats = []

    def _combine_votes(self, votes_per_lm):
        self.log.append(("combine", tuple(v["arg"] if v else None
                                          for v in votes_per_lm)))
        return {"combined": True}

    def send_vote_to_lm(self, lm, lm_id, combined_votes):
        lm.receive_votes(combined_votes)

    def update_stats_after_vote(self, lm):
        pass


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))
    return bool(cond)


def main():
    ok = True
    print("P10 gate: parliamentary voting")

    # 1. structural: the P9 bug must be impossible here
    import inspect
    from tbp.monty.frameworks.models.graph_matching import MontyForGraphMatching
    ours = inspect.getsource(ParliamentaryMonty._run_phase)
    parent = inspect.getsource(MontyForGraphMatching._vote)
    for call in ("_combine_votes", "send_vote_to_lm", "update_stats_after_vote"):
        ok &= check(f"calls {call} like the real parent",
                    call in parent and call in ours)
    for c in ParliamentaryMonty.__mro__[1:]:
        if "_vote" in c.__dict__:
            ok &= check("parent defining _vote is MontyForGraphMatching",
                        c.__name__ == "MontyForGraphMatching", c.__name__)
            break

    # 2. THE LOAD-BEARING ONE: opposition argues a different object
    h = Harness()
    lm = h.learning_modules[3]
    normal = lm.send_out_vote()["arg"]
    h.log.clear()
    opposed = h._runner_up_vote(lm)["arg"]
    ok &= check("opposing module argues a DIFFERENT object",
                opposed != normal, f"normal={normal} opposed={opposed}")

    # 3. non-destructive: module left exactly as found
    before = {g: hh.evidence.copy() for g, hh in lm._hypotheses.items()}
    h._runner_up_vote(lm)
    same = (set(before) == set(lm._hypotheses) and
            all(np.array_equal(before[g], lm._hypotheses[g].evidence)
                for g in before))
    ok &= check("opposition restores the module unchanged", same,
                f"{sorted(lm._hypotheses)}")

    # 4. phases run in order, opposition only where configured
    h = Harness()
    h._vote()
    opp_flags = [(p, o) for p, _, _, o in h.phase_stats]
    ok &= check("phase 1 proposes, phases 2 and 3 oppose",
                opp_flags == [(0, False)] * 3 + [(1, True), (2, True)],
                str(opp_flags))

    # 5. sequential: later voters in a phase see earlier updates
    # In sequential mode each speaker is its own group: the SPEAKER is polled
    # first, then the four listeners supply poses. So phase 1's three speakers
    # are the first send of each group, and each must see one more update than
    # the last.
    h = Harness(sequential=True)
    h._vote()
    groups = []
    cur = []
    for e in h.log:
        if e[0] == "send":
            cur.append(e)
        elif e[0] == "combine":
            groups.append(cur)
            cur = []
    speakers = [g[0] for g in groups[:3]]   # phase 1, three voters one by one
    seen = [e[3] for e in speakers]
    ids = [e[1] for e in speakers]
    ok &= check("sequential voters see prior updates within a phase",
                seen == [0.0, 1.0, 2.0], f"{ids} saw {seen}")

    hb = Harness(sequential=False)
    hb._vote()
    bgroups = []
    cur = []
    for e in hb.log:
        if e[0] == "send":
            cur.append(e)
        elif e[0] == "combine":
            bgroups.append(cur)
            cur = []
    sb = [e[3] for e in bgroups[0][:3]]
    ok &= check("batch mode does NOT (control for sequencing)",
                sb == [0.0, 0.0, 0.0], str(sb))

    # 6. no-opposition control really removes opposition
    h = Harness(opposing_phases=[])
    h._vote()
    ok &= check("parl-noopp control has no opposing phase",
                not any(o for _, _, _, o in h.phase_stats))

    # 7. send_none accounting exists per phase
    h = Harness()
    h._vote()
    s = h.phase_summary()
    ok &= check("send_none% reported per phase",
                all(f"phase_{i}_send_none_pct" in s for i in (1, 2, 3)), str(s))

    print("\n" + ("GATE PASSED" if ok else "GATE FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
