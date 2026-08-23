#!/usr/bin/env python3
"""Generate P11 arm configs: the P10 parliament under vote_mode=consensus.

P10 found the parliamentary STRUCTURE cuts confident errors while the devil's
advocate itself contributed nothing (parl-noopp matched parl-3 on every
measure). The registered cause is mechanical: `np.ma.max` takes the loudest
vote, and an opposing module argues its runner-up, which carries LOWER evidence
by construction. Max has no channel through which dissent can be expressed.

`consensus` (agreement-weighted mean, frozen at CP-3) does have one: a lone loud
vote is discounted and a mutually-agreeing group is amplified, so a dissenting
argument can move the result rather than simply losing.

Five arms, all consensus, all sharing seeds:

  p11_parl3       propose(0,1,2) -> oppose(3) -> oppose(4), sequential
  p11_parlnoopp   same phase structure, NO opposition  [decides P11a]
  p11_parlbatch   opposition, batch within phase       [sequencing control]
  p11_plain3      3 plain iterated rounds              [equal-exchange control]
  p11_plain1      1 plain exchange                     [REPLICATION control:
                  must reproduce P7's consensus arm within noise]

plain1/plain3 must be re-run under consensus rather than reused from P9, whose
arms are all max. Comparing a consensus parliament against a max baseline would
confound the rule with the structure.
"""
from pathlib import Path

CFG = Path(__file__).resolve().parents[1] / "configs" / "experiment"
base = (CFG / "p7_e1_ood_max.yaml").read_text()

HEADER = """# @package _global_
# P11 -- {desc}, under vote_mode=consensus.
#
# The fair test of Nadi's parliament: consensus is agreement-weighted, so unlike
# max it can express dissent. Pre-registered in PREDICTIONS.md before running.
"""

PARL_ARMS = {
    "p11_parl3":     dict(opp="[1, 2]", seq="true",  desc="parliament, sequential"),
    "p11_parlnoopp": dict(opp="[]",     seq="true",  desc="phase structure, no opposition"),
    "p11_parlbatch": dict(opp="[1, 2]", seq="false", desc="parliament, batch within phase"),
}
PLAIN_ARMS = {"p11_plain1": 1, "p11_plain3": 3}

ANCHOR = "  config:\n    show_sensor_output: false\n"


def start(name, desc):
    s = base[base.index("defaults:"):]
    s = HEADER.format(desc=desc) + s
    s = s.replace("run_name: p7_e1_ood_max", f"run_name: {name}")
    s = s.replace("  vote_mode: max\n", "  vote_mode: consensus\n")
    assert "vote_mode: consensus" in s and ANCHOR in s, "p7 config shape changed"
    return s


for name, a in PARL_ARMS.items():
    s = start(name, a["desc"]).replace(ANCHOR,
        "  config:\n"
        "    monty_config:\n"
        "      monty_class: ${monty.class:polybrains.parliament.ParliamentaryMonty}\n"
        "      monty_args:\n"
        "        phases: [[0, 1, 2], [3], [4]]\n"
        f"        opposing_phases: {a['opp']}\n"
        f"        sequential: {a['seq']}\n"
        "    show_sensor_output: false\n")
    (CFG / f"{name}.yaml").write_text(s)
    print("wrote", name)

for name, r in PLAIN_ARMS.items():
    s = start(name, f"{r} plain vote round(s)")
    s = s.replace("  vote_mode: consensus\n", f"  vote_mode: consensus\n  vote_rounds: {r}\n")
    s = s.replace(ANCHOR,
        "  config:\n"
        "    monty_config:\n"
        "      monty_class: ${monty.class:polybrains.iterated_vote.IteratedVotingMonty}\n"
        "      monty_args:\n"
        f"        vote_rounds: {r}\n"
        "    show_sensor_output: false\n")
    (CFG / f"{name}.yaml").write_text(s)
    print("wrote", name)
