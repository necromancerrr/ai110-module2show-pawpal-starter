# PawPal+ — Final System Architecture (UML)

Paste the code block below into [Mermaid Live Editor](https://mermaid.live) to render the diagram.

```mermaid
classDiagram
    class Task {
        +str name
        +str time
        +int duration_minutes
        +str priority
        +str frequency
        +str description
        +bool completed
        +date due_date
        +mark_complete() Task|None
        +__str__() str
    }

    class Pet {
        +str name
        +str species
        +str breed
        +int age
        +list~Task~ tasks
        +add_task(task: Task) None
        +remove_task(task: Task) None
        +get_pending_tasks() list~Task~
        +__str__() str
    }

    class Owner {
        +str name
        +str email
        +list~Pet~ pets
        +add_pet(pet: Pet) None
        +remove_pet(pet_name: str) None
        +get_pet(pet_name: str) Pet|None
        +get_all_tasks() list~tuple~
        +__str__() str
    }

    class Scheduler {
        +Owner owner
        +get_all_tasks() list~tuple~
        +get_daily_schedule(target_date: date) list~tuple~
        +sort_by_time(tasks: list) list~tuple~
        +filter_by_status(completed: bool, tasks: list) list~tuple~
        +filter_by_pet(pet_name: str) list~tuple~
        +filter_by_priority(priority: str) list~tuple~
        +detect_conflicts() list~tuple~
        +mark_task_complete(task: Task, pet: Pet) Task|None
        +summary(target_date: date) str
    }

    Owner "1" --> "0..*" Pet : owns
    Pet "1" --> "0..*" Task : has
    Scheduler "1" --> "1" Owner : reads from
    Task ..> Task : creates next occurrence
```

## Relationships

| Relationship | Type | Description |
|---|---|---|
| Owner → Pet | Composition | An Owner holds a list of Pet objects; pets are managed through the Owner |
| Pet → Task | Composition | A Pet holds a list of Task objects; tasks are added and removed via the Pet |
| Scheduler → Owner | Association | Scheduler reads from the Owner to retrieve all pets and tasks |
| Task → Task | Dependency | `mark_complete()` on a recurring Task produces a new Task instance |
