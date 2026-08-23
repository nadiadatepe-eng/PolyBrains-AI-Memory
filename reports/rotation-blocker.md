# CP-5 blocker — which rotations work under MuJoCo, and why five do not

**Date:** 2026-08-18 · **Sha:** `0c81b1f` · Probe: `tools/probe_rotations.sh`
Raw results: `reports/rotation-probe.tsv`

CP-0 sidestepped this by training on `[[0,0,0]]` alone, which is why its 60% accuracy is a
liveness check and not a baseline. This measures the real situation instead of guessing.

## Result: 9 of 14 usable, and the 5 failures are **two different bugs**

| Rotation | Status | s |
|---|---|---|
| `[0,0,0]` | OK | 48 |
| `[0,90,0]` | OK | 43 |
| `[0,180,0]` | **NO_VIEW** | 11 |
| `[0,270,0]` | OK | 43 |
| `[90,0,0]` | OK | 44 |
| `[90,180,0]` | OK | 43 |
| `[35,45,0]` | OK | 45 |
| `[325,45,0]` | OK | 45 |
| `[35,315,0]` | OK | 43 |
| `[325,315,0]` | OK | 44 |
| `[35,135,0]` | **ERROR** | 16 |
| `[325,135,0]` | **ERROR** | 16 |
| `[35,225,0]` | **ERROR** | 29 |
| `[325,225,0]` | **ERROR** | 17 |

The plan assumed a single "placement" problem. There are two, with different causes and
different fixes.

---

## Failure 1 — `[0,180,0]` genuinely out of view

`ValueError: May be initializing experiment with no visible target object`, raised from
`positioning_procedures.py:360` when the semantic image contains no pixels of the target.

This is the placement problem as originally described: the habitat-tuned camera geometry does
not see the object when it is rotated 180° about the y axis. **Configuration issue, ours to
fix**, by re-tuning the MuJoCo camera or excluding the rotation.

## Failure 2 — four rotations hit an **upstream bug**

`sklearn.utils._param_validation.InvalidParameterError: The 'n_neighbors' parameter of
kneighbors_graph must be an int in the range [1, inf). Got None instead.`

This is not a placement problem and not our configuration. It is a latent null-handling
defect in Monty:

`frameworks/utils/graph_matching_utils.py:25` — `get_correct_k_n` returns **`None`** when a
module collects 2 or fewer observations:

```python
if num_datapoints <= k_n:
    if num_datapoints > 2:
        k_n = num_datapoints - 1
    else:
        logger.error("not enough observations collected to build graph.")
        return None          # <-- returns None
return k_n
```

`frameworks/models/object_model.py:323` — the caller guards the *input* but then reassigns
`k_n` and uses the result unguarded:

```python
if k_n is not None:                      # guards the INPUT
    k_n = get_correct_k_n(k_n, num_nodes)   # may now be None
    scipy_graph = kneighbors_graph(
        locations_reduced, n_neighbors=k_n,  # <-- None reaches sklearn
        include_self=False
    )
```

Reproducible in three lines:

```python
from tbp.monty.frameworks.utils.graph_matching_utils import get_correct_k_n
get_correct_k_n(10, 2)   # -> None
get_correct_k_n(10, 3)   # -> 2
```

The `logger.error("not enough observations collected to build graph.")` fires exactly as
designed, then the code crashes anyway instead of skipping the graph. **The error message is
correct and the control flow is not.**

### Why these four rotations

`[35,135,0]`, `[325,135,0]`, `[35,225,0]`, `[325,225,0]` are the "back-facing" tilted views.
At least one of the five sensor patches lands on a part of the object where it collects ≤2
usable points, and that module then trips the null. The failure is fast (16-29 s vs 43-48 s
for a success), consistent with crashing during graph building rather than after a full run.

**This is a real upstream bug worth reporting**, and it is plausible it does not manifest
under HabitatSim because the sensor geometry differs. That would explain why upstream has not
hit it.

---

## Consequences

1. **We have 9 usable rotations, not 1.** That is enough for a real baseline and a genuine
   OOD split. CP-5 is unblocked without solving either bug.
2. **Proposed split, to be pre-registered before any run:**
   - *In-domain train:* `[0,0,0]`, `[0,90,0]`, `[0,270,0]`, `[90,0,0]`, `[90,180,0]`
   - *OOD test:* `[35,45,0]`, `[325,45,0]`, `[35,315,0]`, `[325,315,0]`
   The tilted views are held out, which is a defensible OOD notion: the system trains on axis
   aligned poses and is tested on oblique ones.
3. **The exclusion must be reported in the paper**, with this table. Silently dropping 5 of 14
   rotations would be exactly the selective reporting the project is written against.
4. Fixing the upstream bug is optional for us. A one-line guard
   (`if k_n is not None:` after the reassignment) would let those four rotations run, but
   changing upstream violates our own contract. **Better: report it upstream after
   publication**, consistent with the CP-0 decision to keep our layer separate for now.

## Reproduce

```bash
bash ~/PolyBrains/tools/probe_rotations.sh   # ~8 min, 14 runs
```
