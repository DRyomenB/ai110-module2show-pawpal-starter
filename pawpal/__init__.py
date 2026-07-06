"""PawPal+ — Pet Activity Scheduling System.

Class stubs generated from diagrams/uml.mmd. No scheduling logic yet;
method bodies raise NotImplementedError until implemented.
"""

from pawpal.enums import Priority, Status
from pawpal.models import (
    Activity,
    Appointment,
    Grooming,
    Owner,
    Pet,
    Preferences,
    Schedule,
    Training,
    VetVisit,
    Walk,
)
from pawpal.scheduler import Scheduler

__all__ = [
    "Priority",
    "Status",
    "Preferences",
    "Activity",
    "Walk",
    "Grooming",
    "VetVisit",
    "Training",
    "Appointment",
    "Schedule",
    "Pet",
    "Owner",
    "Scheduler",
]
