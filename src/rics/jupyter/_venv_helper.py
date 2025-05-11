import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

from rics.logs import get_logger


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

        resolvers = [Resolve.poetry, Resolve.uv, Resolve.sys]
        logger.debug(f"Resolver order ({len(resolvers)}): {' | '.join(r.__name__ for r in resolvers)}.")

        for i, resolver in enumerate(resolvers, start=1):
            name = resolver.__name__
            msg = f"Resolver {i}/{len(resolvers)}: {name}(): %s."
            logger.debug(msg, "Starting")
            result = resolver()

            if result:
                logger.debug(msg, f"returned {result=}")
                return name, *result

            logger.debug(msg, "Failed")

        raise RuntimeError("exec resolution failed")

    def _read_pyvenv_cfg(self) -> dict[str, str]:
        self.logger.debug("Reading pyvenv.cfg for manager='%s': '%s'.", self.manager, self.config_path)
        if not self.config_path.is_file():
            msg = f"Not a virtualenv: '{self.executable}'."
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
    def poetry(cls) -> tuple[str, str] | None:
        """Implementation for https://github.com/python-poetry/poetry."""
        exec_prefix = _get_output("poetry", "env", "info", "-p")
        executable = _get_output("poetry", "env", "info", "-e")
        return (exec_prefix, executable) if exec_prefix and executable else None

    @classmethod
    def uv(cls) -> None:
        """Implementation for https://github.com/astral-sh/uv. Always returns ``None``."""
        return None  # TODO(rs): uv

    @classmethod
    def sys(cls) -> tuple[str, str]:
        return sys.exec_prefix, sys.executable


def _get_output(*args: str) -> str | None:
    try:
        process = subprocess.run(args, capture_output=True, check=False)  # noqa: S603
    except OSError:
        return None

    if process.returncode:
        return None

    return process.stdout.decode().strip()
