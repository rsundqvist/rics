"""CLI entrypoint.

For details, see the :doc:`CLI documentation </documentation/cli/notebooks/cli>` page.
"""

from importlib.metadata import entry_points as _entry_points

import click as _c

from rics import click as _rc
from rics import logs as _logs
from rics.click import _alias_command_group


@_c.group(
    context_settings={"auto_envvar_prefix": "RICS"},
    epilog="""
    \b
    Python package documentation:
        https://id-translation.readthedocs.io/
        https://time-split.readthedocs.io/
        https://rics.readthedocs.io/
    Please let me know if any of these resources helped you!
    """,
    cls=_alias_command_group.AliasedCommandGroup,
)
@_rc.logging_verbosity_option(
    "-v",
    "--verbose",
    mode="forward_both",
    format=_logs.FORMAT_MS,
    levels=[{"rics": "INFO"}, {"root": "INFO"}, {"rics": "DEBUG"}, {"root": "DEBUG"}],
    show_envvar=True,
)
@_c.pass_context
def main(cxt: _c.Context, verbose: tuple[int, _logs.LoggingSetupHelper]) -> None:
    """👻 RiCS: My little CLI program."""
    _rc.get_user_command(cxt, meta=True)

    # Configure logging "manually" since mode="forward_both" does not call LoggingSetupHelper.configure_logging().
    verbosity, helper = verbose
    helper.configure_logging(verbosity)
    cxt.meta["verbosity"] = verbosity
    cxt.meta["logging_setup_helper"] = helper


for ep in _entry_points(group="rics.cli"):
    result = ep.load()
    assert isinstance(result, _c.Command), f"{result=} | {type(result)=}"  # noqa: S101
    main.add_command(result, ep.name)  # Register


if __name__ == "__main__":
    main()
