"""Supporting functions for implementations."""
from typing import Any, Collection, List, Sequence

from rics.translation.fetching import exceptions
from rics.translation.fetching.types import FetchInstruction
from rics.translation.offline.types import PlaceholderTranslations


def from_records(
    instr: FetchInstruction,
    known_placeholders: Collection[str],
    records: Sequence[Sequence[Any]],
) -> PlaceholderTranslations:
    """Create :class:`.PlaceholderTranslations` instance from records.

    Convenience method meant for use by implementations.

    Args:
        instr: A fetch instruction.
        known_placeholders: Known placeholders for the `instr.source`.
        records: Records produced from the instruction.

    Returns:
        Placeholder translation elements.

    Raises:
        ImplementationError: If the underlying fetcher does not return enough IDs.
    """
    if instr.ids is not None and len(records) < len(set(instr.ids)):
        actual_len = len(records)
        minimum = len(set(instr.ids))
        raise exceptions.ImplementationError(f"Got {actual_len} records, expected at least {minimum}.")

    return PlaceholderTranslations(instr.source, tuple(known_placeholders), records)


def select_placeholders(instr: FetchInstruction, known_placeholders: Collection[str]) -> List[str]:
    """Select as many known placeholders as possible."""
    return list(
        known_placeholders if instr.all_placeholders else filter(known_placeholders.__contains__, instr.placeholders)
    )
