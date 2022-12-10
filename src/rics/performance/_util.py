from typing import Any, Literal, Tuple, Union

import pandas as pd

from ._multi_case_timer import ResultsDict


def to_dataframe(run_results: ResultsDict) -> pd.DataFrame:
    """Create a DataFrame from performance run output, adding derived values.

    Args:
        run_results: Output from :meth:`rics.performance.MultiCaseTimer.run`.

    Returns:
        The `run_result` input wrapped in a DataFrame.
    """
    ans = []
    for candidate_label, candidate_results in run_results.items():
        for data_label, data_results in candidate_results.items():
            ans.append(
                pd.DataFrame(
                    {
                        "Candidate": candidate_label,
                        "Test data": data_label,
                        "Run no": range(len(data_results)),
                        "Time [s]": data_results,
                    }
                )
            )

    df = pd.concat(ans, ignore_index=True)
    df["Time [ms]"] = df["Time [s]"] * 1000
    df["Time [μs]"] = df["Time [ms]"] * 1000

    groupby = df.groupby("Test data")["Time [s]"]
    df["Times min"] = df["Time [s]"] / df["Test data"].map(groupby.min())
    df["Times mean"] = df["Time [s]"] / df["Test data"].map(groupby.mean())

    return df


def get_best(run_results: Union[ResultsDict, pd.DataFrame], per_candidate: bool = False) -> pd.DataFrame:
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


def plot_run(
    run_results: Union[ResultsDict, pd.DataFrame],
    x: Literal["candidate", "data"] = None,
    unit: Literal["s", "ms", "μs", "us"] = "ms",
    **figure_kwargs: Any,
) -> None:
    """Plot the results of a performance test.

    .. figure:: ../_images/perf_plot.png

       Comparison of ``time.sleep(t)`` and ``time.sleep(5*t)``.

    Args:
        run_results: Output of :meth:`rics.performance.MultiCaseTimer.run`.
        x: The value to plot on the X-axis. Default=derive.
        unit: Time unit to plot on the Y-axis.
        **figure_kwargs: Keyword arguments for the barplot.

    Raises:
        ModuleNotFoundError: If Seaborn isn't installed.
        ValueError: For unknown `unit` arguments.
    """
    import matplotlib.pyplot as plt
    from seaborn import barplot, move_legend

    data = to_dataframe(run_results) if isinstance(run_results, dict) else run_results.copy()
    data[["Test data", "Candidate"]] = data[["Test data", "Candidate"]].astype("category")

    x_arg, hue = (
        _smaller_as_hue(data)
        if x is None
        else (("Test data", "Candidate") if x == "data" else ("Candidate", "Test data"))
    )
    y = f"Time [{unit.replace('us', 'μs')}]"
    if y not in data:  # pragma: no cover
        raise ValueError(f"Bad {unit=}; column '{y}' not present in data.")

    fig, (left, right) = plt.subplots(
        ncols=2, tight_layout=True, figsize=(8 + 4 * data.Candidate.nunique(), 7), sharey=True
    )
    left.set_title("Average")
    right.set_title("Best")
    fig.suptitle("Performance", size=24)

    barplot(ax=left, data=data, x=x_arg, y=y, hue=hue, errorbar="sd", **figure_kwargs)
    best = data.groupby(["Test data", "Candidate"]).min().reset_index()
    barplot(ax=right, data=best, x=x_arg, y=y, hue=hue, errorbar=None, **figure_kwargs)

    move_legend(right, "upper left", bbox_to_anchor=(1, 1))
    left.get_legend().remove()


def _smaller_as_hue(data: pd.DataFrame) -> Tuple[str, str]:
    unique = data.nunique()
    return ("Test data", "Candidate") if unique["Test data"] < unique["Candidate"] else ("Candidate", "Test data")
