"""Plotting utility methods."""

import functools
from typing import Literal, Optional, Protocol as _Protocol, Union

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
from matplotlib.axis import Axis as _Axis, XAxis as _XAxis
from matplotlib.ticker import FuncFormatter as _FuncFormatter, IndexLocator as _IndexLocator

ERROR_BAR_CAPSIZE: float = 0.1


class HasXAxis(_Protocol):
    """Protocol class indicating something that as an X-axis."""

    xaxis: _XAxis
    """X-Axis attribute."""


def configure() -> None:
    """Call all configure-functions in this module.

    See this `demo notebook <https://github.com/rsundqvist/rics/blob/master/jupyterlab/demo/plotting/Style.ipynb>`_ for
    an example of figures rendered using these settings.
    """
    configure_seaborn()
    configure_matplotlib()


def configure_seaborn() -> None:
    """Configure Seaborn figure plotting.

    Caveat Emptor: May do strange stuff 👻.

    Raises:
        ModuleNotFoundError: If Seaborn is not installed.
    """
    sns.set_theme(context="talk")

    sns.barplot = functools.partial(sns.barplot, capsize=ERROR_BAR_CAPSIZE)
    sns.catplot = functools.partial(sns.catplot, capsize=ERROR_BAR_CAPSIZE, height=5)


def configure_matplotlib() -> None:
    """Configure Matplotlib figure plotting.

    Caveat Emptor: May do strange stuff 👻.

    Raises:
        ModuleNotFoundError: If matplotlib is not installed.
    """
    plt.rcParams["figure.figsize"] = (20, 5)
    # plt.rcParams["figure.tight_layout"] = True # Doesn't exist -- must call afterwards if figure is created for you
    plt.subplots = functools.partial(plt.subplots, tight_layout=True)

    mtick.PercentFormatter = functools.partial(mtick.PercentFormatter, xmax=1)


def pi_ticks(ax: Union[_Axis, HasXAxis], half_rep: Literal["frac", "dec"] = None) -> None:
    """Decorate an axis by setting the labels to multiples of pi.

    The `half_rep` must be one of:

        * `'frac'`: output `0/2π, 1/2π, 2/2π, 3/2π..`
        * `'dec'`: output `0.0π, 0.5π, 1.0π, 1.5π..`
        * ``None``: output `0, π, 2π, 3π..`

    Args:
        ax: An axis to decorate, or an object with an `xaxis` attribute.
        half_rep: Controls how fractions of pi are represented on the x-axis.

    """
    axis: _Axis = ax.xaxis if hasattr(ax, "xaxis") else ax

    start = axis.get_data_interval()[0]
    helper = _PiTickHelper(half_rep, start)

    axis.set_major_locator(helper.locator)
    axis.set_major_formatter(helper.formatter)


class _PiTickHelper:
    PI: float = 3.14159265359
    HALF_PI = PI / 2

    def __init__(self, half: Optional[Literal["frac", "dec"]], start: float) -> None:
        if half not in (None, "frac", "dec"):
            raise ValueError(f"Argument {half=} not in ('frac', 'dec', None).")

        self.half = half
        r = self.HALF_PI if half else self.PI
        self.offset = r * round(start / r) - start  # Offset from nearest (half) multiple of pi.

        self.locator = _IndexLocator(base=self.HALF_PI if self.half else self.PI, offset=self.offset)
        self.formatter = _FuncFormatter(self._format)

    def _format(self, x: float, _pos: int) -> str:
        n = round(x / self.PI, 1)

        if self.half is None:
            if x == 0:
                return "0"
            if x == self.PI:
                return "π"

            return f"{int(n)}π"

        if self.half == "dec":
            return f"{n}π"

        return f"{int(n * 2)}/2π"
