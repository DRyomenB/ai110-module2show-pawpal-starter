"""Enumerations used across the PawPal+ domain model."""

from enum import Enum


class Priority(Enum):
    """How important a care activity is when the scheduler orders the day."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def rank(self) -> int:
        """Sort key: higher-priority activities rank lower (placed first)."""
        return {"high": 0, "medium": 1, "low": 2}[self.value]


class Status(Enum):
    """Lifecycle state of a scheduled appointment."""

    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
