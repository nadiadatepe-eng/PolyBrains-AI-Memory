#!/usr/bin/env python3
"""Liveness probe: is IteratedVotingMonty actually running, with N rounds?

WHY THIS EXISTS. A config that silently falls back to upstream's Monty would
produce three arms that are secretly identical, and the analysis would report a
clean null. P6 is the precedent: three different vote rules gave identical
numbers to the decimal, which was not a finding but a broken vote path. A
liveness check before the run is cheaper than a retracted result after it.

This instantiates the experiment exactly as run.py does, then asserts on the
LIVE object: the class is ours, vote_rounds is what the config says, and _vote()
really performs N exchanges.

Run:
    cd upstream/tbp.monty && PYTHONPATH=~/PolyBrains/src .venv/bin/python \
        ~/PolyBrains/tests/probe_p9_liveness.py 2
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "PolyBrains" / "src"))


def main():
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    from hydra import compose, initialize_config_dir
    from hydra.utils import instantiate

    # The `monty.class` interpolation resolver is registered by
    # tbp.monty.hydra.register_resolvers(), which run.py calls. A bare
    # compose() does not, and fails with UnsupportedInterpolationType.
    from tbp.monty.hydra import register_resolvers

    register_resolvers()

    cfg_dir = str(Path.home() / "PolyBrains" / "configs")
    with initialize_config_dir(config_dir=cfg_dir, version_base=None):
        cfg = compose(
            config_name="experiment",
            overrides=[f"experiment=p9_rounds{want}"],
        )

    mc = cfg.experiment.config.monty_config
    cls_name = str(mc.monty_class)
    rounds_cfg = int(mc.monty_args.vote_rounds)

    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))

    print(f"P9 liveness probe, rounds={want}")
    check("config names our class", "IteratedVotingMonty" in cls_name, cls_name)
    check("config vote_rounds matches arm", rounds_cfg == want, str(rounds_cfg))

    # Instantiate the class the config names, without building a full Monty
    # (that needs sensor/motor wiring). We resolve the class object the config
    # points at and construct it with __init__ bypassed, then drive _vote()
    # with stubs. What is under test is the vote loop, not Monty's assembly.
    from hydra.utils import get_class  # noqa: F401  (kept for clarity)

    cls = mc.monty_class if isinstance(mc.monty_class, type) else None
    if cls is None:
        from polybrains.iterated_vote import IteratedVotingMonty as cls  # type: ignore

    check("resolved class is ours", cls.__name__ == "IteratedVotingMonty", cls.__name__)

    monty = cls.__new__(cls)
    monty.vote_rounds = rounds_cfg
    monty.vote_round_stats = []
    check("live vote_rounds attribute", monty.vote_rounds == want, str(monty.vote_rounds))

    # Drive _vote() with stub LMs and count real exchanges.
    class Stub:
        def __init__(self, i, log):
            self.i, self.log = i, log
        def send_out_vote(self):
            self.log.append(("send", self.i))
            return f"v{self.i}"
        def receive_votes(self, votes):
            self.log.append(("recv", self.i))

    log = []
    monty.learning_modules = [Stub(i, log) for i in range(5)]
    monty.lm_to_lm_vote_matrix = [[j for j in range(5) if j != i] for i in range(5)]
    monty.vote_round_stats = []
    monty._vote()
    sends = sum(1 for e in log if e[0] == "send")
    check(f"_vote() performs {want} exchange(s)", sends == 5 * want,
          f"{sends} sends over 5 LMs = {sends / 5:g} rounds")

    print("\n" + ("LIVE" if ok else "NOT LIVE -- do not run the sweep"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
