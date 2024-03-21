from dataclasses import dataclass
from typing import Any

from seaborn import FacetGrid

from rics.performance.plot.types import Postprocessor


def make_postprocessors(kwargs: dict[str, Any]) -> list[Postprocessor]:
    """Construct postprocessors based on `kwargs`.

    Args:
        kwargs: Keyword arguments for :func:`seaborn.catplot`. May be modified.

    Returns:
        A list of postprocessors.
    """
    kind = kwargs["kind"]
    postprocessors: list[Postprocessor] = []

    if kind == "bar":
        # TODO(seaborn==0.13.2): log_scale makes bars vanish, so we do this instead.
        set_log_y = kwargs.pop("log_scale", None)
        postprocessors.append(BarPlotProcessor(bool(set_log_y)))

    return postprocessors


@dataclass(frozen=True)
class BarPlotProcessor(Postprocessor):
    set_log_y: bool

    def __call__(self, facet_grid: FacetGrid) -> None:
        fmt = "{:.3g}" if self.set_log_y else "{:.1f}"

        axes = facet_grid.axes.flat
        for ax in axes:
            for c in ax.containers:
                ax.bar_label(c, fmt=fmt, label_type="center", bbox={"boxstyle": "round", "fc": "0.8"})

        if self.set_log_y:
            # TODO(seaborn==0.13.2): log_scale makes bars vanish, so we do this instead.
            for ax in axes:
                ax.set_yscale("log")
