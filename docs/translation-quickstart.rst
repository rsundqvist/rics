ID Translation
==============

Turn meaningless IDs into human-readable labels.

.. figure:: covid-europe-mplcyberpunk-theme.png

   Total number of `Covid cases`_ cases per day. IDs have been translated using the standard **id:name**-format.

.. note::
    The recommended way of creating and configuring fetchers is the :meth:`Translator.from_config()
    <rics.translation.Translator.from_config>` method. For details, see the :doc:`translation-config-format` page.

=============================
Translating IDs in 30 seconds
=============================
.. note::

   For a more complicated (and more realistic) use case, see
   `Example: DVD Rental Database <translation-quickstart.html#example-dvd-rental-database>`__.

In this example, we will translate data represented by::

    people:                       animals:
       id | name    | Gender        bestie_id | name   | is_nice
    ------+---------+--------      -----------+--------+---------
     1991 | Richard | Male                  0 | Tarzan | false
     1999 | Sofia   | Female                1 | Morris | true
                                            2 | Simba  | true

Normally, translations are fetched from external sources. For this demonstration however, we will simply enumerate the
translations:

>>> from rics.translation.fetching import MemoryFetcher
>>> from rics.translation import Translator
>>> # Create the translation keys
>>> MemoryFetcher(data={
...     "animals": {"id": [0, 1, 2], "name": ["Tarzan", "Morris", "Simba"], "is_nice": [True, True, False]},
...     "people": {"id": [1999, 1991], "name": ["Sofia", "Richard"]},
... })
>>> # Create translator
>>> translator = Translator(fetcher, fmt='{id}:{name}[, nice={is_nice}]')
>>> # Translate
>>> data = {'animals': [0, 2], 'people': [1991, 1999]}
>>> for key, translated_table in translator.translate(data).items():
>>>     print(f'Translations for {repr(key)}:')
>>>     for translated_id in translated_table:
>>>         print(f'    {repr(translated_id)}')
Translations for 'animal':
    '0:Tarzan, nice=False'
    '2:Simba, nice=True'
Translations for 'people':
    '1991:Richard'
    '1999:Sofia'
