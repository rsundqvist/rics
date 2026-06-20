"""Grouping of test-data variants into *strata* of comparable cost.

A stratum is a group of data labels that share a single calibrated iteration ``number`` (see :mod:`._autonumber`).
Without stratification all variants share one ``number`` -- driven by the slowest variant -- which leaves cheap
variants under-sampled. The :func:`resolve_stratify` helper turns the user-facing `stratify` argument into a
``(data_label) -> stratum_key`` callable, and :func:`build_strata` uses it to bucket the labels.

The ``"auto"`` mode does not guess from the label shape; it relies on the autotimer (see
:func:`estimate_label_costs`) to measure per-label cost and then picks the single tuple level whose grouping best
clusters comparable-cost variants -- see :func:`choose_auto_level`.
"""

import logging
from collections.abc import Callable, Hashable, Iterable, Iterator, Mapping
from time import perf_counter
from timeit import Timer
from typing import TYPE_CHECKING, Any, TypeAlias

from rics.strings import format_perf_counter

from ._skip_if import SkipIfFunc
from .types import CandFunc, DataType, StratifyArg, StratifyFunc, Ts

if TYPE_CHECKING:
    from ._generated_data import GeneratedData

_Cost: TypeAlias = dict[Hashable, float]
"""Measured per-label cost estimate (seconds per call); see :func:`estimate_label_costs`."""

_MIN_AUTO_LEVELS = 2
"""``stratify="auto"`` needs at least this many tuple levels to have a meaningful choice between groupings."""

_AUTO_PROBE_SECONDS = 1e-3
"""Default per ``(candidate, label)`` time budget for the ``"auto"`` cost probe; just enough to measure reliably."""

_Strata: TypeAlias = dict[Hashable, set[Hashable]]
"""Stratum key -> the data labels grouped into that stratum (the raw mapping wrapped by :class:`Strata`)."""

_AnySkipIf: TypeAlias = "SkipIfFunc[Any, *tuple[Any, ...]] | None"


class Strata(Mapping[Hashable, frozenset[Hashable]]):
    """A fitted stratification: ``{stratum_key: {data_label, ...}}``, plus a record of how it was derived.

    Behaves as a read-only :class:`~collections.abc.Mapping` of ``stratum_key`` to the labels in that stratum. Pass an
    instance to :meth:`.MultiCaseTimer.run` (or get one from :meth:`.MultiCaseTimer.compute_strata`) to reuse a grouping
    without re-deriving it -- handy to avoid repeating the ``"auto"`` cost probe across runs, or to inspect what
    ``"auto"`` chose.

    Attributes:
        source: How the grouping was derived, e.g. ``"auto(level=0)"``, ``"level=1"``, ``"full"``, ``"callable"`` or
            ``"none"`` (a single shared stratum).
        skip_if: The `skip_if` filter in effect when the grouping was fit (``None`` if unfiltered). Recorded so
            :meth:`.MultiCaseTimer.run` can warn when the grouping is reused under a different filter.
        costs: Per-label costs measured by the ``"auto"`` probe, or ``None`` for other modes.
    """

    def __init__(
        self,
        groups: Mapping[Hashable, Iterable[Hashable]],
        *,
        source: str,
        skip_if: _AnySkipIf = None,
        costs: _Cost | None = None,
    ) -> None:
        self._groups: dict[Hashable, frozenset[Hashable]] = {k: frozenset(v) for k, v in groups.items()}
        self._stratum_of: dict[Hashable, Hashable] = {
            label: key for key, labels in self._groups.items() for label in labels
        }
        self.source = source
        self.skip_if = skip_if
        self.costs = None if costs is None else dict(costs)

    def stratum_of(self, label: Hashable) -> Hashable:
        """Return the stratum key that `label` was grouped into."""
        return self._stratum_of[label]

    @property
    def labels(self) -> frozenset[Hashable]:
        """All data labels covered across the strata."""
        return frozenset(self._stratum_of)

    def __getitem__(self, key: Hashable) -> frozenset[Hashable]:
        return self._groups[key]

    def __iter__(self) -> Iterator[Hashable]:
        return iter(self._groups)

    def __len__(self) -> int:
        return len(self._groups)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(source={self.source!r}, strata={len(self)}, labels={len(self._stratum_of)})"


