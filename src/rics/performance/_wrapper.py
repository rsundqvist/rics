from typing import TYPE_CHECKING, Any, Union

from ._multi_case_timer import CandidateMethodArg, MultiCaseTimer, TestDataArg
from ._util import plot_run, to_dataframe
from .types import DataType, ResultsDict

if TYPE_CHECKING:
    import pandas


def run_multivariate_test(
    candidate_method: CandidateMethodArg[DataType],
    test_data: TestDataArg[DataType],
    time_per_candidate: float = 6.0,
    plot: bool = True,
    **figure_kwargs: Any,
) -> Union["pandas.DataFrame", ResultsDict]:
    """Run performance tests for multiple candidate methods on collections of test data.

    .. note::

       Returns a :attr:`~rics.performance.types.ResultsDict` if :mod:`pandas` is not
       installed. Plotting requires :func:`seaborn <seaborn.barplot>`.

    This is a convenience method which combines :meth:`MultiCaseTimer.run() <rics.performance.MultiCaseTimer.run>`,
    :meth:`~rics.performance.to_dataframe` and -- if plotting is enabled -- :meth:`~rics.performance.plot_run`. For full
    functionally these methods should be use directly.

    Args:
        candidate_method: A single method, collection of functions or a dict {label: function} of candidates.
        test_data: A single datum, or a dict ``{label: data}`` to evaluate candidates on.
        time_per_candidate: Desired runtime for each repetition per candidate label.
        plot: If ``True``, plot a figure using :meth:`~rics.performance.plot_run`.
        **figure_kwargs: Keyword arguments for the :func:`seaborn.barplot`. Ignored if ``plot=False``.

    Returns:
        A long-format :class:`pandas.DataFrame` of results.

    Raises:
        ModuleNotFoundError: If Seaborn isn't installed and ``plot=True``.

    See Also:
        The :func:`~rics.performance.plot_run` and :func:`~rics.performance.get_best` functions.
    """
    timer: MultiCaseTimer[DataType] = MultiCaseTimer(candidate_method, test_data)
    run_results = timer.run(time_per_candidate=time_per_candidate)
    data = to_dataframe(run_results)

    if plot:
        from matplotlib.pyplot import show

        plot_run(data, **figure_kwargs)
        show(block=False)

    return data
