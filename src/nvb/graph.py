"""cp-graph model of a triangular mesh on top of a plain ``networkx.Graph``.

* Triangle: node ``label="T"`` with ``R`` (0/1, marked for refinement) and ``P1``, ``P2``, ``P3``
  (vertex coordinates). Ids are ints.
* Bond: node ``label="bond"`` with ``index`` (1..3), ``RE``, ``B``, ``BR`` (0/1). Id ``(t, index)``.
  Bond ``i`` is the side opposite vertex ``Pi`` -> the peak is the vertex opposite the ``RE`` bond.
* Edges: triangle-bond (ownership) and bond-bond (side shared by two triangles).
"""

import math
from collections.abc import Iterable
from typing import NamedTuple

import networkx as nx

type Point = tuple[float, float]
type Bond = tuple[int, int]
type Vertices = tuple[Point, Point, Point]

T = "T"
BOND = "bond"
INDICES = (1, 2, 3)


def add_triangle(
    g: nx.Graph,
    p1: Point,
    p2: Point,
    p3: Point,
    *,
    r: int = 0,
    re: Iterable[int] = (0, 0, 0),
    b: Iterable[int] = (0, 0, 0),
    br: Iterable[int] = (0, 0, 0),
) -> int:
    """Add a triangle with its three bonds; returns the new triangle id."""
    t = g.graph.get("next_id", 0)
    g.graph["next_id"] = t + 1
    g.add_node(t, label=T, R=r, P1=p1, P2=p2, P3=p3)
    for i, re_i, b_i, br_i in zip(INDICES, re, b, br, strict=True):
        g.add_node((t, i), label=BOND, index=i, RE=re_i, B=b_i, BR=br_i)
        g.add_edge(t, (t, i))
    return t


def remove_triangle(g: nx.Graph, t: int) -> None:
    g.remove_nodes_from([t, *bonds(g, t)])


def connect(g: nx.Graph, a: Bond, b: Bond) -> None:
    """Join two bonds of different triangles (they share a mesh side)."""
    g.add_edge(a, b)


def rewire(g: nx.Graph, old: Bond, new: Bond) -> None:
    """Move the external connection of ``old`` to ``new`` (fixed embedding of cp-graphs)."""
    if (other := neighbour(g, old)) is not None:
        g.remove_edge(old, other)
        g.add_edge(new, other)


def triangles(g: nx.Graph) -> list[int]:
    return [n for n, label in g.nodes(data="label") if label == T]


def bonds(g: nx.Graph, t: int) -> list[Bond]:
    """Bonds of triangle ``t`` ordered by index."""
    return sorted(
        (n for n in g[t] if g.nodes[n]["label"] == BOND), key=lambda n: g.nodes[n]["index"]
    )


def owner(g: nx.Graph, bond: Bond) -> int:
    return next(n for n in g[bond] if g.nodes[n]["label"] == T)


def neighbour(g: nx.Graph, bond: Bond) -> Bond | None:
    """Bond of the adjacent triangle across this side, ``None`` if not connected."""
    return next((n for n in g[bond] if g.nodes[n]["label"] == BOND), None)


def vertices(g: nx.Graph, t: int) -> tuple[Point, Point, Point]:
    d = g.nodes[t]
    return d["P1"], d["P2"], d["P3"]


def side(g: nx.Graph, bond: Bond) -> tuple[Point, Point]:
    """Endpoints of the mesh side represented by ``bond``."""
    i = g.nodes[bond]["index"]
    p = vertices(g, owner(g, bond))
    return p[i % 3], p[(i + 1) % 3]


def midpoint(a: Point, b: Point) -> Point:
    return (a[0] + b[0]) / 2, (a[1] + b[1]) / 2


def distance(a: Point, b: Point) -> float:
    return math.dist(a, b)


class Child(NamedTuple):
    """One half of a bisected triangle (Calculate1/Calculate2 on the slides).

    ``vertices`` = (newest vertex, old peak, end of the refinement edge), so in the child
    bond 1 is the parent's outer side (new refinement edge), bond 2 half of the parent's
    refinement edge, bond 3 the new interior side shared by both children.
    ``outer`` is the parent bond index whose connection moves to the child's bond 1.
    """

    vertices: Vertices
    outer: int


def bisect(p: Vertices, ref: int) -> tuple[Child, Child]:
    """Split a triangle with vertices ``p`` along its refinement edge (bond ``ref``).

    Both children share the same bond convention (1=outer, 2=half-RE, 3=interior), which
    reverses vertex orientation on one child. In P3, pair the two shared-edge halves by
    coordinates (``set(side(g, ...))``), not by child index 0/1.
    """
    peak, a, b = p[ref - 1], p[ref % 3], p[(ref + 1) % 3]
    m = midpoint(a, b)
    return Child((m, peak, a), (ref + 1) % 3 + 1), Child((m, peak, b), ref % 3 + 1)
