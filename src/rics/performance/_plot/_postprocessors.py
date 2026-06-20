from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from seaborn import FacetGrid

    from ._params import CatplotParams

from rics.performance.plot_types import Postprocessor


def make_postprocessors(kwargs: dict[str, Any], params: "CatplotParams") -> list[Postprocessor]:
    """Construct postprocessors based on `kwargs`.

    Args:
        kwargs: Keyword arguments for :func:`seaborn.catplot`. May be modified.
        params: The :class:`.CatplotParams` used to build `kwargs`.

    Returns:
        A list of postprocessors ``(FacetGrid) -> None``.
    """
    kind = kwargs["kind"]
    postprocessors: list[Postprocessor] = []

    if kind == "bar":
        # TODO(seaborn==0.13.2): log_scale makes bars vanish, so we do this instead.
        log_scale = kwargs.pop("log_scale", None)
        postprocessors.append(BarPlotProcessor(bool(log_scale), params.horizontal))

    if params.reference is not None:
        postprocessors.append(ReferenceLineProcessor(params.reference, params.horizontal))

    return postprocessors


@dataclass(frozen=True)
class BarPlotProcessor:
    log_scale: bool
    horizontal: bool

    def __call__(self, facet_grid: "FacetGrid") -> None:
        fmt = "{:.3g}" if self.log_scale else "{:.2f}"

        axes = [*facet_grid.axes.flat]
        for ax in axes:
            for c in ax.containers:
                ax.bar_label(c, fmt=fmt, padding=10, bbox={"boxstyle": "round", "fc": "0.8"})

        if self.log_scale:
            # TODO(seaborn==0.13.2): log_scale makes bars vanish, so we do this instead.
            for ax in axes:
                if self.horizontal:
                    ax.set_xscale("log")
                else:
                    ax.set_yscale("log")


@dataclass(frozen=True)
class ReferenceLineProcessor:
    """Draw a guide line on the metric axis (e.g. ``speedup == 1`` in :func:`.relative_to` mode)."""

    value: float
    horizontal: bool

    def __call__(self, facet_grid: "FacetGrid") -> None:
        for ax in facet_grid.axes.flat:
            line = ax.axvline if self.horizontal else ax.axhline
            line(self.value, ls="--", lw=1, color="0.4", zorder=0)
