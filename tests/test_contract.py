"""Production contract: what each production must hand over to the next stage.

Shared by the whole team and independent of who writes ``PN``. Every production is checked
alone, on a graph built by hand in the state the previous stage leaves, so no PR depends on
another teammate's production; tests of productions not registered yet are skipped. Only the
resulting cp-graph is checked (attributes, bonds, connections, coordinates), never the code.
"""

from collections.abc import Callable

import networkx as nx
import pytest

from nvb import graph as cg
from nvb import mesh
from nvb.productions import PRODUCTIONS
from nvb.productions.base import Production

LHS_TRIANGLES = {"P0": 1, "P1": 1, "P2": 2, "P3": 2, "P4": 1}


def production(name: str) -> Production:
    if name not in PRODUCTIONS:
        pytest.skip(f"{name} not registered yet")
    return PRODUCTIONS[name]


def re_bond(g: nx.Graph, t: int) -> cg.Bond:
    (b,) = [b for b in cg.bonds(g, t) if g.nodes[b]["RE"]]
    return b


def area(g: nx.Graph, t: int) -> float:
    (ax, ay), (bx, by), (cx, cy) = cg.vertices(g, t)
    return abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax)) / 2


def check_mesh(g: nx.Graph, total_area: float) -> None:
    """Invariants every production must keep: a conforming mesh without hanging nodes."""
    for n, d in g.nodes(data=True):
        if d["label"] == cg.BOND:
            owners = [x for x in g[n] if g.nodes[x]["label"] == cg.T]
            others = [x for x in g[n] if g.nodes[x]["label"] == cg.BOND]
            assert len(owners) == 1, f"bond {n} must belong to exactly one triangle"
            assert len(others) <= 1, f"bond {n} may be connected to at most one bond"
            if others:
                assert d["B"] == 0, f"connected bond {n} must have B=0"
                assert set(cg.side(g, n)) == set(cg.side(g, others[0])), (
                    f"bonds {n}-{others[0]} must lie on the same side "
                    "(in P3, pair shared-edge halves by set(side(g, ...)), not bisect index)"
                )
            else:
                assert d["B"] == 1, f"free bond {n} must be on the boundary (B=1); rewire lost?"
    for t in cg.triangles(g):
        bonds = cg.bonds(g, t)
        assert [g.nodes[b]["index"] for b in bonds] == [1, 2, 3], f"T{t} needs bonds 1..3"
        assert g.nodes[t]["R"] in (0, 1)
        assert all(g.nodes[b][k] in (0, 1) for b in bonds for k in ("RE", "B", "BR"))
        assert sum(g.nodes[b]["RE"] for b in bonds) == 1, f"T{t} needs exactly one RE"
        assert area(g, t) > 0, f"T{t} is degenerate"
    assert sum(area(g, t) for t in cg.triangles(g)) == pytest.approx(total_area)


# --- states left by the previous stage ------------------------------------------------


def broken(g: nx.Graph, t: int) -> nx.Graph:
    """State after P0 and P1 on ``t``: R=1, BR=1 on its refinement edge."""
    g.nodes[t]["R"] = 1
    g.nodes[re_bond(g, t)]["BR"] = 1
    return g


def unmarked() -> nx.Graph:
    return mesh.square(2)


def marked() -> nx.Graph:
    """After P0 on T5 -> P1."""
    g = mesh.square(2)
    g.nodes[5]["R"] = 1
    return g


def boundary() -> nx.Graph:
    """Refinement edge of T0 marked and on the boundary -> P4."""
    return broken(mesh.square(1), 0)


def shared() -> nx.Graph:
    """Refinement edge of T7 marked and also the refinement edge of T1 -> P3."""
    return broken(mesh.square(2), 7)


def shared_flipped() -> nx.Graph:
    """Shared RE where T0 (CCW) and T1 (CW) have opposite orientation -> P3.

    Catches P3 implementations that pair bisect children by index 0/1 instead of coordinates.
    """
    g = mesh.from_triangles([(0, 0), (1, 0), (0, 1), (1, 1)], [(0, 1, 2), (1, 2, 3)])
    return broken(g, 0)


def propagate() -> nx.Graph:
    """Refinement edge of T0 marked; T1 across it has its refinement edge elsewhere -> P2."""
    g = mesh.from_triangles([(0, 0), (1, 0), (0, 1), (1, 1)], [(0, 1, 2), (1, 3, 2)], [1, 1])
    return broken(g, 0)


STATES: dict[str, tuple[Callable[[], nx.Graph], str | None]] = {
    "unmarked": (unmarked, None),
    "marked": (marked, "P1"),
    "boundary": (boundary, "P4"),
    "shared": (shared, "P3"),
    "propagate": (propagate, "P2"),
}


