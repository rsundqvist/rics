from typing import TypeVar

FuncType = TypeVar("FuncType")  # No proper way to type this?


def add_docstrings(**kwargs: str) -> None:
    """Add a documented argument to the ``@docs`` decorator."""
    _DOCSTRINGS.update(kwargs)


def docs(function: FuncType) -> FuncType:
    """Add info the docstring of a function."""
    assert function.__doc__ is not None  # noqa: S101
    function.__doc__ = function.__doc__.format(**_DOCSTRINGS)
    return function


_OFFSET = "pandas :ref:`offset alias <pandas:timeseries.offset_aliases>`"
_SPAN = (
    f"Range {{arg}} `schedule` timestamps. Either a {_OFFSET}, an integer (`schedule`-based offsets), "
    f"or `'all'` (requires `available` data)."
)
_DOCSTRINGS = {
    "schedule": f"A collection of timestamps, a {_OFFSET}, or a cron expression.",
    "before": _SPAN.format(arg="before"),
    "after": _SPAN.format(arg="after"),
    "step": "Select a subset of folds, preferring folds later in the schedule.",
    "n_splits": "Maximum number of folds, preferring folds later in the schedule.",
    "available": "Binds `schedule` to a range.",
    "flex": f'A {_OFFSET} used to expand `available` data to its likely `"true"` limits. Pass ``False`` to disable.',
    "USER_GUIDE": (
        "For more information about the `schedule`, `before/after` and `flex`-arguments" ", see the :ref:`User guide`."
    ),
    "OFFSET": _OFFSET,
    "DatetimeIndexSplitterKwargs": "See :func:`~rics.ml.time_split.split`. The `available` keyword is managed by the integration.",
}
