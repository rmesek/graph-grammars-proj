"""P0 (slide 20): mark an element for refinement.

LHS: one triangle. Predicate: ``(REFINEMENT CRITERION) and R == 0``. RHS: the same graph
with ``R = 1``; no node, edge or coordinate changes, so the embedding stays untouched.
"""

from collections.abc import Callable

import networkx as nx

from nvb.graph import Point, vertices
from nvb.productions.base import Match, Production, pattern

type Criterion = Callable[[nx.Graph, int], bool]


def everywhere(g: nx.Graph, t: int) -> bool:
    """Default criterion: any triangle; pick the element with ``apply(g, at=t)``."""
    return True


def contains(p: Point) -> Criterion:
    """Criterion: triangles containing point ``p`` (boundary included)."""

    def criterion(g: nx.Graph, t: int) -> bool:
        a, b, c = vertices(g, t)
        s = [_cross(a, b, p), _cross(b, c, p), _cross(c, a, p)]
        return min(s) >= 0 or max(s) <= 0

    return criterion


def _cross(o: Point, a: Point, p: Point) -> float:
    return (a[0] - o[0]) * (p[1] - o[1]) - (a[1] - o[1]) * (p[0] - o[0])


class P0(Production):
    """Mark an element for refinement: criterion and R==0 -> R=1."""

    name = "P0"
    lhs = pattern(1)

    def __init__(self, criterion: Criterion = everywhere) -> None:
        self.criterion = criterion

    def predicate(self, g: nx.Graph, m: Match) -> bool:
        return g.nodes[m[0]]["R"] == 0 and self.criterion(g, m[0])

    def transform(self, g: nx.Graph, m: Match) -> None:
        g.nodes[m[0]]["R"] = 1
