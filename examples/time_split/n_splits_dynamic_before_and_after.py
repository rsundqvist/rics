"""Removing folds with ``n_splits``. Dynamic ``before`` and ``after``-data.
===========================================================================

Dynamic before/after-ranges, with removed partitions.
"""

import pandas
from rics import configure_stuff
from rics.ml.time_split import log_split_progress, plot, split

configure_stuff(datefmt="")

data = pandas.date_range("2022", "2022-2", freq="15s")
config = dict(schedule="0 0 * * MON,FRI", before=1, after=2, available=data, n_splits=4)

plot(**config, show_removed=True)
# %%
# Any non-zero integer before/after-range may be used. Setting ``show_removed=True`` forces plotting of folds that would
# be silently discarded by the :func:`~rics.ml.time_split.split`-function. Later folds are preferred.

for fold in log_split_progress(split(**config), logger="my-logger"):
    print("Doing work..")
