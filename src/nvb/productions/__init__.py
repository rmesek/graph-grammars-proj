"""Production registry used by the CLI. Implement ``pN.py`` and register it below."""

from nvb.productions.base import Production
from nvb.productions.p0 import P0

PRODUCTIONS: dict[str, Production] = {
    "P0": P0(),
}
