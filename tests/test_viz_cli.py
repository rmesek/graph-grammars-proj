from typer.testing import CliRunner

from nvb import viz
from nvb.cli import app


def test_save_writes_png(square, tmp_path):
    path = viz.save(square, tmp_path / "g.png")
    assert path.read_bytes().startswith(b"\x89PNG")


def test_cli_draw(tmp_path):
    out = tmp_path / "mesh.png"
    result = CliRunner().invoke(app, ["draw", "-n", "2", "-o", str(out)])
    assert result.exit_code == 0, result.output
    assert out.exists()


def test_cli_apply_rejects_unknown_production(tmp_path):
    result = CliRunner().invoke(app, ["apply", "NOPE", "-o", str(tmp_path / "x.png")])
    assert result.exit_code != 0