def resolve_stratify(
    stratify: StratifyArg,
    labels: Iterable[Hashable],
    *,
    cost: _Cost | None = None,
) -> StratifyFunc | None:
    """Resolve the user-facing `stratify` argument into a :data:`StratifyFunc` (or ``None``).

    Args:
        stratify: See :data:`StratifyArg`.
        labels: All data labels; inspected to resolve ``"auto"``.
        cost: Measured per-label costs used to resolve ``"auto"``; see :func:`choose_auto_level`. When omitted (e.g.
            an explicit ``number`` makes calibration -- and therefore grouping -- moot), ``"auto"`` falls back to the
            first viable level.

    Returns:
        A ``(data_label) -> stratum_key`` callable, or ``None`` for a single shared stratum.

    Raises:
        TypeError: If `stratify` is a ``bool``, a string other than ``"full"`` or ``"auto"``, or an otherwise
            unsupported type.
        ValueError: If `stratify` is ``"auto"`` when `labels` are not tuples with at least two levels. The message
            advises the viable alternative (e.g. ``stratify=0`` for single-level tuples, ``"full"`` for non-tuples).
    """
    if stratify is None:
        return None
    if isinstance(stratify, str):
        if stratify == "full":
            return _identity
        if stratify == "auto":
            return _level_stratifier(_auto_level(labels, cost))
        raise TypeError(f"Invalid {stratify=}; expected 'full', 'auto', an int level, or a callable.")
    if isinstance(stratify, bool):  # bool is an int subclass; reject it as an ambiguous level.
        raise TypeError(f"Invalid {stratify=}; expected 'full', 'auto', an int level, or a callable.")
    if isinstance(stratify, int):
        return _level_stratifier(stratify)
    if callable(stratify):
        return stratify
    raise TypeError(f"Invalid {stratify=}; expected 'full', 'auto', an int level, or a callable.")


def build_strata(labels: Iterable[Hashable], stratify: StratifyFunc | None) -> _Strata:
    """Group `labels` into strata using the (already resolved) `stratify` callable.

    Args:
        labels: All data labels.
        stratify: A resolved :data:`StratifyFunc`, or ``None`` for a single shared stratum.

    Returns:
        A mapping ``stratum_key -> {data_label, ...}``. The single-stratum key is ``None``.
    """
    if stratify is None:
        return {None: set(labels)}
    strata: _Strata = {}
    for label in labels:
        strata.setdefault(stratify(label), set()).add(label)
    return strata


def make_strata(
    labels: Iterable[Hashable],
    stratify: StratifyArg,
    *,
    cost: _Cost | None = None,
    skip_if: _AnySkipIf = None,
) -> Strata:
    """Resolve `stratify` and bucket `labels` into a fitted :class:`Strata`.

    Args:
        labels: All data labels.
        stratify: Any :data:`StratifyArg`. A :class:`Strata` is returned unchanged; any other
            :data:`StrataMapping` is wrapped (and validated to cover `labels`). ``"auto"`` requires `cost` to pick the
            best level; without it the first viable level is used.
        cost: Per-label costs for ``"auto"``; see :func:`estimate_label_costs`.
        skip_if: The filter in effect while fitting, recorded on the returned :class:`Strata`.

    Returns:
        The fitted grouping.

    Raises:
        ValueError: If `stratify` is a mapping that does not cover every data label.
    """
    if isinstance(stratify, Strata):
        return stratify
    labels = [*labels]
    if isinstance(stratify, Mapping):
        strata = Strata(stratify, source="mapping", skip_if=skip_if)
        uncovered = [label for label in labels if label not in strata.labels]
        if uncovered:
            raise ValueError(f"stratify mapping does not cover every data label; missing: {uncovered}.")
        return strata
    stratify_func = resolve_stratify(stratify, labels, cost=cost)
    groups = build_strata(labels, stratify_func)
    return Strata(groups, source=_describe_source(stratify, labels, cost), skip_if=skip_if, costs=cost)


def _describe_source(stratify: StratifyArg, labels: list[Hashable], cost: _Cost | None) -> str:
    if stratify is None:
        return "none"
    if stratify == "full":
        return "full"
    if stratify == "auto":
        return f"auto(level={_auto_level(labels, cost)})"
    if isinstance(stratify, int):  # bool already rejected by resolve_stratify
        return f"level={stratify}"
    return "callable"


def _identity(label: Hashable) -> Hashable:
    return label


def _level_stratifier(level: int) -> StratifyFunc:
    def stratify(label: Hashable) -> Hashable:
        if not isinstance(label, tuple):
            raise TypeError(
                f"Cannot stratify by {level=}: data label {label!r} is not a tuple. "
                "Only stratify='full' or a callable can stratify non-tuple labels.",
            )
        if not -len(label) <= level < len(label):
            raise ValueError(
                f"Cannot stratify by {level=}: data label {label!r} has only {len(label)} level(s). "
                f"Use a level in [{-len(label)}, {len(label) - 1}], or 'full'/a callable.",
            )
        key: Hashable = label[level]
        return key

    return stratify


