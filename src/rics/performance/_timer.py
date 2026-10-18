"""Timer construction for :class:`.MultiCaseTimer`.

:class:`timeit.Timer` ``exec``s its loop from a source template, which may leave the dataset in a reference cycle.
Dropping the last reference to a variant then does not free it; only the cyclic collector does, and that runs on
container *allocation* counts rather than bytes -- so it rarely fires for the few-but-huge datasets the timer's memory
guarantee targets. Hence :func:`collect_dead_variants`.

:class:`CycleFreeTimer` builds the loop directly, leaving no cycle to collect.
"""

import functools
import gc
import itertools
import timeit
from time import perf_counter
from typing import Generic, Protocol

from rics.env.read import read_bool

from .types import CandFunc, DataType, SetupFunc

ENV_VAR = "RICS_PERF_EXPERIMENTAL_TIMER"
"""Set to ``true`` to time with :class:`CycleFreeTimer` instead of :class:`timeit.Timer`. Resolve in 7.0.0."""

USE_EXPERIMENTAL_TIMER: bool = read_bool(ENV_VAR, default=False)
"""Resolved :data:`ENV_VAR` value. Patch this attribute to toggle the timer in tests."""


class TimerLike(Protocol):
    """The :class:`timeit.Timer` surface used by this package."""

    def timeit(self, number: int) -> float:
        """Call the candidate `number` times, returning the elapsed seconds."""

    def repeat(self, repeat: int, number: int) -> list[float]:
        """Run :meth:`timeit` `repeat` times, returning the elapsed seconds of each."""


class CycleFreeTimer(Generic[DataType]):
    """A :class:`timeit.Timer` work-alike that does not leave `data` in a reference cycle.

    Semantics match the stdlib class for the surface this package uses: `setup` is untimed and runs once per
    :meth:`timeit` call, and the cyclic collector is disabled while timing.

    Args:
        func: The candidate to time.
        data: The input passed to `func`.
        setup: Optional ``(data) -> data`` producing a fresh input.
    """

    def __init__(self, func: CandFunc[DataType], data: DataType, setup: SetupFunc[DataType] | None = None) -> None:
        self._func = func
        self._data = data
        self._setup = setup

    def timeit(self, number: int) -> float:
        """Call the candidate `number` times, returning the elapsed seconds."""
        func = self._func
        data = self._data
        setup = self._setup

        gc_was_enabled = gc.isenabled()
        gc.disable()
        try:
            if setup is not None:
                data = setup(data)  # Untimed, as in timeit.Timer.

            it = itertools.repeat(None, number)
            t0 = perf_counter()
            for _ in it:
                func(data)
            t1 = perf_counter()
        finally:
            if gc_was_enabled:
                gc.enable()

        return t1 - t0

    def repeat(self, repeat: int, number: int) -> list[float]:
        """Run :meth:`timeit` `repeat` times, returning the elapsed seconds of each."""
        return [self.timeit(number) for _ in range(repeat)]


def make_timer(func: CandFunc[DataType], data: DataType, setup: SetupFunc[DataType] | None) -> TimerLike:
    """Build a timer for `func` and `data`. With `setup`, fresh input is produced (unmeasured) per repetition."""
    if USE_EXPERIMENTAL_TIMER:
        return CycleFreeTimer(func, data, setup)

    if setup is None:
        return timeit.Timer(functools.partial(func, data))

    holder: dict[str, DataType] = {}

    def _setup() -> None:
        holder.clear()  # Else the previous repetition's copy is alive while setup() builds the next.
        holder["data"] = setup(data)

    def _stmt() -> None:
        func(holder["data"])

    return timeit.Timer(_stmt, _setup)


def collect_dead_variants() -> None:
    """Reclaim variants that :class:`timeit.Timer` may leave in reference cycles; see the module docstring.

    Call only for generated data: a full collection costs O(heap), and dict-backed test data holds every variant
    anyway.
    """
    if USE_EXPERIMENTAL_TIMER:
        return  # No cycles to break.

    gc.collect()
