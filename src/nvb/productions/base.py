"""Base class of all productions: LHS pattern + applicability predicate + transformation.

A match ``m`` maps pattern nodes to host nodes: triangle ``k`` (0, 1, ...) and its bonds
``(k, 1)``, ``(k, 2)``, ``(k, 3)``. On two-triangle slides, bonds 4,5,6 map to ``(0, 1..3)``
and 1,2,3 to ``(1, 1..3)``. Pattern bond numbers are free (any host bond may match bond 1);
for geometry (e.g. ``bisect``) always read the host bond's ``g.nodes[bond]["index"]``.
"""

from abc import ABC, abstractmethod
from collections.abc import Hashable, Iterator, Sequence
from typing import ClassVar

import networkx as nx
from networkx.algorithms.isomorphism import GraphMatcher

from nvb.graph import BOND, INDICES, T

type Match = dict[Hashable, Hashable]

# T -> bond -> bond -> T -> bond: everything a two-triangle pattern can touch.
_RADIUS = 4


def pattern(n: int, links: Sequence[tuple[tuple[int, int], tuple[int, int]]] = ()) -> nx.Graph:
    """LHS graph with ``n`` triangles; ``links`` connect bonds, e.g. ``[((0, 3), (1, 1))]``."""
    p = nx.Graph()
    for k in range(n):
        p.add_node(k, label=T)
        for i in INDICES:
            p.add_node((k, i), label=BOND)
            p.add_edge(k, (k, i))
    p.add_edges_from(links)
    return p


class Production(ABC):
    name: ClassVar[str]
    lhs: ClassVar[nx.Graph]

    def predicate(self, g: nx.Graph, m: Match) -> bool:
        """Applicability predicate on attributes of the matched host nodes."""
        return True

    @abstractmethod
    def transform(self, g: nx.Graph, m: Match) -> None:
        """Rewrite ``g`` in place for match ``m`` (LHS -> RHS, keep embedding)."""

    def matches(self, g: nx.Graph, at: Hashable | None = None) -> Iterator[Match]:
        """Yield matches satisfying the predicate; ``at`` restricts them to contain that node."""
        if at is not None and at not in g:
            return
        host = g if at is None else g.subgraph(nx.ego_graph(g, at, radius=_RADIUS))
        gm = GraphMatcher(host, self.lhs, node_match=lambda h, p: h["label"] == p["label"])
        for host_to_lhs in gm.subgraph_monomorphisms_iter():
            m = {p: h for h, p in host_to_lhs.items()}
            if (at is None or at in host_to_lhs) and self.predicate(g, m):
                yield m

    def apply(self, g: nx.Graph, at: Hashable | None = None) -> bool:
        """Apply to the first match (optionally anchored at node ``at``); ``False`` if none."""
        if (m := next(self.matches(g, at), None)) is None:
            return False
        self.transform(g, m)
        return True
