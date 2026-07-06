"""Tests for core PawPal+ behaviors."""

from datetime import datetime

import pytest

from pawpal import Owner, Priority, Status, Walk
from pawpal.models import Appointment


def make_appointment() -> Appointment:
    """A simple scheduled appointment to exercise status changes."""
    activity = Walk("a1", "Morning walk", 30, Priority.HIGH)
    return Appointment("appt-1", activity, datetime(2026, 7, 6, 8, 0))


# --------------------------------------------------------------------------
# mark_complete() changes the task's status
# --------------------------------------------------------------------------
def test_mark_complete_changes_status():
    appt = make_appointment()
    assert appt.status is Status.SCHEDULED  # precondition

    appt.mark_complete()

    assert appt.status is Status.COMPLETED


def test_mark_complete_rejects_cancelled():
    appt = make_appointment()
    appt.cancel()
    with pytest.raises(ValueError):
        appt.mark_complete()


# --------------------------------------------------------------------------
# adding a task to a Pet increases that pet's task count
# --------------------------------------------------------------------------
def test_scheduling_activity_increases_task_count():
    owner = Owner("o1", "Jordan", "jordan@example.com")
    pet = owner.add_pet("Biscuit", "dog")
    assert pet.task_count == 0  # no schedule/tasks yet

    pet.schedule_activity(Walk("a1", "Morning walk", 30, Priority.HIGH))
    assert pet.task_count == 1

    pet.schedule_activity(Walk("a2", "Evening walk", 20, Priority.MEDIUM))
    assert pet.task_count == 2
