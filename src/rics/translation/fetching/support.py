"""Supporting functions for implementations."""
from typing import Any, Collection, List, Sequence

from rics.translation.fetching import exceptions
from rics.translation.fetching.types import FetchInstruction as _FetchInstruction
from rics.translation.offline.types import PlaceholderTranslations as _PlaceholderTranslations
from rics.translation.types import IdType, SourceType


def from_records(
    instr: _FetchInstruction[SourceType, IdType],
    known_placeholders: Collection[str],
    records: Sequence[Sequence[Any]],
) -> _PlaceholderTranslations:
    """Create :class:`.PlaceholderTranslations` instance from records.

    Convenience method meant for use by implementations.

    Args:
        instr: A fetch instruction.
        known_placeholders: Known placeholders for the `instr.source`.
        records: Records produced from the instruction.

    Returns:
        Placeholder translation elements.

    Raises:
        ImplementationError: If the underlying ``Fetcher`` does not return enough IDs.
    """
    if instr.ids is not None and len(records) < len(set(instr.ids)):
        actual_len = len(records)
        minimum = len(set(instr.ids))
        raise exceptions.ImplementationError(f"Got {actual_len} records, expected at least {minimum}.")

    return _PlaceholderTranslations(instr.source, tuple(known_placeholders), records)


def select_placeholders(instr: _FetchInstruction[SourceType, IdType], known_placeholders: Collection[str]) -> List[str]:
    """Select from a subset of known placeholders.

    Args:
        instr: Instruction object with placeholders.
        known_placeholders: A collection of known placeholders.

    Returns:
        As many known placeholders from `instr` as possible.
    """
    return list(
        known_placeholders if instr.all_placeholders else filter(known_placeholders.__contains__, instr.placeholders)
    )
