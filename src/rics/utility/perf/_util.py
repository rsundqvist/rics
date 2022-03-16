from typing import Any, Literal, Tuple, Union

import pandas as pd

from rics.utility.perf._multi_case_timer import ResultsDict

try:
    import seaborn as sns  # type: ignore

    _SEABORN_INSTALLED = True
except ModuleNotFoundError:
    _SEABORN_INSTALLED = False


def to_dataframe(run_results: ResultsDict) -> pd.DataFrame:
    """Create a DataFrame from performance run output.

    Args:
        run_results: Output from :meth:`rics.utility.perf.MultiCaseTimer.run`.

    Returns:
        The `run_result` input wrapped in a DataFrame.
    """
    ans = []
    for candidate_label, candidate_results in run_results.items():
        for data_label, data_results in candidate_results.items():
            ans.append(
                pd.DataFrame(
                    {
                        "Time [s]": data_results,
                        "Test data": data_label,
                        "Candidate": candidate_label,
                        "Run no": range(len(data_results)),
                    }
                )
            )

    df = pd.concat(ans, ignore_index=True)
    df["Time [ms]"] = df["Time [s]"] * 1000
    df["Time [μs]"] = df["Time [ms]"] * 1000
    return df


def plot_run(
    run_results: Union[ResultsDict, pd.DataFrame],
    x: Literal["candidate", "data"] = None,
    unit: Literal["s", "ms", "μs", "us"] = "ms",
    **figure_kwargs: Any,
) -> None:
    """Plot the results of a test run.

    Args:
        run_results: Output of :meth:`rics.utility.perf.MultiCaseTimer.run`.
        x: The value to plot on the X-axis. Default=derive.
        unit: Time unit to plot on the Y-axis.
        **figure_kwargs: Keyword arguments for the barplot.

    Raises:
        ModuleNotFoundError: If Seaborn isn't installed.
        ValueError: For unknown `unit` arguments.
    """
    if not _SEABORN_INSTALLED:
        raise ModuleNotFoundError("Install Seaborn to use this method.")

    data = to_dataframe(run_results) if isinstance(run_results, dict) else run_results

    x_arg, hue = (
        _smaller_as_hue(data)
        if x is None
        else (("Test data", "Candidate") if x == "data" else ("Candidate", "Test data"))
    )
    y = f"Time [{unit.replace('us', 'μs')}]"
    if y not in data:
        raise ValueError(f"Bad {unit=}; column '{y}' not present in data.")

    sns.barplot(data=data, x=x_arg, y=y, hue=hue, **figure_kwargs)


def _smaller_as_hue(data: pd.DataFrame) -> Tuple[str, str]:
    unique = data.nunique()
    return ("Test data", "Candidate") if unique["Test data"] < unique["Candidate"] else ("Candidate", "Test data")
