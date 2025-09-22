from typing import Any

from rics.misc import tname


class KwargsFormatter:
    def __init__(
        self,
        max_value_length: int,
    ) -> None:
        self._max_value_length = max_value_length

    def format_value(self, value: Any) -> str:
        if self._max_value_length == 0:
            return self._serialize_as_value(value)
        if self._max_value_length < 0:
            shape = self._get_shape(value)
            return self._serialize_as_class(value, shape)

        for serializer in [
            self._repr_str,
            self._repr_collection,
            self._format_ndim_array,  # E.g. pandas.DataFrame or polars.DataFrame
        ]:
            value_repr = serializer(value)
            if isinstance(value_repr, str):
                return value_repr
            elif value_repr is False:
                break

        value_repr = self._serialize_as_value(value)
        if len(value_repr) <= self._max_value_length:
            return value_repr

        return self._serialize_as_class(value, ())

    @classmethod
    def _serialize_as_value(cls, value: Any) -> str:
        from pprint import PrettyPrinter

        pp = PrettyPrinter(
            indent=2,
            width=120,
            depth=4,
            compact=True,
            sort_dicts=True,
            underscore_numbers=True,
        )
        return pp.pformat(value)

    @classmethod
    def _serialize_as_class(cls, value: Any, shape: tuple[int, ...]) -> str:
        value_cls = tname(value)

        if not shape:
            return value_cls

        dims = "x".join(map(str, shape))
        return f"{value_cls}[{dims}]"

    def _repr_str(self, value: Any) -> str | bool:
        if isinstance(value, str):
            if len(value) > self._max_value_length:
                return "str"
            else:
                return value

        return True

    def _repr_collection(self, value: Any) -> str | bool:
        if isinstance(value, (list, tuple, set)):
            if len(value) * 3 > self._max_value_length:
                shape = (len(value),)
                return self._serialize_as_class(value, shape)
            else:
                return False

        if isinstance(value, dict):
            if len(value) * 6 > self._max_value_length:
                shape = (len(value),)
                return self._serialize_as_class(value, shape)
            else:
                return False

        return True

    @classmethod
    def _format_ndim_array(cls, value: Any) -> str | None:
        if shape := cls._get_shape(value):
            # TODO  self._max_value_length
            return cls._serialize_as_class(value, shape)

        return None

    @classmethod
    def _get_shape(cls, value: Any) -> tuple[int, ...]:
        if hasattr(value, "shape") and isinstance(value.shape, tuple):
            return value.shape
        elif hasattr(value, "__len__"):
            return (len(value),)
        return ()
