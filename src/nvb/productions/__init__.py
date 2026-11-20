"""Production registry used by the CLI. Implement ``pN.py`` and register it below."""

from nvb.productions.base import Production

PRODUCTIONS: dict[str, Production] = {
    # "P0": P0(),
}
