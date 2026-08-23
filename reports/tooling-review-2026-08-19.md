# Two repos assessed, 2026-08-19

Both checked against what this account actually runs, not against how good they are
in general. The question asked of each was: **does this remove work we are currently
doing by hand, and on this hardware?**

---

## 1. ArjanCodes `2026/libraries` — 15 Python libraries

Source: `github.com/ArjanCodes/examples/tree/main/2026/libraries`, read in full
(sparse clone, 15 example files + `pyproject.toml`).

**Note before anything else:** the project pins `requires-python = ">=3.14"`. Every
venv here is Python 3.12 (PolyBrains, cuda-agent-ref, colibri's convert env). The
examples are single-file and dependency-light, so this is not a blocker for the
libraries themselves, but the repo as given will not `uv sync` on this machine.

### Worth adopting — three of them

**`msgspec`** — the strongest fit. Typed struct decode/encode with validation, and
substantially faster than pydantic for pure serialisation. Where it pays here:
`tvfeed` parses TradingView screener JSON and its whole selling point is *an error
contract you can trust*; `msgspec.ValidationError` on a typed `Struct` is exactly
that contract, enforced at the boundary rather than by hand. Also relevant to
`CODEX-TradingSystem` for candle payloads.

**`duckdb`** — SQL directly over CSV/Parquet with no server, no schema, no load step:
`duckdb.sql("SELECT ... FROM 'file.csv'")`, and `.df()` when a DataFrame is wanted.
Where it pays: `eval_stats.csv` analysis in PolyBrains. `tools/analyse_p8.py` and
`analyse_p9.py` hand-roll `csv.DictReader` + `defaultdict` grouping over 40-file
globs. That is a `GROUP BY` and a `JOIN`. Would have made the P8 re-scoring a
half-hour job instead of a script, and would make per-rotation breakdowns trivial —
exactly the cut that exposed P7's unbalanced design.

**`complexipy`** — cognitive-complexity linter, Rust-backed, with a before/after
example pair in the repo. Fits the existing `fallow`/`ponytail` habits already in
this account and is cheap to run in CI.

### Situationally useful — two

**`pint`** — physical units with dimensional analysis; `distance + duration` raises.
Not useful for PolyBrains (unitless evidence scores), but genuinely useful for
`agentos-lab/volatility-lab`, where returns, annualised vol and per-bar vol get
mixed and a wrong scale factor is silent. The cost is that every quantity must be
wrapped, so it is worth it only where the unit confusion is real.

**`whenever`** — DST-correct datetime arithmetic. `CODEX-TradingSystem` runs on
closed 1H candles across exchanges; adding 8 hours across a DST boundary with naive
datetimes is the classic silent bug. Only worth it if we ever leave UTC — if
everything stays UTC, stdlib is fine and this is a dependency for nothing.

### Skip, with reasons

- **`pydantic-settings`** — env/config loading. Our configs are Hydra YAML, which
  already does this. Adding a second config system is strictly worse.
- **`dacite`** — dict → dataclass. `msgspec` covers this and is faster; picking both
  is redundant.
- **`dishka`** — DI container. These projects have no dependency graph deep enough
  to need one. Would be architecture for its own sake.
- **`python-statemachine`**, **`schedium`**, **`autoregistry`** — no state machines,
  no scheduling, no plugin registries in play.
- **`geopy`**, **`faker`**, **`nicegui`**, **`zensical`** — no geocoding, no fake
  data need (our data is measured), and the UI/docs slots are already filled by
  Tauri and the HTML plan documents.

### Verdict

Two clear wins (`msgspec`, `duckdb`), one cheap quality tool (`complexipy`), two
conditional (`pint`, `whenever`), ten irrelevant. Nothing here changes a research
result; it removes hand-rolled parsing and grouping code. **Adopt on next touch of
the relevant file, not as a migration project.**

---

## 2. NVIDIA PhysicsNeMo — assessed and **not** recommended

Source: `github.com/NVIDIA/physicsnemo`, Apache-2.0, README read in full plus the
model tree (24 architecture families: FNO, DoMINO, GraphCast, MeshGraphNet,
diffusion, Transolver, PINNs, ...).

**What it is:** a framework for *physics* AI — surrogate models for CFD, weather,
structural mechanics. Neural operators that learn PDE solution maps, GNNs over
meshes, diffusion models for flow fields. It is a serious, actively developed
library and is the right tool for those problems.

**Why it does not fit anything we are doing:**

- **PolyBrains** studies sensorimotor object recognition with reference-frame voting
  between learning modules. There is no PDE, no mesh, no field to regress. The
  overlap with PhysicsNeMo is "both use PyTorch".
- **volatility-lab** is GARCH on 1H returns — econometrics, not continuum physics.
  PhysicsNeMo's neural operators solve the wrong kind of problem.
- **CODEX-TradingSystem** is deterministic rule evaluation. No ML at all.
- **Morpho-HomeGraph** is retrieval and graph search.

**Hardware note, since it is the usual reason to want this:** it would install. The
RTX 5060 Ti (sm_120) needs the `cu13` or `cu12` extra, and we have a working local
CUDA 12.8 at `~/opt/cuda-12.8` from the CUDA-Agent work, so the wheels would resolve.
Installing it is not the problem. Having no problem for it to solve is.

**One genuinely transferable idea, worth taking without the dependency:** its
`DistributedManager` pattern — a single object that owns rank/device/stream setup so
model code never touches `torch.distributed` directly. If PolyBrains ever needs
multi-GPU, that is the shape to copy. We do not need it now: CP-0 measured a 5-LM
voting eval at 58 s and 1.3 GB peak RSS. **Compute is not a constraint on this
project, so a scaling framework solves a problem we do not have.**

### Verdict

**Do not install.** Right tool, wrong domain. Revisit only if the work turns toward
physical simulation or field prediction. Recorded here so the question does not get
re-asked from scratch.

---

## Adoption tested, not just recommended

`duckdb` was installed into the project venv and used to **independently
re-derive P8's headline numbers** from the raw CSVs, sharing no code with
`tools/analyse_p8.py`:

| comparison | analyse_p8.py | DuckDB SQL | |
|---|---|---|---|
| `any`, no voting − max | +2.80 pp (t=4.58) | +2.80 pp (t=4.58) | match |
| `majority` | +0.20 pp (t=0.13) | +0.20 pp (t=0.13) | match |
| **`unanimous`** | **−30.20 pp (t=−14.40)** | **−30.20 pp (t=−14.40)** | match |
| mean modules correct | +0.564 (t=15.11) | +0.564 (t=15.11) | match |

Committed as `tools/crosscheck_p8_duckdb.py`. **P8 now reproduces in two
independent implementations**, which matters because it overturned the project's
central finding on the strength of a single script.

**One trap found while doing it, kept in the file's docstring:** `eval_stats.csv`
has no episode-id column, so episodes are identified positionally. A first version
used `row_number() OVER (PARTITION BY lm ORDER BY 1)` — `ORDER BY 1` is a constant,
so row order was unspecified, modules were paired against the wrong episodes, and
unanimity read 39.4% instead of 41.0%. Fixed with an explicit file-order row id.
A silent 1.6 pp error from a plausible-looking query is a good argument for keeping
the Python and the SQL as two independent implementations rather than replacing one
with the other.

`msgspec` was **not** installed: it belongs in `tvfeed`, which has its own
environment, and installing it here would serve nothing.
