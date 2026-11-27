import pytest
from matplotlib.figure import Figure
from typer.testing import CliRunner

from nvb import graph as cg
from nvb import mesh, viz
from nvb.cli import app


def test_save_writes_png(square, tmp_path):
    path = viz.save(square, tmp_path / "g.png")
    assert path.read_bytes().startswith(b"\x89PNG")


@pytest.mark.parametrize(("n", "graph"), [(2, True), (5, False)])
def test_cp_graph_drawn_only_for_small_meshes_by_default(n, graph):
    g = mesh.square(n)  # 16 and 100 triangles
    ax = viz.draw(g, Figure().subplots())
    sides = 3 * len(cg.triangles(g))
    assert len(ax.lines) == sides + (g.number_of_edges() if graph else 0)
    assert len(ax.texts) == (len(cg.triangles(g)) if graph else 0)  # T labels
    assert len(ax.patches) == len(cg.triangles(g))  # attributes are always drawn


def test_graph_flag_overrides_default():
    g = mesh.square(5)
    assert len(viz.draw(g, Figure().subplots(), graph=True).texts) == len(cg.triangles(g))
    assert not viz.draw(mesh.square(1), Figure().subplots(), graph=False).texts


def test_cli_draw(tmp_path):
    out = tmp_path / "mesh.png"
    result = CliRunner().invoke(app, ["draw", "-n", "8", "--no-graph", "-o", str(out)])
    assert result.exit_code == 0, result.output
    assert out.exists()


def test_cli_apply_rejects_unknown_production(tmp_path):
    result = CliRunner().invoke(app, ["apply", "NOPE", "-o", str(tmp_path / "x.png")])
    assert result.exit_code != 0


def legend_rows(ax) -> list[str]:
    return [t.get_text() for t in ax.get_legend().get_texts() if t.get_text()]


def test_legend_groups_graph_element_and_edge():
    rows = legend_rows(viz.draw(mesh.square(1), Figure().subplots()))
    assert rows[:3] == ["$\\bf{Graph\\ structure}$", "(node T or bond)", "(id of node T)"]
    assert "R==1 (element to refine)" in rows
    assert "RE==1 and B==1 (refinement and boundary edge)" in rows
    assert rows[-1] == "BR==1 (edge to be broken)"


def test_legend_without_cp_graph_drops_graph_group():
    rows = legend_rows(viz.draw(mesh.square(1), Figure().subplots(), graph=False))
    assert rows[0] == "$\\bf{Element\\ (node\\ T)}$"
    assert not any("node T or bond" in r or "id of node T" in r for r in rows)
    assert len(rows) == 9  # Element: header + 2, Edge: header + 5


def test_triangle_id_sits_towards_the_peak():
    g = mesh.square(1)  # T0: P3 = (0.5, 0.5) is the peak (RE is the bottom side)
    (label,) = [t for t in viz.draw(g, Figure().subplots()).texts if t.get_text() == "T0"]
    x, y = label.get_position()
    assert x == pytest.approx(0.5) and y > 1 / 6  # above the centroid (0.5, 1/6)
