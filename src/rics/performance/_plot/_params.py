from collections.abc import Hashable, Iterable, Mapping
from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING, Any, ClassVar, Self

import numpy as np
import pandas as pd

from rics.collections.dicts import compute_if_absent
from rics.performance.plot_types import Candidate, Kind, TestData, Unit

from ..types import ResultsDict

if TYPE_CHECKING:
    from ..plot_types import Aggregation

FUNC: Candidate = "Candidate"
DATA: TestData = "Test data"

# Keyword aliases accepted for the `x`/`hue` arguments, in addition to test-data dimension names.
_ALIASES: dict[str, str] = {"candidate": FUNC, "func": FUNC, "data": DATA, "test data": DATA, FUNC: FUNC, DATA: DATA}
_COMPLEMENT: dict[str, str] = {FUNC: DATA, DATA: FUNC}


@dataclass(frozen=True, kw_only=True)
class CatplotParams:
    data: pd.DataFrame = field(repr=False)
    x: str
    y: str
    hue: str
    kind: Kind

    horizontal: bool = field(metadata={"skip": True})
    names: list[str] = field(metadata={"skip": True})
    user_kwargs: Mapping[str, Any] = field(metadata={"skip": True})
    reference: float | None = field(default=None, metadata={"skip": True})
    """Reference value for the metric axis (e.g. ``1.0`` in speedup mode); draws a guide line. ``None`` disables."""

    DEFAULTS: ClassVar[dict[str, Any]] = {"errorbar": "sd", "estimator": "min", "aspect": 2}
    DEFAULTS_BY_KIND: ClassVar[dict[Kind, dict[str, Any]]] = {
        "bar": {"capsize": 0.2},
        "point": {"capsize": 0.2},
    }
    COMPUTED_DEFAULTS: ClassVar[tuple[str, ...]] = ("order", "hue_order", "log_scale")

    @classmethod
    def reserved_keys(cls) -> set[str]:
        return {f.name for f in fields(cls) if not f.metadata.get("skip")}

    def __post_init__(self) -> None:
        if keys := self.reserved_keys().intersection(self.user_kwargs):
            msg = f"Bad `kwargs`: {keys=} are reserved."
            error = ValueError(msg)

            if "y" in keys:
                y = self.user_kwargs["y"]
                error.add_note(f"HINT ({y=}): Use `horizontal=True` to plot timings on the X-axis.")
            if "hue" in keys:
                hue = self.user_kwargs["hue"]
                error.add_note(f"HINT ({hue=}): Use the `hue=` argument of `plot_run` instead.")

            raise error

        for role, column in (("x", self.x), ("hue", self.hue)):
            if column not in self.data.columns:
                msg = f"Bad {role}={column!r}; not a column in the data ({list(self.data.columns)})."
                raise ValueError(msg)

    @classmethod
    def make(
        cls,
        run_results: ResultsDict | pd.DataFrame,
        *,
        x: str | None = None,
        hue: str | None = None,
        horizontal: bool = False,
        unit: Unit | None = None,
        kind: Kind = "bar",
        names: Iterable[str] = (),
        relative_to: str | None = None,
        agg: "Aggregation" = "min",
        **kwargs: Any,
    ) -> Self:
        """Create instance from run results."""
        names = [*names]

        if relative_to is None:
            df = _make_df(run_results, names)
            y = _resolve_y(unit, df=df)
            reference = None
        else:
            if unit is not None:
                msg = f"Cannot combine {unit=} with relative_to={relative_to!r}; speedup is dimensionless."
                raise ValueError(msg)
            df = _make_speedup_df(run_results, baseline=relative_to, names=names, agg=agg)
            y = "speedup"
            reference = 1.0

        x_col, hue_col = _resolve_x_hue(x, hue, names=names, df=df)

        return cls(
            data=df,
            x=x_col,
            y=y,
            horizontal=horizontal,
            hue=hue_col,
            kind=kind,
            names=names,
            reference=reference,
            user_kwargs={**kwargs},
        )

    def to_kwargs(self) -> dict[str, Any]:
        """Convert to :func:`seaborn.catplot` keyword arguments."""
        kwargs = dict(self.user_kwargs)

        for key in self.reserved_keys():
            kwargs[key] = getattr(self, key)

        for key, default in self.DEFAULTS.items():
            kwargs.setdefault(key, default)

        for key, default in self.DEFAULTS_BY_KIND.get(self.kind, {}).items():
            kwargs.setdefault(key, default)

        for key in self.COMPUTED_DEFAULTS:
            compute_if_absent(kwargs, key, self._compute_default)

        if self.names:
            self._handle_row_col(kwargs)

        if self.horizontal:
            x = kwargs["x"]
            kwargs["x"] = kwargs["y"]
            kwargs["y"] = x

        return kwargs

    @property
    def want_log_scale_hack(self) -> bool:
        return self.kind == "bar"

        user_log_scale = self.user_kwargs.get("log_scale")
        if not user_log_scale:
            return True  # No explicit user choice - apply

        # TODO(me): bool, number, or pair of bools or numbers

        # and isinstance(self.user_kwargs.get("log_scale"), tuple)

    def _compute_default(self, key: str) -> Any:
        df = self.data

        match key:
            case "order":
                return df[self.x].unique().tolist()
            case "hue_order":
                return df[self.hue].unique().tolist()
            case "log_scale":
                if self.reference is not None:
                    return None  # Speedup is a linear ratio; the reference line marks the baseline.
                column = next(filter(lambda c: c.startswith("Time ["), df.columns))
                means = df.groupby([DATA, FUNC], observed=True)[column].mean()
                return (False, True) if means.max() / means.min() > 20 else None  # noqa: PLR2004

        raise KeyError(f"Bad {key=}. Possible choices={self.COMPUTED_DEFAULTS}.")

    def _handle_row_col(self, kwargs: dict[str, Any]) -> None:
        names = self.names
        updates = {}

        # We could print something like f"{label}: [row]", but this could add a lot of additional text to the legend
        # or x-axis. I think this is a better way to do it.
        hidden = {names.index(name) for key in ("row", "col") if (name := kwargs.get(key)) in names}

        # Would be nice if data label formatting was configurable. For now though, we'll settle for this.
        formatters = {i: f"{name} = {{}}" for i, name in enumerate(names) if i not in hidden}

        def format_label(label: tuple[Hashable]) -> str:
            if not isinstance(label, tuple) or len(label) != len(names):
                raise TypeError(f"Cannot format {label=} using {names=}.")
            g = (template.format(lv) for i, lv in enumerate(label) if (template := formatters.get(i)))
            return " | ".join(g)

        # Only the axis that actually shows the composite DATA label needs its order reformatted; x/hue bound to a
        # single named dimension (or the candidate) keep their raw order.
        for axis, order_key in (("x", "order"), ("hue", "hue_order")):
            if getattr(self, axis) == DATA and (old_order := kwargs.get(order_key)):
                updates[order_key] = np.unique([format_label(label) for label in old_order]).tolist()

        data = kwargs["data"].copy()
        data[DATA] = data[DATA].map(format_label)
        updates["data"] = data

        # Don't write updates until we're done; allows caller to skip if needed.
        kwargs.update(updates)


