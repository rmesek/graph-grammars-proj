import networkx as nx

from nvb.graph import (
    Bond,
    add_triangle,
    bisect,
    connect,
    remove_triangle,
    rewire,
    side,
    vertices,
)
from nvb.productions.base import Match, Production, pattern


class P3(Production):
    """Bisect two adjacent triangles whose shared side is the refinement edge of both."""

    name = "P3"
    lhs = pattern(2, [((0, 3), (1, 1))])

    def predicate(self, g: nx.Graph, m: Match) -> bool:
        b6 = g.nodes[m[(0, 3)]]
        b1 = g.nodes[m[(1, 1)]]
        b2 = g.nodes[m[(1, 2)]]
        b3 = g.nodes[m[(1, 3)]]
        return (
            b6["BR"] == 1
            and b6["RE"] == 1
            and b1["RE"] == 1
            and b1["BR"] == 0
            and b2["BR"] == 0
            and b3["BR"] == 0
        )

    def transform(self, g: nx.Graph, m: Match) -> None:
        t0, shared0 = m[0], m[(0, 3)]
        t1, shared1 = m[1], m[(1, 1)]

        children0 = _bisect_parent(g, t0, shared0)
        children1 = _bisect_parent(g, t1, shared1)

        halves0 = {frozenset(side(g, (c, 2))): (c, 2) for c in children0}
        for c in children1:
            half = (c, 2)
            connect(g, halves0[frozenset(side(g, half))], half)

        remove_triangle(g, t0)
        remove_triangle(g, t1)


def _bisect_parent(g: nx.Graph, t: int, shared: Bond) -> tuple[int, int]:
    ref = g.nodes[shared]["index"]
    shared_b = g.nodes[shared]["B"]
    child_ids: list[int] = []

    for child in bisect(vertices(g, t), ref):
        parent_outer = (t, child.outer)
        outer = g.nodes[parent_outer]
        c_id = add_triangle(
            g,
            *child.vertices,
            r=0,
            re=(1, 0, 0),
            b=(outer["B"], shared_b, 0),
            br=(outer["BR"], 0, 0),
        )
        rewire(g, parent_outer, (c_id, 1))
        child_ids.append(c_id)

    c0, c1 = child_ids
    connect(g, (c0, 3), (c1, 3))
    return c0, c1
