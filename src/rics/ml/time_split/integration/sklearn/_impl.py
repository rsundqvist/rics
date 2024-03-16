from collections.abc import Iterable, Sequence
from typing import Any, cast, get_args

from numpy import array, datetime64, logical_and, ndarray, nonzero
from numpy.typing import NDArray

from ..._backend import DatetimeIndexSplitter
from ..._docstrings import docs
from ...types import (
    DatetimeIterable,
    DatetimeSplits,
    DatetimeTypes,
    Flex,
    Schedule,
    Span,
)
from .._log_progress import LogProgressArg, handle_log_progress_arg

try:
    from sklearn.model_selection import BaseCrossValidator  # type: ignore[import-untyped]

except ModuleNotFoundError:
    BaseCrossValidator = object

IndexTuple = tuple[Sequence[int], Sequence[int]]


@docs
class ScikitLearnSplitter(BaseCrossValidator):  # type: ignore[misc]
    """A scikit-learn compatible datetime splitter.

    This class may be used to create temporal folds from heterogeneous/unaggregated data, typically used for training
    models (e.g. on raw transaction data). If your data is a well-formed time series, consider using the
    `TimeSeriesSplit`_ class from scikit-learn instead.

    .. _TimeSeriesSplit: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html

    If a ``pandas`` type is passed to the :meth:`ScikitLearnSplitter.split`-method, the index will be used.

    Args:
        schedule: {schedule}
        before: {before}
        after: {after}
        step: {step}
        n_splits: {n_splits}
        flex: {flex}
        log_progress: {log_progress}
        verify_xy: If ``True``, split X and y independently and verify that they are equal.

    {USER_GUIDE}

    """

    def __init__(
        self,
        schedule: Schedule,
        *,
        before: Span = "7d",
        after: Span = 1,
        n_splits: int | None = None,
        flex: Flex = "auto",
        step: int = 1,
        log_progress: LogProgressArg = False,
        verify_xy: bool = True,
    ) -> None:
        super().__init__()
        self._splitter = DatetimeIndexSplitter(
            schedule,
            before=before,
            after=after,
            step=step,
            n_splits=n_splits,
            flex=flex,
        )
        self.log_progress = log_progress
        self.verify_xy = verify_xy

    def get_n_splits(
        self, X: DatetimeIterable | None = None, y: DatetimeIterable | None = None, groups: Any = None
    ) -> int:
        """Returns the number of splitting iterations in the cross-validator.

        Equivalent to ``len(list(split(X, y, groups))``.

        Args:
            X: Training data (features).
            y: Target variable.
            groups: Always ignored, exists for compatibility.

        Returns:
            Number of splits with given arguments.

        Raises:
            ValueError: If both `X` and `y` are ``None``.
            ValueError: If splits of `X` and `y` are not equal when ``verify_xy=True``.

        """
        _, splits = self._get_splits(X, y)
        return len(splits)

    def split(
        self,
        X: DatetimeIterable | None = None,
        y: DatetimeIterable | None = None,
        groups: Any = None,
    ) -> Iterable[IndexTuple]:
        """Generate indices to split data into training and test set.

        Args:
            X: Training data (features).
            y: Target variable.
            groups: Always ignored, exists for compatibility.

        Yields:
            The training/test set indices for that split.

        Raises:
            ValueError: If both `X` and `y` are ``None``.
            ValueError: If splits of `X` and `y` are not equal when ``verify_xy=True``.
            TypeError: If `X` or `y` have an ``index``-attribute, but index elements are not datetime-like.

        """
        index, splits = self._get_splits(self._handle_pandas(X, "X"), self._handle_pandas(y, "y"))
        for fold in handle_log_progress_arg(self.log_progress, splits=splits) or splits:
            yield cast(
                IndexTuple,
                (
                    nonzero(logical_and(fold.start <= index, index < fold.mid))[0],
                    nonzero(logical_and(fold.mid <= index, index < fold.end))[0],
                ),
            )

    @staticmethod
    def _handle_pandas(arg: DatetimeIterable | None, name: str) -> DatetimeIterable | None:
        if arg is None or not hasattr(arg, "index"):
            return arg

        index = arg.index

        if type(arg.index[0]) in get_args(DatetimeTypes):
            return cast(DatetimeIterable, index)

        raise TypeError(f"{name}.index does not appear to be a datetime-like iterable.")

    def _get_splits(
        self,
        X: DatetimeIterable | None = None,
        y: DatetimeIterable | None = None,
    ) -> tuple[NDArray[datetime64], DatetimeSplits]:
        splits: DatetimeSplits | None = None
        y_splits: DatetimeSplits | None = None
        timestamps: Any | None = None

        if X is not None:
            splits = self._splitter.get_splits(X)
            timestamps = X
        if y is not None:
            y_splits = self._splitter.get_splits(y)
            timestamps = y
        if self.verify_xy and splits and y_splits and splits != y_splits:
            raise ValueError("Splits of X and y are not equal.")

        # Cast should not be needed, but MyPy things this is nullable.
        if splits is None and y_splits is None:
            raise ValueError("At least one of (X, y) must be given.")

        timestamps = timestamps if isinstance(timestamps, ndarray) else array(timestamps)
        if len(timestamps.shape) > 1:
            raise NotImplementedError(f"shape {timestamps.shape} not supported")
        return timestamps, cast(DatetimeSplits, splits or y_splits)
