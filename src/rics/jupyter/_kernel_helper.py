import json
import logging
import subprocess
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from rics.logs import get_logger
from rics.paths import any_path_to_path

from ..misc import tname
from . import _kernel_spec, _venv_helper


class KernelHelper:
    """Helper class for working with Jupyter kernels."""

    def __init__(
        self,
        *,
        extra_packages: Iterable[str] = (),
        variant: str | None = None,
        callback: Callable[[_kernel_spec.KernelSpec], None] | None = None,
        venv_helper: _venv_helper.VenvHelper | None = None,
        logger: logging.Logger | str = __package__,
    ) -> None:
        self.extra_packages = [p for p in map(str.strip, extra_packages) if p]
        self.venv = _venv_helper.VenvHelper() if venv_helper is None else venv_helper
        self.variant = variant
        self.callback = callback
        self.logger = get_logger(logger)

    def resolve_display_name(self, display_name: str | None = None) -> str:
        """Construct kernel display name.

        Uses `display_name` as-is if given. Keys `slug`, `variant` and `manager` are provided.
        """
        if display_name:
            return display_name.format(slug=self.venv.slug, variant=self.variant, manager=self.venv.manager)
        return f"{self.venv.slug} [{self.variant or self.venv.manager}]"

    def resolve_kernel_name(self, kernel_name: str | None = None) -> str:
        """Construct kernel name. Uses `kernel_name` as-is if given."""
        if kernel_name:
            return kernel_name

        kernel_name = f"{__package__}.{self.venv.slug}"
        if variant := self.variant:
            kernel_name = f"{kernel_name}.{variant.replace(' ', '-')}".lower()

        return kernel_name

    def install(
        self,
        user: bool | None = None,
        kernel_name: str | None = None,
        display_name: str | None = None,
        prefix: str | None = None,
        profile: str | None = None,
        env: dict[str, str] | None = None,
        frozen_modules: bool = False,
    ) -> str:
        """Install kernel spec for a virtual environment.

        Args:
            user: {user}
            kernel_name: Name of kernel. Created by :meth:`resolve_kernel_name` if ``None``.
            display_name: {display_name} Created by :meth:`resolve_display_name` if ``None``.
            prefix: {prefix}
            profile: {profile}
            env: {env}
            frozen_modules: {frozen_modules}

        Returns:
            Path where the spec was installed.

        See Also:
            Uses ``ipykernel.kernelspec.install``. See https://pypi.org/project/ipykernel/ for details.
        """
        try:
            from ipykernel.kernelspec import install
        except ModuleNotFoundError as e:
            msg = "Package `ipykernel` not installed. Run of one:\n  pip install ipykernel\n  pip install rics[cli]\nto use this feature."
            raise RuntimeError(msg) from e

        logger = self.logger
        if user is None:
            user = prefix is None
            logger.debug(f"Setting {user=} from {prefix=}.")

        if self.variant and display_name is None and (env or profile) and logger.isEnabledFor(logging.INFO):
            lines = [f"Installing variant={self.variant!r}:"]
            if env:
                lines.append(f" - Kernel variables ({len(env)}): {sorted(env)}.")
            if profile:
                lines.append(f" - Kernel profile: {profile!r}.")
            logger.info("\n".join(lines))

        path = install(
            user=user,
            kernel_name=self.resolve_kernel_name(kernel_name),
            display_name=self.resolve_display_name(display_name),
            prefix=prefix,
            profile=profile,
            env=env,
            frozen_modules=frozen_modules,
        )

        self.patch_kernel(Path(path) / "kernel.json")
        self.install_packages()

        return path

    @classmethod
    def read_kernel_spec(cls, path: str | Path) -> _kernel_spec.KernelSpec:
        path = any_path_to_path(path, postprocessor=Path.is_file)

        kernel_spec_json = path.read_text()
        kernel_spec: _kernel_spec.KernelSpec = json.loads(kernel_spec_json)

        required = {"argv", "display_name", "language"}
        if missing := required.difference(kernel_spec):
            msg = f"Not a valid {_kernel_spec.KernelSpec.__name__}: Missing required keys {sorted(missing)}."
            raise TypeError(msg)
        return kernel_spec

    @property
    def packages(self) -> list[str]:
        """List of packages to install in the kernel."""
        return ["ipykernel", *self.extra_packages]

    def patch_kernel(self, path: Path) -> None:
        """Apply kernel fixups to ensure that it actually runs in a notebook."""
        logger = self.logger

        logger.info("Patching kernel '%s' at '%s'.", self.venv.slug, path)
        kernel_spec = self.read_kernel_spec(path)
        logger.debug("Read kernel spec from path='%s':\n%s", path, kernel_spec)

        assert kernel_spec["argv"][0] == sys.executable, f"{kernel_spec['argv']=}"  # noqa: S101
        kernel_spec["argv"][0] = self.venv.executable

        metadata: dict[str, Any] = kernel_spec.setdefault("metadata", {})
        logger.debug("Updating metadata: %s.", metadata)
        self._update_metadata(metadata)

        if self.callback:
            if logger.isEnabledFor(logging.DEBUG):
                func = tname(self.callback, include_module=True)
                arg = _kernel_spec.KernelSpec.__name__
                logger.debug(f"Invoking callback: {func}({arg}).")
            self.callback(kernel_spec)

        kernel_spec_json = json.dumps(kernel_spec, indent=2, sort_keys=True)
        logger.debug("Writing kernel spec to path='%s':\n%s", path, kernel_spec_json)
        path.write_text(kernel_spec_json)

    def _update_metadata(self, metadata: dict[str, Any]) -> None:
        program_metadata: dict[str, Any] = metadata.setdefault(__package__, {})

        program_metadata["venv"] = {
            "slug": self.venv.slug,
            "version_info": self.venv.config.get("version_info"),
            "manager": self.venv.manager,
            "pyvenv.cfg": str(self.venv.config_path),
        }
        program_metadata["variant"] = self.variant
        _kernel_spec.set_metadata(program_metadata)

    def install_packages(self) -> None:
        """Installed required :attr:`additional packages <packages>`."""
        packages = self.packages
        self.logger.info("Installing packages: %s.", packages)
        flags = ["--disable-pip-version-check", "--quiet", "--require-virtualenv"]
        args = [self.venv.executable, "-m", "pip", "install", *flags, *packages]
        self.logger.debug("Installing packages: Command: %s", " ".join(args))
        self._check_call(args)

    @classmethod
    def _check_call(cls, args: list[str]) -> None:
        subprocess.check_call(args, timeout=30)  # noqa: S603


DOCSTRINGS = {
    "user": "Select user [default] or system-wide install. System install may require elevated privileges.",
    "display_name": "Explicit display name.",
    "prefix": "Spec location prefix for non-default locations such as conda.",
    "profile": "An IPython profile to be loaded by the kernel.",
    "env": "Extra environment variables for the kernel.",
    "frozen_modules": "Set for potentially faster startup. Prevents debugging of built-in modules.",
}

assert isinstance(KernelHelper.install.__doc__, str)  # noqa: S101
KernelHelper.install.__doc__ = KernelHelper.install.__doc__.format_map(DOCSTRINGS)
