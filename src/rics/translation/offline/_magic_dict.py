from typing import Any, Callable, Dict, Iterator, Mapping, Optional, Union

from rics._internal_support.types import NO_DEFAULT, NoDefault
from rics.translation.offline.types import IdType, PlaceholdersTuple, TranslatedIds


class MagicDict(Mapping[IdType, str]):
    """Immutable mapping for translated IDs.

    If `default_value` is given, it is used as the default answer for any calls to `__getitem__` where the key is
    not in `translated_ids`.

    Should the `add_id` flag also be set, it will be converted into a callable that includes the ID requested in the
    returned value. In this case `default_value` must include exactly one positional placeholder.

    If `has_placeholder` is not set, there should not be any placeholders in `default_value` at all.

    Args:
        real_translations: A dict holding real translations.
        default_value: String format callable with a single positional placeholder.
        add_id: Indicates that `string` has a single placeholder that should be replaced by the given key when key not
            in `translated_ids`.
    """

    @classmethod
    def make(
        cls,
        real_translations: TranslatedIds,
        fstring: str,
        placeholders: PlaceholdersTuple,
        default: Optional[Union[NoDefault, Dict[str, Any]]] = NO_DEFAULT,
    ) -> "MagicDict[IdType]":
        """Create a new instance.

        Args:
            real_translations: A backing dict to get keys from.
            fstring: A positional format string to create a default return value from.
            placeholders: Names of placeholders in `fstring`, in order.
            default: A dict of default values for placeholders in `fstring`.

        Returns:
            A new MagicDict.
        """
        if default == NO_DEFAULT or default is None:
            return MagicDict(real_translations)

        return (
            MagicDict(
                real_translations,
                fstring.format(*(default.get(p, "{}") for p in placeholders)),  # Verify exactly one in result?
            )
            if "id" in placeholders
            else MagicDict(real_translations, fstring.format(*(default[p] for p in placeholders)), False)
        )

    def __init__(
        self,
        real_translations: TranslatedIds,
        default_value: str = None,
        add_id: bool = True,
    ) -> None:
        self._real: TranslatedIds = real_translations

        self._has_default = default_value is not None
        self._plain_string: str = default_value or "<You're not supposed to see this>"
        self._fstring: Optional[Callable[[IdType], str]] = self._plain_string.format if add_id else None

    def __getitem__(self, key: IdType) -> str:
        if key in self._real or not self._has_default:
            return self._real[key]
        return self._fstring(key) if self._fstring is not None else self._plain_string

    def __contains__(self, idx: Any) -> bool:
        return self._has_default or idx in self._real  # pragma: no cover

    def __len__(self) -> int:
        return len(self._real)  # pragma: no cover

    def __iter__(self) -> Iterator[IdType]:
        return iter(self._real)  # pragma: no cover

    def __repr__(self) -> str:
        return repr(self._real)  # pragma: no cover
