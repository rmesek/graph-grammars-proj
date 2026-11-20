"""P0: mark an element for refinement. Sections follow the README "Definition of Done".

Pattern for every production test: build ``expected`` by hand (a copy of the input plus
the RHS changes), apply, then ``nx.utils.graphs_equal`` checks nodes, edges, labels and all
attributes at once, so damage anywhere in a bigger graph is caught.
"""

import networkx as nx
import pytest
from matplotlib.colors import to_hex
from matplotlib.figure import Figure
from typer.testing import CliRunner

from nvb import graph as cg
from nvb import mesh, viz
from nvb.cli import app
from nvb.productions import PRODUCTIONS
from nvb.productions.p0 import P0, contains


def marked(g: nx.Graph, t: int) -> nx.Graph:
    """Expected RHS: copy of ``g`` with triangle ``t`` marked."""
    expected = g.copy()
    expected.nodes[t]["R"] = 1
    return expected


# --- LHS-isomorphic graph -------------------------------------------------------------


def test_applies_to_lhs_isomorphic_graph(triangle, viz_save):
    expected = marked(triangle, 0)
    viz_save(triangle, "before")
    assert P0().apply(triangle)
    viz_save(triangle, "after")
    assert nx.utils.graphs_equal(triangle, expected)


def test_rhs_is_complete(triangle):
    """One T node with R=1, three bonds 1..3 with untouched attributes and coordinates."""
    before = triangle.copy()
    P0().apply(triangle)
    (t,) = cg.triangles(triangle)
    assert triangle.nodes[t] == {**before.nodes[t], "R": 1}
    assert cg.vertices(triangle, t) == ((1, 0), (0, 1), (0, 0))
    assert [triangle.nodes[b]["index"] for b in cg.bonds(triangle, t)] == [1, 2, 3]
    for b in cg.bonds(triangle, t):
        assert triangle.nodes[b] == before.nodes[b]
    assert set(triangle.edges) == set(before.edges)


# --- wrong attributes / invalid LHS -----------------------------------------------------


def test_already_marked_is_not_applied(triangle):
    triangle.nodes[0]["R"] = 1
    before = triangle.copy()
    assert not P0().apply(triangle)
    assert nx.utils.graphs_equal(triangle, before)


def test_criterion_false_is_not_applied(triangle):
    assert not P0(contains((5, 5))).apply(triangle)
    assert triangle.nodes[0]["R"] == 0


def test_triangle_without_all_bonds_does_not_match(triangle):
    """Single-triangle LHS has no bond-bond edge; the analogue is a missing T-bond edge."""
    triangle.remove_edge(0, (0, 2))
    assert not list(P0().matches(triangle))


# --- LHS inside a bigger graph -----------------------------------------------------------


@pytest.mark.parametrize("t", range(16))
def test_anchored_in_bigger_graph_changes_only_target(t):
    g = mesh.square(2)
    expected = marked(g, t)
    assert P0().apply(g, at=t)
    assert nx.utils.graphs_equal(g, expected)  # rest untouched, embedding (bond-bond) kept


@pytest.mark.parametrize(("point", "t"), [((0.5, 0.1), 0), ((0.9, 0.5), 1), ((0.5, 0.9), 2)])
def test_criterion_selects_triangle_containing_point(square, point, t):
    expected = marked(square, t)
    assert P0(contains(point)).apply(square)
    assert nx.utils.graphs_equal(square, expected)


def test_each_triangle_is_marked_once(square):
    p0 = P0()
    while p0.apply(square):
        pass
    assert all(square.nodes[t]["R"] == 1 for t in cg.triangles(square))
    assert not p0.apply(square, at=0)


def test_contains_includes_boundary(square):
    assert contains((0.5, 0.5))(square, 0)  # shared vertex of all four triangles
    assert contains((0.5, 0))(square, 0)  # boundary side
    assert not contains((0.5, 0.9))(square, 0)


# --- drawing and CLI ------------------------------------------------------------------


def test_drawing_shows_mark(viz_save):
    g = mesh.square(2)
    viz_save(g, "before")
    P0().apply(g, at=5)
    viz_save(g, "after")
    ax = viz.draw(g, Figure().subplots())
    fills = [to_hex(p.get_facecolor()) for p in ax.patches]
    assert fills.count(viz.FILL[1]) == 1
    assert len(fills) == len(cg.triangles(g))
    assert len(ax.lines) == 3 * len(fills) + g.number_of_edges()  # sides + graph edges


def test_cli_applies_p0(tmp_path):
    out = tmp_path / "p0.png"
    result = CliRunner().invoke(app, ["apply", "P0", "--at", "2", "-o", str(out)])
    assert result.exit_code == 0, result.output
    assert "P0: applied" in result.output
    assert out.exists()


def test_registered():
    assert isinstance(PRODUCTIONS["P0"], P0)
