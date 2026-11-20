"""Shared fixtures. ``uv run pytest --viz`` saves drawings from ``viz_save`` to out/tests."""

import re
from pathlib import Path

import networkx as nx
import pytest

from nvb import mesh, viz


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--viz", action="store_true", help="save graph drawings to out/tests")


@pytest.fixture
def viz_save(request: pytest.FixtureRequest):
    """Call ``viz_save(g, "before")`` in a test; no-op unless run with ``--viz``."""

    def save(g: nx.Graph, tag: str) -> None:
        if request.config.getoption("--viz"):
            safe = re.sub(r'[<>:"/\\|?*]', "_", request.node.name)
            path = Path("out/tests") / request.path.stem / f"{safe}-{tag}.png"
            viz.save(g, path, title=tag)

    return save


@pytest.fixture
def triangle() -> nx.Graph:
    """Single right triangle, all sides on the boundary, RE = hypotenuse (bond 3)."""
    return mesh.from_triangles([(0, 0), (1, 0), (0, 1)], [(1, 2, 0)])


@pytest.fixture
def square() -> nx.Graph:
    """Unit square split by both diagonals: 4 triangles, RE on the boundary."""
    return mesh.square(1)
