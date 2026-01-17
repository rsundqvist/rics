from functools import partial

from docutils.nodes import Node
from sphinx.addnodes import toctree
from sphinx.ext.autosummary import Autosummary, autosummary_toc

_real = Autosummary.run


def patch(*, max_parents: int = 1) -> None:
    """Use shorter TOC tree entries.

    For example, with `max_parents=1`, a TOC title `'rics.collections.dicts'` will be replaced by `'collections.dicts'`.

    Args:
        max_parents: Maximum number of parent modules to show.
    """
    if max_parents < 0:
        raise ValueError(f"bad {max_parents=} < 0")

    if Autosummary.run is _real:
        Autosummary.run = partial(_hack, n=max_parents + 1)  #  type: ignore[method-assign]
        print("patch: Autosummary.run")


def _hack(self: Autosummary, n: int) -> list[Node]:
    nodes = _real(self)

    for node in nodes:
        if not isinstance(node, autosummary_toc):
            continue

        for child in node.children:
            if not isinstance(child, toctree):
                continue

            entries = child["entries"]

            for i, (original_title, ref) in enumerate(entries):
                if original_title is None and ref.count(".") >= n:
                    new_title = ".".join(ref.rsplit(".", n)[-n:])
                    entries[i] = (new_title, ref)

    return nodes
