"""
PawPal+ Streamlit UI
"""

import streamlit as st
from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# ---------------------------------------------------------------------------
# Session-state bootstrap
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = Owner("My Owner")

owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)

# ---------------------------------------------------------------------------
# Sidebar – owner info + add pet
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🐾 PawPal+")
    st.divider()

    st.subheader("Owner")
    new_name = st.text_input("Your name", value=owner.name, key="owner_name_input")
    if new_name != owner.name:
        owner.name = new_name

    st.divider()

    st.subheader("Add a Pet")
    with st.form("add_pet_form", clear_on_submit=True):
        pet_name   = st.text_input("Pet name")
        pet_species = st.selectbox("Species", ["dog", "cat", "other"])
        pet_breed  = st.text_input("Breed (optional)")
        pet_age    = st.number_input("Age (years)", min_value=0, max_value=30, value=1)
        submitted  = st.form_submit_button("Add Pet")

    if submitted:
        if not pet_name.strip():
            st.sidebar.error("Pet name cannot be empty.")
        elif owner.get_pet(pet_name.strip()):
            st.sidebar.error(f"A pet named '{pet_name}' already exists.")
        else:
            owner.add_pet(Pet(pet_name.strip(), pet_species, pet_breed, pet_age))
            st.sidebar.success(f"{pet_name} added!")

    st.divider()

    if owner.pets:
        st.subheader("Your Pets")
        for pet in owner.pets:
            pending = len(pet.get_pending_tasks())
            st.write(f"**{pet.name}** ({pet.species}) — {pending} pending task(s)")
        if st.button("Remove last pet", key="remove_last"):
            owner.pets.pop()
            st.rerun()
    else:
        st.info("No pets yet. Add one above.")

# ---------------------------------------------------------------------------
# Main area – tabs
# ---------------------------------------------------------------------------
tab_schedule, tab_tasks, tab_add_task = st.tabs(
    ["📅 Today's Schedule", "📋 All Tasks", "➕ Add Task"]
)

# ============================================================
# Tab 1: Today's Schedule
# ============================================================
with tab_schedule:
    st.header(f"Schedule for {date.today().strftime('%A, %B %d %Y')}")

    if not owner.pets:
        st.info("Add a pet in the sidebar to get started.")
    else:
        # Conflict banner
        conflicts = scheduler.detect_conflicts()
        if conflicts:
            for pet_name, t, a, b in conflicts:
                st.warning(
                    f"⚠️ **Conflict detected** — {pet_name} has "
                    f"**{a}** and **{b}** both scheduled at {t}"
                )

        schedule = scheduler.get_daily_schedule(date.today())

        if not schedule:
            st.info("No tasks scheduled for today. Add some in the **Add Task** tab.")
        else:
            priority_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}

            for pet, task in schedule:
                col_check, col_time, col_pet, col_name, col_dur, col_pri, col_freq = st.columns(
                    [0.5, 1, 1.2, 2.5, 1, 1, 1]
                )
                with col_check:
                    done = st.checkbox(
                        "", value=task.completed,
                        key=f"complete_{id(task)}",
                        label_visibility="collapsed"
                    )
                    if done and not task.completed:
                        scheduler.mark_task_complete(task, pet)
                        st.rerun()
                with col_time:
                    st.write(f"**{task.time}**")
                with col_pet:
                    st.write(pet.name)
                with col_name:
                    if task.description:
                        st.write(f"{task.name} — *{task.description}*")
                    else:
                        st.write(task.name)
                with col_dur:
                    st.write(f"{task.duration_minutes} min")
                with col_pri:
                    st.write(priority_color.get(task.priority, "") + f" {task.priority}")
                with col_freq:
                    st.write(task.frequency)

        st.divider()
        col_a, col_b = st.columns(2)
        with col_a:
            total = len(scheduler.get_all_tasks())
            pending = len(scheduler.filter_by_status(completed=False))
            st.metric("Tasks today", len(schedule))
            st.metric("Pending (all time)", pending)
        with col_b:
            total_min = sum(t.duration_minutes for _, t in schedule)
            st.metric("Minutes planned today", total_min)
            st.metric("Conflicts", len(conflicts),
                      delta=len(conflicts) if conflicts else None,
                      delta_color="inverse")

