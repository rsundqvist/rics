from typing import Any, Collection, Dict, Union

import pandas as pd

from rics.performance._multi_case_timer import CandFunc, MultiCaseTimer
from rics.performance._util import plot_run, to_dataframe


def run_multivariate_test(
    candidate_method: Union[CandFunc, Collection[CandFunc], Dict[str, CandFunc]],
    test_data: Union[Any, Dict[str, Any]],
    time_per_candidate: float = 6.0,
    plot: bool = True,
    **figure_kwargs: Any,
) -> pd.DataFrame:
    """Run performance tests for multiple candidate methods on collections of test data.

    This is a convenience method which combines :meth:`MultiCaseTimer.run() <rics.performance.MultiCaseTimer.run>`,
    :meth:`~rics.performance.to_dataframe` and -- if plotting is enabled -- :meth:`~rics.performance.plot_run`. For full
    functionally these methods should be use directly.

    Args:
        candidate_method: Candidate methods to evaluate.
        test_data: Test data to evaluate.
        time_per_candidate: Desired runtime for each repetition per candidate label.
        plot: If ``True``, plot a figure using :meth:`~rics.performance.plot_run`.
        **figure_kwargs: Keyword arguments for the barplot. Ignored if ``plot=False``.

    Returns:
        A long-format DataFrame of results.

    Raises:
        ModuleNotFoundError: If Seaborn isn't installed and ``plot=True``.
    """
    run_results = MultiCaseTimer(candidate_method, test_data).run(time_per_candidate=time_per_candidate)

    data = to_dataframe(run_results)
    if plot:  # pragma: no cover
        from matplotlib.pyplot import show

        plot_run(data, **figure_kwargs)
        show(block=False)
    return data
