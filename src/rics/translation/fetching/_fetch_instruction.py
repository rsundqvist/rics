from dataclasses import dataclass
from typing import Set

from rics.translation.fetching._ids_to_fetch import IdsToFetch
from rics.translation.offline.types import IdType, PlaceholdersTuple, SourceType


@dataclass(frozen=True)
class FetchInstruction(IdsToFetch[SourceType, IdType]):
    """Instructions given to an implementation.

    Tuples of this type are passed to the :meth:`_fetch_translations` method implemented by inheriting classes.

    Attributes:
        placeholders: All desired placeholders in preferred order.
        required: Placeholders that must be included in the response.
        all_placeholders: Flag indicated whether to retrieve as many placeholders as possible.
    """

    placeholders: PlaceholdersTuple
    required: Set[str]
    all_placeholders: bool
