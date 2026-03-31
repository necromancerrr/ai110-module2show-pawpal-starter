# PawPal+ 🐾

A smart pet care management system that helps owners stay consistent with daily routines — feedings, walks, medications, and appointments — powered by algorithmic scheduling logic and a Streamlit UI.

---

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

---

## Features

### Core OOP System
- **Owner** — manages a household of pets; single access point for all tasks
- **Pet** — holds a profile (name, species, breed, age) and an owned task list
- **Task** — a care activity with time, duration, priority, frequency, and completion state
- **Scheduler** — the algorithmic brain; reads from Owner and applies all scheduling logic

### Smarter Scheduling

| Feature | How it works |
|---|---|
| **Sort by time** | Tasks are sorted chronologically using `HH:MM` string comparison — zero-padded format makes lexicographic and numeric order identical, with no parsing overhead |
| **Filter by pet / status / priority** | Compose filters to narrow any task list to exactly what you need |
| **Daily recurrence** | Marking a `daily` task complete automatically creates a new copy due the next day using `timedelta(days=1)` |
| **Weekly recurrence** | Same as daily but advances by `timedelta(weeks=1)` |
| **Conflict detection** | Flags any two tasks for the same pet scheduled at the same start time on the same date — returns a warning message instead of crashing |
| **Daily schedule view** | `get_daily_schedule()` returns only pending tasks due today, sorted by time |

### Streamlit UI
- Sidebar: owner name, add-pet form, live pet list with pending task counts
- **Today's Schedule** tab — sorted task list, conflict banners, checkboxes to mark tasks complete
- **All Tasks** tab — filter by pet, status, and priority; rendered as a table
- **Add Task** tab — form with HH:MM validation and immediate conflict warning on submit

---

## 📸 Demo

<a href="/course_images/ai110/pawpal_screenshot.png" target="_blank">
  <img src='/course_images/ai110/pawpal_screenshot.png' title='PawPal App' width='' alt='PawPal App' class='center-block' />
</a>

---

## System Architecture (UML)

See [`uml_final.md`](uml_final.md) for the full Mermaid.js class diagram and relationship table.

```
Owner  ──owns──▶  Pet  ──has──▶  Task
  ▲                                │
  └──────── Scheduler reads ───────┘
```

---

## Getting Started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the CLI demo

```bash
python main.py
```

Prints a formatted daily schedule, filtering demos, recurring task advancement, and conflict detection — all without the UI.

### Run the Streamlit app

```bash
streamlit run app.py
```

---

## Testing PawPal+

```bash
python -m pytest
```

The test suite covers 25 behaviors across all four classes:

| Category | What is verified |
|---|---|
| Task completion | `mark_complete()` sets `completed = True` |
| Recurrence — daily | Next task is due `today + 1 day` |
| Recurrence — weekly | Next task is due `today + 7 days` |
| Recurrence — once | No follow-up task is created |
| Attribute inheritance | Recurring copies preserve name, time, duration, priority |
| Pet task management | `add_task` / `remove_task` / `get_pending_tasks` |
| Owner pet management | `add_pet` / `remove_pet` / `get_pet` (found and not found) |
| Sorting | Tasks returned in strict `HH:MM` chronological order |
| Filtering | By completion status, pet name, and priority level |
| Conflict detection | Flags same pet + same time + same date; no false positives for different times or different pets |
| Recurrence side-effect | `Scheduler.mark_task_complete()` appends next occurrence to the pet |
| Daily schedule | Excludes tasks from other dates and already-completed tasks |

**Confidence level: ★★★★☆** — all 25 tests pass; one star withheld for untested edge cases (midnight boundary, malformed time strings, zero-pet/zero-task states, UI rerun flow).

---

## Project Structure

```
pawpal_system.py   # Logic layer — Owner, Pet, Task, Scheduler
app.py             # Streamlit UI
main.py            # CLI demo script
tests/
  test_pawpal.py   # 25 automated pytest tests
uml_final.md       # Mermaid.js class diagram
reflection.md      # Design decisions and AI collaboration notes
requirements.txt
```

---

## Design Notes

See [`reflection.md`](reflection.md) for a full write-up covering:
- Class responsibilities and initial UML design
- Design changes made during implementation
- Scheduling tradeoffs (exact-time vs. duration-overlap conflict detection)
- How AI assistance was used and where AI suggestions were rejected
- Test coverage rationale and confidence assessment
