"""P1: mark the refinement edge of a marked element. Sections follow the README "Definition
of Done".
"""

import networkx as nx
import pytest
from matplotlib.axes import Axes
from matplotlib.colors import to_hex
from matplotlib.figure import Figure
from typer.testing import CliRunner

from nvb import graph as cg
from nvb import mesh, viz
from nvb.cli import app
from nvb.productions import PRODUCTIONS
from nvb.productions.p1 import P1


def re_bond(g: nx.Graph, t: int) -> cg.Bond:
    (b,) = [b for b in cg.bonds(g, t) if g.nodes[b]["RE"]]
    return b


def marked(g: nx.Graph, t: int) -> nx.Graph:
    """State after P0 on ``t`` (in place): R=1."""
    g.nodes[t]["R"] = 1
    return g


def broken(g: nx.Graph, t: int) -> nx.Graph:
    """Expected RHS: copy of ``g`` with BR=1 on the refinement edge of ``t``."""
    expected = g.copy()
    expected.nodes[re_bond(g, t)]["BR"] = 1
    return expected


def dashed(ax: Axes) -> list:
    return [line for line in ax.lines if line.get_linestyle() == "--"]


@pytest.fixture
def lhs(triangle) -> nx.Graph:
    """Single triangle marked by P0; RE = hypotenuse (bond 3), all BR=0."""
    return marked(triangle, 0)


# --- LHS-isomorphic graph -------------------------------------------------------------


def test_applies_to_lhs_isomorphic_graph(lhs, viz_save):
    expected = broken(lhs, 0)
    viz_save(lhs, "before")
    assert P1().apply(lhs)
    viz_save(lhs, "after")
    assert nx.utils.graphs_equal(lhs, expected)


@pytest.mark.parametrize("ref", cg.INDICES)
def test_marks_refinement_edge_whatever_its_index(ref):
    """Pattern bond 1 is the host bond with RE=1, whichever index it has."""
    g = marked(mesh.from_triangles([(0, 0), (1, 0), (0, 1)], [(1, 2, 0)], [ref]), 0)
    assert P1().apply(g)
    assert [g.nodes[b]["BR"] for b in cg.bonds(g, 0)] == [int(i == ref) for i in cg.INDICES]


def test_rhs_is_complete(lhs):
    """One T node (R=1, same coordinates), bonds 1..3; only BR of the RE bond changes."""
    before = lhs.copy()
    P1().apply(lhs)
    (t,) = cg.triangles(lhs)
    assert lhs.nodes[t] == before.nodes[t]
    assert lhs.nodes[t]["R"] == 1
    assert cg.vertices(lhs, t) == ((1, 0), (0, 1), (0, 0))
    assert [lhs.nodes[b]["index"] for b in cg.bonds(lhs, t)] == [1, 2, 3]
    assert lhs.nodes[(t, 3)] == {**before.nodes[(t, 3)], "BR": 1}
    for b in [(t, 1), (t, 2)]:
        assert lhs.nodes[b] == before.nodes[b]
    assert set(lhs.nodes) == set(before.nodes)
    assert set(lhs.edges) == set(before.edges)


# --- wrong attributes / invalid LHS -----------------------------------------------------


def assert_not_applied(g: nx.Graph) -> None:
    before = g.copy()
    assert not P1().apply(g)
    assert nx.utils.graphs_equal(g, before)


def test_unmarked_triangle_is_not_applied(triangle):
    assert_not_applied(triangle)  # R=0


@pytest.mark.parametrize("i", cg.INDICES)
def test_any_side_already_broken_is_not_applied(lhs, i):
    lhs.nodes[(0, i)]["BR"] = 1
    assert_not_applied(lhs)


def test_triangle_without_refinement_edge_is_not_applied(lhs):
    lhs.nodes[(0, 3)]["RE"] = 0
    assert_not_applied(lhs)


def test_is_not_applied_twice(lhs):
    assert P1().apply(lhs)
    assert_not_applied(lhs)


@pytest.mark.parametrize("i", cg.INDICES)
def test_triangle_without_all_bonds_does_not_match(lhs, i):
    """Single-triangle LHS has no bond-bond edge; the analogue is a missing T-bond edge."""
    lhs.remove_edge(0, (0, i))
    assert not list(P1().matches(lhs))


# --- LHS inside a bigger graph -----------------------------------------------------------


@pytest.mark.parametrize("t", range(16))
def test_anchored_in_bigger_graph_changes_only_target(t):
    g = marked(mesh.square(2), t)
    expected = broken(g, t)
    assert P1().apply(g, at=t)
    assert nx.utils.graphs_equal(g, expected)  # rest untouched, embedding (bond-bond) kept


def test_finds_the_marked_triangle_in_bigger_graph():
    g = marked(mesh.square(2), 5)
    expected = broken(g, 5)
    assert not P1().apply(g, at=4)  # unmarked neighbour
    assert P1().apply(g)
    assert nx.utils.graphs_equal(g, expected)


def test_every_marked_triangle_gets_only_its_refinement_edge_broken():
    g = mesh.square(2)
    for t in cg.triangles(g):
        marked(g, t)
    p1, applied = P1(), 0
    while p1.apply(g):
        applied += 1
    assert applied == len(cg.triangles(g))  # once per triangle, then it stops
    for t in cg.triangles(g):
        assert all(g.nodes[b]["BR"] == g.nodes[b]["RE"] for b in cg.bonds(g, t))


# --- drawing and CLI ------------------------------------------------------------------


def test_drawing_shows_broken_refinement_edge(viz_save):
    g = marked(mesh.square(2), 5)
    viz_save(g, "before")
    assert not dashed(viz.draw(g, Figure().subplots()))
    P1().apply(g, at=5)
    viz_save(g, "after")
    ax = viz.draw(g, Figure().subplots())
    (line,) = dashed(ax)
    assert to_hex(line.get_color()) == to_hex("tab:red")  # the RE side is the dashed one
    assert len(ax.lines) == 3 * len(cg.triangles(g)) + g.number_of_edges()  # sides + edges
    assert len(ax.collections[0].get_offsets()) == g.number_of_nodes()  # all T + bond nodes
    assert len(ax.texts) == len(cg.triangles(g))  # T labels
    assert [to_hex(p.get_facecolor()) for p in ax.patches].count(viz.FILL[1]) == 1  # R=1


def test_cli_applies_p1_after_p0(tmp_path):
    out = tmp_path / "p1.png"
    result = CliRunner().invoke(app, ["apply", "P0", "P1", "--at", "2", "-o", str(out)])
    assert result.exit_code == 0, result.output
    assert "P0: applied" in result.output
    assert "P1: applied" in result.output
    assert out.exists()


def test_cli_p1_needs_marked_element(tmp_path):
    result = CliRunner().invoke(app, ["apply", "P1", "--at", "2", "-o", str(tmp_path / "x.png")])
    assert result.exit_code == 0, result.output
    assert "P1: no match" in result.output


def test_registered():
    assert isinstance(PRODUCTIONS["P1"], P1)
