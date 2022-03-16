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
The `IMDb dataset`_ consists of multiple data collections. The following example retrieves Title Basics data.

>>> from rics.utility.misc import get_local_or_remote
>>> import pandas as pd
>>>
>>> file = "name.basics.tsv.gz"
>>> local_root = "my-data"
>>> remote_root = "https://datasets.imdbws.com"
>>> path = get_local_or_remote(file, local_root, remote_root, show_progress=True) # doctest: +SKIP
>>> pd.read_csv(path, sep="\t").shape # doctest: +SKIP
https://datasets.imdbws.com/name.basics.tsv.gz: 100%|██████████| 214M/214M [00:05<00:00, 39.3MiB/s]
(11453719, 6)

We have download `name.basics.tsv.gz` the first time, but ``get_local_or_remote`` returns immediately the second
time it is called. A refetch can be forced using ``force_remote=True``.

>>> path = get_local_or_remote(file, local_root, remote_root, show_progress=True) # doctest: +SKIP
>>> pd.read_csv(path, sep="\t").shape # doctest: +SKIP
(11453719, 6)

.. _IMDb dataset:
    https://www.imdb.com/interfaces/
