"""Entry point for the performance testing CLI program."""
import datetime

import click

from rics._internal_support.types import PathLikeType
from rics.performance import run_multivariate_test as _run
from rics.performance._util import get_best as _get_best


def run(
    time_per_candidate: float = 2.0,
    name: PathLikeType = "performance",
    save_raw: bool = True,
) -> None:
    """Run a multivariate performance test.

    Required files:
        * candidates.py - Public functions are used as candidates.
        * test_data.py - Members whose name start with `'case_'` are used as test case data.

    Hint:
       Define an ``ALL``-attribute to declare explicit members to use.

    Args:
        time_per_candidate: Time in seconds to allocate to each candidate function.
        name: Name to use for artifacts produced. Also used as the figure title (stylized).
        save_raw: If ``True``, write raw performance data to disk.

    Raises:
        ValueError: If ``candidates.py`` or ``test_data.py`` are missing or empty.
    """
    import inspect
    import pathlib
    import sys

    import matplotlib.pyplot as plt

    from rics.utility import configure_stuff

    name = pathlib.Path(str(name))
    pretty = name.stem.replace("-", " ").replace("_", " ").title()

    print(f"{' Begin Performance Evaluation ':=^80}")
    print(f"|  {f'  {repr(pretty)}  ':^74}  |")
    print("-" * 80)

    configure_stuff()
    sys.path.insert(0, ".")

    try:
        import candidates as candidates_module  # type: ignore

        candidates = (
            candidates_module.ALL
            if hasattr(candidates_module, "ALL")
            else [func for name, func in inspect.getmembers(candidates_module, inspect.isfunction) if name[0] != "_"]
        )
    except ModuleNotFoundError:
        raise ValueError("No file called 'candidates.py' in the current working directory.")

    try:
        import test_data as test_data_module  # type: ignore

        test_data = (
            test_data_module.ALL
            if hasattr(test_data_module, "ALL")
            else {
                name[len("case_") :]: data
                for name, data in inspect.getmembers(test_data_module)
                if name.lower().startswith("case_")
            }
        )
    except ModuleNotFoundError:
        raise ValueError("No file called 'test_data.py' in the current working directory.")

    now = datetime.datetime.now()
    eta_str = (now + datetime.timedelta(seconds=len(candidates) * time_per_candidate)).strftime("%A %d, %H:%M:%S")
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    print(f"{f'| Found {len(candidates)} candidates and {len(test_data)} data variants.':<78} |")
    print(f"{f'| Started: {now_str}, ETA: {eta_str}':<78} |")
    print("=" * 80)

    try:
        result = _run(candidates, test_data, time_per_candidate=time_per_candidate)
    except ValueError as e:
        if str(e).startswith("No candidates"):
            raise ValueError(
                "No candidate functions found. Candidates must be public, "
                "or you must define the 'ALL'-attribute in 'candidates.py"
            )
        if str(e).startswith("No case"):
            raise ValueError(
                "No case data found. Case data attributes must start with 'case_', "
                "or you must define the 'ALL'-attribute in 'test_data.py"
            )
        else:
            raise e

    print(_get_best(result))

    fig = plt.gcf()
    fig.suptitle(pretty)
    figure_path = name.with_suffix(".png")
    plt.savefig(figure_path)
    print(f"Figure saved: '{figure_path}'")

    if save_raw:
        performance_report_path = name.with_suffix(".txt")
        result.set_index(["Candidate", "Test data"]).to_string(performance_report_path)
        print(f"Data saved: '{performance_report_path.absolute()}'")


@click.command("Multivariate performance test")
@click.option(
    "--time-per-candidate",
    help="Time in seconds to allocate to each candidate function.",
    type=float,
    default="2.0",
    show_default=True,
)
@click.option(
    "--name",
    help="Name to use for artifacts produced. Also used as the figure title (stylized).",
    type=click.Path(dir_okay=False, writable=True),
    default="performance.png",
    show_default=True,
)
@click.option(
    "--save-raw/--no-save-raw",
    help="If set, write raw performance data to disk.",
    default=True,
    is_flag=True,
    show_default=True,
)
def _main(time_per_candidate: float, name: str, save_raw: bool) -> None:
    """Run a multivariate performance test.

    \b
    Required files:
        candidates.py - Public functions are used as candidates.
        test_data.py - Members whose name start with 'case_' are used as case data.

    Hint: Define an 'ALL'-attribute to declare explicit members to use.
    """  # noqa: DAR101, D301
    run(time_per_candidate, name, save_raw)


if __name__ == "__main__":
    _main()
