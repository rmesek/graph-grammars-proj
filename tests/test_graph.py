import networkx as nx

from nvb import graph as cg
from nvb import mesh


def test_add_triangle_creates_node_with_three_bonds():
    g = nx.Graph()
    t = cg.add_triangle(g, (0, 0), (1, 0), (0, 1), re=(1, 0, 0))
    assert g.nodes[t]["label"] == cg.T
    assert [g.nodes[b]["index"] for b in cg.bonds(g, t)] == [1, 2, 3]
    assert g.nodes[(t, 1)]["RE"] == 1
    assert cg.side(g, (t, 1)) == ((1, 0), (0, 1))  # bond i is opposite vertex Pi


def test_triangle_fixture_refinement_edge_is_hypotenuse(triangle):
    (t,) = cg.triangles(triangle)
    re = [b for b in cg.bonds(triangle, t) if triangle.nodes[b]["RE"]]
    assert len(re) == 1
    assert cg.distance(*cg.side(triangle, re[0])) == max(
        cg.distance(*cg.side(triangle, b)) for b in cg.bonds(triangle, t)
    )
    assert all(triangle.nodes[b]["B"] for b in cg.bonds(triangle, t))


def test_square_mesh_structure(square):
    assert len(cg.triangles(square)) == 4
    shared = [e for e in square.edges if all(square.nodes[n]["label"] == cg.BOND for n in e)]
    assert len(shared) == 4
    for t in cg.triangles(square):
        (re,) = [b for b in cg.bonds(square, t) if square.nodes[b]["RE"]]
        assert square.nodes[re]["B"] == 1  # compatibly divisible: RE on the boundary


def test_bigger_square_connects_cells():
    g = mesh.square(2)
    assert len(cg.triangles(g)) == 16
    boundary = [n for n, b in g.nodes(data="B") if b == 1]
    assert len(boundary) == 8
    assert all(cg.neighbour(g, b) is None for b in boundary)


def test_rewire_moves_connection():
    g = mesh.square(1)
    t_old = 0
    bond = next(b for b in cg.bonds(g, t_old) if cg.neighbour(g, b))
    other = cg.neighbour(g, bond)
    t_new = cg.add_triangle(g, *cg.vertices(g, t_old))
    cg.rewire(g, bond, (t_new, 1))
    cg.remove_triangle(g, t_old)
    assert cg.neighbour(g, (t_new, 1)) == other
    assert t_old not in g


def test_bisect_children_follow_bond_convention():
    p = ((0, 0), (2, 0), (0, 2))
    c1, c2 = cg.bisect(p, ref=1)
    assert c1.vertices == ((1, 1), (0, 0), (2, 0))
    assert c2.vertices == ((1, 1), (0, 0), (0, 2))
    g = nx.Graph()
    parent = cg.add_triangle(g, *p)
    refinement_edge = set(cg.side(g, (parent, 1)))
    for c in (c1, c2):
        t = cg.add_triangle(g, *c.vertices)
        assert set(cg.side(g, (t, 1))) == set(cg.side(g, (parent, c.outer)))
        half = set(cg.side(g, (t, 2)))
        assert (1, 1) in half and len(half & refinement_edge) == 1
        assert set(cg.side(g, (t, 3))) == {(1, 1), (0, 0)}  # interior side: newest vertex-peak
