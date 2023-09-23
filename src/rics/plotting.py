"""Plotting utility methods."""
import typing as _t

from matplotlib.axis import Axis as _Axis, XAxis as _XAxis
from matplotlib.ticker import FuncFormatter as _FuncFormatter, IndexLocator as _IndexLocator

ERROR_BAR_CAPSIZE: float = 0.1

HalfRep = _t.Literal["fraction", "decimal", "frac", "dec", "f", "d"]


class HasXAxis(_t.Protocol):
    """Protocol class indicating something that as an X-axis."""

    xaxis: _XAxis
    """X-Axis attribute."""


def configure() -> None:
    """Call all configure-functions in this module."""
    configure_matplotlib()
    configure_seaborn()


def configure_seaborn() -> None:
    """Configure Seaborn figure plotting.

    Caveat Emptor: May do strange stuff 👻.

    Raises:
        ModuleNotFoundError: If Seaborn is not installed.
    """
    import functools
    import warnings

    import seaborn as sns

    warnings.filterwarnings("ignore", module="seaborn")

    sns.set_theme(context="talk")

    sns.barplot = functools.partial(sns.barplot, capsize=ERROR_BAR_CAPSIZE)
    sns.catplot = functools.partial(sns.catplot, capsize=ERROR_BAR_CAPSIZE, height=5)


def configure_matplotlib() -> None:
    """Configure Matplotlib figure plotting.

    Caveat Emptor: May do strange stuff 👻.

    Raises:
        ModuleNotFoundError: If matplotlib is not installed.
    """
    import functools

    import matplotlib.pyplot as plt
    import matplotlib.ticker as mtick

    plt.rcParams["figure.figsize"] = (20, 5)
    # plt.rcParams["figure.tight_layout"] = True # Doesn't exist -- must call afterward if figure is created for you
    plt.subplots = functools.partial(plt.subplots, tight_layout=True)

    mtick.PercentFormatter = functools.partial(mtick.PercentFormatter, xmax=1)


def pi_ticks(ax: _t.Union[_Axis, HasXAxis], half_rep: HalfRep = None) -> None:
    """Decorate an axis by setting the labels to multiples of pi.

    .. image:: ../_images/pi_ticks.png

    .. list-table:: Options for the `half_rep` argument.
       :header-rows: 1

       * - Value
         - Interpretation
         - Example output
       * - ``None``
         - Show integer multiples only.
         - `0, π, 2π, 3π..`
       * - `'f'` or `'fraction'`
         - Halves of `π` use fractional representation.
         - `0/2π, 1/2π, 2/2π, 3/2π..`
       * - `'d'` or `'decimal'`
         - Halves of `π` use decimal representation.
         - `0.0π, 0.5π, 1.0π, 1.5π..`

    Args:
        ax: An axis to decorate, or an object with an `xaxis` attribute.
        half_rep: Controls how fractions of `π` are represented on the x-axis.
    """
    axis: _Axis = ax.xaxis if hasattr(ax, "xaxis") else ax

    helper = _PiTickHelper(half_rep, start=axis.get_data_interval()[0])
    axis.set_major_locator(helper.locator)
    axis.set_major_formatter(helper.formatter)


class _PiTickHelper:
    PI: float = 3.14159265359
    HALF_PI: float = PI / 2

    def __init__(
        self,
        half_rep: _t.Optional[HalfRep],
        *,
        start: float,
    ) -> None:
        self.half = self._parse_half_rep(half_rep)
        r = self.HALF_PI if half_rep else self.PI
        self.offset = r * round(start / r) - start  # Offset from nearest (half) multiple of pi.

        self.locator = _IndexLocator(base=self.HALF_PI if self.half else self.PI, offset=self.offset)
        self.formatter = _FuncFormatter(self._format)

    @staticmethod
    def _parse_half_rep(half_rep: _t.Optional[str]) -> _t.Optional[_t.Literal["frac", "dec"]]:
        if half_rep is None:
            return None

        parsed_half = half_rep.lower()
        if parsed_half.startswith("f"):
            return "frac"
        if parsed_half.startswith("d"):
            return "dec"

        raise TypeError(f"Argument {half_rep=} not in ('[f]raction', '[d]ecimal', None).")

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
