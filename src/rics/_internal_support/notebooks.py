import shutil
from pathlib import Path


def copy_notebooks(source: str | Path, destination: str | Path, *, clean: bool = True) -> None:
    """Copy the `source` directory to `destination`, optionally stripping notebook metadata in the copy.

    Args:
        source: Directory to copy.
        destination: Target directory; existing files are overwritten.
        clean: If ``True``, call :func:`strip_metadata` on every ``.ipynb`` file in `destination` after copying.
    """
    shutil.copytree(source, destination, dirs_exist_ok=True)
    if clean:
        for path in Path(destination).rglob("*.ipynb"):
            strip_metadata(path)


def strip_metadata(path: str | Path) -> None:
    """Strip volatile cell metadata from the notebook at `path`, in place.

    Removes the ``execution`` timing metadata.

    Args:
        path: Path to an ``.ipynb`` file.
    """
    import nbformat

    notebook = nbformat.read(path, as_version=nbformat.NO_CONVERT)

    for cell in notebook.cells:
        cell.metadata.pop("execution", None)

    nbformat.write(notebook, path)
