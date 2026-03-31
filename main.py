"""
CLI demo for PawPal+.

Run:  python main.py

Demonstrates Owner/Pet/Task creation, sorting, filtering, conflict detection,
and recurring task advancement — all without the Streamlit UI.
"""

from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler


def main() -> None:
    # ------------------------------------------------------------------
    # Setup: owner + pets
    # ------------------------------------------------------------------
    owner = Owner("Jordan", "jordan@example.com")

    mochi = Pet("Mochi", "dog", "Shiba Inu", 3)
    luna = Pet("Luna", "cat", "Tabby", 5)

    owner.add_pet(mochi)
    owner.add_pet(luna)

    today = date.today()

    # ------------------------------------------------------------------
    # Mochi's tasks  (intentionally added out of chronological order)
    # ------------------------------------------------------------------
    mochi.add_task(Task("Evening Walk",   "18:00", 45, "high",   "daily",  "Long evening walk",          due_date=today))
    mochi.add_task(Task("Morning Walk",   "07:00", 30, "high",   "daily",  "30-min walk around the block", due_date=today))
    mochi.add_task(Task("Breakfast",      "08:00", 10, "high",   "daily",  "1 cup dry kibble",           due_date=today))
    mochi.add_task(Task("Heartworm Med",  "09:00",  5, "high",   "weekly", "Monthly heartworm pill",     due_date=today))

    # This task intentionally conflicts with Heartworm Med (same pet, same time)
    mochi.add_task(Task("Vet Check-in",   "09:00", 60, "high",   "once",   "Annual vet visit",           due_date=today))

    # ------------------------------------------------------------------
    # Luna's tasks
    # ------------------------------------------------------------------
    luna.add_task(Task("Breakfast",  "08:00",  5, "high",   "daily",  "1/2 cup wet food",       due_date=today))
    luna.add_task(Task("Playtime",   "17:00", 20, "medium", "daily",  "Interactive toy session", due_date=today))
    luna.add_task(Task("Grooming",   "14:00", 15, "low",    "weekly", "Brush coat",              due_date=today))

    scheduler = Scheduler(owner)

    # ------------------------------------------------------------------
    # 1. Full daily schedule (sorted)
    # ------------------------------------------------------------------
    print(scheduler.summary(today))

    # ------------------------------------------------------------------
    # 2. Filtering demos
    # ------------------------------------------------------------------
    print("\n--- Pending tasks only ---")
    pending = scheduler.filter_by_status(completed=False)
    for pet, task in scheduler.sort_by_time(pending):
        print(f"  {task.time}  {pet.name:8}  {task.name}")

    print("\n--- Mochi's tasks only ---")
    for pet, task in scheduler.filter_by_pet("Mochi"):
        print(f"  {task.time}  {task.name}")

    print("\n--- High-priority tasks ---")
    for pet, task in scheduler.sort_by_time(scheduler.filter_by_priority("high")):
        print(f"  {task.time}  {pet.name:8}  {task.name}")

    # ------------------------------------------------------------------
    # 3. Recurring task demo
    # ------------------------------------------------------------------
    print("\n--- Recurring task demo ---")
    morning_walk = mochi.tasks[1]   # Morning Walk (daily)
    print(f"  Before: '{morning_walk.name}'  completed={morning_walk.completed}  due={morning_walk.due_date}")
    next_task = scheduler.mark_task_complete(morning_walk, mochi)
    print(f"  After:  '{morning_walk.name}'  completed={morning_walk.completed}")
    if next_task:
        print(f"  Next occurrence → '{next_task.name}'  due={next_task.due_date}")

    # ------------------------------------------------------------------
    # 4. Owner summary
    # ------------------------------------------------------------------
    print(f"\n{owner}")
    for pet in owner.pets:
        print(f"  {pet}  |  {len(pet.tasks)} task(s)  |  {len(pet.get_pending_tasks())} pending")


if __name__ == "__main__":
    main()
