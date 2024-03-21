"""Timedelta-schedule, 5 days ``before``-data.
==============================================

Using an unbounded timedelta-schedule, with custom bar labels.
"""

import pandas
from rics import configure_stuff
from rics.ml.time_split import log_split_progress, plot, split

configure_stuff(datefmt="")

data = pandas.date_range("2022", "2022-1-21", freq="38min").to_series()
config = dict(schedule="3d", before="5d", available=data)

plot(**config, bar_labels=[(f"{i}-left", f"{i}-right") for i in range(4)])
# %%
# Unbounded (timedelta-string or CRON) schedules require available data to materialize the schedule. When using the
# ``plot``-function, this data is also used to create bar labels unless they're explicitly given, as seen above.

for fold in log_split_progress(split(**config), logger="my-logger"):
    print("Doing work..")