def _make_df(run_results: ResultsDict | pd.DataFrame, names: list[str]) -> pd.DataFrame:
    from rics.performance import to_dataframe

    if isinstance(run_results, dict):
        df = to_dataframe(run_results, names=names)
    else:
        df = run_results.copy()

        if names and {*names}.difference(df.columns):
            df[names] = pd.DataFrame.from_records(df[DATA])

        return df

    as_category = [DATA, FUNC]
    df[as_category] = df[as_category].astype("category")
    return df


def _make_speedup_df(
    run_results: ResultsDict | pd.DataFrame,
    *,
    baseline: str,
    names: list[str],
    agg: "Aggregation",
) -> pd.DataFrame:
    from rics.performance import relative_to

    summary = relative_to(run_results, baseline=baseline, names=names, agg=agg)
    df = summary.rename(columns={"candidate": FUNC, "data": DATA})
    df[[DATA, FUNC]] = df[[DATA, FUNC]].astype("category")
    return df


def _resolve_x_hue(
    x: str | None,
    hue: str | None,
    *,
    names: list[str],
    df: pd.DataFrame,
) -> tuple[str, str]:
    """Resolve `x` and `hue` to real column names.

    Accepts the ``'candidate'``/``'data'`` aliases, a test-data dimension `name`, or a raw column. When omitted, `x`
    defaults to the complement of `hue` (or the higher-cardinality of candidate/data), and `hue` to the complement of
    `x` (falling back to the candidate column when `x` is a named dimension).
    """

    def resolve(value: str | None, role: str) -> str | None:
        if value is None:
            return None
        column = _ALIASES.get(value.lower(), value)
        if column not in df.columns and column not in names:
            allowed = ["candidate", "data", *names]
            msg = f"Bad {role}={value!r}; expected one of {allowed} or a data column."
            raise ValueError(msg)
        return column

    x_col = resolve(x, "x")
    hue_col = resolve(hue, "hue")

    if x_col is None:
        if hue_col in _COMPLEMENT:
            x_col = _COMPLEMENT[hue_col]
        else:
            n_data, n_func = df[[DATA, FUNC]].nunique()
            x_col = DATA if n_data > n_func else FUNC

    if hue_col is None:
        hue_col = _COMPLEMENT.get(x_col, FUNC)

    return x_col, hue_col


def _resolve_y(unit: Unit | None, *, df: pd.DataFrame) -> str:
    if unit is None:
        return _compute_nice_y(df)

    if unit == "us":
        unit = "μs"

    y = f"Time [{unit}]"
    if y not in df:
        msg = f"Bad {unit=}; column '{y}' not present in data."
        raise TypeError(msg)
    return y


def _compute_nice_y(df: pd.DataFrame) -> str:
    """Pick the unit with the most "human" scale; whole numbers around one hundred."""
    from numpy import log10

    columns = [c for c in df.columns if c.startswith("Time [")]
    means = df.groupby([DATA, FUNC], observed=True)[columns].mean()

    residuals = log10(means) - 2
    avg_residual_by_time_column = residuals.mean(axis="index")
    y = avg_residual_by_time_column.abs().idxmin()

    assert isinstance(y, str)  # noqa: S101
    return y
