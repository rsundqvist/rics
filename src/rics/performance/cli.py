"""Multivariate performance testing from the command line.

For details, see the CLI docs.
"""

import datetime
import importlib
import inspect
import os
import sys
from pathlib import Path as _Path
from typing import Any as _Any

import click
import pandas as pd

from .._just_the_way_i_like_it import configure_stuff as _configure_stuff
from ._util import get_best as _get_best
from ._wrapper import run_multivariate_test as _run

LARGE_RESULT_ROW_LIMIT = 10000


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
        raise ValueError(
            "No file called 'test_data.py' in the current working directory."
            "\nHint: Create by running with flag --create"
        ) from None
    return test_data


def _get_candidates() -> _Any:
    try:
        candidates_module = importlib.import_module("candidates")

        if hasattr(candidates_module, "ALL"):
            candidates = candidates_module.ALL
        else:
            candidates = [func for name, func in inspect.getmembers(candidates_module) if name.startswith("candidate_")]
    except ModuleNotFoundError:
        raise ValueError(
            "No file called 'candidates.py' in the current working directory."
            "\nHint: Create by running with flag --create"
        ) from None
    return candidates


@click.command("Multivariate performance test")
@click.option(
    "--time-per-candidate",
    default=2.0,
    help="Time in seconds to allocate to each candidate function.",
    type=float,
    show_default=True,
)
@click.option(
    "--name",
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
def main(time_per_candidate: float, name: str, create: bool, per_candidate: bool) -> None:
    """Run a multivariate performance test.

    This is the https://pypi.org/project/rics/ version of the python timeit module. It may be used to run performance
    tests evaluating one or more candidate functions ('candidates.py') on one or more different kinds of inputs
    ('test_data.py'). See below for details on these modules.

    \b
    This script will:
        0. Create 'candidates.py' and 'test_data.py' (iff --create is set)
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
    if create:
        name, time_per_candidate = _create_input_files()

    name_path = _Path(name).absolute()
    title = name_path.stem.replace("-", " ").replace("_", " ").title()

    click.secho(f"{' Begin Performance Evaluation ':=^80}", fg="green")
    click.secho(f"|  {f'  {title!r}  ':^74}  |", fg="green")
    click.secho("-" * 80, fg="green")

    # force=False has no effect during normal operation (i.e. when running from CLI), but keeps things tidy for CI/CD.
    os.environ["JTWILI"] = "true"  # Suppress warnings
    _configure_stuff()

    try:
        sys.path.insert(0, str(_Path().absolute()))
        candidates = _get_candidates()
        test_data = _get_test_data()
    finally:
        sys.path.pop(0)

    now = datetime.datetime.now()
    eta_str = (now + datetime.timedelta(seconds=len(candidates) * time_per_candidate)).strftime("%A %d, %H:%M:%S")
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    click.secho(
        f"{f'| Found {len(candidates)} candidates and {len(test_data)} data variants.':<78} |",
        fg="green",
    )
    click.secho(f"{f'| Started: {now_str}, ETA: {eta_str}':<78} |", fg="green")
    click.secho("=" * 80, fg="green")

    try:
        result = _run(candidates, test_data, time_per_candidate=time_per_candidate)
    except ValueError as e:  # pragma: no cover
        msg = str(e)
        file: _Path | None = None
        if msg.startswith("No candidates"):
            msg += " Candidate functions must start with 'candidate_'."
            file = _Path("candidates.py")
        elif msg.startswith("No case"):
            msg += " Case data attributes must start with 'case_'."
            file = _Path("candidates.py")
        if file is not None:
            msg += f" Alternatively, you may define an attribute  'ALL = {{label: ...}}' in '{file}'"
            click.secho("ABORT: " + msg, fg="red")
            sys.exit(-1)
        else:
            raise

    _print_best_result(per_candidate, result, title)
    _save_plot(name_path, title)
    _save_report(name_path, result)


def _print_best_result(per_candidate: bool, result: pd.DataFrame, title: str) -> None:
    click.secho("=" * 80, fg="green")
    click.secho("|  {f'  Best Times  ':^74}  |", fg="green")
    click.secho(f"|  {f'  {title!r}  ':^74}  |", fg="green")
    click.secho("=" * 80, fg="green")
    click.secho(_get_best(result, per_candidate=per_candidate), fg="red")
    click.secho("=" * 80, fg="green")


def _save_report(name_path: _Path, result: pd.DataFrame) -> None:
    performance_report_path = name_path.with_suffix(".csv")

    if len(result) > LARGE_RESULT_ROW_LIMIT:
        click.secho(
            f"WARNING: The full timing report has {len(result)} rows, which may take a while to serialize.",
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
    figure_path = name_path.with_suffix(".png")
    plt.savefig(figure_path)
    click.secho(f"Figure saved: '{figure_path}'", fg="green")


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


if __name__ == "__main__":
    main()
