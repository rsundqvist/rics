import logging
import pickle  # noqa: S403
from pathlib import Path
from typing import Any, BinaryIO, Callable, Iterable, Optional
from urllib.parse import urljoin

from rics._internal_support.types import PathLikeType

try:
    from tqdm.auto import tqdm

    TQDM_INSTALLED = True
except ModuleNotFoundError:
    TQDM_INSTALLED = False

_CHUNK_SIZE: int = 1024

LOGGER = logging.getLogger("rics.utility.misc")
_GLOR_LOGGER = LOGGER.getChild("get_local_or_remote")


def get(
    file: PathLikeType,
    remote_root: PathLikeType,
    local_root: PathLikeType,
    force: bool = False,
    postprocessor: Callable[[str], Any] = None,
    show_progress: bool = TQDM_INSTALLED,
) -> Path:
    """Retrieve the path of a local file, downloading it if needed."""
    if show_progress and not TQDM_INSTALLED:
        raise ModuleNotFoundError("The tqdm package is not installed; cannot show progress.")

    return _get_file(
        file=str(file),
        remote_root=str(remote_root),
        local_root=Path(str(local_root)).absolute(),
        force=force,
        postprocessor=postprocessor,
        show_progress=show_progress,
    )


def _get_file(
    file: str,
    remote_root: str,
    local_root: Path,
    force: bool,
    postprocessor: Optional[Callable[[str], Any]],
    show_progress: bool,
) -> Path:
    local_file_path = local_root.joinpath(file)
    remote_file_path = None if remote_root is None else urljoin(remote_root, file)

    _GLOR_LOGGER.debug(f"Local file path: '{local_file_path}'.")
    _GLOR_LOGGER.debug(f"Remote file path: '{remote_file_path}'.")

    if not local_root.is_dir():
        raise ValueError(f"Local root path '{local_root}' does not exist or is not a directory.")

    need_postprocessing = False
    if force or not local_file_path.exists():
        if remote_file_path is None:
            raise ValueError(f"Local file does not exist: '{local_file_path}'.")
        _fetch(local_file_path, remote_file_path, show_progress)
        if postprocessor is not None:
            need_postprocessing = True

    if postprocessor is not None:
        local_processed_file_path = local_root.joinpath(postprocessor.__name__).joinpath(file).with_suffix(".pkl")
        _GLOR_LOGGER.info(f"Local processed file path: '{local_processed_file_path}'.")
        need_postprocessing = need_postprocessing or not local_processed_file_path.exists()
        if force or need_postprocessing:
            local_processed_file_path.parent.mkdir(parents=True, exist_ok=True)
            _GLOR_LOGGER.info(f"Running {postprocessor.__name__}..")
            result = postprocessor(str(local_file_path))
            _GLOR_LOGGER.info(f"Serializing processed data to '{local_processed_file_path}'..")
            with open(local_processed_file_path, "wb") as f:
                pickle.dump(result, f)

        return local_processed_file_path
    else:
        return local_file_path


def _fetch(local_file_path: Path, remote_file_path: str, show_progress: bool) -> None:
    try:
        import requests
    except ModuleNotFoundError:
        raise ModuleNotFoundError("The requests package is not installed; cannot download remote content.")

    _GLOR_LOGGER.info(f"Fetching data from '{remote_file_path}'..")
    response = requests.get(remote_file_path, stream=True)
    chunks = response.iter_content(_CHUNK_SIZE)
    with open(local_file_path, "wb") as output_file:
        if show_progress:
            total = response.headers.get("Content-Length")
            _with_progress(chunks, output_file, remote_file_path, total=None if not total else int(total))
        else:
            _without_progress(chunks, output_file)


def _without_progress(chunks: Iterable[bytes], output_file: BinaryIO) -> None:
    for chunk in chunks:
        if chunk:
            output_file.write(chunk)


def _with_progress(chunks: Iterable[bytes], output_file: BinaryIO, remote_file_path: str, total: Optional[int]) -> None:
    kwargs = {
        "total": total,
        "desc": str(remote_file_path),
        "unit": "iB",
        "unit_scale": True,
        "unit_divisor": _CHUNK_SIZE,
    }
    with tqdm(chunks, **kwargs) as progress:
        for chunk in chunks:
            if chunk:
                output_file.write(chunk)
                progress.update(_CHUNK_SIZE)
        if total is not None:
            progress.n = total
