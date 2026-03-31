"""
Automated test suite for PawPal+.

Run:  python -m pytest
"""

import pytest
from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def owner() -> Owner:
    """Owner with two pets (no tasks attached yet)."""
    o = Owner("Jordan")
    o.add_pet(Pet("Mochi", "dog"))
    o.add_pet(Pet("Luna", "cat"))
    return o


@pytest.fixture
def scheduler(owner: Owner) -> Scheduler:
    return Scheduler(owner)


@pytest.fixture
def today() -> date:
    return date.today()


# ---------------------------------------------------------------------------
# Task – mark_complete & recurrence
# ---------------------------------------------------------------------------

def test_mark_complete_sets_flag():
    """mark_complete() must flip task.completed to True."""
    task = Task("Walk", "08:00", 30, "high", "once")
    task.mark_complete()
    assert task.completed is True


def test_once_task_returns_no_next():
    """A one-time task should return None (no follow-up task)."""
    task = Task("Vet Visit", "10:00", 60, "high", "once")
    assert task.mark_complete() is None


def test_daily_recurrence_next_day(today):
    """Completing a daily task must produce a new task for the next calendar day."""
    task = Task("Morning Walk", "07:00", 30, "high", "daily", due_date=today)
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.completed is False
    assert next_task.name == task.name


def test_weekly_recurrence_next_week(today):
    """Completing a weekly task must produce a new task seven days later."""
    task = Task("Grooming", "14:00", 15, "low", "weekly", due_date=today)
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.due_date == today + timedelta(weeks=1)


def test_recurrence_copies_attributes(today):
    """The generated follow-up task should inherit all key attributes."""
    task = Task("Medication", "09:00", 5, "high", "daily",
                description="Give pill", due_date=today)
    next_task = task.mark_complete()
    assert next_task.time == task.time
    assert next_task.duration_minutes == task.duration_minutes
    assert next_task.priority == task.priority
    assert next_task.description == task.description


# ---------------------------------------------------------------------------
# Pet – task management
# ---------------------------------------------------------------------------

def test_add_task_increases_count():
    """add_task() should increase the pet's task list length by 1."""
    pet = Pet("Mochi", "dog")
    assert len(pet.tasks) == 0
    pet.add_task(Task("Walk", "08:00", 30, "high", "daily"))
    assert len(pet.tasks) == 1


def test_get_pending_excludes_completed():
    """get_pending_tasks() must omit tasks where completed=True."""
    pet = Pet("Mochi", "dog")
    done = Task("Walk", "08:00", 30, "high", "once")
    done.completed = True
    pending = Task("Meds", "09:00", 5, "high", "daily")
    pet.add_task(done)
    pet.add_task(pending)
    result = pet.get_pending_tasks()
    assert len(result) == 1
    assert result[0].name == "Meds"


def test_remove_task(today):
    """remove_task() should reduce the task list length by 1."""
    pet = Pet("Mochi", "dog")
    task = Task("Walk", "08:00", 30, "high", "once", due_date=today)
    pet.add_task(task)
    pet.remove_task(task)
    assert len(pet.tasks) == 0


# ---------------------------------------------------------------------------
# Owner – pet management
# ---------------------------------------------------------------------------

def test_owner_add_pet():
    """add_pet() should increase the owner's pet count."""
    owner = Owner("Jordan")
    assert len(owner.pets) == 0
    owner.add_pet(Pet("Mochi", "dog"))
    assert len(owner.pets) == 1


def test_owner_remove_pet(owner):
    """remove_pet() should remove the named pet from the owner's list."""
    owner.remove_pet("Mochi")
    assert all(p.name != "Mochi" for p in owner.pets)


def test_owner_get_pet_returns_correct(owner):
    """get_pet() should return the Pet object with the matching name."""
    pet = owner.get_pet("Luna")
    assert pet is not None
    assert pet.name == "Luna"


def test_owner_get_pet_missing(owner):
    """get_pet() should return None when no pet matches."""
    assert owner.get_pet("Rex") is None


# ---------------------------------------------------------------------------
# Scheduler – sorting
# ---------------------------------------------------------------------------

def test_sort_by_time_is_chronological(owner, today):
    """sort_by_time() must return tasks in ascending HH:MM order."""
    mochi = owner.get_pet("Mochi")
    mochi.add_task(Task("Evening Walk", "18:00", 30, "high",   "daily", due_date=today))
    mochi.add_task(Task("Morning Walk", "07:00", 30, "high",   "daily", due_date=today))
    mochi.add_task(Task("Noon Feeding", "12:00", 10, "medium", "daily", due_date=today))

    scheduler = Scheduler(owner)
    times = [t.time for _, t in scheduler.sort_by_time()]
    assert times == sorted(times)


def test_sort_empty_list(scheduler):
    """sort_by_time() on an empty list must return an empty list."""
    assert scheduler.sort_by_time([]) == []


# ---------------------------------------------------------------------------
# Scheduler – filtering
# ---------------------------------------------------------------------------

def test_filter_by_status_pending(owner, today):
    """filter_by_status(False) should return only incomplete tasks."""
    pet = owner.get_pet("Mochi")
    done = Task("Walk", "08:00", 30, "high", "once", due_date=today)
    done.completed = True
    todo = Task("Meds", "09:00", 5, "high", "daily", due_date=today)
    pet.add_task(done)
    pet.add_task(todo)

    scheduler = Scheduler(owner)
    pending = scheduler.filter_by_status(completed=False)
    assert all(not t.completed for _, t in pending)


