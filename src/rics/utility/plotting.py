"""Plotting utility methods."""

import functools

ERROR_BAR_CAPSIZE: float = 0.1


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
    import seaborn as sns  # type: ignore

    sns.set_theme(context="talk")

    sns.barplot = functools.partial(sns.barplot, capsize=ERROR_BAR_CAPSIZE)
    sns.catplot = functools.partial(sns.catplot, capsize=ERROR_BAR_CAPSIZE, height=5)


def configure_matplotlib() -> None:
    """Configure Matplotlib figure plotting.

    Caveat Emptor: May do strange stuff 👻.

    Raises:
        ModuleNotFoundError: If matplotlib is not installed.
    """
    import matplotlib.pyplot as plt  # type: ignore
    import matplotlib.ticker as mtick  # type: ignore

    plt.rcParams["figure.figsize"] = (20, 5)
    # plt.rcParams["figure.tight_layout"] = True # Doesn't exist -- must call afterwards if figure is created for you
    plt.subplots = functools.partial(plt.subplots, tight_layout=True)

    mtick.PercentFormatter = functools.partial(mtick.PercentFormatter, xmax=1)
