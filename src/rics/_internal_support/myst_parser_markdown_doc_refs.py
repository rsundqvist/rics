from typing import Any

from myst_parser.sphinx_ext.myst_refs import MystReferenceResolver
from sphinx.addnodes import pending_xref

_real = MystReferenceResolver.resolve_myst_ref_doc


def patch() -> None:
    if MystReferenceResolver.resolve_myst_ref_doc is _real:
        MystReferenceResolver.resolve_myst_ref_doc = _myst_parser_markdown_doc_refs  # type: ignore[method-assign]
        print("patch: MystReferenceResolver.resolve_myst_ref_doc")


def _myst_parser_markdown_doc_refs(self: MystReferenceResolver, node: pending_xref) -> Any:
    ref_docname: str = node["reftarget"]
    prefix, _, name = ref_docname.rpartition("/")

    if prefix and name in {"LICENSE", "CONTRIBUTING", "CODE_OF_CONDUCT"}:
        node["reftarget"] = name

    return _real(self, node)
