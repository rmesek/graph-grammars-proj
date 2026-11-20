"""Behaviour of the Production base class, shown on toy productions."""

import networkx as nx

from nvb import graph as cg
from nvb.productions.base import Production, pattern


class MarkAll(Production):
    """Toy single-triangle production: R 0 -> 1."""

    name = "mark"
    lhs = pattern(1)

    def predicate(self, g, m):
        return g.nodes[m[0]]["R"] == 0

    def transform(self, g, m):
        g.nodes[m[0]]["R"] = 1


class SharedRefinementEdge(Production):
    """Toy two-triangle production: both sides of a shared edge are refinement edges."""

    name = "shared"
    lhs = pattern(2, [((0, 1), (1, 1))])

    def predicate(self, g, m):
        return g.nodes[m[(0, 1)]]["RE"] == 1 and g.nodes[m[(1, 1)]]["RE"] == 1

    def transform(self, g, m):
        pass


def test_applies_to_lhs_isomorphic_graph(triangle, viz_save):
    viz_save(triangle, "before")
    assert MarkAll().apply(triangle)
    viz_save(triangle, "after")
    assert triangle.nodes[0]["R"] == 1


def test_predicate_blocks_application(triangle):
    triangle.nodes[0]["R"] = 1
    assert not MarkAll().apply(triangle)


def test_anchor_inside_bigger_graph(square):
    assert MarkAll().apply(square, at=2)
    assert [square.nodes[t]["R"] for t in cg.triangles(square)] == [0, 0, 1, 0]


def test_two_triangle_pattern_requires_edge():
    g = nx.Graph()
    a = cg.add_triangle(g, (0, 0), (1, 0), (0, 1), re=(1, 0, 0))
    b = cg.add_triangle(g, (1, 1), (0, 1), (1, 0), re=(1, 0, 0))
    assert not list(SharedRefinementEdge().matches(g))  # missing bond-bond edge
    cg.connect(g, (a, 1), (b, 1))
    assert list(SharedRefinementEdge().matches(g))
