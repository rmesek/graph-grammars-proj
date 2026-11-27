import operator

import networkx as nx
import pytest
from matplotlib.colors import to_hex
from matplotlib.figure import Figure

from nvb import graph as cg
from nvb import mesh, viz
from nvb.productions import PRODUCTIONS
from nvb.productions.p3 import P3


def re_bond(g: nx.Graph, t: int) -> cg.Bond:
    (b,) = [b for b in cg.bonds(g, t) if g.nodes[b]["RE"]]
    return b


def area(g: nx.Graph, t: int) -> float:
    (ax, ay), (bx, by), (cx, cy) = cg.vertices(g, t)
    return abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax)) / 2


def assert_conforming_mesh(g: nx.Graph, expected_area: float) -> None:
    """Verify valid bond-bond connections and absence of hanging nodes."""
    for n, d in g.nodes(data=True):
        if d["label"] == cg.BOND:
            owners = [x for x in g[n] if g.nodes[x]["label"] == cg.T]
            others = [x for x in g[n] if g.nodes[x]["label"] == cg.BOND]
            assert len(owners) == 1
            assert len(others) <= 1
            if others:
                assert d["B"] == 0
                assert set(cg.side(g, n)) == set(cg.side(g, others[0]))
            else:
                assert d["B"] == 1
    for t in cg.triangles(g):
        bonds = cg.bonds(g, t)
        assert [g.nodes[b]["index"] for b in bonds] == [1, 2, 3]
        assert g.nodes[t]["R"] in (0, 1)
        assert sum(g.nodes[b]["RE"] for b in bonds) == 1
        assert area(g, t) > 0
    assert sum(area(g, t) for t in cg.triangles(g)) == pytest.approx(expected_area)


def two_triangle_pair(*, flipped: bool = False) -> nx.Graph:
    """Two triangles sharing diagonal (1, 0)-(0, 1) as RE, with T0 marked (R=1, BR=1)."""
    tris = [(0, 1, 2), (1, 2, 3)] if flipped else [(0, 1, 2), (1, 3, 2)]
    g = mesh.from_triangles([(0, 0), (1, 0), (0, 1), (1, 1)], tris)
    g.nodes[0]["R"] = 1
    g.nodes[re_bond(g, 0)]["BR"] = 1
    return g


def expected_bisected(g: nx.Graph, t0: int, t1: int) -> nx.Graph:
    """Expected RHS built by hand for comparing whole graphs via isomorphism."""
    expected = g.copy()
    new_groups: list[list[int]] = []
    for t in (t0, t1):
        shared = re_bond(expected, t)
        ref = expected.nodes[shared]["index"]
        shared_b = expected.nodes[shared]["B"]
        group: list[int] = []
        for child in cg.bisect(cg.vertices(expected, t), ref):
            parent_outer = (t, child.outer)
            outer = expected.nodes[parent_outer]
            c_id = cg.add_triangle(
                expected,
                *child.vertices,
                r=0,
                re=(1, 0, 0),
                b=(outer["B"], shared_b, 0),
                br=(outer["BR"], 0, 0),
            )
            cg.rewire(expected, parent_outer, (c_id, 1))
            group.append(c_id)
        cg.connect(expected, (group[0], 3), (group[1], 3))
        new_groups.append(group)

    halves0 = {frozenset(cg.side(expected, (c, 2))): (c, 2) for c in new_groups[0]}
    for c in new_groups[1]:
        half = (c, 2)
        cg.connect(expected, halves0[frozenset(cg.side(expected, half))], half)

    cg.remove_triangle(expected, t0)
    cg.remove_triangle(expected, t1)
    return expected


# --- LHS-isomorphic graph -------------------------------------------------------------


@pytest.mark.parametrize("flipped", [False, True], ids=["same-orientation", "flipped-orientation"])
def test_applies_to_lhs_isomorphic_graph(flipped, viz_save):
    g = two_triangle_pair(flipped=flipped)
    expected = expected_bisected(g, 0, 1)
    if not flipped:
        viz_save(g, "before")
    assert P3().apply(g)
    if not flipped:
        viz_save(g, "after")
    assert nx.is_isomorphic(g, expected, node_match=operator.eq)
    assert_conforming_mesh(g, 1.0)


