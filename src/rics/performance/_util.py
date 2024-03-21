from typing import Any, Hashable, Iterable, Literal, TypeGuard, cast, get_args

import pandas as pd

from .types import ResultsDict


def to_dataframe(run_results: ResultsDict, names: Iterable[str] = ()) -> pd.DataFrame:
    """Create a DataFrame from performance run output, adding derived values.

    Args:
        run_results: Output from :meth:`rics.performance.MultiCaseTimer.run`.
        run_results: A dict `run_results` on the form ``{candidate_label: {data_label: [runtime, ...]}}``, returned
            by :meth:`rics.performance.MultiCaseTimer.run`.
        names: Categories for keys in the data. If given, all data labels must be tuples of the same length
            as `names`.

    Returns:
        The `run_result` input wrapped in a DataFrame.

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
    df["Time [ms]"] = df["Time [s]"] * 1000
    df["Time [μs]"] = df["Time [ms]"] * 1000
    df["Time [ns]"] = df["Time [μs]"] * 1000

    groupby = df.groupby("Test data")["Time [s]"]
    df["Times min"] = df["Time [s]"] / df["Test data"].map(groupby.min())
    df["Times mean"] = df["Time [s]"] / df["Test data"].map(groupby.mean())

    return df


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


def get_best(run_results: ResultsDict | pd.DataFrame, per_candidate: bool = False) -> pd.DataFrame:
    """Get a summarized view of the best run results for each candidate/data pair.

    Args:
        run_results: Output of :meth:`rics.performance.MultiCaseTimer.run`.
        per_candidate: If ``True``, show the best times for all candidate/data pairs. Otherwise, just show the best
            candidate per data label.

    Returns:
        The best (lowest) times for each candidate/data pair.

    """
    df = run_results if isinstance(run_results, pd.DataFrame) else to_dataframe(run_results)
    return df.sort_values("Time [s]").groupby(["Candidate", "Test data"] if per_candidate else "Test data").head(1)


Unit = Literal["s", "ms", "μs", "us", "ns"]


def plot_run(
    run_results: ResultsDict | pd.DataFrame,
    x: Literal["candidate", "data"] | None = None,
    unit: Unit | None = None,
    **kwargs: Any,
) -> None:
    """Plot the results of a performance test.

    .. figure:: ../_images/perf_plot.png

       Comparison of ``time.sleep(t)`` and ``time.sleep(5*t)``.

    Args:
        run_results: Output of :meth:`rics.performance.MultiCaseTimer.run`.
        x: The value to plot on the X-axis. Default=derive.
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

    x_arg, hue = (
        _smaller_as_hue(data)
        if x is None
        else (("Test data", "Candidate") if x == "data" else ("Candidate", "Test data"))
    )

    if unit is None:
        unit = _unit_from_data(data)

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


def _smaller_as_hue(data: pd.DataFrame) -> tuple[str, str]:
    unique = data.nunique()
    return ("Test data", "Candidate") if unique["Test data"] < unique["Candidate"] else ("Candidate", "Test data")


def _unit_from_data(df: pd.DataFrame) -> Unit:
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
