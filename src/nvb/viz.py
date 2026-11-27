"""Draw a cp-graph over the mesh it represents.

Triangles are shrunk towards their centroid so both bonds of a shared side stay visible.
Node ``T`` sits in the centroid, bonds on side midpoints; the id ``Tn`` sits towards the peak,
off the cp-graph edges. Attributes: fill = ``R``, red side = ``RE``, dashed side = ``BR``,
thick side = ``B``, explained by a grouped legend below light coordinate axes. Big meshes
(slide 27) are drawn without the cp-graph (ids, bond nodes, edges), which would be unreadable.
"""

from pathlib import Path

import networkx as nx
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.legend_handler import HandlerBase
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Polygon
from matplotlib.text import Text
from matplotlib.ticker import MaxNLocator

from nvb.graph import Point, bonds, side, triangles, vertices

SHRINK = 0.8
GRAPH_LIMIT = 64  # default: draw the cp-graph only up to this many triangles
FILL = {0: "#cfe3f7", 1: "#f7c56b"}
ID_COLOR = "#444444"
TICK_COLOR = "#6b7480"
GRID_COLOR = "#e3e7ec"


def _towards(p: Point, c: Point, k: float) -> Point:
    return c[0] + k * (p[0] - c[0]), c[1] + k * (p[1] - c[1])


class _IdSample:
    """Legend handle drawn as a real triangle id (see ``_IdHandler``)."""

    def get_label(self) -> str:
        return "(id of node T)"


class _IdHandler(HandlerBase):
    def create_artists(
        self, legend, orig_handle, xdescent, ydescent, width, height, fontsize, trans
    ):
        x, y = width / 2 - xdescent, height / 2 - ydescent
        text = Text(x, y, "T0", ha="center", va="center", fontsize=7, color=ID_COLOR)
        text.set_transform(trans)
        return [text]


def _header(text: str) -> Patch:
    """Bold legend row without a sample."""
    return Patch(fc="none", ec="none", label="$\\bf{" + text.replace(" ", "\\ ") + "}$")


def _legend(ax: Axes, graph: bool) -> None:
    """Grouped legend below the axes, wording as on slides 17-18: graph | element, edge."""
    left = [
        _header("Element (node T)"),
        Patch(fc=FILL[0], label="R==0 (element not to refine)"),
        Patch(fc=FILL[1], label="R==1 (element to refine)"),
    ]
    if graph:
        node = Line2D([], [], color="dimgray", marker="o", ms=4, lw=0.7, label="(node T or bond)")
        left = [_header("Graph structure"), node, _IdSample(), *left]
    right = [
        _header("Edge (bond)"),
        Line2D([], [], color="black", lw=1.2, label="RE==B==BR==0 (other edge)"),
        Line2D([], [], color="tab:red", lw=1.2, label="RE==1 (refinement edge)"),
        Line2D([], [], color="black", lw=3, label="B==1 (boundary edge)"),
        Line2D(
            [], [], color="tab:red", lw=3, label="RE==1 and B==1 (refinement and boundary edge)"
        ),
        Line2D([], [], color="tab:red", ls="--", label="BR==1 (edge to be broken)"),  # BR is on RE
    ]
    # Columns are filled top to bottom, so pad the left one to keep each group in its column.
    left += [Patch(fc="none", ec="none", label="")] * (len(right) - len(left))
    handles = left + right
    ax.legend(
        handles=handles,
        labels=[h.get_label() for h in handles],
        handler_map={_IdSample: _IdHandler()},
        loc="upper center",
        bbox_to_anchor=(0.5, -0.05),
        ncol=2,
        fontsize=8,
        frameon=False,
    )


def _light_axes(ax: Axes) -> None:
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.xaxis.set_major_locator(MaxNLocator(steps=[1, 2, 5, 10]))
    ax.yaxis.set_major_locator(MaxNLocator(steps=[1, 2, 5, 10]))
    ax.tick_params(labelsize=7, colors=TICK_COLOR, length=0)
    ax.grid(True, color=GRID_COLOR, lw=0.6)
    ax.set_axisbelow(True)


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
        if graph:  # id towards the peak (vertex opposite RE): off the node dot and T-bond edges
            re = [g.nodes[b]["index"] for b in bonds(g, t) if g.nodes[b]["RE"]]
            at = _towards(pts[re[0] - 1], c, 0.45) if re else c
            ax.text(*at, f"T{t}", ha="center", va="center", fontsize=7, color=ID_COLOR, zorder=4)
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
    _legend(ax, graph)
    _light_axes(ax)
    ax.set_aspect("equal")
    ax.autoscale_view()
    if title:
        ax.set_title(title)
    return ax


def save(g: nx.Graph, path: Path, title: str | None = None, graph: bool | None = None) -> Path:
    fig = Figure(figsize=(7, 6))
    draw(g, fig.subplots(), title, graph)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    return path
