import logging
from datetime import date
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from backend.app.models.schemas import (
    TaskResponse,
    TaskCreate,
    ReminderResponse,
    ReminderCreate,
    ReminderUpdate,
)
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
    {"id": 1, "patient_id": 1, "title": "Drink a glass of warm water", "reminder_time": "08:30", "frequency": "Daily", "category": "Water/Hydration", "done": True, "enabled": True},
    {"id": 2, "patient_id": 1, "title": "Take blood pressure tablet", "reminder_time": "14:00", "frequency": "Daily", "category": "Medicine", "done": False, "enabled": True},
    {"id": 3, "patient_id": 1, "title": "Relaxing flute music time", "reminder_time": "17:30", "frequency": "Daily", "category": "Custom", "done": False, "enabled": True}
]

REMINDER_CATEGORIES = {
    "Medicine",
    "Water/Hydration",
    "Food/Meal",
    "Exercise",
    "Medical Appointment",
    "Custom",
}

# Legacy delimiter for decoding any old rows during migration
_CATEGORY_SEP = " |#| "
_DISABLED_SENTINEL = "9999-12-31T00:00:00+00:00"
_REMINDERS_EXTENDED_SCHEMA = None


def _normalize_reminder_category(value) -> str:
    text = (value or "Custom").strip()
    return text if text in REMINDER_CATEGORIES else "Custom"


def _decode_legacy_title(title: Optional[str]):
    text = title or ""
    if _CATEGORY_SEP in text:
        raw_title, raw_category = text.rsplit(_CATEGORY_SEP, 1)
        return raw_title, _normalize_reminder_category(raw_category)
    return text, None


def _encode_legacy_title(title: str, category: str) -> str:
    clean_title, _ = _decode_legacy_title(title)
    return f"{clean_title}{_CATEGORY_SEP}{_normalize_reminder_category(category)}"


def _is_disabled_sentinel(value) -> bool:
    return bool(value) and str(value).startswith("9999-12-31")


def _reminders_have_extended_schema(supabase) -> bool:
    global _REMINDERS_EXTENDED_SCHEMA
    if supabase is None:
        return True
    if _REMINDERS_EXTENDED_SCHEMA is not None:
        return _REMINDERS_EXTENDED_SCHEMA
    try:
        supabase.table("reminders").select("id,category,enabled").limit(1).execute()
        _REMINDERS_EXTENDED_SCHEMA = True
    except Exception:
        _REMINDERS_EXTENDED_SCHEMA = False
        logger.warning(
            "public.reminders is missing category/enabled columns; using compatible persistence until schema.sql ALTER is applied."
        )
    return _REMINDERS_EXTENDED_SCHEMA


def _normalize_reminder(reminder: dict) -> dict:
    normalized = dict(reminder)
    stored_title = normalized.get("title") or ""
    decoded_title, decoded_category = _decode_legacy_title(stored_title)
    normalized["title"] = decoded_title
    normalized["reminder_time"] = _normalize_task_time(normalized.get("reminder_time"))
    if decoded_category and not normalized.get("category"):
        normalized["category"] = decoded_category
    else:
        normalized["category"] = _normalize_reminder_category(normalized.get("category") or decoded_category)
    if "enabled" in reminder and reminder.get("enabled") is not None:
        normalized["enabled"] = bool(reminder.get("enabled"))
    else:
        normalized["enabled"] = not _is_disabled_sentinel(reminder.get("last_triggered"))
    normalized["done"] = bool(normalized.get("done", False))
    normalized["frequency"] = normalized.get("frequency") or "Daily"
    return normalized


def load_patient_reminders(patient_id: int, supabase=None) -> List[dict]:
    """Load reminders from Supabase, with in-memory fallback for tests/offline."""
    reminders = None
    if supabase:
        try:
            res = (
                supabase.table("reminders")
                .select("*")
                .eq("patient_id", patient_id)
                .order("reminder_time", desc=False)
                .execute()
            )
            if res.data is not None:
                reminders = res.data
        except Exception as e:
            logger.warning(f"Supabase reminders fetch failed: {e}. Using fallback.")

    if reminders is None:
        reminders = [dict(r) for r in MOCK_REMINDERS if r["patient_id"] == patient_id]

    return [_normalize_reminder(r) for r in reminders]


def _prepare_reminder_record(record: dict, supabase=None) -> dict:
    prepared = dict(record)
    if _reminders_have_extended_schema(supabase):
        return prepared

    category = _normalize_reminder_category(prepared.pop("category", "Custom"))
    enabled = bool(prepared.pop("enabled", True))
    if "title" in prepared and prepared["title"] is not None:
        prepared["title"] = _encode_legacy_title(prepared["title"], category)
    prepared["last_triggered"] = None if enabled else _DISABLED_SENTINEL
    return prepared


def _insert_reminder_row(supabase, record: dict):
    payload = _prepare_reminder_record(record, supabase)
    return supabase.table("reminders").insert(payload).execute()


def _update_reminder_row(supabase, reminder_id: int, updates: dict, current: Optional[dict] = None):
    payload = dict(updates)
    if not _reminders_have_extended_schema(supabase):
        current = current or {}
        category = payload.pop("category", None) or current.get("category") or "Custom"
        title = payload.get("title", current.get("title"))
        if title is not None or "category" in updates:
            payload["title"] = _encode_legacy_title(title or "", category)
        if "enabled" in updates:
            payload.pop("enabled", None)
            payload["last_triggered"] = None if updates["enabled"] else _DISABLED_SENTINEL
    return supabase.table("reminders").update(payload).eq("id", reminder_id).execute()


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
# REMINDERS ENDPOINTS (Supabase Persisted)
# =========================================================

