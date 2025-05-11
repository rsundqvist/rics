import os
import sys
from datetime import UTC, datetime
from getpass import getuser
from typing import Any, Literal, NotRequired, TypedDict

from rics import __version__


class KernelSpec(TypedDict):
    """Simplified `kernel.json` type. See the `Jupyter kernel documentation`_ for details.

    .. _Jupyter kernel documentation: https://jupyter-client.readthedocs.io/en/stable/kernels.html#kernel-specs
    """

    argv: list[str]
    display_name: str
    language: Literal["python"]
    metadata: dict[str, Any]
    env: NotRequired[dict[str, str]]


def set_metadata(metadata: dict[str, Any]) -> None:
    """Set kernelspec metadata."""
    metadata["created_at"] = datetime.now(UTC).replace(microsecond=0).isoformat()
    metadata["created_by"] = getuser()

    metadata["installer"] = {
        "version": __version__,
        "sys.executable": sys.executable,
        "sys.version": sys.version,
        "workdir": os.getcwd(),  # noqa: PTH109
    }
