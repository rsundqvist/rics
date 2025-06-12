import logging
import os
import subprocess
import sys
import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Any

from rics.logs import get_logger

Resolver = Callable[[Path, logging.Logger], tuple[str, str] | None]


class VenvHelper:
    """Helper class for working with virtual environments."""

    def __init__(
        self,
        logger: logging.Logger | str = __package__ + ".VenvHelper",
    ) -> None:
        self.logger = get_logger(logger)

        manager, exec_prefix, executable = self.resolve()
        self._manager = manager
        self.exec_prefix = exec_prefix
        self.executable = executable
        self.config_path = Path(self.exec_prefix) / "pyvenv.cfg"
        self._config = self._read_pyvenv_cfg()

    @property
    def manager(self) -> str:
        """Manager name."""
        return self._manager

    @property
    def config(self) -> dict[str, Any]:
        """Parsed `pyvenv.cfg` dict."""
        return {**self._config}

    @property
    def slug(self) -> str:
        """Virtual environment slug. Typically, the shell prompt."""
        return self._config.get("prompt") or self.config_path.parent.parent.name

    def resolve(self) -> tuple[str, str, str]:
        """Resolve venv paths.

        Returns:
            A tuple ``(name, exec_prefix, executable)``.
        """
        logger = self.logger.getChild("resolve")

        resolvers: list[Resolver] = [Resolve.poetry, Resolve.uv, Resolve.sys]
        logger.debug(f"Resolver order ({len(resolvers)}): {' | '.join(r.__name__ for r in resolvers)}.")

        cwd = Path.cwd()
        for i, resolver in enumerate(resolvers, start=1):
            name = resolver.__name__
            msg = f"Resolver {i}/{len(resolvers)}: {name}(): %s."
            logger.debug(msg, "Starting")
            result = resolver(cwd, logger)

            if result:
                logger.debug(msg, f"succeeded with {result=}")
                return name, *result

            logger.debug(msg, "Failed")

        raise RuntimeError("exec resolution failed")

    def _read_pyvenv_cfg(self) -> dict[str, str]:
        self.logger.debug("Reading pyvenv.cfg for manager='%s': '%s'.", self.manager, self.config_path)
        if not self.config_path.is_file():
            msg = f"Not a virtualenv: '{self.exec_prefix}'."
            raise RuntimeError(msg)

        lines = self.config_path.read_text().splitlines()
        rv = {key: value for key, value in map(self._convert_pyenvcfg_line, lines)}
        self.logger.debug("Found %i keys in pyvenv.cfg: %s.", len(rv), [*rv])
        return rv

    @classmethod
    def _convert_pyenvcfg_line(cls, line: str) -> tuple[str, str]:
        key, _, value = line.partition(" = ")
        return key, value


class Resolve:
    """Get ``(exec_prefix, executable)``-tuples for various package managers."""

    @classmethod
    def poetry(cls, cwd: Path, logger: logging.Logger) -> tuple[str, str] | None:
        """Implementation for https://github.com/python-poetry/poetry."""
        if not _check_files(cwd, "poetry", logger):
            return None

        return _print_paths(logger, "poetry", "run", "python")

    @classmethod
    def uv(cls, cwd: Path, logger: logging.Logger) -> tuple[str, str] | None:
        """Implementation for https://github.com/astral-sh/uv."""
        if not _check_files(cwd, "uv", logger):
            return None

        paths = _print_paths(logger, "uv", "run")

        if paths is None:
            return None

        logger.debug("Ensure pip in uv venv.")  # Not installed unless --seed/UV_VENV_SEED=pip is used.
        _get_output(logger, "uv", "pip", "install", "--no-upgrade", "--quiet", "pip")

        return paths

    @classmethod
    def sys(cls, cwd: Path, logger: logging.Logger) -> tuple[str, str]:  # noqa: ARG003
        return sys.exec_prefix, sys.executable


def _check_files(cwd: Path, name: str, logger: logging.Logger) -> bool:
    lock = cwd / f"{name}.lock"
    if lock.is_file():
        logger.debug("Found lockfile: '%s'.", lock)
        return True

    pyproject = cwd / "pyproject.toml"
    if not pyproject.is_file():
        return False
    logger.debug("Found project file: '%s'.", pyproject)

    with pyproject.open("rb") as f:
        toml = tomllib.load(f)

    rv = name in toml

    if rv:
        logger.debug("Found key=%r in project file: '%s'.", name, pyproject)

    return rv


def _print_paths(logger: logging.Logger, *args: str) -> tuple[str, str] | None:
    file = Path(__file__).parent / "_print_paths.py"
    output = _get_output(logger, *args, str(file))
    if output is None:
        return None

    exec_prefix = ""
    executable = ""
    for line in output.strip().splitlines():
        # This is a bit redundant, but helps in cases where the manager writes junk to stdout.
        if line.startswith("exec_prefix="):
            exec_prefix = line.removeprefix("exec_prefix=").rstrip()

        if line.startswith("executable="):
            executable = line.removeprefix("executable=").rstrip()

    if not (exec_prefix and executable):
        raise ValueError(f"Could not find 'exec_prefix' and 'executable' in output:\n{output}")

    return exec_prefix, executable


def _get_output(logger: logging.Logger, *args: str) -> str | None:
    logger.debug("Executing command: %s", args)

    env = {
        **os.environ,
        "VIRTUAL_ENV": "",  # Break out of current virtualenv.
    }

    try:
        process = subprocess.run(args, capture_output=True, check=False, env=env)  # noqa: S603
    except OSError as e:
        _log_failed_command(logger, args, e)
        return None

    if process.returncode:
        _log_failed_command(logger, args, process)
        return None

    if logger.isEnabledFor(logging.DEBUG):
        msg = f"Command {args} succeeded:{_format_streams(process)}"
        logger.debug(msg)

    return process.stdout.decode().strip()


def _log_failed_command(
    logger: logging.Logger,
    args: tuple[str, ...],
    result: subprocess.CompletedProcess[bytes] | Exception,
) -> None:
    if not logger.isEnabledFor(logging.DEBUG):
        return

    msg = f"Command {args} failed"
    if isinstance(result, Exception):
        msg += f". {type(result).__name__}: {result}"
    else:
        msg += f" (status={result.returncode}): {_format_streams(result)}"
    logger.debug(msg)


def _format_streams(process: subprocess.CompletedProcess[bytes]) -> str:
    rows = []

    divider = "-" * 36

    if process.stderr:
        rows.append(f"\n{divider} stderr {divider}\n{process.stderr.decode().strip()}")
    if process.stdout:
        rows.append(f"\n{divider} stdout {divider}\n{process.stdout.decode().strip()}")

    return "".join(rows) if rows else " <no output>"
