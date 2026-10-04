from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from backend.app.core import database as db_module
from backend.app.core.access import ensure_patient_access
from backend.app.core.security import get_current_user, normalize_role
from backend.app.models.schemas import (
    MOOD_VALUES,
    NOTE_TYPES,
    ClinicalNoteCreate,
    ClinicalNoteResponse,
    MoodLogCreate,
    MoodLogResponse,
)

router = APIRouter(prefix="/tracking", tags=["Cognitive Tracking"])

# In-memory fallback stores (demo/tests only; Supabase is source of truth when configured)
MOCK_MOOD_LOGS: List[dict] = []
MOCK_CLINICAL_NOTES: List[dict] = []


def _supabase():
    return db_module.get_supabase_admin() if db_module.is_supabase_configured() else None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _serialize_mood(m: dict) -> MoodLogResponse:
    flags = m.get("behavior_flags") or []
    if isinstance(flags, str):
        flags = [flags]
    return MoodLogResponse(
        id=m["id"],
        patient_id=m["patient_id"],
        mood=m.get("mood"),
        behavior_flags=list(flags),
        note=m.get("note"),
        recorded_by=str(m.get("recorded_by")) if m.get("recorded_by") else None,
        created_at=m.get("created_at"),
    )


def _serialize_note(n: dict) -> ClinicalNoteResponse:
    return ClinicalNoteResponse(
        id=n["id"],
        patient_id=n["patient_id"],
        author_id=str(n.get("author_id")) if n.get("author_id") else None,
        note_type=n.get("note_type", "general"),
        body=n.get("body"),
        created_at=n.get("created_at"),
    )


# =========================================================
# MOOD / BEHAVIOR (BPSD) LOGS
# =========================================================
@router.get("/mood", response_model=List[MoodLogResponse])
async def list_mood_logs(patient_id: int = 1, user: dict = Depends(get_current_user)):
    await ensure_patient_access(user, patient_id)
    supabase = _supabase()
    if supabase:
        try:
            res = (
                supabase.table("mood_logs")
                .select("*")
                .eq("patient_id", patient_id)
                .order("created_at", desc=True)
                .limit(50)
                .execute()
            )
            return [_serialize_mood(r) for r in (res.data or [])]
        except Exception:
            pass
    return [_serialize_mood(m) for m in MOCK_MOOD_LOGS if m["patient_id"] == patient_id]


@router.post("/mood", response_model=MoodLogResponse, status_code=201)
async def add_mood_log(payload: MoodLogCreate, user: dict = Depends(get_current_user)):
    await ensure_patient_access(user, payload.patient_id)
    role = normalize_role(user.get("role"))
    if role not in ("caregiver", "doctor", "admin"):
        raise HTTPException(status_code=403, detail="Only caregivers or clinicians can record mood.")
    if payload.mood not in MOOD_VALUES:
        raise HTTPException(status_code=400, detail="Invalid mood value.")

    record = {
        "patient_id": payload.patient_id,
        "mood": payload.mood,
        "behavior_flags": payload.behavior_flags or [],
        "note": payload.note,
        "recorded_by": user["id"],
        "created_at": _now(),
    }
    supabase = _supabase()
    if supabase:
        try:
            res = supabase.table("mood_logs").insert(record).execute()
            if res.data:
                return _serialize_mood(res.data[0])
        except Exception:
            pass

    next_id = max([m["id"] for m in MOCK_MOOD_LOGS], default=0) + 1
    new_m = {"id": next_id, **record}
    MOCK_MOOD_LOGS.append(new_m)
    return _serialize_mood(new_m)


@router.delete("/mood/{mood_id}")
async def delete_mood_log(mood_id: int, patient_id: int = 1, user: dict = Depends(get_current_user)):
    await ensure_patient_access(user, patient_id)
    role = normalize_role(user.get("role"))
    if role not in ("caregiver", "doctor", "admin"):
        raise HTTPException(status_code=403, detail="Only caregivers or clinicians can delete mood logs.")
    supabase = _supabase()
    if supabase:
        try:
            supabase.table("mood_logs").delete().eq("id", mood_id).eq("patient_id", patient_id).execute()
        except Exception:
            pass

    global MOCK_MOOD_LOGS
    MOCK_MOOD_LOGS = [m for m in MOCK_MOOD_LOGS if not (m["id"] == mood_id and m["patient_id"] == patient_id)]
    return {"success": True, "message": f"Mood log {mood_id} deleted"}


# =========================================================
# CLINICAL NOTES (doctor notes / care plan)
# =========================================================
@router.get("/notes", response_model=List[ClinicalNoteResponse])
async def list_notes(patient_id: int = 1, user: dict = Depends(get_current_user)):
    await ensure_patient_access(user, patient_id)
    supabase = _supabase()
    if supabase:
        try:
            res = (
                supabase.table("clinical_notes")
                .select("*")
                .eq("patient_id", patient_id)
                .order("created_at", desc=True)
                .execute()
            )
            return [_serialize_note(r) for r in (res.data or [])]
        except Exception:
            pass
    return [_serialize_note(n) for n in MOCK_CLINICAL_NOTES if n["patient_id"] == patient_id]


@router.post("/notes", response_model=ClinicalNoteResponse, status_code=201)
async def add_note(payload: ClinicalNoteCreate, user: dict = Depends(get_current_user)):
    await ensure_patient_access(user, payload.patient_id)
    role = normalize_role(user.get("role"))
    if role not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Only doctors or admins can write clinical notes.")
    if payload.note_type not in NOTE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid note type.")

    record = {
        "patient_id": payload.patient_id,
        "author_id": user["id"],
        "note_type": payload.note_type,
        "body": payload.body,
        "created_at": _now(),
    }
    supabase = _supabase()
    if supabase:
        try:
            res = supabase.table("clinical_notes").insert(record).execute()
            if res.data:
                return _serialize_note(res.data[0])
        except Exception:
            pass

    next_id = max([n["id"] for n in MOCK_CLINICAL_NOTES], default=0) + 1
    new_n = {"id": next_id, **record}
    MOCK_CLINICAL_NOTES.append(new_n)
    return _serialize_note(new_n)
