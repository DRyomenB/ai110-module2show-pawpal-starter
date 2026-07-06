"""Scheduling engine for PawPal+.

Turns a pet's list of care activities into an ordered daily plan that respects
the owner's preferences (working window, daily time budget, blackout times),
resolves overlaps, and can explain its choices.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import List

from pawpal.models import Activity, Appointment, Pet, Preferences, Schedule, _new_id

#: Step used when nudging a start time out of a blackout window.
_BLACKOUT_STEP = timedelta(minutes=15)


class Scheduler:
    """Builds and explains a daily care plan from a pet's activities."""

    def generate_plan(
        self, pet: Pet, activities: List[Activity], prefs: Preferences
    ) -> Schedule:
        """Select and order activities into a Schedule that respects prefs.

        Activities are placed highest-priority first, back to back from the
        preferred start time. An activity is skipped when it would exceed the
        daily time budget or run past the preferred end time.
        """
        plan_date = date.today()
        schedule = Schedule(schedule_id=_new_id("sched"), date=plan_date)

        day_end = datetime.combine(plan_date, prefs.preferred_end)
        cursor = datetime.combine(plan_date, prefs.preferred_start)
        used_minutes = 0

        for activity in self.sort_by_priority(activities):
            if used_minutes + activity.duration_minutes > prefs.max_daily_minutes:
                continue  # over the daily budget — skip

            start = self._skip_blackouts(cursor, prefs, day_end)
            finish = start + timedelta(minutes=activity.duration_minutes)
            if finish > day_end:
                continue  # no room left in the day — skip

            schedule.add(
                Appointment(
                    appointment_id=_new_id("appt"),
                    activity=activity,
                    start_time=start,
                )
            )
            cursor = finish
            used_minutes += activity.duration_minutes

        pet.schedule = schedule
        return schedule

    def sort_by_priority(self, activities: List[Activity]) -> List[Activity]:
        """Return activities ordered by priority, then longest duration first."""
        return sorted(
            activities,
            key=lambda a: (a.priority.rank, -a.duration_minutes),
        )

    def resolve_conflicts(self, schedule: Schedule) -> Schedule:
        """Push overlapping appointments later so none start before the prior ends."""
        ordered = sorted(schedule.appointments, key=lambda a: a.start_time)
        for prev, current in zip(ordered, ordered[1:]):
            if current.start_time < prev.end_time:
                current.reschedule(prev.end_time)
        schedule.appointments = sorted(ordered, key=lambda a: a.start_time)
        return schedule

    def explain(self, schedule: Schedule) -> str:
        """Return a human-readable rationale for the generated plan."""
        if not schedule.appointments:
            return "No activities could be scheduled within the given constraints."

        lines = [f"Daily plan for {schedule.date.isoformat()}:"]
        for appt in sorted(schedule.appointments, key=lambda a: a.start_time):
            clock = appt.start_time.strftime("%H:%M")
            lines.append(
                f"  {clock} — {appt.activity.describe()} "
                f"[priority: {appt.activity.priority.value}]"
            )
        return "\n".join(lines)

    def _skip_blackouts(
        self, cursor: datetime, prefs: Preferences, day_end: datetime
    ) -> datetime:
        """Advance cursor past any preferred blackout start times."""
        blackout = set(prefs.blackout_times or [])
        while cursor.strftime("%H:%M") in blackout and cursor < day_end:
            cursor += _BLACKOUT_STEP
        return cursor
