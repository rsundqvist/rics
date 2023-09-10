"""Global settings for the splitting logic."""


class plot:
    """Global settings for the :func:`.plot`-function."""

    THOUSANDS_SEPARATOR: str = "'"
    """Sign to use when printing `bar_labels`."""
    THOUSANDS_SEPARATOR_CUTOFF: int = 10_000
    """Minimum value before `bar_labels` include a :attr:`THOUSANDS_SEPARATOR`."""
    ROW_UNIT: str = "rows"
    """Unit to append to the count when displaying number of rows on the bars."""

    DATA_LABEL: str = "Data"
    """Label of the blue bar."""
    FUTURE_DATA_LABEL: str = "Future data"
    """Label of the red bar."""

    DEFAULT_TIME_UNIT: str = "h"
    """Time unit to use by default when ``bar_labels=True`` and ``available=None``."""
