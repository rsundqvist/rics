"""Multivariate performance testing from the command line.

For details, see the :doc:`CLI documentation </documentation/cli/notebooks/timeit>` page.
"""

import datetime
import importlib
import inspect
import os
import shutil as _shutil
import sys
import warnings as _warnings
from pathlib import Path as _Path
from typing import Any as _Any
from typing import Never as _Never

import click
import pandas as pd

from rics import click as _rclick

from .._just_the_way_i_like_it import configure_stuff as _configure_stuff
from ._multi_case_timer import MultiCaseTimer as _Timer
from ._util import get_best as _get_best
from ._wrapper import run_multivariate_test as _run

LARGE_RESULT_ROW_LIMIT: int = 100_000
"""Ask for confirmation before writing results frames above this length."""

_show_warning_orig = _warnings.showwarning


@click.command(
    "timeit",
    epilog="""
    \b
    The CLI does not support facets (rows and columns). Please use
        https://rics.readthedocs.io/en/stable/api/rics.performance.html
    if your test data should be categorized into subgroups.
    """,
)
@click.pass_context
@click.option(
    "--time-per-candidate",
    "-t",
    default=2.0,
    help="Time in seconds to allocate to each candidate function.",
    type=float,
    show_default=True,
)
@click.option(
    "--name",
    "-n",
    default="performance.png",
    help="Name to use for artifacts produced. Also used as the figure title (stylized).",
    type=click.Path(dir_okay=False, writable=True),
    show_default=True,
)
@click.option(
    "--create/--no-create",
    default=False,
    help="Create files 'candidates.py' and 'test_data.py' and run a demo. Will not overwrite existing files.",
    is_flag=True,
    show_default=True,
)
@click.option(
    "--per-candidate/--no-per-candidate",
    default=True,
    help="Enable to print per-candidate best times. Just shows the best overall per data if disabled.",
    is_flag=True,
    show_default=True,
)
@click.option(
    "--yes",
    "-y",
    help=f"Automatic yes to prompts for things like writing large (>{LARGE_RESULT_ROW_LIMIT:_d} rows) result files.",
    is_flag=True,
)
@click.option(
    "--plot/--no-plot",
    help="Plotting requires `seaborn`.",
    is_flag=True,
)
def main(
    cxt: click.Context,
    time_per_candidate: float,
    name: str,
    create: bool,
    per_candidate: bool,
    yes: bool,
    plot: bool,
) -> None:
    """Multivariate performance testing.

    This is the https://pypi.org/project/rics/ version of the python timeit module. It may be used to run performance
    tests evaluating one or more candidate functions ('candidates.py') on one or more different kinds of inputs
    ('test_data.py').

    \b
    This script will:
        0. Create 'candidates.py' and 'test_data.py' (only if --create is set; will never overwrite).
        1. Quickly evaluate each candidate on all test data "a few times".
        2. Decide how many times to evaluate each candidate, such that the
           --time-per-candidate argument is respected.
        3. Print the best times per candidate/test_data
           combination to stdout.
        4. Save a performance overview figure to disk.
        5. Save raw timing data to disk as CSV.

    \b
    Required files:
        candidates.py - Members starting with 'candidate_' are used as candidates.
        test_data.py - Members starting with 'case_' are used as the case case data.

    Hint: Define a 'ALL'-attributes in 'candidates' and 'test_data' to declare explicit members to use.
    """  # noqa: D301
    _deprecated(cxt)

    if create:
        name, time_per_candidate = _create_input_files()

    name_path = _Path(name).with_suffix(".jpg").absolute()
    title = name_path.stem.replace("-", " ").replace("_", " ").title()

    width = _width()
    c6 = f"^{_width() - 6}"
    click.secho(f"{' Begin Performance Evaluation ':=^{width}}", fg="green")
    click.secho(f"|  {f'  {title!r}  ':{c6}}  |", fg="green")
    click.secho("-" * width, fg="green")

    # force=False has no effect during normal operation (i.e. when running from CLI), but keeps things tidy for CI/CD.
    os.environ["JTWILI"] = "true"  # Suppress warnings

    _configure_stuff(
        logging=cxt.meta.get("verbosity") is None,  # Configure logging only when invoked directly.
        ghost=False,
    )

    try:
        sys.path.insert(0, str(_Path().absolute()))
        candidates = _get_candidates()
        test_data = _get_test_data()
    finally:
        sys.path.pop(0)

    now = datetime.datetime.now()
    eta_str = (now + datetime.timedelta(seconds=len(candidates) * time_per_candidate)).strftime("%A %d, %H:%M:%S")
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    w2 = f"<{_width() - 2}"
    click.secho(f"{f'| Found {len(candidates)} candidates and {len(test_data)} data variants:':{w2}} |", fg="green")
    click.secho(f"{f'|  -    Candidates: {[*_Timer.process_candidates(candidates)]}':{w2}} |", fg="green")
    click.secho(f"{f'|  - Data variants: {[*_Timer.process_test_data(test_data)]}':{w2}} |", fg="green")
    click.secho(f"{f'| Started: {now_str}, ETA: {eta_str}':{w2}} |", fg="green")
    click.secho("=" * width, fg="green")

    try:
        _warnings.showwarning = _show_warnings

        result = _run(candidates, test_data, time_per_candidate=time_per_candidate, plot=plot, show=False)
    except ValueError as e:  # pragma: no cover
        _handle_value_error(e)
        raise
    finally:
        _warnings.showwarning = _show_warning_orig

    _print_best_result(per_candidate, result, title)
    _save_plot(name_path, title)
    _save_report(name_path, result, not yes)


