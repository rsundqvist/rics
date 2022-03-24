"""Miscellaneous utility methods for Python collections."""
from typing import Any, Callable, Dict, Hashable, List, Optional


def reverse_dict(d: Dict[Hashable, Hashable], inplace: bool = False) -> Optional[Dict[Hashable, Hashable]]:
    """Swap keys and values.

    Args:
        d: A dict to reverse.
        inplace: If True, perform the reversal inplace.

    Returns:
        A reversed version of `d`, or None if inplace is True.

    Examples:
        Reversing a dict with two elements.

        >>> from rics.utility.collections import reverse_dict
        >>> reverse_dict({"A": 0, "B": 1})
        {0: 'A', 1: 'B'}
    """
    ans = {}
    for key, value in d.items():
        ans[value] = key

    if inplace:
        d.clear()
        d.update(ans)
        return None
    else:
        return ans


def flatten_dict(
    d: Dict[str, Any],
    join_string: str = ".",
    filter_predicate: Callable[[str, Any], bool] = None,
) -> Dict[str, Any]:
    """Flatten a nested dictionary.

    Args:
        d: A dict to flatten.
        join_string: Joiner for nested keys.
        filter_predicate: A callable which takes a key and value, returning True if the entry should be kept.

    Returns:
        A flattened version of `d`.

    Examples:
        Flattening a shallow nested dict.

        >>> from rics.utility.collections import flatten_dict
        >>> flatten_dict({"foo": 0, "bar": {"foo": 1, "bar": 2}})
        {'foo': 0, 'bar.foo': 1, 'bar.bar': 2}
    """
    return _flatten_inner(d, {}, [], join_string, filter_predicate)


def _flatten_inner(
    arg: Any,
    flattened: Dict[str, Any],
    parents: List[str],
    join_string: str = ".",
    filter_predicate: Callable[[str, Any], bool] = None,
) -> Dict[str, Any]:
    if isinstance(arg, dict):
        for key, value in arg.items():
            if filter_predicate is not None and not filter_predicate(key, value):
                continue
            new_parents = parents + [key]
            flat_key = join_string.join(new_parents)
            inner = _flatten_inner(value, flattened, new_parents, join_string, filter_predicate)
            if not isinstance(inner, dict):
                flattened[flat_key] = inner
        return flattened
    else:
        return arg
