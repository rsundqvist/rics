"""Jupyter kernel installation for virtual environments.

For details, see the :doc:`CLI documentation </documentation/cli/notebooks/kernel>` page.
"""

import click

from rics import click as _rc
from rics import jupyter as _rj


@click.command("kernel")
@click.pass_context
@click.option(
    "--user/--system",
    is_flag=True,
    default=None,
    help=_rj._kernel_helper.DOCSTRINGS["user"],
)
@click.option(
    "--name",
    type=str,
    help=_rj._kernel_helper.DOCSTRINGS["display_name"],
    show_default="automatic",
)
@click.option(
    "--profile",
    type=str,
    help=_rj._kernel_helper.DOCSTRINGS["profile"],
)
@click.option(
    "--prefix",
    type=str,
    help=_rj._kernel_helper.DOCSTRINGS["prefix"] + " Mutually exclusive with --user."
    "\n\n\b\nThe kernel JSON will be located at:\n   `<prefix>/share/jupyter/kernels/rics.kernel.<slug>/kernel.json`.",
)
@click.option(
    "--env",
    "-e",
    type=(str, str),
    multiple=True,
    help=_rj._kernel_helper.DOCSTRINGS["env"]
    + "\n\n\b\nGiven as [<Key> <Value>]-pairs. Example:\n    `<cmd> -e OMP_NUM_THREADS 32 -e MY_VAR my_value`",
)
@click.option(
    "--variant",
    help="Install a variant of the kernel, e.g. with extra environment variables.",
)
@click.option(
    "--add-package",
    "-p",
    type=str,
    default=(
        "jupyterlab-execute-time",
        "jupyterlab-git",
        "jupyterlab-code-formatter",
        "ipywidgets",
        "black",
        "isort",
    ),
    multiple=True,
    show_default=True,
    help="Packages to install in the kernel. Pass a single character to disable extra packages, e.g. `-p0`.",
)
def main(
    cxt: click.Context,
    *,
    user: bool | None,
    name: str | None,
    prefix: str | None,
    profile: str | None,
    env: tuple[tuple[str, str], ...],
    variant: str | None,
    add_package: tuple[str, ...],
) -> None:
    """Install Jupyter kernel spec for a virtual environment."""
    extra_packages = [] if len(add_package) == 1 and len(add_package[0]) == 1 else add_package
    helper = _rj.KernelHelper(
        extra_packages=extra_packages,
        variant=variant,
        callback=_Callback(cxt),
    )

    display_name = helper.resolve_display_name(name)
    click.secho(
        f"Installing KernelSpec({display_name=}, name={helper.resolve_kernel_name()!r}, executable='{helper.venv.executable}').",
        fg="green",
    )

    path = helper.install(
        user=user,
        display_name=display_name,
        prefix=prefix,
        profile=profile,
        env=dict(env),
        frozen_modules=True,
    )
    click.secho(f"Kernel spec installed: '{path}'", fg="green")


class _Callback:
    def __init__(self, cxt: click.Context) -> None:
        self.cxt = cxt

    def write_user_command(self, kernel_spec: _rj.KernelSpec) -> None:
        installer_metadata = kernel_spec["metadata"][__package__]["installer"]
        installer_metadata["user_command"] = _rc.get_user_command(self.cxt)

    __call__ = write_user_command
    __name__: str = __call__.__name__


if __name__ == "__main__":
    # TODO(alternative): Creates a new kernel spec for each project. Something like https://pypi.org/project/pyproject-local-kernel/
    #  could be an interesting alternative. But it's more opaque, and seems outdated (looks for tool.poetry.name).
    main()
