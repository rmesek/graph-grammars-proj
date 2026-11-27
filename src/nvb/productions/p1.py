"""P1 (slide 21): mark the refinement edge of an element marked for refinement.

LHS: one triangle. Predicate: ``R1 == 1 and BR1 == BR2 == BR3 == 0 and RE1 == 1``. RHS: the
same graph with ``BR1 = 1``. Pattern bond 1 matches whichever host bond is the refinement
edge, so the host ``index`` is never read. No node, edge or coordinate changes, so the
embedding stays untouched. ``R`` is not drawn on the slide's RHS and stays 1.
"""

import networkx as nx

from nvb.graph import INDICES
from nvb.productions.base import Match, Production, pattern


class P1(Production):
    """Mark the refinement edge of a marked element: R==1, BR1..3==0, RE1==1 -> BR1=1."""

    name = "P1"
    lhs = pattern(1)

    def predicate(self, g: nx.Graph, m: Match) -> bool:
        bonds = [g.nodes[m[(0, i)]] for i in INDICES]
        return g.nodes[m[0]]["R"] == 1 and all(b["BR"] == 0 for b in bonds) and bonds[0]["RE"] == 1

    def transform(self, g: nx.Graph, m: Match) -> None:
        g.nodes[m[(0, 1)]]["BR"] = 1
