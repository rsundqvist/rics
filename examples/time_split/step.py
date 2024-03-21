"""Fold sampling using the ``step``-argument.
=============================================

Filtering every other Thursday, preferring later folds.
"""

import pandas
from rics import configure_stuff
from rics.ml.time_split import log_split_progress, plot, split

configure_stuff(datefmt="")

data = pandas.date_range("2022-01", "2022-03")
config = dict(schedule="0 0 * * THU", after="5d", step=2, n_splits=3, available=data)

plot(**config, bar_labels="h", show_removed=True)
# %%
# Specifying a `step` is useful especially when working with non-stationary but slow-moving distributions. The `step`
# argument will never reduce the number of folds below 1. The `n_splits` argument sets the `upper limit` on the number
# of folds created; fewer folds may be produced, depending on the outer range of the available data.

for fold in log_split_progress(split(**config), logger="my-logger"):
    print("Doing work..")

# %%
# You may also use cron directly to filter a weekday based on the date. For example, ``'0 0 * * THU#2'`` will select the
# second Thursday of every month.
