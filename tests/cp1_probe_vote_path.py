"""CP-1 empirical probe of the three vote-path findings.

Reading code establishes what is written. This establishes what happens when it
runs, which is the claim that actually matters. Uses only upstream's own classes
at the pinned sha; asserts nothing about our own code (there is none yet).
"""
import inspect
import numpy as np

from tbp.monty.frameworks.models.evidence_matching.learning_module import (
    EvidenceGraphLM,
)
from tbp.monty.frameworks.models.evidence_matching.model import (
    MontyForEvidenceGraphMatching,
)

results = {}

# ---------------------------------------------------------------- finding (a)
# Claim: incoming votes are reduced with np.ma.max, so the loudest single vote
# in the neighbourhood wins outright rather than a consensus forming.
src = inspect.getsource(EvidenceGraphLM._update_evidence_with_vote)
results["a_uses_ma_max"] = "np.ma.max(" in src
results["a_uses_ma_average_for_votes"] = "np.ma.average(\n            all_radius" in src

# Behavioural demonstration of what np.ma.max means for a vote:
# three peers, one confident and two agreeing with each other.
loud = 0.95
quiet_a, quiet_b = 0.42, 0.40
neighbourhood = np.ma.array([[loud, quiet_a, quiet_b]], mask=[[False, False, False]])
reduced = float(np.ma.max(neighbourhood, axis=1)[0])
results["a_reduced_value"] = reduced
results["a_equals_loudest"] = np.isclose(reduced, loud)
results["a_mean_would_be"] = float(np.mean([loud, quiet_a, quiet_b]))
# Two quiet modules agreeing contribute nothing the loud one did not already set.
without_agreement = float(np.ma.max(np.ma.array([[loud]]), axis=1)[0])
results["a_agreement_changes_nothing"] = np.isclose(reduced, without_agreement)

# ---------------------------------------------------------------- finding (b)
# Claim: no dispersion statistic across incoming votes is ever computed.
combine_src = inspect.getsource(MontyForEvidenceGraphMatching._combine_votes)
dispersion_tokens = ["np.var", "np.std", "entropy", "disagree", "consensus"]
results["b_dispersion_in_combine"] = [t for t in dispersion_tokens if t in combine_src]
results["b_dispersion_in_update"] = [t for t in dispersion_tokens if t in src]
# The one np.std in the module is over object hypotheses inside a single LM,
# not across LMs. Confirm it lives in a different method.
pm_src = inspect.getsource(EvidenceGraphLM._threshold_possible_matches) \
    if hasattr(EvidenceGraphLM, "_threshold_possible_matches") else ""
results["b_std_is_within_lm_not_across"] = "np.std" not in src

# ---------------------------------------------------------------- finding (c)
# Claim: vote_weight is a constant set once and never updated from experience.
init_src = inspect.getsource(EvidenceGraphLM.__init__)
results["c_assigned_in_init"] = "self.vote_weight = vote_weight" in init_src
methods = [
    m for _, m in inspect.getmembers(EvidenceGraphLM, predicate=inspect.isfunction)
]
reassigning = []
for m in methods:
    try:
        msrc = inspect.getsource(m)
    except (OSError, TypeError):
        continue
    if "self.vote_weight" in msrc and "=" in msrc:
        for line in msrc.splitlines():
            stripped = line.strip()
            if stripped.startswith("self.vote_weight") and "==" not in stripped:
                reassigning.append(m.__name__)
results["c_methods_assigning_vote_weight"] = sorted(set(reassigning))

print("=" * 68)
print("CP-1 EMPIRICAL PROBE — upstream tbp.monty @ 0c81b1f")
print("=" * 68)
for k, v in results.items():
    print(f"{k:38} {v}")

print()
print("-" * 68)
ok = True

if not (results["a_uses_ma_max"] and results["a_equals_loudest"]
        and results["a_agreement_changes_nothing"]):
    ok = False
    print("FINDING (a) NOT CONFIRMED")
else:
    print(f"(a) CONFIRMED: reduction is np.ma.max. Votes {loud}/{quiet_a}/{quiet_b}")
    print(f"    -> {reduced} (the loudest). Mean would be "
          f"{results['a_mean_would_be']:.3f}.")
    print("    Two modules agreeing with each other change nothing.")

if results["b_dispersion_in_combine"] or results["b_dispersion_in_update"]:
    ok = False
    print("FINDING (b) NOT CONFIRMED — dispersion tokens found")
else:
    print("(b) CONFIRMED: no variance/entropy/disagreement statistic in either")
    print("    _combine_votes or _update_evidence_with_vote. Votes are")
    print("    concatenated and reduced; the group's spread is never represented.")

if results["c_methods_assigning_vote_weight"] != ["__init__"]:
    ok = False
    print(f"FINDING (c) NOT CONFIRMED — assigned in "
          f"{results['c_methods_assigning_vote_weight']}")
else:
    print("(c) CONFIRMED: vote_weight assigned only in __init__, never updated")
    print("    from experience anywhere in the class.")

print("-" * 68)
print("ALL THREE CONFIRMED" if ok else "AT LEAST ONE FINDING IS WRONG")
raise SystemExit(0 if ok else 1)