@router.get("/reminders", response_model=List[ReminderResponse])
async def list_reminders(patient_id: int = 1, supabase = Depends(get_supabase)):
    """Returns persisted reminders for the patient from Supabase."""
    return load_patient_reminders(patient_id, supabase)

@router.post("/reminders", response_model=ReminderResponse)
async def add_reminder(reminder: ReminderCreate, supabase = Depends(get_supabase)):
    """Creates a reminder in public.reminders."""
    record = {
        "patient_id": reminder.patient_id,
        "title": reminder.title,
        "reminder_time": _normalize_task_time(reminder.reminder_time),
        "frequency": reminder.frequency or "Daily",
        "category": _normalize_reminder_category(reminder.category),
        "done": False,
        "enabled": True if reminder.enabled is None else bool(reminder.enabled),
    }

    if supabase:
        try:
            res = _insert_reminder_row(supabase, record)
            if res.data and len(res.data) > 0:
                logger.info(f"Reminder created in Supabase with ID {res.data[0]['id']}")
                return _normalize_reminder({**record, **res.data[0]})
        except Exception as e:
            logger.error(f"Failed to insert reminder into Supabase: {e}. Storing in mock.")

    next_id = max([r["id"] for r in MOCK_REMINDERS], default=0) + 1
    new_r = {"id": next_id, **record}
    MOCK_REMINDERS.append(new_r)
    return _normalize_reminder(new_r)

@router.put("/reminders/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(reminder_id: int, reminder: ReminderUpdate, supabase = Depends(get_supabase)):
    """Updates an existing reminder in Supabase."""
    updates = reminder.model_dump(exclude_unset=True)
    if "reminder_time" in updates and updates["reminder_time"] is not None:
        updates["reminder_time"] = _normalize_task_time(updates["reminder_time"])
    if "category" in updates and updates["category"] is not None:
        updates["category"] = _normalize_reminder_category(updates["category"])

    if supabase and updates:
        try:
            current_row = None
            fetch_res = supabase.table("reminders").select("*").eq("id", reminder_id).single().execute()
            if fetch_res.data:
                current_row = _normalize_reminder(fetch_res.data)
            res = _update_reminder_row(supabase, reminder_id, updates, current_row)
            if res.data and len(res.data) > 0:
                merged = {**(current_row or {}), **res.data[0], **updates}
                return _normalize_reminder(merged)
        except Exception as e:
            logger.error(f"Failed to update reminder {reminder_id} in Supabase: {e}")

    for r in MOCK_REMINDERS:
        if r["id"] == reminder_id:
            r.update(updates)
            return _normalize_reminder(r)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")

@router.post("/reminders/{reminder_id}/toggle", response_model=ReminderResponse)
async def toggle_reminder_done(reminder_id: int, supabase = Depends(get_supabase)):
    """Toggles today's completion flag (done) for a reminder."""
    if supabase:
        try:
            fetch_res = supabase.table("reminders").select("*").eq("id", reminder_id).single().execute()
            if fetch_res.data:
                new_done = not bool(fetch_res.data.get("done", False))
                update_res = supabase.table("reminders").update({"done": new_done}).eq("id", reminder_id).execute()
                if update_res.data and len(update_res.data) > 0:
                    return _normalize_reminder(update_res.data[0])
                updated = dict(fetch_res.data)
                updated["done"] = new_done
                return _normalize_reminder(updated)
        except Exception as e:
            logger.error(f"Failed to toggle reminder {reminder_id} in Supabase: {e}")

    for r in MOCK_REMINDERS:
        if r["id"] == reminder_id:
            r["done"] = not r.get("done", False)
            return _normalize_reminder(r)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")

@router.post("/reminders/{reminder_id}/toggle-enabled", response_model=ReminderResponse)
async def toggle_reminder_enabled(reminder_id: int, supabase = Depends(get_supabase)):
    """Enables or disables a reminder and persists the change."""
    if supabase:
        try:
            fetch_res = supabase.table("reminders").select("*").eq("id", reminder_id).single().execute()
            if fetch_res.data:
                current = _normalize_reminder(fetch_res.data)
                new_enabled = not current.get("enabled", True)
                update_res = _update_reminder_row(
                    supabase, reminder_id, {"enabled": new_enabled}, current
                )
                if update_res.data and len(update_res.data) > 0:
                    return _normalize_reminder({**current, **update_res.data[0], "enabled": new_enabled})
                updated = dict(current)
                updated["enabled"] = new_enabled
                return _normalize_reminder(updated)
        except Exception as e:
            logger.error(f"Failed to toggle reminder enabled {reminder_id} in Supabase: {e}")

    for r in MOCK_REMINDERS:
        if r["id"] == reminder_id:
            r["enabled"] = not r.get("enabled", True)
            return _normalize_reminder(r)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")

@router.delete("/reminders/{reminder_id}")
async def delete_reminder(reminder_id: int, supabase = Depends(get_supabase)):
    """Deletes a reminder by ID from Supabase."""
    if supabase:
        try:
            supabase.table("reminders").delete().eq("id", reminder_id).execute()
        except Exception as e:
            logger.error(f"Failed to delete reminder {reminder_id} in Supabase: {e}")

    global MOCK_REMINDERS
    MOCK_REMINDERS = [r for r in MOCK_REMINDERS if r["id"] != reminder_id]
    return {"success": True, "message": f"Reminder {reminder_id} deleted successfully"}
