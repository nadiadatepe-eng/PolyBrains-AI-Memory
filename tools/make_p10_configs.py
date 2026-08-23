#!/usr/bin/env python3
"""Generate P10 arm configs from P7's max arm.

Four arms, one variable at a time:
  parl3       propose(0,1,2) -> oppose(3) -> oppose(4), sequential
  parlnoopp   same phase structure, NO opposition (isolates structure)
  parlbatch   same as parl3 but batch within phase (isolates sequencing)
  (plain3 is P9's rounds=3 arm, already run -- the equal-exchange control)
"""
from pathlib import Path

CFG = Path(__file__).resolve().parents[1] / "configs" / "experiment"
base = (CFG / "p7_e1_ood_max.yaml").read_text()

ARMS = {
    "p10_parl3":     dict(opp="[1, 2]", seq="true",  desc="propose then two oppositions"),
    "p10_parlnoopp": dict(opp="[]",     seq="true",  desc="same phases, no opposition"),
    "p10_parlbatch": dict(opp="[1, 2]", seq="false", desc="opposition, batch within phase"),
}

HEADER = """# @package _global_
# P10 -- parliamentary voting: {desc}
#
# phase 1 PROPOSE  LMs 0,1,2      phase 2 OPPOSE LM 3      phase 3 OPPOSE LM 4
# An opposing module argues its RUNNER-UP object, not its best.
# Pre-registered at 5b8d64f. Gated by tests/test_parliament.py.
"""

for name, a in ARMS.items():
    s = base[base.index("defaults:"):]
    s = HEADER.format(desc=a["desc"]) + s
    s = s.replace("run_name: p7_e1_ood_max", f"run_name: {name}")
    anchor = "  config:\n    show_sensor_output: false\n"
    assert anchor in s, "p7 config shape changed"
    s = s.replace(anchor,
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
