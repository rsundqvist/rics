"""Miscellaneous utility methods for Python applications."""
import os
from datetime import timedelta
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Optional, Type, Union

from rics._internal_support import local_or_remote
from rics._internal_support.types import NO_DEFAULT, NoDefault, PathLikeType
from rics.utility.strings import without_prefix


def tname(arg: Optional[Union[Type[Any], Any, Callable]]) -> str:
    """Get name of method or class.

    Args:
        arg: Something get a name for.

    Returns:
        A type name.
    """
    if arg is None:
        return "None"  # pragma: no cover
    if isinstance(arg, type):
        return arg.__name__
    if hasattr(arg, "__class__") and not callable(arg):
        return arg.__class__.__name__

    return arg.__name__ if hasattr(arg, "__name__") else arg.__class__.__name__


def format_perf_counter(start: float, end: float = None) -> str:
    """Format performance counter output.

    This function formats performance counter output based on the time elapsed. For ``t < 60 sec``, accuracy is
    increased whereas for durations above one minute a more user-friendly formatting is used.

    Args:
        start: Start time.
        end: End time. Set to now if not given.

    Returns:
        A formatted performance counter time.

    Examples:
        >>> from rics.utility.misc import format_perf_counter
        >>> format_perf_counter(0, 3131)  # 3131 seconds is about 52 minutes.
        '0:52:11'
        >>> format_perf_counter(0, 0.154)
        '0.154 sec'

    See Also:
        :py:func:`time.perf_counter`
    """
    t = (end or perf_counter()) - start
    if t < 1.0:
        return f"{t:.6g} sec"
    if t < 60.0:
        return f"{t:.2f} sec"
    else:
        return str(timedelta(seconds=round(t)))


def get_local_or_remote(
    file: PathLikeType,
    local_root: PathLikeType,
    remote_root: PathLikeType = None,
    force: bool = False,
    postprocessor: Callable[[str], Any] = None,
    show_progress: bool = local_or_remote.TQDM_INSTALLED,
) -> Path:
    r"""Retrieve the path of a local file, downloading it if needed.

    If `file` is not available at the local root path, it will be downloaded using `requests.get`_. A postprocessor may
    be given in which case the name of the final file will be ``<local_root>/<name-of-postprocessor>/file``. Removing
    a raw local file will invalidate postprocessed files.

    Args:
        file: A file to retrieve or download.
        local_root: Local directory where the file may be cached.
        remote_root: Remote URL where the data may be retrieved using ``requests.get``.
        force: If True, always download and apply processing (if applicable). Existing files will be overwritten.
        postprocessor: A function which takes a single argument `input_path` and returns a pickleable type.
        show_progress: If True, show a progress bar. Requires the `tqdm`_ package.

    Returns:
        An absolute path to the data.

    Raises:
        ValueError: If local root path does not exist or is not a directory.
        ValueError: If the local file does not exist and ``remote==None``.
        ModuleNotFoundError: If the ``tqdm`` package is not installed but ``show_progress==True``.

    Notes:
        This function is meant for **manual** work. Downloads may fail and data may become corrupt. There is no handling
        for this, so it does not belong in a pipeline.

    .. _requests.get:
        https://2.python-requests.org/en/master/api/#requests.get
    .. _tqdm:
        https://pypi.org/project/tqdm/
    """
    return local_or_remote.get(
        file=file,
        local_root=local_root,
        remote_root=remote_root,
        force=force,
        postprocessor=postprocessor,
        show_progress=show_progress,
    )


def read_env_or_literal(
    arg: str,
    default: Union[NoDefault, str] = NO_DEFAULT,
    env_marker: str = "@",
) -> str:
    """Read an environment variable if `arg` if prefixed by `env_marker`, otherwise return `arg` as-is.

    Args:
        arg: A literal value or environment variable to read.
        env_marker: A prefix which indicates that `arg` should be interpreted as environment variable name.
        default: Default value to use if the variable denoted by `arg` doesn't exist.

    Returns:
        A processed version `arg` where the final response is ``ans_type(processed-arg)``.

    Raises:
        ValueError: If `arg` does not start with `env_marker` and `enforce_env_var` is True.

    Notes:
        The constructor of `desired_return_type` may raise errors not listed here.
    """
    if not arg.startswith(env_marker):
        return arg

    env_var_name = without_prefix(arg, env_marker)
    return os.environ[env_var_name] if default == NO_DEFAULT else os.environ.get(env_var_name, default)


def serializable(obj: Any) -> bool:
    """Check if `obj` is serializable using Pickle.

    Serializes to memory for speed.

    Args:
        obj: An object to attempt to serialize.

    Returns:
        True if `obj` was pickled without issues.
    """
    import io
    import pickle  # noqa: S403

    bio = io.BytesIO()
    try:
        pickle.dump(obj, bio)
        return True
    except Exception:  # noqa: B902
        return False
