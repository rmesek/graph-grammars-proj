"""Builders of initial meshes (as cp-graphs) used by tests, the CLI and notebooks."""

from collections.abc import Sequence

import networkx as nx

from nvb.graph import INDICES, Bond, Point, add_triangle, connect, distance


def from_triangles(
    points: Sequence[Point],
    tris: Sequence[tuple[int, int, int]],
    refinement: Sequence[int] | None = None,
) -> nx.Graph:
    """Build a cp-graph from point coordinates and triangles given as point indices.

    ``refinement[k]`` is the bond index (1..3) of the refinement edge of triangle ``k``;
    by default the longest side is used. Shared sides are connected, the rest get ``B=1``.
    """
    g = nx.Graph()
    sides: dict[frozenset[int], list[Bond]] = {}
    for k, tri in enumerate(tris):
        pts = [points[v] for v in tri]
        ref = refinement[k] if refinement else _longest(pts)
        t = add_triangle(g, *pts, re=[int(i == ref) for i in INDICES])
        for i in INDICES:
            key = frozenset(v for j, v in enumerate(tri, 1) if j != i)
            sides.setdefault(key, []).append((t, i))
    for owners in sides.values():
        if len(owners) == 2:
            connect(g, *owners)
        else:
            g.nodes[owners[0]]["B"] = 1
    return g


def square(n: int = 1) -> nx.Graph:
    """``n x n`` unit cells, each split by both diagonals into 4 triangles (as on the slides)."""
    points: list[Point] = [(x, y) for y in range(n + 1) for x in range(n + 1)]
    tris: list[tuple[int, int, int]] = []
    for y in range(n):
        for x in range(n):
            a, b = y * (n + 1) + x, y * (n + 1) + x + 1
            c, d = b + n + 1, a + n + 1
            m = len(points)
            points.append((x + 0.5, y + 0.5))
            tris += [(a, b, m), (b, c, m), (c, d, m), (d, a, m)]
    return from_triangles(points, tris)


def _longest(pts: Sequence[Point]) -> int:
    return max(INDICES, key=lambda i: distance(pts[i % 3], pts[(i + 1) % 3]))


MESHES = {"square": square}
