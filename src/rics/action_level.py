"""Action level enumeration types."""

import typing as _t
from enum import Enum as _Enum


class ActionLevel(_Enum):
    """Action level enumeration type for events."""

    _ignore_: _t.ClassVar = ("ParseType",)  # type: ignore[misc]

    ParseType: _t.TypeAlias = "str | ActionLevel"
    """Types that may be interpreted as an ``ActionLevel``."""

    RAISE = "raise"
    """Raise an error."""
    WARN = "warn"
    """Raise a warning"""
    IGNORE = "ignore"
    """Ignore the event."""

    @classmethod
    def verify(
        cls,
        action: ParseType,
        purpose: str | None = None,
        forbidden: "ActionLevel.ParseType | None" = None,
    ) -> "ActionLevel":
        """Verify an action level.

        Args:
            action: The value to verify.
            purpose: Additional information to add if an exception is raised.
            forbidden: Which of ('ignore', 'warn', 'raise') not to accept. Accept all if ``None``.

        Returns:
            A valid action level for the given purpose.

        Raises:
            BadActionLevelError: If `action` is not in ('ignore', 'warn', 'raise') or if `action` is in `forbidden`.

        """
        forbidden = None if forbidden is None else cls.verify(forbidden)

        if isinstance(action, ActionLevel):
            action_level = action
        else:
            try:
                action_level = ActionLevel[action.upper()]
            except KeyError:
                raise BadActionLevelError(action, purpose, forbidden) from None
            except AttributeError:
                raise BadActionLevelError(action, purpose, forbidden) from None

        if action_level is forbidden:
            raise BadActionLevelError(action, purpose, forbidden)

        return action_level

    def __eq__(self, other: _t.Any) -> bool:
        if isinstance(other, ActionLevel):
            other = other.name

        if isinstance(other, str):
            return bool(self.name == other.upper())

        return False

    def __hash__(self) -> int:
        return hash(self.name)


ActionLevel.ParseType = _t.Literal["ignore", "warn", "raise", "IGNORE", "WARN", "RAISE"] | ActionLevel  # type: ignore


class ActionLevelHelper:
    """Helper class for keeping track of per-purpose forbidden actions.

    Args:
        require_purpose: Determine how to handle the `purpose` argument given in :meth:`verify`; require that it exists,
            or just that it is given. Must be one of ('given', 'exists').
        **forbidden_for_purpose: Per-purpose forbidden actions.
    """

    def __init__(
        self,
        require_purpose: _t.Literal["given", "exists"] = "exists",
        **forbidden_for_purpose: "ActionLevel.ParseType | None",
    ) -> None:
        self._require = require_purpose
        self._forbidden_for_purpose = forbidden_for_purpose

    def verify(self, action: ActionLevel.ParseType, purpose: str) -> ActionLevel:
        """Verify an action level with constraints.

        Args:
            action: The value to verify.
            purpose: Additional information to add if an exception is raised.

        Returns:
            A valid action level for the given purpose.

        Raises:
            BadActionLevelError: If `action` is not in ('ignore', 'warn', 'raise') or if `action` is in `remove`.
            ValueError: If `purpose` is unknown and `require_purpose` is set to `'exists'`.

        """
        if self._require == "exists" and purpose not in self._forbidden_for_purpose:
            raise ValueError(f"Unknown {purpose=} given.")
        return ActionLevel.verify(action, purpose, forbidden=self._forbidden_for_purpose.get(purpose))


class BadActionLevelError(ValueError):
    """Error raised for unknown or disallowed action arguments."""

    def __init__(
        self,
        action: ActionLevel.ParseType,
        purpose: str | None = None,
        forbidden: "ActionLevel | None" = None,
    ) -> None:
        extra = f" for {purpose}" if purpose else ""
        all_options = {ActionLevel.RAISE, ActionLevel.WARN, ActionLevel.IGNORE}
        if forbidden:
            all_options.discard(forbidden)
        accepted = tuple(a.name.lower() for a in all_options)
        super().__init__(f"Permitted choices{extra} are {accepted}, but got {action=}.")
