"""Production registry used by the CLI.

Every module ``pN.py`` in this package must define class ``PN``; it is registered here
automatically, so adding a production never edits this file (no merge conflicts).
"""

import importlib
import pkgutil
import re

from nvb.productions.base import Production

PRODUCTIONS: dict[str, Production] = {
    m.name.upper(): getattr(importlib.import_module(f"{__name__}.{m.name}"), m.name.upper())()
    for m in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name)
    if re.fullmatch(r"p\d+", m.name)
}
