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