def test_filter_by_status_completed(owner, today):
    """filter_by_status(True) should return only completed tasks."""
    pet = owner.get_pet("Mochi")
    done = Task("Walk", "08:00", 30, "high", "once", due_date=today)
    done.completed = True
    pet.add_task(done)
    pet.add_task(Task("Meds", "09:00", 5, "high", "daily", due_date=today))

    scheduler = Scheduler(owner)
    completed = scheduler.filter_by_status(completed=True)
    assert all(t.completed for _, t in completed)


def test_filter_by_pet_returns_correct_owner(owner, today):
    """filter_by_pet('Mochi') should only return tasks belonging to Mochi."""
    owner.get_pet("Mochi").add_task(Task("Walk", "07:00", 30, "high", "daily", due_date=today))
    owner.get_pet("Luna").add_task(Task("Playtime", "17:00", 20, "medium", "daily", due_date=today))

    scheduler = Scheduler(owner)
    mochi_tasks = scheduler.filter_by_pet("Mochi")
    assert len(mochi_tasks) == 1
    assert all(p.name == "Mochi" for p, _ in mochi_tasks)


def test_filter_by_priority(owner, today):
    """filter_by_priority('high') should return only high-priority tasks."""
    pet = owner.get_pet("Mochi")
    pet.add_task(Task("Walk", "07:00", 30, "high",   "daily", due_date=today))
    pet.add_task(Task("Play", "15:00", 20, "low",    "daily", due_date=today))

    scheduler = Scheduler(owner)
    high = scheduler.filter_by_priority("high")
    assert all(t.priority == "high" for _, t in high)


# ---------------------------------------------------------------------------
# Scheduler – conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflict_same_pet_same_time(owner, today):
    """Two tasks for the same pet at the same time and date must be flagged."""
    pet = owner.get_pet("Mochi")
    pet.add_task(Task("Walk",      "09:00", 30, "high", "once", due_date=today))
    pet.add_task(Task("Vet Visit", "09:00", 60, "high", "once", due_date=today))

    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) == 1
    assert conflicts[0][1] == "09:00"


def test_no_conflict_different_times(owner, today):
    """Tasks at different times must not produce a conflict."""
    pet = owner.get_pet("Mochi")
    pet.add_task(Task("Walk", "07:00", 30, "high", "daily", due_date=today))
    pet.add_task(Task("Meds", "08:00",  5, "high", "daily", due_date=today))

    scheduler = Scheduler(owner)
    assert scheduler.detect_conflicts() == []


def test_no_conflict_different_pets(owner, today):
    """Same time is fine if tasks belong to different pets."""
    owner.get_pet("Mochi").add_task(Task("Walk",    "08:00", 30, "high", "daily", due_date=today))
    owner.get_pet("Luna").add_task( Task("Feeding", "08:00",  5, "high", "daily", due_date=today))

    scheduler = Scheduler(owner)
    assert scheduler.detect_conflicts() == []


# ---------------------------------------------------------------------------
# Scheduler – mark_task_complete with recurrence side-effect
# ---------------------------------------------------------------------------

def test_mark_complete_appends_recurrence(owner, today):
    """mark_task_complete() for a daily task should add a new task to the pet."""
    pet = owner.get_pet("Mochi")
    task = Task("Morning Walk", "07:00", 30, "high", "daily", due_date=today)
    pet.add_task(task)
    initial_count = len(pet.tasks)

    scheduler = Scheduler(owner)
    scheduler.mark_task_complete(task, pet)

    assert len(pet.tasks) == initial_count + 1
    assert pet.tasks[-1].due_date == today + timedelta(days=1)


def test_mark_complete_once_no_append(owner, today):
    """mark_task_complete() for a one-time task must NOT add a new task."""
    pet = owner.get_pet("Mochi")
    task = Task("Vet Visit", "10:00", 60, "high", "once", due_date=today)
    pet.add_task(task)
    initial_count = len(pet.tasks)

    scheduler = Scheduler(owner)
    scheduler.mark_task_complete(task, pet)

    assert len(pet.tasks) == initial_count


# ---------------------------------------------------------------------------
# Scheduler – daily schedule
# ---------------------------------------------------------------------------

def test_daily_schedule_only_today(owner, today):
    """get_daily_schedule() should exclude tasks due on other dates."""
    pet = owner.get_pet("Mochi")
    pet.add_task(Task("Walk",    "07:00", 30, "high", "daily", due_date=today))
    pet.add_task(Task("Old Task","08:00", 10, "low",  "once",
                      due_date=today - timedelta(days=1)))

    scheduler = Scheduler(owner)
    schedule = scheduler.get_daily_schedule(today)
    assert len(schedule) == 1
    assert schedule[0][1].name == "Walk"


def test_daily_schedule_excludes_completed(owner, today):
    """get_daily_schedule() should not include tasks already marked complete."""
    pet = owner.get_pet("Mochi")
    done = Task("Walk", "07:00", 30, "high", "daily", due_date=today)
    done.completed = True
    pet.add_task(done)
    pet.add_task(Task("Meds", "08:00", 5, "high", "daily", due_date=today))

    scheduler = Scheduler(owner)
    schedule = scheduler.get_daily_schedule(today)
    assert len(schedule) == 1
    assert schedule[0][1].name == "Meds"