def test_rhs_is_complete_and_inherits_outer_br():
    """Exact coordinates, nodes, bonds, edges, and inherited outer BR on all 4 children."""
    g = two_triangle_pair()
    # Outer bond 2 of T0 ((0, 0)-(0, 1)) carries BR=1, which must be inherited by its child.
    g.nodes[(0, 2)]["BR"] = 1

    expected = nx.Graph()
    c0 = cg.add_triangle(expected, (0.5, 0.5), (0, 0), (1, 0), re=(1, 0, 0), b=(1, 0, 0))
    c1 = cg.add_triangle(
        expected, (0.5, 0.5), (0, 0), (0, 1), re=(1, 0, 0), b=(1, 0, 0), br=(1, 0, 0)
    )
    c2 = cg.add_triangle(expected, (0.5, 0.5), (1, 1), (0, 1), re=(1, 0, 0), b=(1, 0, 0))
    c3 = cg.add_triangle(expected, (0.5, 0.5), (1, 1), (1, 0), re=(1, 0, 0), b=(1, 0, 0))
    cg.connect(expected, (c0, 3), (c1, 3))
    cg.connect(expected, (c2, 3), (c3, 3))
    cg.connect(expected, (c0, 2), (c3, 2))
    cg.connect(expected, (c1, 2), (c2, 2))

    assert P3().apply(g)
    assert len(cg.triangles(g)) == 4
    assert sum(1 for _, lbl in g.nodes(data="label") if lbl == cg.BOND) == 12
    assert g.number_of_edges() == 16
    assert nx.is_isomorphic(g, expected, node_match=operator.eq)


# --- wrong attributes / invalid LHS -----------------------------------------------------


@pytest.mark.parametrize(
    "corrupt",
    [
        lambda g: g.nodes[(0, 1)].__setitem__("BR", 0),  # BR6 == 0
        lambda g: g.nodes[(0, 1)].__setitem__("RE", 0),  # RE6 == 0
        lambda g: g.nodes[(1, 2)].__setitem__("RE", 0),  # RE1 == 0 (case for P2)
        lambda g: g.nodes[(1, 2)].__setitem__("BR", 1),  # BR1 == 1
        lambda g: g.nodes[(1, 1)].__setitem__("BR", 1),  # BR2 == 1
        lambda g: g.nodes[(1, 3)].__setitem__("BR", 1),  # BR3 == 1
    ],
    ids=["BR6=0", "RE6=0", "RE1=0", "BR1=1", "BR2=1", "BR3=1"],
)
def test_wrong_attribute_is_not_applied(corrupt):
    g = two_triangle_pair()
    corrupt(g)
    before = g.copy()
    assert not P3().apply(g)
    assert nx.utils.graphs_equal(g, before)


def test_missing_shared_edge_does_not_match():
    """Two triangles without the bond-bond edge between them must not match."""
    g = two_triangle_pair()
    g.remove_edge((0, 1), (1, 2))
    assert not list(P3().matches(g))
    before = g.copy()
    assert not P3().apply(g)
    assert nx.utils.graphs_equal(g, before)


def test_boundary_refinement_edge_does_not_match(triangle):
    """Single triangle with boundary RE marked (case for P4) must not match P3."""
    triangle.nodes[0]["R"] = 1
    triangle.nodes[re_bond(triangle, 0)]["BR"] = 1
    before = triangle.copy()
    assert not P3().apply(triangle)
    assert nx.utils.graphs_equal(triangle, before)


# --- LHS inside a bigger graph -----------------------------------------------------------


@pytest.mark.parametrize("anchor", [7, 1])
def test_in_bigger_graph_rewires_embedding_and_keeps_rest_intact(anchor, viz_save):
    g = mesh.square(2)
    g.nodes[7]["R"] = 1
    g.nodes[re_bond(g, 7)]["BR"] = 1
    expected = expected_bisected(g, 7, 1)

    if anchor == 7:
        viz_save(g, "before")
    assert P3().apply(g, at=anchor)
    if anchor == 7:
        viz_save(g, "after")

    assert len(cg.triangles(g)) == 18
    assert nx.is_isomorphic(g, expected, node_match=operator.eq)
    assert_conforming_mesh(g, 4.0)


# --- drawing and registration ------------------------------------------------------------


def test_drawing_renders_bisected_triangles():
    g = two_triangle_pair()
    P3().apply(g)
    ax = viz.draw(g, Figure().subplots())
    fills = [to_hex(p.get_facecolor()) for p in ax.patches]
    assert len(fills) == 4
    assert all(f == viz.FILL[0] for f in fills)
    assert len(ax.lines) == 3 * len(fills) + g.number_of_edges()


def test_registered():
    assert isinstance(PRODUCTIONS["P3"], P3)
