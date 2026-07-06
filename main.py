"""PawPal+ testing ground.

A runnable walkthrough of the pawpal package logic. Run it with:

    python3 main.py

Each section prints what it does so you can eyeball the behavior end to end:
registering pets, generating a daily plan, viewing upcoming appointments,
rescheduling, cancelling, and resolving conflicts.
"""

from datetime import datetime, time

from pawpal import (
    Grooming,
    Owner,
    Preferences,
    Priority,
    Scheduler,
    Training,
    VetVisit,
    Walk,
)


def section(title: str) -> None:
    """Print a labeled divider so each step is easy to spot in the output."""
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def main() -> None:
    scheduler = Scheduler()

    # ------------------------------------------------------------------
    section("1. Register an owner and a pet")
    # ------------------------------------------------------------------
    owner = Owner(
        owner_id="o1",
        name="Jordan",
        email="jordan@example.com",
        preferences=Preferences(
            preferred_start=time(8, 0),
            preferred_end=time(12, 0),
            max_daily_minutes=120,
            blackout_times=["09:00"],
        ),
    )
    biscuit = owner.add_pet(name="Biscuit", species="dog")
    print(f"Owner {owner.name} now has pets: {[p.name for p in owner.list_pets()]}")
    print(f"Preferences: {owner.preferences.preferred_start}–"
          f"{owner.preferences.preferred_end}, "
          f"budget {owner.preferences.max_daily_minutes} min, "
          f"blackout {owner.preferences.blackout_times}")

    # ------------------------------------------------------------------
    section("2. Define the day's candidate activities")
    # ------------------------------------------------------------------
    activities = [
        Walk("a1", "Morning walk", 30, Priority.HIGH, route="the park", distance_km=1.5),
        VetVisit("a2", "Vaccine booster", 20, Priority.HIGH, clinic="PetCare", reason="vaccines"),
        Training("a3", "Recall practice", 60, Priority.MEDIUM, skill="recall", trainer="Kim"),
        Grooming("a4", "Full groom", 45, Priority.LOW, groomer="Sam", bath_included=True),
    ]
    for a in activities:
        print(f"  • {a.describe()}  [priority: {a.priority.value}]")

    # ------------------------------------------------------------------
    section("3. Generate a daily plan (respecting preferences)")
    # ------------------------------------------------------------------
    plan = scheduler.generate_plan(biscuit, activities, owner.preferences)
    print(scheduler.explain(plan))
    print(f"\nPlaced {len(plan.appointments)} of {len(activities)} activities.")
    print("(Grooming is expected to drop: 30+20+60 = 110 min already near the "
          "120-min budget, and it runs past the noon window.)")

    # ------------------------------------------------------------------
    section("4. View upcoming appointments for the pet")
    # ------------------------------------------------------------------
    # Use a fixed 'now' so this is deterministic regardless of the real clock.
    fixed_now = datetime.combine(plan.date, time(8, 15))
    upcoming = plan.upcoming(now=fixed_now)
    print(f"As of {fixed_now:%H:%M}, {len(upcoming)} appointment(s) still upcoming:")
    for appt in upcoming:
        print(f"  {appt.start_time:%H:%M} — {appt.activity.title} ({appt.status.value})")

    # ------------------------------------------------------------------
    section("5. Reschedule an appointment")
    # ------------------------------------------------------------------
    first = plan.appointments[0]
    print(f"Before: {first.activity.title} at {first.start_time:%H:%M}")
    first.reschedule(first.start_time.replace(hour=11, minute=0))
    print(f"After:  {first.activity.title} at {first.start_time:%H:%M}")

    # ------------------------------------------------------------------
    section("6. Cancel an appointment")
    # ------------------------------------------------------------------
    target = plan.appointments[-1]
    target.cancel()
    print(f"Cancelled: {target.activity.title} -> status = {target.status.value}")
    print(f"Upcoming now excludes it: "
          f"{[a.activity.title for a in plan.upcoming(now=fixed_now)]}")
    try:
        target.reschedule(fixed_now)
    except ValueError as exc:
        print(f"Rescheduling a cancelled appointment is blocked: {exc}")

    # ------------------------------------------------------------------
    section("7. Conflict detection & resolution")
    # ------------------------------------------------------------------
    # Rescheduling the first appointment onto another created an overlap; let the
    # scheduler push overlapping appointments apart.
    print("Appointments before resolve:")
    for appt in sorted(plan.appointments, key=lambda a: a.start_time):
        print(f"  {appt.start_time:%H:%M}–{appt.end_time:%H:%M} {appt.activity.title}")
    scheduler.resolve_conflicts(plan)
    print("After resolve_conflicts:")
    for appt in sorted(plan.appointments, key=lambda a: a.start_time):
        print(f"  {appt.start_time:%H:%M}–{appt.end_time:%H:%M} {appt.activity.title}")

    print("\nDone. Edit main.py to poke at other scenarios.")


if __name__ == "__main__":
    main()
