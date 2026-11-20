# AGENTS.md

Newest Vertex Bisection of triangular meshes as a cp-graph grammar (productions P0–P4).
Spec: README "Wymagania" + `docs/NewestVertex.pdf` (theory: `docs/Lab_CP_grafyS.pdf`). Team of 5, one production each.

## Commands

```bash
uv sync
uv run ruff format . && uv run ruff check --fix .
uv run pytest            # add --viz to write before/after PNGs to out/tests/
uv run nvb --help        # draw | list | apply
```

All three (format, lint, tests) must pass before a commit; CI runs the same.

## Architecture

- `nvb.graph` — cp-graph on `networkx.Graph`. Triangle node `label="T"` (`R`, `P1..P3`), id int.
  Bond node `label="bond"` (`index`, `RE`, `B`, `BR`), id `(t, index)`. Bond `i` is the side
  opposite `Pi`; the peak is opposite the `RE` bond. Edges: T–bond, bond–bond (shared side).
- `nvb.productions.base.Production` — subclass sets `name`, `lhs = pattern(...)`, implements
  `predicate(g, m)` and `transform(g, m)`. `m` maps pattern ids (`k`, `(k, i)`, slide numbering)
  to host nodes. Matching is `networkx` subgraph monomorphism; `apply(g, at=node)` anchors it.
  Pattern bond numbers are free; geometry must use the host bond's `index`.
- Embedding: new triangles take over external connections via `graph.rewire(old, new)`.
- `graph.bisect(vertices, ref)` gives both children (Calculate1/2): newest vertex = midpoint
  of the refinement edge; child bond 1 = new refinement edge. Use it in P3 and P4.
- `nvb.mesh` initial meshes, `nvb.viz` matplotlib drawing, `nvb.cli` typer CLI.

## Adding production PN

1. `src/nvb/productions/pN.py` with `class PN(Production)`; registered automatically.
2. `tests/test_pN.py` covering every README "Definition of Done" item, modelled on
   `tests/test_p0.py`: build the expected graph by hand, compare with `nx.utils.graphs_equal`;
   `viz_save` for before/after drawings; reuse `tests/conftest.py` fixtures, define new ones
   in your own test file.
3. Log changes under your issue's section in `PROGRESS.md`.

A production PR touches only these three places. Changes to shared code (`graph`, `base`,
`mesh`, `viz`, `conftest`, CI) go in a separate small PR, so parallel PRs do not conflict.

## Rules

- Compose well-known libraries (networkx, matplotlib, typer, stdlib) over custom code; new
  dependency only via `uv add` with a reason in the PR.
- Small, testable functions; type hints; English identifiers; docstrings only where non-obvious.
- Keep every file short and focused on the project; no speculative abstractions.
- Notebooks only for presentation; all logic lives in `nvb` and works from the CLI.
- Must run comfortably on a laptop (anchored `apply(at=...)` for large meshes).

## Git

- Never push to `main`; branch `<issue>-<slug>`, PR via `gh pr create` with `Closes #<issue>`.
- Commit messages: imperative, short. **No `Co-authored-by` or other AI attribution trailers.**
- PR description ends with one short line naming the agent and model, e.g.
  `Agent: Claude Code (Claude Opus 5.5)`.
- Update your section of `PROGRESS.md` in every PR.
- Never amend or force-push pushed commits; add new ones (PRs are squash-merged). Push when
  a change is ready: every push restarts CI.
