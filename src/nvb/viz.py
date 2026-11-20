"""Draw a cp-graph over the mesh it represents.

Triangles are shrunk towards their centroid so both bonds of a shared side stay visible.
Node ``T`` sits in the centroid, bonds on side midpoints. Attributes: fill = ``R``,
red side = ``RE``, dashed side = ``BR``, thick side = ``B``. Big meshes (slide 27) are drawn
without the cp-graph (labels, bond nodes, edges), which would be unreadable there.
"""

from pathlib import Path

import networkx as nx
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Polygon

from nvb.graph import Point, bonds, side, triangles, vertices

SHRINK = 0.8
GRAPH_LIMIT = 64  # default: draw the cp-graph only up to this many triangles
FILL = {0: "#cfe3f7", 1: "#f7c56b"}


def _towards(p: Point, c: Point, k: float) -> Point:
    return c[0] + k * (p[0] - c[0]), c[1] + k * (p[1] - c[1])


def draw(g: nx.Graph, ax: Axes, title: str | None = None, graph: bool | None = None) -> Axes:
    """Draw the mesh with attributes; ``graph`` (default: small meshes only) adds the cp-graph."""
    if graph is None:
        graph = len(triangles(g)) <= GRAPH_LIMIT
    k, lw = (SHRINK, 1.0) if graph else (0.9, 0.4)
    pos: dict = {}
    for t in triangles(g):
        pts = vertices(g, t)
        c = (sum(p[0] for p in pts) / 3, sum(p[1] for p in pts) / 3)
        pos[t] = c
        ax.add_patch(Polygon([_towards(p, c, k) for p in pts], fc=FILL[g.nodes[t]["R"]], ec="none"))
        if graph:
            ax.text(*c, f"T{t}", ha="center", va="center", fontsize=8, zorder=4)
        for b in bonds(g, t):
            d = g.nodes[b]
            p, q = (_towards(v, c, k) for v in side(g, b))
            ax.plot(
                [p[0], q[0]],
                [p[1], q[1]],
                color="tab:red" if d["RE"] else "black",
                ls="--" if d["BR"] else "-",
                lw=lw * (3 if d["B"] else 1.2),
                zorder=2,
            )
            pos[b] = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
    if graph:
        for u, v in g.edges:
            ax.plot(*zip(pos[u], pos[v], strict=True), color="gray", lw=0.7, zorder=1)
        xs, ys = zip(*pos.values(), strict=True) if pos else ((), ())
        ax.scatter(xs, ys, s=12, color="dimgray", zorder=3)
    ax.legend(
        handles=[
            Patch(fc=FILL[1], label="R=1"),
            Line2D([], [], color="tab:red", label="RE=1"),
            Line2D([], [], color="black", ls="--", label="BR=1"),
            Line2D([], [], color="black", lw=3, label="B=1"),
        ],
        loc="upper left",
        bbox_to_anchor=(1, 1),
        fontsize=8,
    )
    ax.set_aspect("equal")
    ax.autoscale_view()
    ax.axis("off")
    if title:
        ax.set_title(title)
    return ax


def save(g: nx.Graph, path: Path, title: str | None = None, graph: bool | None = None) -> Path:
    fig = Figure(figsize=(7, 6))
    draw(g, fig.subplots(), title, graph)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    return path