# ============================================================
# Tab 2: All Tasks
# ============================================================
with tab_tasks:
    st.header("All Tasks")

    if not owner.pets:
        st.info("Add a pet in the sidebar first.")
    elif not scheduler.get_all_tasks():
        st.info("No tasks yet. Use the **Add Task** tab.")
    else:
        # Filter controls
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            pet_options = ["All pets"] + [p.name for p in owner.pets]
            selected_pet = st.selectbox("Filter by pet", pet_options, key="filter_pet")
        with col_f2:
            status_options = ["All", "Pending", "Completed"]
            selected_status = st.selectbox("Filter by status", status_options, key="filter_status")
        with col_f3:
            priority_options = ["All", "high", "medium", "low"]
            selected_priority = st.selectbox("Filter by priority", priority_options, key="filter_priority")

        # Apply filters
        tasks = scheduler.get_all_tasks()

        if selected_pet != "All pets":
            tasks = [(p, t) for p, t in tasks if p.name == selected_pet]
        if selected_status == "Pending":
            tasks = [(p, t) for p, t in tasks if not t.completed]
        elif selected_status == "Completed":
            tasks = [(p, t) for p, t in tasks if t.completed]
        if selected_priority != "All":
            tasks = [(p, t) for p, t in tasks if t.priority == selected_priority]

        tasks = scheduler.sort_by_time(tasks)

        if not tasks:
            st.info("No tasks match your filters.")
        else:
            rows = [
                {
                    "Pet":       pet.name,
                    "Task":      task.name,
                    "Time":      task.time,
                    "Duration":  f"{task.duration_minutes} min",
                    "Priority":  task.priority,
                    "Frequency": task.frequency,
                    "Due":       str(task.due_date),
                    "Done":      "✓" if task.completed else "",
                }
                for pet, task in tasks
            ]
            st.table(rows)

# ============================================================
# Tab 3: Add Task
# ============================================================
with tab_add_task:
    st.header("Add a Task")

    if not owner.pets:
        st.info("Add a pet in the sidebar before adding tasks.")
    else:
        with st.form("add_task_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                target_pet  = st.selectbox("Pet", [p.name for p in owner.pets])
                task_name   = st.text_input("Task name", value="Morning Walk")
                description = st.text_input("Description (optional)")
                task_time   = st.text_input("Time (HH:MM)", value="08:00")
            with col2:
                duration    = st.number_input("Duration (minutes)", min_value=1, max_value=480, value=30)
                priority    = st.selectbox("Priority", ["high", "medium", "low"])
                frequency   = st.selectbox("Frequency", ["daily", "weekly", "once"])
                due         = st.date_input("Due date", value=date.today())

            add_submitted = st.form_submit_button("Add Task")

        if add_submitted:
            # Validate time format
            import re
            if not re.match(r"^\d{2}:\d{2}$", task_time):
                st.error("Time must be in HH:MM format (e.g. 08:00).")
            elif not task_name.strip():
                st.error("Task name cannot be empty.")
            else:
                pet = owner.get_pet(target_pet)
                new_task = Task(
                    name=task_name.strip(),
                    time=task_time,
                    duration_minutes=int(duration),
                    priority=priority,
                    frequency=frequency,
                    description=description.strip(),
                    due_date=due,
                )
                pet.add_task(new_task)

                # Check for immediate conflicts
                conflicts_after = scheduler.detect_conflicts()
                new_conflicts = [
                    c for c in conflicts_after
                    if c[1] == task_time and (c[2] == task_name or c[3] == task_name)
                ]

                st.success(f"✅ '{task_name}' added to {target_pet}.")
                if new_conflicts:
                    for c in new_conflicts:
                        st.warning(
                            f"⚠️ Conflict: **{c[2]}** and **{c[3]}** are both at {c[1]} for {c[0]}."
                        )
                st.rerun()
