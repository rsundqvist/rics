=================================
Fetching data from remote sources
=================================
Get data from a remote source, then cache it locally. Supports postprocessing as well in which case both raw and
postprocessed data is stored.

.. automethod:: rics.utility.misc.get_local_or_remote
   :noindex:

.. warning::
    This function is meant for manual work. There is no automatic handling of failures of any kind.

------------------------------------------
Example: Downloading data with local cache
------------------------------------------
Fetch the Title Basics table (a CSV file) of the `IMDb dataset`_.

>>> from rics.utility.misc import get_local_or_remote
>>> import pandas as pd
>>>
>>> file = "name.basics.tsv.gz"
>>> local_root = "my-data"  # default = "."
>>> remote_root = "https://datasets.imdbws.com"
>>> path = get_local_or_remote(file, remote_root, local_root, show_progress=True) # doctest: +SKIP
>>> pd.read_csv(path, sep="\t").shape # doctest: +SKIP
https://datasets.imdbws.com/name.basics.tsv.gz: 100%|██████████| 214M/214M [00:05<00:00, 39.3MiB/s]
(11453719, 6)

We had download `name.basics.tsv.gz` the first time, but ``get_local_or_remote`` returns immediately the second
time it is called. Fetching can be forced using ``force_remote=True``.

>>> path = get_local_or_remote(file, remote_root, local_root, show_progress=True) # doctest: +SKIP
>>> pd.read_csv(path, sep="\t").shape # doctest: +SKIP
(11453719, 6)

.. _IMDb dataset:
    https://www.imdb.com/interfaces/
