"""Timedelta-based ``schedule`` and ``after`` arguments.
========================================================

By default, passing :attr:`~rics.ml.time_split.types.TimedeltaTypes` as both the ``schedule`` and the ``after`` argument
causes the folds to align to the right edge of the ``available`` data.
"""

from rics import configure_stuff
from rics.ml.time_split import log_split_progress, plot, settings, split

configure_stuff(datefmt="")

data = ("2022-02", "2022-03")
config = dict(schedule="7d", before="3d", after="5d", available=data)

plot(**config, bar_labels=False)

for fold in log_split_progress(split(**config), logger="my-logger"):
    print("Doing work..")

# %%
# Setting :attr:`settings.misc.snap_to_end <rics.ml.time_split.settings.misc.snap_to_end>` to ``False`` will adopt the
# default behavior used by :func:`pandas.date_range`.

settings.misc.snap_to_end = False
plot(**config, bar_labels=False)

for fold in log_split_progress(split(**config), logger="my-logger"):
    print("Doing work..")

# %%
# The configuration in :mod:`rics.ml.time_split.settings` are global, so changes made will remain in effect for all
# callers until the original value is reset.
settings.misc.snap_to_end = True