def _auto_levels(labels: list[Hashable]) -> range:
    """Validate that `labels` support ``stratify="auto"`` and return the candidate tuple levels to choose between.

    Raises:
        ValueError: If `labels` are not tuples, or are tuples with fewer than two levels (so there is nothing for
            ``"auto"`` to choose between). The message advises the viable alternative for the specific case.
    """
    tuples = [label for label in labels if isinstance(label, tuple)]
    if len(tuples) != len(labels):
        # int levels also require tuples, so they are not viable here either.
        raise ValueError(
            f"Cannot stratify={'auto'!r}: not all data labels are tuples. "
            "Only stratify='full' or a callable can stratify non-tuple labels.",
        )
    width = min((len(t) for t in tuples), default=0)
    if width < _MIN_AUTO_LEVELS:
        hint = (
            "Use stratify=0 to group by the first tuple element, or 'full'/a callable."
            if width >= 1
            else "Only stratify='full' or a callable can stratify these labels."
        )
        raise ValueError(
            f"Cannot stratify={'auto'!r}: tuple labels have only {width} level(s), too few to choose between. {hint}",
        )
    return range(width)


def choose_auto_level(labels: Iterable[Hashable], levels: Iterable[int], cost: _Cost) -> int:
    """Pick the tuple `level` whose grouping best clusters `labels` of comparable measured `cost`.

    A stratum shares a single calibrated ``number``, so its members must have comparable cost. The chosen level is
    the one minimizing the worst within-group cost *ratio* -- i.e. the grouping least likely to mix scales (such as
    1k/100k/10M-row inputs) into one stratum. Ratios make the choice scale-free, so moderate intra-group differences
    are tolerated while order-of-magnitude jumps dominate. Ties resolve to the lowest level.

    Args:
        labels: All data labels (already validated as uniform tuples by :func:`_auto_levels`).
        levels: The candidate levels to choose between.
        cost: Per-label costs; labels absent from it (e.g. fully ``skip_if``-filtered) are ignored.

    Returns:
        The selected tuple level.
    """
    costed = [label for label in labels if label in cost]

    def worst_within_group_ratio(level: int) -> float:
        groups: dict[Hashable, list[float]] = {}
        for label in costed:
            groups.setdefault(label[level], []).append(cost[label])  # type: ignore[index]
        return max((max(g) / min(g) for g in groups.values()), default=1.0)

    return min(levels, key=worst_within_group_ratio)


def _auto_level(labels: Iterable[Hashable], cost: _Cost | None) -> int:
    """Resolve the ``"auto"`` tuple level: the cost-optimal level, or the first viable one when `cost` is unknown."""
    labels = [*labels]
    levels = _auto_levels(labels)
    return levels[0] if cost is None else choose_auto_level(labels, levels, cost)


def estimate_label_costs(
    candidates: dict[str, CandFunc[DataType]],
    test_data: "dict[Hashable, DataType] | GeneratedData[DataType, *Ts]",
    *,
    skip_if: SkipIfFunc[DataType, *Ts] | None,
    make_timer: Callable[[CandFunc[DataType], DataType], Timer],
    logger: logging.Logger | logging.LoggerAdapter[Any],
    min_probe_time: float = _AUTO_PROBE_SECONDS,
) -> _Cost:
    """Measure a per-call cost estimate for each data label, to drive ``stratify="auto"``.

    Each label is timed -- via the same autorange machinery used for calibration -- against every candidate, and the
    worst (slowest) per-call time is kept as the label's cost. Labels skipped by `skip_if` for every candidate are
    omitted. `min_probe_time` is the per ``(candidate, label)`` budget: larger values reduce noise at the cost of a
    slower probe; a label whose single call already exceeds it is timed exactly once.

    Returns:
        A ``data_label -> seconds_per_call`` mapping.
    """
    from ._autonumber import autonumber  # Local import: _autonumber imports this module at top level.

    start = perf_counter()
    costs: _Cost = {}
    for data_label in test_data:
        for candidate_label, func in candidates.items():
            calibration = autonumber(
                func,
                candidate_label,
                test_data,
                {data_label},
                time_allocation=min_probe_time,
                skip_if=skip_if,
                make_timer=make_timer,
            )
            if calibration is None:
                continue
            number, total_time = calibration
            per_call = total_time / number
            costs[data_label] = max(costs.get(data_label, 0.0), per_call)

    logger.debug("Estimated per-label costs for stratify='auto' in %s: %s.", format_perf_counter(start), costs)
    return costs
