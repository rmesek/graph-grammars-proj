"""Command line interface: ``uv run nvb --help``."""

from pathlib import Path
from typing import Annotated

import typer

from nvb import viz
from nvb.mesh import MESHES
from nvb.productions import PRODUCTIONS

app = typer.Typer(no_args_is_help=True, help="Newest Vertex Bisection as a cp-graph grammar.")

MeshOpt = Annotated[str, typer.Option(help=f"Initial mesh: {', '.join(MESHES)}.")]
SizeOpt = Annotated[int, typer.Option("-n", help="Mesh size (cells per side).")]
OutOpt = Annotated[Path, typer.Option("--out", "-o", help="Output PNG.")]
GraphOpt = Annotated[
    bool | None,
    typer.Option(
        "--graph/--no-graph",
        help=f"Draw the cp-graph (default: up to {viz.GRAPH_LIMIT} triangles).",
    ),
]


@app.command("list")
def list_productions() -> None:
    """List registered productions."""
    for name, p in PRODUCTIONS.items():
        typer.echo(f"{name}: {(type(p).__doc__ or '').strip()}")


@app.command()
def draw(
    mesh: MeshOpt = "square",
    n: SizeOpt = 1,
    out: OutOpt = Path("out/mesh.png"),
    graph: GraphOpt = None,
) -> None:
    """Draw an initial mesh with its cp-graph."""
    typer.echo(viz.save(MESHES[mesh](n), out, title=f"{mesh} n={n}", graph=graph))


@app.command()
def apply(
    names: Annotated[list[str], typer.Argument(help="Productions to apply in order, e.g. P0 P1.")],
    mesh: MeshOpt = "square",
    n: SizeOpt = 1,
    at: Annotated[int | None, typer.Option(help="Anchor triangle id.")] = None,
    out: OutOpt = Path("out/apply.png"),
    graph: GraphOpt = None,
) -> None:
    """Apply productions to an initial mesh and draw the result."""
    if unknown := [x for x in names if x not in PRODUCTIONS]:
        raise typer.BadParameter(f"unknown productions: {unknown}; see `nvb list`")
    g = MESHES[mesh](n)
    for name in names:
        typer.echo(f"{name}: {'applied' if PRODUCTIONS[name].apply(g, at) else 'no match'}")
    typer.echo(viz.save(g, out, title=" -> ".join(names), graph=graph))
