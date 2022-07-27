import shutil
from pathlib import Path
from typing import Dict, List

from rics._internal_support.changelog._patch_notes import PatchNotes
from rics._internal_support.types import PathLikeType

BASE_LINES: List[str] = [
    "Changelog",
    "=========",
    "All notable changes to this project will be documented in this file.",
    "The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_",
    "and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.",
    "",
    ".. toctree::",
    "   :hidden:",
    "",
]


def write_changelog(
    output_dir: PathLikeType,
    notes: List[PatchNotes],
    refs: Dict[str, str],
) -> None:
    """Write changelog parts to several pages in an output directory.

    Args:
        output_dir: Output directory where pages will be placed. Only ``index.rst`` needs to be manually imported.
        notes: A list of patch notes, in the order in which they should be added to the TOC.
        refs: Title references.
    """
    root = Path(str(output_dir))
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir()

    index_lines = BASE_LINES.copy()

    for note in notes:
        page = note.title.replace("[", "").replace("]", "").replace("#", "").lower().strip()
        index_lines.append(f"   {page}")
        file = root.joinpath(f"{page}.md")
        lines = ["# " + note.title + (f" ({note.date})" if note.date else "")]

        if note.extras:
            lines.extend(note.extras)
            lines.append("")

        for section, l in note.sections.items():
            lines.append("## " + section)
            lines.extend(l)

        lines.append("\n" + refs[note.title])
        file.write_text("\n".join(lines))

    root.joinpath("index.rst").write_text("\n".join(index_lines))
