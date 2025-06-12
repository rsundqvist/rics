from collections.abc import Collection, Iterable
from typing import Any

import pandas as pd

from ._multi_case_timer import CandidateMethodArg, MultiCaseTimer, TestDataArg
from ._util import to_dataframe
from .types import DataFunc, DataType, Ts


def run_multivariate_test(
    candidate_method: CandidateMethodArg[DataType],
    test_data: TestDataArg[DataType] | DataFunc[*Ts, DataType],  # DataFunc[DataFuncP, DataType]
    # *, TODO(6.0.0): KW only at this point.
    # case_args: Collection[tuple[*Ts]] | None = None,
    # kwargs: Any | None = None,
    time_per_candidate: float = 6.0,
    plot: bool = True,
    *,
    show: bool = True,
    names: Iterable[str] | None = (),
    progress: bool = False,
    case_args: Collection[tuple[*Ts]] | None = None,
    kwargs: Any | None = None,
    **plot_kwargs: Any,
) -> pd.DataFrame:
    """Run performance tests for multiple candidate methods on collections of test data.

    This is a convenience method which combines :meth:`MultiCaseTimer.run() <rics.performance.MultiCaseTimer.run>`,
    :meth:`~rics.performance.to_dataframe` and -- if plotting is enabled -- :meth:`~rics.performance.plot_run`. For full
    functionally these methods should be use directly.

    Args:
        candidate_method: A single method, collection of functions or a dict {label: function} of candidates.
        test_data: A single datum, or a dict ``{label: data}`` to evaluate candidates on.
        time_per_candidate: Desired runtime for each repetition per candidate label.
        plot: If ``True``, plot a figure using :meth:`~rics.performance.plot_run`.
        show: If ``True``, attempt to display the figure. Ignored when ``plot=False``.
        names: Level names for tuple keys in the data (creates new columns). See :func:`.plot_run` for details. Set to
            ``None`` to disable derived names when `test_data` is callable.
        progress: If ``True``, display a progress bar. Requires ``tqdm``.
        case_args: These are positional arguments for the `test_data` callable.
        kwargs: Shared keyword arguments for the `test_data` callable.
        **plot_kwargs: See :func:`.plot_run` for details. Ignored if ``plot=False``.

    Returns:
        A long-format DataFrame of results.

    Raises:
        ModuleNotFoundError: If Seaborn isn't installed and ``plot=True``.
        TypeError: If `args` or `kwargs` are set when `test_data` is not a callable.
        ValueError: If `args` is empty and `test_data` is a callable.

    See Also:
        The :func:`~rics.performance.plot_run` and :func:`~rics.performance.get_best` functions.
    """
    if plot:
        _verify_can_plot()

    timer: MultiCaseTimer[DataType, *Ts] = MultiCaseTimer(
        candidate_method,
        test_data,
        case_args=case_args,
        kwargs=kwargs,
    )
    run_results = timer.run(time_per_candidate=time_per_candidate, progress=progress)

    if names is None:
        names = ()
    else:
        names = [*names]
        if not names and timer.is_data_generated:
            names = timer.derive_names()

    data = to_dataframe(run_results, names=names)

    if plot:
        from matplotlib.pyplot import show as show_figure

        from ._plot import plot_run

        plot_run(data, names=names, **plot_kwargs)

        if show:
            show_figure(block=False)

    return data


def _verify_can_plot() -> None:
    from importlib.util import find_spec

    if find_spec("seaborn") is None:
        msg = (
            "Package `seaborn` not installed. Run of one:"
            "\n  pip install seaborn"
            "\n  pip install rics[plotting]"
            "\nto enable plots."
        )
        raise RuntimeError(msg)
