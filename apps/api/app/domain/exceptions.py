"""Domain layer exceptions.

Domain exceptions represent business rule violations and domain entity errors.
They have zero dependencies on infrastructure, web frameworks, or databases.
"""

from typing import Any


class DomainError(Exception):
    """Base domain exception."""

    def __init__(self, message: str, code: str = "DOMAIN_ERROR", details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class EntityNotFoundError(DomainError):
    """Raised when a requested entity does not exist."""

    def __init__(self, entity_name: str, entity_id: str) -> None:
        super().__init__(
            message=f"{entity_name} with id '{entity_id}' not found.",
            code=f"{entity_name.upper()}_NOT_FOUND",
            details={"entity": entity_name, "id": entity_id},
        )


class DuplicateEntityError(DomainError):
    """Raised when an entity with a unique constraint already exists."""

    def __init__(self, entity_name: str, field: str, value: str) -> None:
        super().__init__(
            message=f"{entity_name} with {field} '{value}' already exists.",
            code=f"DUPLICATE_{entity_name.upper()}_{field.upper()}",
            details={"entity": entity_name, "field": field, "value": value},
        )


class ValidationError(DomainError):
    """Raised when domain entity invariants are violated."""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(
            message=message,
            code="DOMAIN_VALIDATION_ERROR",
            details={"field": field} if field else {},
        )


class InvalidJobStateTransitionError(DomainError):
    """Raised when attempting an invalid status transition on a background job."""

    def __init__(self, job_id: str, current_status: str, target_status: str) -> None:
        super().__init__(
            message=f"Job '{job_id}' cannot transition from '{current_status}' to '{target_status}'.",
            code="INVALID_JOB_STATE_TRANSITION",
            details={
                "job_id": job_id,
                "current_status": current_status,
                "target_status": target_status,
            },
        )


class PokerDomainError(DomainError):
    """Base exception for all poker domain rule violations."""

    def __init__(self, message: str, code: str = "POKER_DOMAIN_ERROR", details: Any = None) -> None:
        super().__init__(message=message, code=code, details=details)


class InvalidCardError(PokerDomainError):
    """Raised when card representation is invalid or cannot be parsed."""

    def __init__(self, card_str: str, reason: str = "Invalid card notation") -> None:
        super().__init__(
            message=f"Invalid card '{card_str}': {reason}.",
            code="INVALID_CARD",
            details={"card": card_str, "reason": reason},
        )


class DuplicateCardError(PokerDomainError):
    """Raised when duplicate cards are detected in a deck, hand, or board."""

    def __init__(self, duplicates: list[str]) -> None:
        super().__init__(
            message=f"Duplicate card(s) detected: {', '.join(duplicates)}.",
            code="DUPLICATE_CARD",
            details={"duplicates": duplicates},
        )


class InvalidActionError(PokerDomainError):
    """Raised when an illegal action is attempted by a player."""

    def __init__(self, player_id: str, action: str, reason: str) -> None:
        super().__init__(
            message=f"Illegal action '{action}' for player '{player_id}': {reason}.",
            code="ILLEGAL_POKER_ACTION",
            details={"player_id": player_id, "action": action, "reason": reason},
        )


class InvalidRangeError(PokerDomainError):
    """Raised when a range notation string cannot be parsed or is invalid."""

    def __init__(self, range_str: str, reason: str) -> None:
        super().__init__(
            message=f"Invalid range '{range_str}': {reason}.",
            code="INVALID_RANGE",
            details={"range": range_str, "reason": reason},
        )


class PermissionDeniedError(DomainError):
    """Raised when an unprivileged client attempts an unauthorized privileged action."""

    def __init__(self, message: str = "Permission denied.") -> None:
        super().__init__(
            message=message,
            code="PERMISSION_DENIED",
        )
