"""Action level enumeration types."""

from enum import Enum
from typing import Literal, Optional, Union

ActionLevelTypes = Union[Literal["ignore", "warn", "raise", "IGNORE", "WARN", "RAISE"], "ActionLevel"]


class BadActionLevelError(ValueError):
    """Error raised for unknown or disallowed action arguments."""

    def __init__(
        self,
        action: ActionLevelTypes,
        purpose: str = None,
        forbidden: "ActionLevel" = None,
    ) -> None:
        extra = f" for {purpose}" if purpose else ""
        all_options = {ActionLevel.RAISE, ActionLevel.WARN, ActionLevel.IGNORE}
        if forbidden:
            all_options.discard(forbidden)
        accepted = tuple(a.name.lower() for a in all_options)
        super().__init__(f"Permitted choices{extra} are {accepted}, but got {action=}.")


class ActionLevel(Enum):
    """Action level enumeration type for events."""

    RAISE = "raise"
    WARN = "warn"
    IGNORE = "ignore"

    @classmethod
    def verify(
        cls,
        action: ActionLevelTypes,
        purpose: str = None,
        forbidden: ActionLevelTypes = None,
    ) -> "ActionLevel":
        """Verify an action level.

        Args:
            action: The value to verify.
            purpose: Additional information to add if an exception is raised.
            forbidden: Which of ('ignore', 'warn', 'raise') not to accept. None=accept all.

        Returns:
            A valid action level for the given purpose.

        Raises:
            BadActionLevelError: If `action` is not in ('ignore', 'warn', 'raise') or if `action` is in `remove`.
        """
        forbidden = None if forbidden is None else cls.verify(forbidden)

        if isinstance(action, ActionLevel):
            action_level = action
        else:
            try:
                action_level = ActionLevel[action.upper()]
            except KeyError:  # pragma: no cover
                raise BadActionLevelError(action, purpose, forbidden)
            except AttributeError:  # pragma: no cover
                raise BadActionLevelError(action, purpose, forbidden)

        if action_level is forbidden:
            raise BadActionLevelError(action, purpose, forbidden)

        return action_level


class ActionLevelHelper:
    """Helper class for keeping track of per-purpose forbidden actions.

    Args:
        require_purpose: Determine how to handle the `purpose` argument given in :meth:`verify`; require that it exists,
            or just that it is given. Must be one of ('given', 'exists').
        **forbidden_for_purpose: Per-purpose forbidden actions.
    """

    def __init__(
        self,
        require_purpose: Literal["given", "exists"] = "exists",
        **forbidden_for_purpose: Optional[ActionLevelTypes],
    ) -> None:
        self._require = require_purpose
        self._forbidden_for_purpose = forbidden_for_purpose

    def verify(self, action: ActionLevelTypes, purpose: str) -> ActionLevel:
        """Verify an action level."""
        if self._require == "exists" and purpose not in self._forbidden_for_purpose:
            raise ValueError(f"Unknown {purpose=} given.")
        return ActionLevel.verify(action, purpose, forbidden=self._forbidden_for_purpose.get(purpose))