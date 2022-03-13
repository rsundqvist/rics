from typing import Any, Collection, Dict, Union

import pandas as pd

from rics.utility.perf._multi_case_timer import CandFunc, MultiCaseTimer
from rics.utility.perf._util import _SEABORN_INSTALLED, plot_run, to_dataframe


def run_multivariate_test(
    candidate_method: Union[CandFunc, Collection[CandFunc], Dict[str, CandFunc]],
    test_data: Union[Any, Dict[str, Any]],
    time_per_candidate: float = 6.0,
    plot: bool = True,
    **figure_kwargs: Any,
) -> pd.DataFrame:
    """Run performance tests for multiple candidate methods on collections of test data.

    This method combines :meth:`rics.utility.perf.MultiCaseTimer.run`,
    :meth:`~rics.utility.perf.to_dataframe` and, if plotting is enabled, :meth:`~rics.utility.perf.plot_run`. For full
    functionally these methods should be used directly.

    Args:
        candidate_method: Candidate methods to evaluate.
        test_data: Test data to evaluate.
        time_per_candidate: Desired runtime for each repetition per candidate label.
        plot: If True, plot a figure using :meth:`~rics.utility.perf.plot_run`.
        **figure_kwargs: Keyword arguments for the barplot. Ignored if plot=False.

    Returns:
        A long-format DataFrame of results.

    Raises:
        ModuleNotFoundError: If Seaborn isn't installed and plot=True.
    """
    if plot and not _SEABORN_INSTALLED:
        raise ModuleNotFoundError("Install Seaborn to plot results.")

    run_results = MultiCaseTimer(candidate_method, test_data).run(time_per_candidate=time_per_candidate)

    data = to_dataframe(run_results)
    if plot:
        plot_run(data, **figure_kwargs)
    return data
