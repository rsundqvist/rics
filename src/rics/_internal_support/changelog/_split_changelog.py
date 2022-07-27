from rics._internal_support.changelog._patch_notes import PatchNotes
from rics._internal_support.changelog._write_changelog import write_changelog
from rics._internal_support.types import PathLikeType


def split_changelog(output_dir: PathLikeType, changelog: PathLikeType = "CHANGELOG.md") -> None:
    """Split a Markdown changelog into multiple pages.

    Args:
        output_dir: Output directory where pages will be placed. Only ``index.rst`` needs to be manually imported.
        changelog: The changelog to split.
    """
    with open(changelog) as f:
        notes, refs = PatchNotes.from_markdown(f.read())

    write_changelog(output_dir, notes, refs)
