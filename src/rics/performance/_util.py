from collections.abc import Hashable, Iterable
from typing import Any, Literal, TypeGuard, cast, get_args

import pandas as pd

from rics.types import verify_literal

from .plot_types import Aggregation
from .types import ResultsDict


def to_dataframe(run_results: ResultsDict, names: Iterable[str] = (), *, tidy: bool = False) -> pd.DataFrame:
    """Create a DataFrame from performance run output, adding derived values.

    Args:
        run_results: A dict `run_results` on the form ``{candidate_label: {data_label: [runtime, ...]}}``, returned
            by :meth:`rics.performance.MultiCaseTimer.run`.
        names: Level names for tuple keys in the data (creates new columns). See :func:`.plot_run` for details.
        tidy: If ``True``, return a minimal analysis-friendly frame with lowercase columns
            ``['candidate', 'data', *names, 'run', 'seconds']`` and **no** presentation columns (unit conversions,
            ``'Times min'`` etc.). The default (``False``) returns the plotting-oriented frame consumed by
            :func:`.plot_run`, which mixes data with presentation (multiple ``'Time [<unit>]'`` columns).

    Returns:
        The `run_result` input as a DataFrame.
    """
    names = tuple(names)
    frames = []
    for candidate_label, candidate_results in run_results.items():
        for data_label, data_results in candidate_results.items():
            n_runs = len(data_results)
            data = {
                "Candidate": candidate_label,
                "Run no": range(n_runs),
                "Time [s]": data_results,
                "Test data": [data_label] * n_runs,
            }

            if _has_names(data_label, names=names):
                for label_part, name in zip(data_label, names, strict=True):
                    if name in data:
                        msg = f"Bad {name=}. Key is already in use: {list(data)}."
                        raise ValueError(msg)
                    data[name] = label_part

            frame = pd.DataFrame.from_dict(data, orient="columns")
            frames.append(frame)

    df = pd.concat(frames, ignore_index=True)

    if tidy:
        renames = {"Candidate": "candidate", "Test data": "data", "Run no": "run", "Time [s]": "seconds"}
        return df.rename(columns=renames)[["candidate", "data", *names, "run", "seconds"]]

    df["Time [ms]"] = df["Time [s]"] * 1000
    df["Time [μs]"] = df["Time [ms]"] * 1000
    df["Time [ns]"] = df["Time [μs]"] * 1000

    groupby = df.groupby("Test data")["Time [s]"]
    df["Times min"] = df["Time [s]"] / df["Test data"].map(groupby.min())
    df["Times mean"] = df["Time [s]"] / df["Test data"].map(groupby.mean())

    return df


def relative_to(
    run_results: ResultsDict | pd.DataFrame,
    baseline: str,
    *,
    names: Iterable[str] = (),
    agg: Aggregation = "min",
) -> pd.DataFrame:
    """Compare candidates against a `baseline` candidate.

    Reduces the repeated timings to one number per candidate/data pair (using `agg`) and expresses each candidate
    relative to `baseline` on the same data.

    Args:
        run_results: Output of :meth:`.MultiCaseTimer.run` (or a :func:`.to_dataframe` frame).
        baseline: Label of the candidate to compare against.
        names: Level names for tuple keys in the data (creates new columns). See :func:`.plot_run` for details.
        agg: How to summarize the repeated timings; one of ``'min'`` (default), ``'median'``, ``'mean'``.

    Returns:
        A tidy frame with columns ``['candidate', 'data', *names, 'seconds', 'baseline_seconds', 'speedup']`` where
        ``speedup = baseline_seconds / seconds`` (``> 1`` means *faster* than the baseline). The geometric-mean speedup
        per candidate is available in ``frame.attrs['geomean']``.

    Raises:
        KeyError: If `baseline` is not one of the candidate labels.
        TypeError: If `agg` is not a valid aggregation.
    """
    import numpy as np

    verify_literal(agg, Aggregation, name="agg")
    names = tuple(names)
    tidy = run_results.copy() if isinstance(run_results, pd.DataFrame) else to_dataframe(run_results, names=names)
    if "Candidate" in tidy.columns:  # Convert a plotting-oriented frame to the tidy schema.
        tidy = tidy.rename(columns={"Candidate": "candidate", "Test data": "data", "Time [s]": "seconds"})

    group = ["candidate", "data", *names]
    summary = tidy.groupby(group, observed=True)["seconds"].agg(agg).reset_index()

    candidates = set(summary["candidate"])
    if baseline not in candidates:
        msg = f"Bad {baseline=}; not one of the candidate labels {sorted(candidates)}."
        raise KeyError(msg)

    base = summary[summary["candidate"] == baseline].set_index("data")["seconds"]
    summary["baseline_seconds"] = summary["data"].map(base)
    summary["speedup"] = summary["baseline_seconds"] / summary["seconds"]

    summary.attrs["geomean"] = summary.groupby("candidate")["speedup"].agg(lambda s: np.exp(np.log(s).mean())).to_dict()
    return summary


