"""
Cron schedule, keeping all data before the schedule.
====================================================

Using a cron schedule with data, showing number of rows in each partition.
"""
import pandas

from rics import configure_stuff
from rics.ml.time_split import log_split_progress, plot, split

configure_stuff(format="[%(name)s:%(levelname)s] %(message)s")

data = pandas.date_range("2022", "2022-1-21", freq="38min")
config = dict(schedule="0 0 * * MON,FRI", before="all", after="3d", available=data)

plot(**config)
# %%
# The vertical, dashed lines shown denote the outer bounds of the data, beyond which the schedule may not extend.

for fold in log_split_progress(split(**config), logger="my-logger"):
    print("Doing work..")
