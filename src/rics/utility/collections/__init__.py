"""Support for Python collections."""

from rics.utility.collections._dict_functions import compute_if_absent, flatten_dict, reverse_dict
from rics.utility.collections.inherited_keys_dict import InheritedKeysDict

__all__ = [
    "compute_if_absent",
    "InheritedKeysDict",
    "reverse_dict",
    "flatten_dict",
]