def _has_names(data_label: Hashable, *, names: tuple[str, ...]) -> TypeGuard[tuple[str, ...]]:
    if len(names) == 0:
        return False

    if not isinstance(data_label, tuple):
        msg = f"Expected a tuple-key in `test_data` since {names=}."
        raise TypeError(msg)

    if len(data_label) != len(names):
        msg = f"Length of {data_label=} ({len(data_label)} does not match length of {names=} ({len(names)})."
        raise TypeError(msg)

    return True


def get_best(
    run_results: ResultsDict | pd.DataFrame,
    per_candidate: bool = False,
    names: Iterable[str] = (),
) -> pd.DataFrame:
    """Get a summarized view of the best run results for each candidate/data pair.

    Args:
        run_results: Output of :meth:`rics.performance.MultiCaseTimer.run`.
        per_candidate: If ``True``, show the best times for all candidate/data pairs. Otherwise, just show the best
            candidate per data label.
        names: Data label columns to show. Use single `'Test data'` column if not given.

    Returns:
        The best (lowest) times for each candidate/data pair.

    """
    df = run_results if isinstance(run_results, pd.DataFrame) else to_dataframe(run_results, names=names)
    return df.sort_values("Time [s]").groupby(["Candidate", "Test data"] if per_candidate else "Test data").head(1)


Unit = Literal["s", "ms", "μs", "us", "ns"]
X = Literal["candidate", "data"]


def legacy_plot_run(  # pragma: no coverage
    run_results: ResultsDict | pd.DataFrame,
    x: X | None = None,
    unit: Unit | None = None,
    **kwargs: Any,
) -> None:
    """Plot the results of a performance test.

    This is a legacy method that does not support facets.

    .. figure:: ../_images/perf_plot.png

       Comparison of ``time.sleep(t)`` and ``time.sleep(5*t)``.

    Args:
        run_results: Output of :meth:`rics.performance.MultiCaseTimer.run`.
        x: The value to plot on the X-axis, using the other to determine hue. Default=derive.
        unit: Time unit to plot on the Y-axis. Default=derive.
        **kwargs: Keyword arguments for :func:`seaborn.barplot`.

    Raises:
        ModuleNotFoundError: If Seaborn isn't installed.
        TypeError: For unknown `unit` arguments.
    """
    import warnings

    import matplotlib.pyplot as plt
    from seaborn import barplot, move_legend

    data = to_dataframe(run_results) if isinstance(run_results, dict) else run_results.copy()
    data[["Test data", "Candidate"]] = data[["Test data", "Candidate"]].astype("category")

    if x is None:
        x_arg, hue = _smaller_as_hue(data)
    else:
        verify_literal(x, X, name="x")
        x_arg, hue = ("Test data", "Candidate") if x == "data" else ("Candidate", "Test data")

    if unit is None:
        unit = _unit_from_data(data)
    else:
        verify_literal(unit, Unit, name="unit")

    y = f"Time [{unit.replace('us', 'μs')}]"

    if y not in data:
        # Unit is not one of the literals, but we still check 'data' in case someone added more units themselves.
        raise TypeError(f"Bad {unit=}; column '{y}' not present in data.")

    fig, (left, right) = plt.subplots(
        ncols=2,
        tight_layout=True,
        figsize=(8 + 4 * data.Candidate.nunique(), 7),
        sharey=True,
    )
    left.set_title("Average")
    right.set_title("Best")
    fig.suptitle("Performance", size=24)

    barplot(ax=left, data=data, x=x_arg, y=y, hue=hue, errorbar="sd", **kwargs)
    best = data.groupby(["Test data", "Candidate"], observed=True).min().reset_index()
    barplot(ax=right, data=best, x=x_arg, y=y, hue=hue, errorbar=None, **kwargs)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=DeprecationWarning)
        move_legend(right, "upper left", bbox_to_anchor=(1, 1))
    left.get_legend().remove()


def _smaller_as_hue(data: pd.DataFrame) -> tuple[str, str]:  # pragma: no coverage
    unique = data.nunique()
    return ("Test data", "Candidate") if unique["Test data"] < unique["Candidate"] else ("Candidate", "Test data")


def _unit_from_data(df: pd.DataFrame) -> Unit:  # pragma: no coverage
    """Pick the unit with the most "human" scale; whole numbers around one hundred."""
    from numpy import log10

    prefix = "Time ["
    columns = [c for c in df.columns if c.startswith(prefix)]
    means = df.groupby(["Test data", "Candidate"], observed=True)[columns].mean()

    residuals = log10(means) - 2
    avg_residual_by_time_column = residuals.mean(axis="index")
    column = avg_residual_by_time_column.abs().idxmin()

    unit = column.removeprefix(prefix).removesuffix("]")

    assert unit in get_args(Unit)  # noqa: S101
    return cast(Unit, unit)
