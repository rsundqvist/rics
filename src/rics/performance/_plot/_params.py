from collections.abc import Hashable, Iterable, Mapping
from dataclasses import dataclass, field, fields
from typing import Any, ClassVar, Literal, Self

import numpy as np
import pandas as pd

from rics.collections.dicts import compute_if_absent
from rics.performance.plot_types import Candidate, FuncOrData, Kind, TestData, Unit
from rics.types import LiteralHelper

from ..types import ResultsDict

FUNC: Candidate = "Candidate"
DATA: TestData = "Test data"


@dataclass(frozen=True, kw_only=True)
class CatplotParams:
    data: pd.DataFrame = field(repr=False)
    x: FuncOrData
    y: str
    hue: FuncOrData
    kind: Kind

    horizontal: bool = field(metadata={"skip": True})
    names: list[str] = field(metadata={"skip": True})
    user_kwargs: Mapping[str, Any] = field(metadata={"skip": True})

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
                error.add_note(f"HINT ({hue=}): Use `x='data' | 'candidate'` to control X-axis and Hue variables.")

            raise error

        helper = LiteralHelper[FuncOrData](FuncOrData)
        helper.check(self.x, "x")
        helper.check(self.hue, "hue")

    @classmethod
    def make(
        cls,
        run_results: ResultsDict | pd.DataFrame,
        *,
        x: Literal["candidate", "data"] | None = None,
        horizontal: bool = False,
        unit: Unit | None = None,
        kind: Kind = "bar",
        names: Iterable[str] = (),
        **kwargs: Any,
    ) -> Self:
        """Create instance from run results."""
        names = [*names]
        df = _make_df(run_results, names)

        # MyPy thinks these are both string
        x_col, hue_col = (DATA, FUNC) if _is_data_x(x, df=df) else (FUNC, DATA)

        return cls(
            data=df,
            x=x_col,
            y=_resolve_y(unit, df=df),
            horizontal=horizontal,
            hue=hue_col,
            kind=kind,
            names=names,
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

        order_key = "hue_order" if self.hue == DATA else "order"
        if old_order := kwargs.get(order_key):
            updates[order_key] = np.unique([format_label(label) for label in old_order]).tolist()

        # assert sorted(self.data.columns.intersection(names)) == sorted(names)

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


def _is_data_x(x_col: Literal["candidate", "data"] | None, *, df: pd.DataFrame) -> bool:
    if x_col is None:
        n_data, n_func = df[[DATA, FUNC]].nunique()
        return n_data > n_func  # type: ignore[no-any-return]
    else:
        return x_col.lower().startswith("d")


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
