#!/usr/bin/env python3
"""Generate the P9 arm configs from P7's max arm.

One variable changes across arms: the number of vote exchanges per step.
Everything else -- rotations, noise on modules 3+4, seed handling, criterion --
is inherited from p7_e1_ood_max.yaml so the comparison is clean and rounds=1 is
a true replication of P7.
"""
from pathlib import Path

CFG = Path(__file__).resolve().parents[1] / "configs" / "experiment"
base = (CFG / "p7_e1_ood_max.yaml").read_text()

HEADER = """# @package _global_
# P9 -- iterated voting: vote, then vote on the result of that vote.
#
# This arm runs {r} vote exchange(s) per step. Because receive_votes() mutates
# the receiving module's evidence, round r>1 re-reads the ALREADY-VOTED state,
# so it votes on the previous round's result rather than re-tallying the same
# votes.
#
# rounds=1 must reproduce P7's max arm exactly; that is gated by
# tests/test_iterated_vote.py, so any difference between arms is the number of
# exchanges and not the loop itself. Pre-registered at 0d9b386.
"""

for r in (1, 2, 3):
    s = base[base.index("defaults:"):]
    s = HEADER.format(r=r) + s
    s = s.replace("  vote_mode: max\n", f"  vote_mode: max\n  vote_rounds: {r}\n")
    s = s.replace("run_name: p7_e1_ood_max", f"run_name: p9_r{r}")
    # monty_class lives under experiment.config.monty_config (see the upstream
    # monty conf group header). Merge into the EXISTING experiment.config block
    # rather than adding a second `config:` key, which YAML would reject.
    anchor = "  config:\n    show_sensor_output: false\n"
    assert anchor in s, "p7 config shape changed; regenerate by hand"
    s = s.replace(
        anchor,
        "  config:\n"
        "    monty_config:\n"
        "      monty_class: "
        "${monty.class:polybrains.iterated_vote.IteratedVotingMonty}\n"
        "      monty_args:\n"
        f"        vote_rounds: {r}\n"
        "    show_sensor_output: false\n",
    )
    out = CFG / f"p9_rounds{r}.yaml"
    out.write_text(s)
    print("wrote", out.name)
