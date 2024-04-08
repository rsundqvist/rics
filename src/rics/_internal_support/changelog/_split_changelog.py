from pathlib import Path

from rics.paths import AnyPath

from ._patch_notes import PatchNotes
from ._write_changelog import write_changelog


def split_changelog(output_dir: AnyPath, changelog: AnyPath = "CHANGELOG.md") -> None:
    """Split a Markdown changelog into multiple pages.

    Args:
        output_dir: Output directory where pages will be placed. Only ``index.rst`` needs to be manually imported.
        changelog: The changelog to split.

    """
    with Path(changelog).open() as f:
        notes, refs = PatchNotes.from_markdown(f.read())

    write_changelog(output_dir, notes, refs)
