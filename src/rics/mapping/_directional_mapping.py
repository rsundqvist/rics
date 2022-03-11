from typing import Any, Dict, Generic, Hashable, Iterable, Optional, Tuple, TypeVar, Union

from rics.cardinality import Cardinality, CardinalityType
from rics.cardinality.exceptions import CardinalityError
from rics.utility.misc import tname

HL = TypeVar("HL", bound=Hashable)
HR = TypeVar("HR", bound=Hashable)
HAnySide = TypeVar("HAnySide", bound=Hashable)
MatchTupleLeft = Tuple[HL, ...]
MatchTupleRight = Tuple[HR, ...]
MatchTupleAnySide = TypeVar("MatchTupleAnySide", bound=Hashable)
DictMapping = Union[Dict[HL, MatchTupleRight], Dict[HR, MatchTupleLeft]]


class DirectionalMapping(Generic[HL, HR]):
    """A two-way mapping between hashable elements.

    Args:
        cardinality: Explicit cardinality. None=derive.
        left_to_right: A left-to-right mapping of elements.
        right_to_left: A right-to-left mapping of elements.
        _verify: If False, input checks are disabled. Intended for internal use.

    Raises:
        ValueError: If both of `left_to_right` and `right_to_left` are None.
        ValueError: If verification of two-sided input fails, and ``verify=True``.
        CardinalityError: If explicit `cardinality` < :attr:`cardinality`, and ``verify=True``.
    """

    def __init__(
        self,
        cardinality: CardinalityType = None,
        left_to_right: DictMapping = None,
        right_to_left: DictMapping = None,
        _verify: bool = True,
    ) -> None:
        self._left_to_right = self._to_other(left_to_right, right_to_left)
        self._right_to_left = self._to_other(right_to_left, left_to_right)

        if left_to_right is not None and right_to_left is not None and _verify:
            self._verify(expected=DirectionalMapping(cardinality, left_to_right=left_to_right, _verify=False))

        self._cardinality = self._handle_cardinality(cardinality, self._left_to_right, self._right_to_left, _verify)

    @property
    def cardinality(self) -> Cardinality:
        """Cardinality with which this mapping was created.

        Returns:
            Cardinality with which this mapping was created.
        """
        return self._cardinality

    @property
    def left(self) -> MatchTupleLeft:
        """Left-side elements in the mapping."""
        return tuple(self._left_to_right)

    @property
    def right(self) -> MatchTupleRight:
        """Right-side elements in the mapping."""
        return tuple(self._right_to_left)

    @property
    def left_to_right(self) -> DictMapping:
        """Left-to-right element mappings."""
        return self._left_to_right

    @property
    def right_to_left(self) -> DictMapping:
        """Right-to-left element mappings."""
        return self._right_to_left

    @property
    def reverse(self) -> "DirectionalMapping":
        """Reverse the mapping by swapping the sides.

        Returns:
            A copy with data identical to the calling instance, but with sides inversed compared to the caller.
        """
        return DirectionalMapping(
            self.cardinality.inverse,
            left_to_right=self._right_to_left.copy(),
            right_to_left=self._left_to_right.copy(),
            _verify=False,
        )

    def flatten(self) -> Dict[HL, HR]:
        """Return a flattened version of self as a dict.

        Returns:
            A dict ``{left: right}``.

        Raises:
            CardinalityError: If cardinality is not :class:`~rics.cardinality.Cardinality.OneToOne`.
        """
        if self._cardinality != Cardinality.OneToOne:
            raise CardinalityError(f"Must have {Cardinality.OneToOne}.", self._cardinality)  # pragma: no cover

        return {left: right[0] for left, right in self._left_to_right.items()}

    def select_left(self, elements: Iterable[HL], exclude: bool = False) -> "DirectionalMapping":
        """Perform a selection on left-side elements.

        Args:
            elements: Elements to select.
            exclude: If True, return everything **except** the given elements.

        Returns:
            A new Mapping for the selection.

        Raises:
            KeyError: If any of the chosen elements do not exist and ``exclude=False``.
        """
        return self._select(elements, left=True, exclude=exclude)

    def select_right(self, elements: Iterable[HR], exclude: bool = False) -> "DirectionalMapping":
        """Perform a selection on right-side elements.

        Args:
            elements: Elements to select.
            exclude: If True, return everything **except** the given elements.

        Returns:
            A new instance for the selection.

        Raises:
            KeyError: If any of the chosen elements do not exist and ``exclude=False``.
        """
        return self._select(elements, left=False, exclude=exclude)

    @staticmethod
    def _to_other(primary_side: Optional[DictMapping], backup_side: Optional[DictMapping]) -> DictMapping:
        if primary_side is not None:
            return primary_side

        if backup_side is None:
            raise ValueError("At least one side must be given")

        from collections import defaultdict

        other_side = defaultdict(list)
        for k, matches_for_k in backup_side.items():
            for m in matches_for_k:
                other_side[m].append(k)
        return {k: tuple(set(m)) for k, m in other_side.items()}

    def _select(self, elements: Iterable[HAnySide], left: bool, exclude: bool) -> "DirectionalMapping":
        """Perform a selection on left-side elements.

        Args:
            elements: Elements to select.
            left: If True, select elements from the left side.
            exclude: If True, return everything **except** the given elements.

        Returns:
            A new instance for the selection.

        Raises:
            KeyError: If any of the chosen elements do not exist and ``exclude=False``.
        """
        items = self._left_to_right if left else self._right_to_left

        if not exclude:
            missing_elements = set(elements).difference(items)
            if missing_elements:
                raise KeyError(f"Unknown {'left' if left else 'right'}: {', '.join(map(str, missing_elements))}.")

        s = set(elements)
        chosen_elements = filter(lambda e: e not in s, items) if exclude else filter(s.__contains__, items)
        one_sided_mapping = {e: items[e] for e in chosen_elements}
        return (
            DirectionalMapping(None, left_to_right=one_sided_mapping)
            if left
            else DirectionalMapping(None, right_to_left=one_sided_mapping)
        )

    def _verify(self, expected: "DirectionalMapping") -> None:
        self._verify_side(self.left, expected.left, "Left")
        self._verify_side(self.right, expected.right, "Right")

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, DirectionalMapping):
            return False

        return (
            self._left_to_right == other._left_to_right
            and self._right_to_left == other._right_to_left
            and self._cardinality == other._cardinality
        )

    def __repr__(self) -> str:
        n_left = len(self._left_to_right)
        n_right = len(self._right_to_left)
        return f"{tname(self)}({n_left} left | {n_right} right, type={self.cardinality.name})"

    @classmethod
    def _handle_cardinality(
        cls,
        expected: Optional[CardinalityType],
        left: DictMapping,
        right: DictMapping,
        verify: bool,
    ) -> Cardinality:
        if not (left and right):
            if expected is None:
                raise ValueError("Explicit cardinality must be given for empty mapping.")  # pragma: no cover
            else:
                return Cardinality.parse(expected)

        actual = Cardinality.from_counts(
            left_count=max(map(len, right.values())), right_count=max(map(len, left.values()))
        )

        if expected is None:
            return actual
        else:
            expected = Cardinality.parse(expected)

        if verify and actual > expected:
            raise CardinalityError(f"Cannot cast explicit given type {expected} to actual type {actual}.", actual)

        return expected

    @classmethod
    def _verify_side(cls, actual: MatchTupleAnySide, expected: MatchTupleAnySide, name: str) -> None:
        if actual != expected:
            raise ValueError(f"{name}-side mismatch: Got {actual} but expected {expected}.")
