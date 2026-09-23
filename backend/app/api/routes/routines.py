from typing import List

from fastapi import APIRouter, Depends, HTTPException

from backend.app.core import database as db_module
from backend.app.core.access import can_write, ensure_patient_access
from backend.app.core.security import get_current_user
from backend.app.models.schemas import ReminderCreate, ReminderResponse, TaskCreate, TaskResponse

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

ALLOWED_TASK_CATEGORIES = {"Daily", "Routine", "Exercise", "Appointment", "Cognitive"}
ALLOWED_FREQUENCIES = {"Daily", "Once", "Hourly", "Weekly"}


def _scoped(table: str):
    return db_module.get_supabase_admin().table(table) if db_module.is_supabase_configured() else None


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(patient_id: int = 1, user: dict = Depends(get_current_user)):
    await ensure_patient_access(user, patient_id)
    q = _scoped("tasks")
    if q is not None:
        try:
            res = q.select("*").eq("patient_id", patient_id).order("task_time").execute()
            return res.data or []
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to load tasks: {exc}") from exc
    return [t for t in MOCK_TASKS if t["patient_id"] == patient_id]


@router.post("/tasks", response_model=TaskResponse)
async def add_task(task: TaskCreate, user: dict = Depends(get_current_user)):
    await ensure_patient_access(user, task.patient_id)
    if not can_write(user):
        raise HTTPException(status_code=403, detail="You cannot add tasks for this patient.")
    if task.category not in ALLOWED_TASK_CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid task category.")
    q = _scoped("tasks")
    if q is not None:
        try:
            res = q.insert(
                {"patient_id": task.patient_id, "title": task.title.strip(),
                 "task_time": task.task_time, "category": task.category, "done": False}
            ).execute()
            return (res.data or [{}])[0]
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to add task: {exc}") from exc
    new_t = {"id": max([t["id"] for t in MOCK_TASKS], default=0) + 1,
             "patient_id": task.patient_id, "title": task.title.strip(),
             "task_time": task.task_time, "category": task.category, "done": False}
    MOCK_TASKS.append(new_t)
    return new_t


@router.post("/tasks/{task_id}/toggle", response_model=TaskResponse)
async def toggle_task_done(task_id: int, patient_id: int = 1, user: dict = Depends(get_current_user)):
    await ensure_patient_access(user, patient_id)
    if not can_write(user):
        raise HTTPException(status_code=403, detail="You cannot update tasks for this patient.")
    q = _scoped("tasks")
    if q is not None:
        try:
            cur = q.select("*").eq("id", task_id).eq("patient_id", patient_id).single().execute()
            new_done = not bool((cur.data or {}).get("done"))
            res = q.update({"done": new_done}).eq("id", task_id).eq("patient_id", patient_id).execute()
            return (res.data or [{}])[0]
        except Exception as exc:
            raise HTTPException(status_code=404, detail=f"Task not found: {exc}") from exc
    for t in MOCK_TASKS:
        if t["id"] == task_id and t["patient_id"] == patient_id:
            t["done"] = not t["done"]
            return t
    raise HTTPException(status_code=404, detail="Task not found")


@router.get("/reminders", response_model=List[ReminderResponse])
async def list_reminders(patient_id: int = 1, user: dict = Depends(get_current_user)):
    await ensure_patient_access(user, patient_id)
    q = _scoped("reminders")
    if q is not None:
        try:
            res = q.select("*").eq("patient_id", patient_id).order("reminder_time").execute()
            return res.data or []
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to load reminders: {exc}") from exc
    return [r for r in MOCK_REMINDERS if r["patient_id"] == patient_id]


@router.post("/reminders", response_model=ReminderResponse)
async def add_reminder(reminder: ReminderCreate, user: dict = Depends(get_current_user)):
    await ensure_patient_access(user, reminder.patient_id)
    if not can_write(user):
        raise HTTPException(status_code=403, detail="You cannot add reminders for this patient.")
    if reminder.frequency not in ALLOWED_FREQUENCIES:
        raise HTTPException(status_code=400, detail="Invalid reminder frequency.")
    q = _scoped("reminders")
    if q is not None:
        try:
            res = q.insert(
                {"patient_id": reminder.patient_id, "title": reminder.title.strip(),
                 "reminder_time": reminder.reminder_time, "frequency": reminder.frequency, "done": False}
            ).execute()
            return (res.data or [{}])[0]
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to add reminder: {exc}") from exc
    new_r = {"id": max([r["id"] for r in MOCK_REMINDERS], default=0) + 1,
             "patient_id": reminder.patient_id, "title": reminder.title.strip(),
             "reminder_time": reminder.reminder_time, "frequency": reminder.frequency, "done": False}
    MOCK_REMINDERS.append(new_r)
    return new_r


@router.post("/reminders/{reminder_id}/toggle", response_model=ReminderResponse)
async def toggle_reminder_done(reminder_id: int, patient_id: int = 1, user: dict = Depends(get_current_user)):
    await ensure_patient_access(user, patient_id)
    if not can_write(user):
        raise HTTPException(status_code=403, detail="You cannot update reminders for this patient.")
    q = _scoped("reminders")
    if q is not None:
        try:
            cur = q.select("*").eq("id", reminder_id).eq("patient_id", patient_id).single().execute()
            new_done = not bool((cur.data or {}).get("done"))
            res = q.update({"done": new_done}).eq("id", reminder_id).eq("patient_id", patient_id).execute()
            return (res.data or [{}])[0]
        except Exception as exc:
            raise HTTPException(status_code=404, detail=f"Reminder not found: {exc}") from exc
    for r in MOCK_REMINDERS:
        if r["id"] == reminder_id and r["patient_id"] == patient_id:
            r["done"] = not r["done"]
            return r
    raise HTTPException(status_code=404, detail="Reminder not found")
