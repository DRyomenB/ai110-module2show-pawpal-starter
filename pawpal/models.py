"""Domain models for PawPal+.

Stubs only: attributes are declared with dataclasses and methods raise
NotImplementedError. Implement the bodies incrementally (see README workflow).
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import List, Optional

from pawpal.enums import Priority, Status

#: Default start of the care day when no owner preference is given.
DAY_START = time(8, 0)


def _new_id(prefix: str) -> str:
    """Return a short unique id such as 'pet-1a2b3c4d'."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


@dataclass
class Preferences:
    """Owner constraints the scheduler must respect when building a plan."""

    preferred_start: time
    preferred_end: time
    max_daily_minutes: int
    blackout_times: List[str] = field(default_factory=list)


@dataclass
class Activity(ABC):
    """A type of care task (walk, grooming, etc.). Placed in time by an Appointment."""

    activity_id: str
    title: str
    duration_minutes: int
    priority: Priority
    recurring: bool = False

    @abstractmethod
    def describe(self) -> str:
        """Return a human-readable summary of this activity."""
        raise NotImplementedError


@dataclass
class Walk(Activity):
    """A walk or exercise outing."""

    route: str = ""
    distance_km: float = 0.0

    def describe(self) -> str:
        detail = f" along {self.route}" if self.route else ""
        return f"{self.title}: {self.distance_km:g} km walk{detail} ({self.duration_minutes} min)"


@dataclass
class Grooming(Activity):
    """A grooming session."""

    groomer: str = ""
    bath_included: bool = False

    def describe(self) -> str:
        bath = " with bath" if self.bath_included else ""
        by = f" by {self.groomer}" if self.groomer else ""
        return f"{self.title}: grooming{bath}{by} ({self.duration_minutes} min)"


@dataclass
class VetVisit(Activity):
    """A veterinary appointment."""

    clinic: str = ""
    reason: str = ""

    def describe(self) -> str:
        reason = f" for {self.reason}" if self.reason else ""
        at = f" at {self.clinic}" if self.clinic else ""
        return f"{self.title}: vet visit{reason}{at} ({self.duration_minutes} min)"


@dataclass
class Training(Activity):
    """A training session."""

    skill: str = ""
    trainer: str = ""

    def describe(self) -> str:
        skill = f" — {self.skill}" if self.skill else ""
        with_ = f" with {self.trainer}" if self.trainer else ""
        return f"{self.title}: training{skill}{with_} ({self.duration_minutes} min)"


@dataclass
class Appointment:
    """An Activity placed at a concrete start time, with a lifecycle status."""

    appointment_id: str
    activity: Activity
    start_time: datetime
    status: Status = Status.SCHEDULED

    @property
    def end_time(self) -> datetime:
        """When this appointment finishes, based on its activity duration."""
        return self.start_time + timedelta(minutes=self.activity.duration_minutes)

    def reschedule(self, new_time: datetime) -> None:
        """Move this appointment to a new start time (no-op if cancelled)."""
        if self.status is Status.CANCELLED:
            raise ValueError("Cannot reschedule a cancelled appointment.")
        self.start_time = new_time

    def cancel(self) -> None:
        """Mark this appointment as cancelled."""
        self.status = Status.CANCELLED

    def mark_complete(self) -> None:
        """Mark this appointment as completed (cannot complete a cancelled one)."""
        if self.status is Status.CANCELLED:
            raise ValueError("Cannot complete a cancelled appointment.")
        self.status = Status.COMPLETED

    def is_upcoming(self, now: Optional[datetime] = None) -> bool:
        """Return True if the appointment is still scheduled and in the future."""
        now = now or datetime.now()
        return self.status is Status.SCHEDULED and self.start_time >= now


@dataclass
class Schedule:
    """A day's worth of appointments for a single pet."""

    schedule_id: str
    date: date
    appointments: List[Appointment] = field(default_factory=list)

    def add(self, appointment: Appointment) -> None:
        """Add an appointment, keeping the list ordered by start time."""
        self.appointments.append(appointment)
        self.appointments.sort(key=lambda a: a.start_time)

    def remove(self, appointment_id: str) -> None:
        """Remove an appointment by id (silently ignores unknown ids)."""
        self.appointments = [
            a for a in self.appointments if a.appointment_id != appointment_id
        ]

    def upcoming(self, now: Optional[datetime] = None) -> List[Appointment]:
        """Return still-upcoming appointments, earliest first."""
        return sorted(
            (a for a in self.appointments if a.is_upcoming(now)),
            key=lambda a: a.start_time,
        )

    def has_conflict(self, appointment: Appointment) -> bool:
        """Return True if the appointment overlaps a non-cancelled existing one."""
        for existing in self.appointments:
            if existing is appointment or existing.status is Status.CANCELLED:
                continue
            if (
                appointment.start_time < existing.end_time
                and existing.start_time < appointment.end_time
            ):
                return True
        return False


@dataclass
class Pet:
    """A pet whose care activities are being scheduled."""

    pet_id: str
    name: str
    species: str
    age: int = 0
    schedule: Optional[Schedule] = None

    def _ensure_schedule(self) -> Schedule:
        """Create this pet's schedule on first use."""
        if self.schedule is None:
            self.schedule = Schedule(schedule_id=_new_id("sched"), date=date.today())
        return self.schedule

    def schedule_activity(self, activity: Activity) -> Appointment:
        """Append an activity right after the last one (or at DAY_START)."""
        schedule = self._ensure_schedule()
        if schedule.appointments:
            start = max(a.end_time for a in schedule.appointments)
        else:
            start = datetime.combine(schedule.date, DAY_START)
        appointment = Appointment(
            appointment_id=_new_id("appt"), activity=activity, start_time=start
        )
        schedule.add(appointment)
        return appointment

    def upcoming_activities(self) -> List[Appointment]:
        """Return this pet's upcoming appointments (empty if no schedule yet)."""
        return self.schedule.upcoming() if self.schedule else []

    @property
    def task_count(self) -> int:
        """Number of appointments (tasks) currently on this pet's schedule."""
        return len(self.schedule.appointments) if self.schedule else 0


@dataclass
class Owner:
    """A pet owner who registers pets and plans their care."""

    owner_id: str
    name: str
    email: str
    preferences: Optional[Preferences] = None
    pets: List[Pet] = field(default_factory=list)

    def register_pet(self, pet: Pet) -> None:
        """Attach an existing pet to this owner (no duplicates)."""
        if pet not in self.pets:
            self.pets.append(pet)

    def add_pet(self, name: str, species: str) -> Pet:
        """Create and register a new pet, returning it."""
        pet = Pet(pet_id=_new_id("pet"), name=name, species=species)
        self.register_pet(pet)
        return pet

    def list_pets(self) -> List[Pet]:
        """Return all pets owned by this owner."""
        return list(self.pets)
