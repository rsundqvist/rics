==========================
Translation format strings
==========================
The :class:`rics.translation.offline.Format` class defines the string format. These are simlar to regular fstrings, with
two significant exceptions:

    a. Keyword placeholders only: ``'{}'`` is not accepted, correct form is ``'{key-name}'``.
    b. Substrings surrounded by ``[]`` denote an optional element.

.. note::

   Most users will have little reason to use ``Format`` instances directly, but a basic understanding of the format is
   needed to customize translator output. The translator uses as many placeholders as possible by default, failing only
   if required placeholders for the format are missing.

Importing the class and defining a string format with an optional element ``', nice={is_nice}'``:

>>> from rics.translation.offline import Format
>>> fmt = Format('{id}:{name}[, nice={is_nice}]')

The ``Format`` class when used directly only returns required placeholders by default..

>>> fmt.fstring(), fmt.fstring().format(id=0, name='Tarzan')
('{id}:{name}', '0:Tarzan')

..but the `placeholders` attribute can be used to retrieve all placeholders, required and optional:

>>> fmt.placeholders
('id', 'name', 'is_nice')
>>> fmt.fstring(fmt.placeholders), fmt.fstring(fmt.placeholders).format(id=1, name='Morris', is_nice=True)
('{id}:{name}, nice={is_nice}', '1:Morris, nice=True')
