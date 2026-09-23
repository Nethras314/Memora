import logging
from datetime import date
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from backend.app.models.schemas import TaskResponse, TaskCreate, ReminderResponse, ReminderCreate
from backend.app.core.database import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routines", tags=["Routines & Reminders"])

# In-memory fallback stores
MOCK_TASKS = [
    {"id": 1, "patient_id": 1, "title": "Breakfast & Warm Milk", "task_time": "09:00", "category": "Routine", "done": True, "date": date.today()},
    {"id": 2, "patient_id": 1, "title": "Cognitive Memory Activity", "task_time": "10:30", "category": "Cognitive", "done": False, "date": date.today()},
    {"id": 3, "patient_id": 1, "title": "Lunch & Short Nap", "task_time": "13:00", "category": "Routine", "done": False, "date": date.today()},
    {"id": 4, "patient_id": 1, "title": "Evening Courtyard Walk", "task_time": "17:00", "category": "Exercise", "done": False, "date": date.today()}
]

MOCK_REMINDERS = [
    {"id": 1, "patient_id": 1, "title": "Drink a glass of warm water", "reminder_time": "08:30", "frequency": "Daily", "done": True},
    {"id": 2, "patient_id": 1, "title": "Take blood pressure tablet", "reminder_time": "14:00", "frequency": "Daily", "done": False},
    {"id": 3, "patient_id": 1, "title": "Relaxing flute music time", "reminder_time": "17:30", "frequency": "Daily", "done": False}
]


def _today_str() -> str:
    return str(date.today())


def _normalize_task_time(value) -> str:
    """Keep elder UI clocks as HH:MM even when Postgres returns TIME."""
    if value is None:
        return ""
    text = str(value)
    return text[:5] if len(text) >= 5 else text


def _task_date_str(task: dict) -> Optional[str]:
    value = task.get("date")
    if value is None:
        return None
    return str(value)[:10]


def _normalize_task(task: dict) -> dict:
    normalized = dict(task)
    normalized["task_time"] = _normalize_task_time(normalized.get("task_time"))
    return normalized


def _apply_day_rollover(tasks: List[dict], supabase=None) -> List[dict]:
    """
    Daily routine steps persist across days, but completion is per-day.
    If a row is still marked done from a previous date, clear it and stamp today.
    """
    today = _today_str()
    stale_ids = [
        t["id"] for t in tasks
        if t.get("id") is not None and _task_date_str(t) is not None and _task_date_str(t) != today
    ]
    if stale_ids and supabase:
        try:
            supabase.table("tasks").update({"done": False, "date": today}).in_("id", stale_ids).execute()
        except Exception as e:
            logger.warning(f"Task day rollover persist failed: {e}")

    for t in tasks:
        if _task_date_str(t) != today:
            t["done"] = False
            t["date"] = today
    return tasks


def load_patient_tasks(patient_id: int, supabase=None) -> List[dict]:
    """Load routine tasks from Supabase, with in-memory fallback for tests/offline."""
    tasks = None
    if supabase:
        try:
            res = (
                supabase.table("tasks")
                .select("*")
                .eq("patient_id", patient_id)
                .order("task_time", desc=False)
                .execute()
            )
            if res.data is not None:
                tasks = res.data
        except Exception as e:
            logger.warning(f"Supabase tasks fetch failed: {e}. Using fallback.")

    if tasks is None:
        tasks = [dict(t) for t in MOCK_TASKS if t["patient_id"] == patient_id]

    tasks = _apply_day_rollover(tasks, supabase)
    return [_normalize_task(t) for t in tasks]


# =========================================================
# TASKS / ROUTINES ENDPOINTS (Supabase Persisted)
# =========================================================

@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(patient_id: int = 1, supabase = Depends(get_supabase)):
    """
    Returns daily routine tasks for the patient from Supabase.
    """
    return load_patient_tasks(patient_id, supabase)

@router.post("/tasks", response_model=TaskResponse)
async def add_task(task: TaskCreate, supabase = Depends(get_supabase)):
    """
    Creates a new routine task in Supabase public.tasks.
    """
    record = {
        "patient_id": task.patient_id,
        "title": task.title,
        "task_time": _normalize_task_time(task.task_time),
        "category": task.category,
        "done": False,
        "date": _today_str()
    }

    if supabase:
        try:
            res = supabase.table("tasks").insert(record).execute()
            if res.data and len(res.data) > 0:
                logger.info(f"Task created in Supabase with ID {res.data[0]['id']}")
                return _normalize_task(res.data[0])
        except Exception as e:
            logger.error(f"Failed to insert task into Supabase: {e}. Storing in mock.")

    next_id = max([t["id"] for t in MOCK_TASKS], default=0) + 1
    new_t = {
        "id": next_id,
        "patient_id": task.patient_id,
        "title": task.title,
        "task_time": _normalize_task_time(task.task_time),
        "category": task.category,
        "done": False,
        "date": date.today()
    }
    MOCK_TASKS.append(new_t)
    return new_t

@router.post("/tasks/{task_id}/toggle", response_model=TaskResponse)
async def toggle_task_done(task_id: int, supabase = Depends(get_supabase)):
    """
    Toggles the completion status of a task in Supabase.
    """
    if supabase:
        try:
            fetch_res = supabase.table("tasks").select("*").eq("id", task_id).single().execute()
            if fetch_res.data:
                current_done = fetch_res.data.get("done", False)
                new_done = not current_done
                update_res = supabase.table("tasks").update({"done": new_done}).eq("id", task_id).execute()
                if update_res.data and len(update_res.data) > 0:
                    return _normalize_task(update_res.data[0])
                updated = dict(fetch_res.data)
                updated["done"] = new_done
                return _normalize_task(updated)
        except Exception as e:
            logger.error(f"Failed to toggle task {task_id} in Supabase: {e}")

    for t in MOCK_TASKS:
        if t["id"] == task_id:
            t["done"] = not t["done"]
            return _normalize_task(t)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int, supabase = Depends(get_supabase)):
    """
    Deletes a task by ID from Supabase.
    """
    if supabase:
        try:
            supabase.table("tasks").delete().eq("id", task_id).execute()
        except Exception as e:
            logger.error(f"Failed to delete task {task_id} in Supabase: {e}")

    global MOCK_TASKS
    MOCK_TASKS = [t for t in MOCK_TASKS if t["id"] != task_id]
    return {"success": True, "message": f"Task {task_id} deleted successfully"}

@router.post("/tasks/reset")
async def reset_tasks(patient_id: int = 1, supabase = Depends(get_supabase)):
    """
    Resets all tasks for a patient to done = False for the current day.
    """
    today = _today_str()
    if supabase:
        try:
            supabase.table("tasks").update({"done": False, "date": today}).eq("patient_id", patient_id).execute()
        except Exception as e:
            logger.error(f"Failed to reset tasks for patient {patient_id} in Supabase: {e}")

    for t in MOCK_TASKS:
        if t["patient_id"] == patient_id:
            t["done"] = False
            t["date"] = date.today()

    return {"success": True, "message": f"All tasks reset for patient {patient_id}"}

# =========================================================
# REMINDERS ENDPOINTS
# =========================================================

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
