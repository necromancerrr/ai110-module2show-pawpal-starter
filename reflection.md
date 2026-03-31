# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

I identified three core actions a user must be able to perform:
1. **Add a pet** — store the pet's name, species, breed, and age under an owner.
2. **Schedule a task** — attach a care activity (with a time, duration, priority, and recurrence) to a specific pet.
3. **See today's tasks** — retrieve and display all pending tasks due today, sorted by time.

From those actions I derived four classes:

| Class | Responsibility |
|---|---|
| `Task` | Holds all data about a single care activity. Knows how to mark itself complete and produce the next occurrence when recurring. |
| `Pet` | Stores a pet's profile and owns its task list. Provides methods to add, remove, and filter tasks. |
| `Owner` | Acts as the root of the object graph. Manages a collection of `Pet` objects and provides a single point to retrieve all tasks across every pet. |
| `Scheduler` | The "brain." Does not store data — it reads from the `Owner` and applies algorithms: sorting, filtering, conflict detection, and recurrence management. |

I used Python `@dataclass` for `Task` and `Pet` because their purpose is primarily to hold structured data. `Owner` and `Scheduler` are plain classes because they contain logic and mutable state that benefits from explicit `__init__` methods.

**b. Design changes**

One change made during implementation: originally `mark_complete()` was a method on `Scheduler`, not on `Task`. After drafting the skeleton I realized that a Task knowing how to produce its own next occurrence is cleaner — it keeps recurrence logic co-located with the data it operates on, and it makes the method independently testable. `Scheduler.mark_task_complete()` was kept as a thin wrapper that calls `task.mark_complete()` and appends the result to the pet's list, so the UI only needs to call one method.

A second change: conflict detection was initially designed to compare any two tasks regardless of date. This produced false positives (e.g., a daily task on Monday conflicting with the same task rescheduled to Tuesday). Scoping the key to `(pet_name, time, due_date)` eliminated those spurious warnings.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints:

1. **Time** — tasks are sorted by their `HH:MM` string field. Since all times share the same format, lexicographic sort produces correct chronological order without parsing.
2. **Date** — `get_daily_schedule()` filters to only tasks whose `due_date` matches the target date, preventing tasks from other days from appearing.
3. **Completion status** — completed tasks are excluded from the daily schedule so finished work does not clutter the view.

Priority (`high / medium / low`) is surfaced in the UI as a visual indicator but does not re-order tasks within the same time slot. The decision was deliberate: most pet care tasks are time-sensitive (medication at 08:00 must happen at 08:00 regardless of priority), so time is the primary sort key.

**b. Tradeoffs**

**Tradeoff: exact-time conflict detection vs. overlap-duration detection.**

The current implementation flags a conflict only when two tasks share the *exact same start time* for the same pet on the same date. It does not check whether a 30-minute task starting at 08:00 overlaps with a 45-minute task starting at 08:15.

This is a reasonable tradeoff for a pet care context because:
- Most pet tasks (feeding, meds, a quick walk) are short and rarely run over.
- Implementing duration-overlap detection requires comparing interval pairs — O(n²) per pet — and adds complexity the average user would never notice.
- A simple exact-match check is transparent: users can understand and predict when a warning will fire.

If the app were extended to support longer appointments (grooming sessions, vet visits > 1 hour), duration-overlap detection would be worth adding.

---

## 3. AI Collaboration

**a. How you used AI**

AI assistance was used across all phases:

- **Design brainstorming** — asked Claude to confirm that splitting recurrence logic between `Task.mark_complete()` and `Scheduler.mark_task_complete()` was the right separation of concerns. It agreed and explained why co-locating recurrence on `Task` made independent testing easier.
- **Scaffolding** — used AI to generate the initial class skeletons and dataclass field definitions, which saved time on boilerplate.
- **Test generation** — asked for a list of edge cases to cover, then used those as a checklist to write the 25-test suite. The AI suggested testing "no conflict when same time but different pets," which I had initially missed.
- **Debugging** — when the conflict detection was producing false positives across dates, I described the symptom and the AI immediately identified that the lookup key was missing the `due_date` dimension.

The most useful prompts were specific and included the context of *why* something wasn't working, rather than just "fix this."

**b. Judgment and verification**

The AI initially suggested implementing `sort_by_time()` by parsing the `HH:MM` string into a `datetime.time` object for comparison:

```python
key=lambda pt: datetime.strptime(pt[1].time, "%H:%M").time()
```

I kept the simpler lexicographic version instead:

```python
key=lambda pt: pt[1].time
```

Both produce the same result — `HH:MM` strings sort correctly as strings because they are zero-padded and fixed-width. The `datetime.strptime` version adds an import and a parse step with no benefit. I verified this by testing both with out-of-order time strings in the Python REPL before deciding.

---

## 4. Testing and Verification

**a. What you tested**

The 25-test suite covers:

| Category | Tests |
|---|---|
| `Task.mark_complete()` | Sets `completed=True`; returns `None` for `once`; returns next-day task for `daily`; returns next-week task for `weekly`; copies all attributes to new task |
| `Pet` task management | `add_task` increases count; `get_pending_tasks` excludes completed; `remove_task` decreases count |
| `Owner` pet management | `add_pet` increases count; `remove_pet` removes by name; `get_pet` returns correct object; `get_pet` returns `None` for missing name |
| `Scheduler` sorting | Chronological order; empty list returns empty list |
| `Scheduler` filtering | Pending-only; completed-only; by pet name; by priority |
| `Scheduler` conflict detection | Flags same pet + same time + same date; no false positive for different times; no false positive for different pets at same time |
| `Scheduler` recurrence side-effect | `mark_task_complete` appends next occurrence to pet; does not append for `once` tasks |
| Daily schedule | Excludes tasks from other dates; excludes completed tasks |

These tests matter because the scheduler's value to the user depends entirely on these behaviors being correct — a missed conflict or a wrong sort order directly causes the owner to give care at the wrong time.

**b. Confidence**

**4 / 5 stars.**

All 25 tests pass. Confidence is high for the behaviors explicitly tested. One star is withheld because:
- Edge cases around midnight (e.g., a task at `23:45` and one at `00:15` the next day) have not been tested.
- The UI's `st.rerun()` flow for marking tasks complete is verified manually but not by automated tests.
- Load/persistence (saving state across browser sessions) is out of scope but would be needed in a production app.

Next edge cases to test: pet with zero tasks, owner with zero pets, tasks with identical names on different dates, sorting stability when two tasks share the same time.

---

## 5. Reflection

**a. What went well**

The CLI-first workflow was the most successful structural decision. Having `main.py` print a readable schedule before touching `app.py` meant every piece of logic was verified in isolation. When the Streamlit UI was connected, it worked almost immediately because the backend had no hidden bugs.

**b. What you would improve**

The `Task.time` field is a plain string with no enforcement — a user could enter `"8:0"` or `"8am"` and break sorting silently. In a next iteration I would either validate the format at construction time (raising a `ValueError` for malformed strings) or replace the field with a `datetime.time` object. The UI already validates the format with a regex, but the class itself has no guard.

**c. Key takeaway**

The most important lesson: AI is a powerful *accelerator* but a poor *architect*. When I asked for code without first specifying the design constraints, the suggestions were technically correct but architecturally messy (e.g., putting recurrence logic in the Scheduler instead of on the Task). Once I established the design rules — "Task owns its own recurrence; Scheduler only orchestrates" — the AI produced clean, consistent code. The lead architect role means deciding *where* logic lives before asking AI to write it.