def _deprecated(cxt: click.Context) -> None:
    name = cxt.info_name
    if name != "mtimeit":
        return

    user_command = _rclick.get_user_command().replace(name, "rics timeit", 1)
    msg = (
        f"WARNING: Entrypoint `{name}` is deprecated."
        f"\nUse `{user_command}` instead, or pin `rics==5.0.1` to hide this warning."
    )
    click.secho(msg, err=True, fg="yellow")


def _get_test_data() -> _Any:
    try:
        import test_data as test_data_module  # type: ignore

        if hasattr(test_data_module, "ALL"):
            test_data = test_data_module.ALL
        else:
            test_data = {
                name.removeprefix("case_").replace("_", " "): data
                for name, data in inspect.getmembers(test_data_module)
                if name.lower().startswith("case_")
            }
    except ModuleNotFoundError:
        _missing_file("test_data.py")
    return test_data


def _get_candidates() -> _Any:
    try:
        candidates_module = importlib.import_module("candidates")

        if hasattr(candidates_module, "ALL"):
            candidates = candidates_module.ALL
        else:
            candidates = [func for name, func in inspect.getmembers(candidates_module) if name.startswith("candidate_")]
    except ModuleNotFoundError:
        _missing_file("candidates.py")
    return candidates


def _missing_file(name: str) -> _Never:
    cxt = click.get_current_context()
    click.secho(
        f"No file called '{name}' in the current working directory."
        f"\nHint: Create by running `{cxt.command_path} --create`.",
        fg="red",
        err=True,
    )
    sys.exit(2)


def _print_best_result(per_candidate: bool, result: pd.DataFrame, title: str) -> None:
    width = _width()
    c6 = f"^{_width() - 6}"
    click.secho("=" * width, fg="green")
    click.secho(f"|  {'  Best Times  ':{c6}}  |", fg="green")
    click.secho(f"|  {f'  {title!r}  ':{c6}}  |", fg="green")
    click.secho("=" * width, fg="green")
    click.secho(_get_best(result, per_candidate=per_candidate), fg="red")
    click.secho("=" * width, fg="green")


def _save_report(name_path: _Path, result: pd.DataFrame, prompt: bool) -> None:
    performance_report_path = name_path.with_suffix(".csv")

    if prompt and len(result) > LARGE_RESULT_ROW_LIMIT:
        click.secho(
            f"WARNING: The full timing report has {len(result):_d} rows, which may take a while to serialize.",
            fg="yellow",
        )
        if not click.confirm(f"Really print full report to '{performance_report_path}'?"):
            sys.exit(0)

    result.set_index(["Candidate", "Test data"]).to_csv(performance_report_path)
    click.secho(f"Data saved: '{performance_report_path}'", fg="green")


def _save_plot(name_path: _Path, title: str) -> None:
    import matplotlib.pyplot as plt

    fig = plt.gcf()
    fig.suptitle(title)
    plt.savefig(name_path)
    click.secho(f"Figure saved: '{name_path}'", fg="green")


def _create_input_files() -> tuple[str, float]:
    time_per_candidate = 0.1
    name = "create-example-run"

    for template_name in "candidates", "test_data":
        path = _Path().joinpath(template_name).with_suffix(".py").absolute()
        if path.exists():
            click.secho(
                f"ABORT: Refusing to overwrite existing file '{path}'. "
                f"Delete files 'candidates.py' and 'test_data.py' in '{path.parent}' to continue.",
                fg="red",
                err=True,
            )
            sys.exit(1)
        text = _Path(__file__).parent.joinpath(f"templates/{template_name}.py.txt").read_text()
        path.write_text(text)

    return name, time_per_candidate


def _handle_value_error(e: ValueError) -> None:
    msg = str(e)

    file: str | None = None
    if msg.startswith("No candidates"):
        msg += " Candidate functions must start with 'candidate_'."
        file = "candidates.py"
    elif msg.startswith("No case"):
        msg += " Case data attributes must start with 'case_'."
        file = "candidates.py"

    if file is None:
        return

    msg += f" Alternatively, you may define an attribute  'ALL = {{label: ...}}' in '{file}'."
    click.secho("ABORT: " + msg, fg="red")
    sys.exit(-1)


def _width() -> int:
    width = _shutil.get_terminal_size()[0]

    return min(width, 120)


def _show_warnings(message: Warning | str, category: type[Warning], *args: _Any, **kwargs: _Any) -> None:
    if isinstance(message, UserWarning) and message.args[0].startswith("The test results may be unreliable"):
        click.secho(f"WARNING: {message}", fg="yellow")
        return
    _show_warning_orig(message, category, *args, **kwargs)


if __name__ == "__main__":
    main()
