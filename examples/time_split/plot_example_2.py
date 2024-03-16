"""List-schedule, without ``available`` data.
=============================================

Using an explicit schedule without data, showing number of hours in each partition.
"""

import pandas
from rics import configure_stuff
from rics.ml.time_split import log_split_progress, plot, split

configure_stuff(format="[%(name)s:%(levelname)s] %(message)s")

data = pandas.date_range("2022", "2022-1-21", freq="38min")
config = dict(schedule="0 0 * * MON,FRI", before="all", after="3d", available=data)

plot(**config)
# %%
# Note that the last timestamp (**'2022-01-14'**) of the schedule was not included; this is because it was used as the
# end date (since ``after=1``) of the second-to-last timestamp (**'2022-01-10'**), which expands the Future data until
# the next scheduled time.

for fold in log_split_progress(split(**config), logger="my-logger"):
    print("Doing work..")