def test_states_are_what_they_claim():
    for build in [*(b for b, _ in STATES.values()), shared_flipped]:
        g = build()
        check_mesh(g, sum(area(g, t) for t in cg.triangles(g)))
    g = shared()
    assert g.nodes[cg.neighbour(g, re_bond(g, 7))]["RE"] == 1
    g = shared_flipped()
    assert g.nodes[cg.neighbour(g, re_bond(g, 0))]["RE"] == 1
    g = propagate()
    assert g.nodes[cg.neighbour(g, re_bond(g, 0))]["RE"] == 0


# --- shape --------------------------------------------------------------------------------


@pytest.mark.parametrize("name", LHS_TRIANGLES)
def test_shape(name):
    p = production(name)
    assert isinstance(p, Production) and type(p).__name__ == p.name == name
    lhs = p.lhs
    assert sum(1 for _, x in lhs.nodes(data="label") if x == cg.T) == LHS_TRIANGLES[name]
    links = [e for e in lhs.edges if all(lhs.nodes[n]["label"] == cg.BOND for n in e)]
    assert len(links) == LHS_TRIANGLES[name] - 1, "two-triangle LHS: one bond-bond edge"


# --- exactly one production fits each state --------------------------------------------


@pytest.mark.parametrize("name", ["P1", "P2", "P3", "P4"])
@pytest.mark.parametrize("state", STATES)
def test_applies_only_where_expected(state, name):
    p = production(name)
    build, expected = STATES[state]
    g = build()
    before = g.copy()
    assert p.apply(g) == (name == expected), f"{name} in state '{state}'; expected {expected}"
    if name != expected:
        assert nx.utils.graphs_equal(g, before), f"{name} changed the graph without applying"


@pytest.mark.parametrize(("state", "anchors"), [("shared", (7, 1)), ("propagate", (0, 1))])
def test_two_triangle_production_applies_from_either_triangle(state, anchors):
    build, name = STATES[state]
    p = production(name)
    for t in anchors:
        assert p.apply(build(), at=t), f"{name} must apply with at=T{t} (control anchors it)"


# --- hand-over to the next stage ----------------------------------------------------------


@pytest.mark.parametrize(("state", "t"), [("marked", 5), ("propagate", 1)])
def test_marking_sets_br_only_on_refinement_edge(state, t):
    """P1 / P2 output: BR=1 on the refinement edge of T{t}, nothing else; no re-application.

    ``R`` of T{t} is left to the author: no later stage reads it.
    """
    build, name = STATES[state]
    p = production(name)
    g = build()
    expected = g.copy()
    expected.nodes[re_bond(g, t)]["BR"] = 1
    assert p.apply(g)
    expected.nodes[t]["R"] = g.nodes[t]["R"]
    assert nx.utils.graphs_equal(g, expected), f"{name}: only BR of the RE bond of T{t} -> 1"
    assert not p.apply(g), f"{name} must not apply again (endless loop in the control)"


@pytest.mark.parametrize(
    ("build", "name", "parents"),
    [
        (boundary, "P4", (0,)),
        (shared, "P3", (7, 1)),
        (shared_flipped, "P3", (0, 1)),
    ],
    ids=["boundary", "shared", "shared-opposite-orientation"],
)
def test_bisection_leaves_fresh_conforming_children(build, name, parents):
    """P3 / P4 output: children from ``graph.bisect``, newest vertex = peak, ready for P1-P4."""
    p = production(name)
    g = build()
    total = sum(area(g, t) for t in cg.triangles(g))
    expected = {
        frozenset(c.vertices)
        for t in parents
        for c in cg.bisect(cg.vertices(g, t), g.nodes[re_bond(g, t)]["index"])
    }
    (newest,) = {cg.midpoint(*cg.side(g, re_bond(g, t))) for t in parents}
    old = set(cg.triangles(g))
    assert p.apply(g)
    new = set(cg.triangles(g)) - old
    assert not set(parents) & set(cg.triangles(g)), (
        f"{name}: remove parent triangles with graph.remove_triangle"
    )
    assert {frozenset(cg.vertices(g, t)) for t in new} == expected, f"{name}: child coordinates"
    check_mesh(g, total)
    for t in new:
        assert newest not in cg.side(g, re_bond(g, t)), f"{name}: newest vertex = child's peak"
        assert g.nodes[t]["R"] == 0, f"{name}: children start unmarked (R=0)"
        # In these states outer sides had BR=0, so inheriting BR on outer sides keeps BR=0.
        assert all(g.nodes[b]["BR"] == 0 for b in cg.bonds(g, t)), f"{name}: children need BR=0"
