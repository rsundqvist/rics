import sys

import click

USER_COMMAND_KEY: str = "USER_COMMAND"


def get_user_command(cxt: click.Context | None = None, *, meta: bool = True) -> str:
    """Recreate the user CLI command.

    Args:
        cxt: Click context. Derive is ``None``.
        meta: If ``True``, use :attr:`click.Context.meta` caching.

    Returns:
        A user command such as ``python -m rics.cli -v kernel --name=my-kernel``.
    """
    if cxt is None:
        cxt = click.get_current_context(silent=False).find_root()

    if not meta:
        return _build_user_command(cxt)

    if user_command := cxt.meta.get(USER_COMMAND_KEY):
        assert isinstance(user_command, str)  # noqa: S101
        return user_command

    user_command = _build_user_command(cxt)
    cxt.meta[USER_COMMAND_KEY] = user_command
    return user_command


def _build_user_command(cxt: click.Context) -> str:
    return " ".join([cxt.command_path, *sys.argv[1:]])
