from fastapi import APIRouter, HTTPException, Depends
from typing import List
from backend.app.models.schemas import TaskResponse, TaskCreate, ReminderResponse, ReminderCreate
from backend.app.core.database import get_supabase

router = APIRouter(prefix="/routines", tags=["Routines & Reminders"])

MOCK_TASKS = [
    {"id": 1, "patient_id": 1, "title": "Breakfast & Warm Milk", "task_time": "09:00", "category": "Routine", "done": True},
    {"id": 2, "patient_id": 1, "title": "Cognitive Memory Activity", "task_time": "10:30", "category": "Cognitive", "done": False},
    {"id": 3, "patient_id": 1, "title": "Lunch & Short Nap", "task_time": "13:00", "category": "Routine", "done": False},
    {"id": 4, "patient_id": 1, "title": "Evening Courtyard Walk", "task_time": "17:00", "category": "Exercise", "done": False}
]

MOCK_REMINDERS = [
    {"id": 1, "patient_id": 1, "title": "Drink a glass of warm water", "reminder_time": "08:30", "frequency": "Daily", "done": True},
    {"id": 2, "patient_id": 1, "title": "Take blood pressure tablet", "reminder_time": "14:00", "frequency": "Daily", "done": False},
    {"id": 3, "patient_id": 1, "title": "Relaxing flute music time", "reminder_time": "17:30", "frequency": "Daily", "done": False}
]

@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(patient_id: int = 1, supabase = Depends(get_supabase)):
    return [t for t in MOCK_TASKS if t["patient_id"] == patient_id]

@router.post("/tasks", response_model=TaskResponse)
async def add_task(task: TaskCreate, supabase = Depends(get_supabase)):
    new_t = {
        "id": len(MOCK_TASKS) + 1,
        "patient_id": task.patient_id,
        "title": task.title,
        "task_time": task.task_time,
        "category": task.category,
        "done": False
    }
    MOCK_TASKS.append(new_t)
    return new_t

@router.post("/tasks/{task_id}/toggle", response_model=TaskResponse)
async def toggle_task_done(task_id: int):
    for t in MOCK_TASKS:
        if t["id"] == task_id:
            t["done"] = not t["done"]
            return t
    raise HTTPException(status_code=404, detail="Task not found")

@router.get("/reminders", response_model=List[ReminderResponse])
async def list_reminders(patient_id: int = 1, supabase = Depends(get_supabase)):
    return [r for r in MOCK_REMINDERS if r["patient_id"] == patient_id]

@router.post("/reminders", response_model=ReminderResponse)
async def add_reminder(reminder: ReminderCreate, supabase = Depends(get_supabase)):
    new_r = {
        "id": len(MOCK_REMINDERS) + 1,
        "patient_id": reminder.patient_id,
        "title": reminder.title,
        "reminder_time": reminder.reminder_time,
        "frequency": reminder.frequency,
        "done": False
    }
    MOCK_REMINDERS.append(new_r)
    return new_r

@router.post("/reminders/{reminder_id}/toggle", response_model=ReminderResponse)
async def toggle_reminder_done(reminder_id: int):
    for r in MOCK_REMINDERS:
        if r["id"] == reminder_id:
            r["done"] = not r["done"]
            return r
    raise HTTPException(status_code=404, detail="Reminder not found")
