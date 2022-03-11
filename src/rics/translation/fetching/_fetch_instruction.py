from dataclasses import dataclass

from rics.translation.fetching._ids_to_fetch import IdsToFetch
from rics.translation.offline.types import IdType, PlaceholdersTuple, SourceType


@dataclass(frozen=True)
class FetchInstruction(IdsToFetch[SourceType, IdType]):
    """Instructions given to an implementation.

    Tuples of this type are passed to the :meth:`_fetch_translations` method implemented by inheriting classes.

    Attributes:
        required: Placeholders that must be included.
        optional: Placeholders which should be included if possible.
    """

    required: PlaceholdersTuple
    optional: PlaceholdersTuple
