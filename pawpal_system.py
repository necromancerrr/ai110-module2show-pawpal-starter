"""
PawPal+ logic layer.

Classes:
    Task      – a single care activity (time, duration, priority, recurrence)
    Pet       – a pet with a list of tasks
    Owner     – an owner who manages one or more pets
    Scheduler – retrieves, sorts, filters, and validates tasks across all pets
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """Represents a single pet care activity."""

    name: str
    time: str               # "HH:MM" – 24-hour format
    duration_minutes: int
    priority: str           # "low" | "medium" | "high"
    frequency: str          # "once" | "daily" | "weekly"
    description: str = ""
    completed: bool = False
    due_date: date = field(default_factory=date.today)

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task complete and return the next occurrence if recurring.

        Returns a new Task for the next day (daily) or next week (weekly),
        or None if frequency is 'once'.
        """
        self.completed = True

        if self.frequency == "daily":
            return Task(
                name=self.name,
                time=self.time,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                frequency=self.frequency,
                description=self.description,
                completed=False,
                due_date=self.due_date + timedelta(days=1),
            )
        if self.frequency == "weekly":
            return Task(
                name=self.name,
                time=self.time,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                frequency=self.frequency,
                description=self.description,
                completed=False,
                due_date=self.due_date + timedelta(weeks=1),
            )
        return None

    def __str__(self) -> str:
        status = "✓" if self.completed else "○"
        return f"[{status}] {self.time}  {self.name} ({self.duration_minutes}min, {self.priority})"


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Represents a pet owned by an Owner."""

    name: str
    species: str            # "dog" | "cat" | "other"
    breed: str = ""
    age: int = 0
    tasks: list = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet's task list."""
        self.tasks.remove(task)

    def get_pending_tasks(self) -> list[Task]:
        """Return all tasks that have not yet been completed."""
        return [t for t in self.tasks if not t.completed]

    def __str__(self) -> str:
        return f"{self.name} ({self.species}, age {self.age})"


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """Manages a collection of pets and provides aggregate task access."""

    def __init__(self, name: str, email: str = "") -> None:
        self.name = name
        self.email = email
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's household."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name (case-sensitive)."""
        self.pets = [p for p in self.pets if p.name != pet_name]

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Return the Pet object with the given name, or None if not found."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every (Pet, Task) pair across all pets."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def __str__(self) -> str:
        return f"Owner: {self.name} | Pets: {[p.name for p in self.pets]}"


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """The brain of PawPal+.

    Retrieves tasks from an Owner, sorts and filters them, detects scheduling
    conflicts, and handles recurring task creation after completion.
    """

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return all (Pet, Task) pairs from the owner."""
        return self.owner.get_all_tasks()

    def get_daily_schedule(self, target_date: Optional[date] = None) -> list[tuple[Pet, Task]]:
        """Return pending tasks due on target_date, sorted by time.

        Defaults to today if no date is provided.
        """
        if target_date is None:
            target_date = date.today()
        due_today = [
            (pet, task)
            for pet, task in self.get_all_tasks()
            if task.due_date == target_date and not task.completed
        ]
        return self.sort_by_time(due_today)

    # ------------------------------------------------------------------
    # Sorting & filtering
    # ------------------------------------------------------------------

    def sort_by_time(self, tasks: Optional[list] = None) -> list[tuple[Pet, Task]]:
        """Sort (Pet, Task) pairs chronologically by task time (HH:MM)."""
        if tasks is None:
            tasks = self.get_all_tasks()
        return sorted(tasks, key=lambda pt: pt[1].time)

    def filter_by_status(
        self, completed: bool, tasks: Optional[list] = None
    ) -> list[tuple[Pet, Task]]:
        """Filter tasks by completion status."""
        if tasks is None:
            tasks = self.get_all_tasks()
        return [(pet, task) for pet, task in tasks if task.completed == completed]

    def filter_by_pet(self, pet_name: str) -> list[tuple[Pet, Task]]:
        """Return all tasks that belong to the named pet."""
        return [(pet, task) for pet, task in self.get_all_tasks() if pet.name == pet_name]

    def filter_by_priority(self, priority: str) -> list[tuple[Pet, Task]]:
        """Return all tasks matching the given priority level."""
        return [(pet, task) for pet, task in self.get_all_tasks() if task.priority == priority]

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(self) -> list[tuple[str, str, str, str]]:
        """Detect tasks for the same pet scheduled at the same time.

        Returns a list of (pet_name, time, task_a_name, task_b_name) tuples.
        Only compares tasks with the same due_date to avoid false positives
        across different days.
        """
        conflicts: list[tuple[str, str, str, str]] = []
        seen: dict[tuple[str, str, date], Task] = {}

        for pet, task in self.get_all_tasks():
            key = (pet.name, task.time, task.due_date)
            if key in seen:
                conflicts.append((pet.name, task.time, seen[key].name, task.name))
            else:
                seen[key] = task

        return conflicts

    # ------------------------------------------------------------------
    # Completion & recurrence
    # ------------------------------------------------------------------

    def mark_task_complete(self, task: Task, pet: Pet) -> Optional[Task]:
        """Mark a task complete and append the next recurrence to the pet.

        Returns the new Task if one was created, otherwise None.
        """
        next_task = task.mark_complete()
        if next_task:
            pet.add_task(next_task)
        return next_task

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def summary(self, target_date: Optional[date] = None) -> str:
        """Return a formatted plaintext schedule for the terminal."""
        if target_date is None:
            target_date = date.today()

        lines = [
            "=" * 56,
            f"  PawPal+ Schedule  |  {target_date.strftime('%A, %B %d %Y')}",
            "=" * 56,
        ]

        schedule = self.get_daily_schedule(target_date)
        if not schedule:
            lines.append("  (no tasks scheduled for today)")
        else:
            for pet, task in schedule:
                flag = "[high]" if task.priority == "high" else "      "
                lines.append(
                    f"  {task.time}  {flag}  {pet.name:10}  {task.name:22}  {task.duration_minutes}min"
                )

        conflicts = self.detect_conflicts()
        if conflicts:
            lines.append("")
            lines.append("  ⚠  CONFLICTS DETECTED")
            for pet_name, t, a, b in conflicts:
                lines.append(f"     {pet_name} @ {t}: '{a}' and '{b}' overlap")

        lines.append("=" * 56)
        return "\n".join(lines)
