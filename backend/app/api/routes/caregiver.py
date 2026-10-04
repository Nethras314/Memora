from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from backend.app.core import database as db_module
from backend.app.core.access import ensure_patient_access, list_accessible_patients
from backend.app.core.security import get_current_user, normalize_role, require_admin
from backend.app.models.schemas import (
    CaregiverAnalyticsResponse,
    CaregiverGlanceResponse,
    CompositeTrendPoint,
    DoctorPatientSummary,
    DomainBreakdownItem,
)
from backend.app.services import analytics_service as svc

router = APIRouter(prefix="/caregiver", tags=["Caregiver Dashboard"])

_READER_ROLES = ("caregiver", "doctor", "admin", "patient")


def _tasks_for(patient_id: int) -> List[Dict[str, Any]]:
    if db_module.is_supabase_configured():
        try:
            from backend.app.api.routes.routines import load_patient_tasks

            return load_patient_tasks(patient_id, db_module.get_supabase_admin())
        except Exception:
            pass
    from backend.app.api.routes.routines import MOCK_TASKS

    return [t for t in MOCK_TASKS if t["patient_id"] == patient_id]


def _reminders_for(patient_id: int) -> List[Dict[str, Any]]:
    from backend.app.api.routes.routines import load_patient_reminders

    if db_module.is_supabase_configured():
        try:
            return load_patient_reminders(patient_id, db_module.get_supabase_admin())
        except Exception:
            pass
    return load_patient_reminders(patient_id, None)


def _sessions_for(patient_id: int, days: Optional[int] = None) -> List[Dict[str, Any]]:
    if db_module.is_supabase_configured():
        try:
            admin = db_module.get_supabase_admin()
            q = (
                admin.table("cognitive_sessions")
                .select("*")
                .eq("patient_id", patient_id)
                .order("created_at", desc=False)
            )
            if days:
                cutoff = (datetime.now() - timedelta(days=days)).isoformat()
                q = q.gte("created_at", cutoff)
            res = q.limit(500).execute()
            rows = res.data or []
            for r in rows:
                created = r.get("created_at")
                if isinstance(created, str):
                    try:
                        r["created_at"] = datetime.fromisoformat(created)
                    except ValueError:
                        r["created_at"] = datetime.now()
            return rows
        except Exception:
            pass

    from backend.app.api.routes.cognitive import COGNITIVE_HISTORY

    rows = [s for s in COGNITIVE_HISTORY if s["patient_id"] == patient_id]
    if days:
        cutoff = datetime.now() - timedelta(days=days)
        rows = [s for s in rows if (s.get("created_at") or datetime.now()) >= cutoff]
    return rows


def _moods_for(patient_id: int) -> List[Dict[str, Any]]:
    if db_module.is_supabase_configured():
        try:
            admin = db_module.get_supabase_admin()
            res = (
                admin.table("mood_logs")
                .select("*")
                .eq("patient_id", patient_id)
                .order("created_at", desc=True)
                .limit(50)
                .execute()
            )
            rows = res.data or []
            for r in rows:
                created = r.get("created_at")
                if isinstance(created, str):
                    try:
                        r["created_at"] = datetime.fromisoformat(created)
                    except ValueError:
                        r["created_at"] = datetime.now()
            return rows
        except Exception:
            pass
    from backend.app.api.routes.tracking import MOCK_MOOD_LOGS

    return [m for m in MOCK_MOOD_LOGS if m["patient_id"] == patient_id]


def _notes_for(patient_id: int) -> List[Dict[str, Any]]:
    if db_module.is_supabase_configured():
        try:
            admin = db_module.get_supabase_admin()
            res = (
                admin.table("clinical_notes")
                .select("*")
                .eq("patient_id", patient_id)
                .order("created_at", desc=True)
                .execute()
            )
            rows = res.data or []
            for r in rows:
                created = r.get("created_at")
                if isinstance(created, str):
                    try:
                        r["created_at"] = datetime.fromisoformat(created)
                    except ValueError:
                        r["created_at"] = datetime.now()
            return rows
        except Exception:
            pass
    from backend.app.api.routes.tracking import MOCK_CLINICAL_NOTES

    return [n for n in MOCK_CLINICAL_NOTES if n["patient_id"] == patient_id]


def _session_trend(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    trend = []
    for s in sessions[-7:]:
        created = s.get("created_at")
        label = created.strftime("%d %b") if isinstance(created, datetime) else str(created or "")
        trend.append({
            "session_id": s.get("id"),
            "date": label,
            "score": s.get("score", 0),
            "latency_sec": round((s.get("reaction_time_ms") or 0) / 1000, 1),
            "level": s.get("difficulty_level", 1),
        })
    return trend


@router.get("/analytics", response_model=CaregiverAnalyticsResponse)
async def get_caregiver_analytics(patient_id: int = 1, user: dict = Depends(get_current_user)):
    """Extended cognitive-tracking summary for caregivers and physicians."""
    role = normalize_role(user.get("role"))
    if role not in _READER_ROLES:
        raise HTTPException(status_code=403, detail="Caregiver access required.")
    patient = await ensure_patient_access(user, patient_id)

    tasks = _tasks_for(patient_id)
    reminders = _reminders_for(patient_id)
    sessions = _sessions_for(patient_id)
    moods = _moods_for(patient_id)

    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.get("done"))
    completion_pct = int(round(completed_tasks / total_tasks * 100)) if total_tasks else 0

    games = svc.games_stability(sessions)
    games_for_display = games if games is not None else 75
    index, _, weights = svc.composite_index(
        games,
        svc.adl_score(tasks),
        svc.medication_score(reminders),
        svc.mood_score(moods),
    )
    status = svc.rag_status(index)
    series = svc.daily_series(sessions, window_days=30)
    delta = svc.index_delta(series)

    med = svc.medication_score(reminders)
    med_pct = int(round(med)) if med is not None else None
    mood_recent = moods[0].get("mood") if moods else None

    return CaregiverAnalyticsResponse(
        patient_id=patient_id,
        patient_name=patient.get("name", "Patient"),
        routine_completion_pct=completion_pct,
        completed_tasks=completed_tasks,
        total_tasks=total_tasks,
        cognitive_stability_score=int(games_for_display),
        recent_sessions_count=len(sessions),
        recommended_focus=svc.recommended_action(status),
        cognitive_trend=_session_trend(sessions),
        index=int(round(index)) if index is not None else None,
        index_delta=delta,
        status=status,
        medication_adherence_pct=med_pct,
        domain_breakdown=[DomainBreakdownItem(**d) for d in svc.domain_breakdown(sessions, tasks, reminders, moods)],
        weights=weights,
        trend_30d=[CompositeTrendPoint(**p) for p in svc.serialize_series(series)],
        mood_recent=mood_recent,
    )


@router.get("/glance", response_model=CaregiverGlanceResponse)
async def get_glance(patient_id: int = 1, user: dict = Depends(get_current_user)):
    """Lightweight caretaker today-card (also used by the mobile glance)."""
    role = normalize_role(user.get("role"))
    if role not in _READER_ROLES:
        raise HTTPException(status_code=403, detail="Caregiver access required.")
    patient = await ensure_patient_access(user, patient_id)

    tasks = _tasks_for(patient_id)
    reminders = _reminders_for(patient_id)
    sessions = _sessions_for(patient_id)
    moods = _moods_for(patient_id)

    total = len(tasks)
    routine_pct = int(round(sum(1 for t in tasks if t.get("done")) / total * 100)) if total else 0

    index, _, _ = svc.composite_index(
        svc.games_stability(sessions),
        svc.adl_score(tasks),
        svc.medication_score(reminders),
        svc.mood_score(moods),
    )
    series = svc.daily_series(sessions, window_days=30)
    delta = svc.index_delta(series)
    status = svc.rag_status(index)

    return CaregiverGlanceResponse(
        patient_id=patient_id,
        patient_name=patient.get("name", "Patient"),
        index=int(round(index)) if index is not None else None,
        index_delta=delta,
        status=status,
        routine_pct=routine_pct,
        flag=svc.plain_language_flag(index, delta, status, series),
        recommended_action=svc.recommended_action(status),
        trend=[CompositeTrendPoint(**p) for p in svc.serialize_series(series[-7:])],
    )


@router.get("/trend", response_model=List[CompositeTrendPoint])
async def get_trend(patient_id: int = 1, window_days: int = 30, user: dict = Depends(get_current_user)):
    if window_days not in (30, 90, 180):
        raise HTTPException(status_code=400, detail="window_days must be 30, 90, or 180.")
    await ensure_patient_access(user, patient_id)
    sessions = _sessions_for(patient_id, days=window_days)
    series = svc.daily_series(sessions, window_days=window_days)
    return [CompositeTrendPoint(**p) for p in svc.serialize_series(series)]


@router.get("/patients/summary", response_model=List[DoctorPatientSummary])
async def get_patients_summary(user: dict = Depends(get_current_user)):
    """Doctor/admin cohort, sorted by decline velocity (worst first)."""
    role = normalize_role(user.get("role"))
    if role not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Doctor or admin access required.")
    patients = await list_accessible_patients(user)

    summaries = []
    for p in patients:
        pid = int(p["id"])
        sessions = _sessions_for(pid)
        tasks = _tasks_for(pid)
        reminders = _reminders_for(pid)
        moods = _moods_for(pid)
        notes = _notes_for(pid)

        index, _, _ = svc.composite_index(
            svc.games_stability(sessions),
            svc.adl_score(tasks),
            svc.medication_score(reminders),
            svc.mood_score(moods),
        )
        series = svc.daily_series(sessions, window_days=180)
        last = svc.since_last_visit(notes, sessions)

        summaries.append(DoctorPatientSummary(
            patient_id=pid,
            patient_name=p.get("name", "Patient"),
            age=p.get("age"),
            index=int(round(index)) if index is not None else None,
            delta_per_week=svc.decline_velocity(series),
            status=svc.rag_status(index),
            last_visit=last["last_visit"],
            sessions_since_visit=last["sessions_since"],
        ))

    summaries.sort(key=lambda s: (s.delta_per_week is None, s.delta_per_week if s.delta_per_week is not None else 0))
    return summaries


@router.get("/export")
async def export_analytics(patient_id: int = 1, format: str = "csv", user: dict = Depends(get_current_user)):
    """CSV export of full cognitive-session history for a patient."""
    role = normalize_role(user.get("role"))
    if role not in ("doctor", "admin", "caregiver"):
        raise HTTPException(status_code=403, detail="Export requires doctor, admin, or caregiver access.")
    patient = await ensure_patient_access(user, patient_id)
    if format != "csv":
        raise HTTPException(status_code=400, detail="Only CSV export is supported.")

    sessions = _sessions_for(patient_id)

    import csv
    from io import StringIO

    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "patient_id", "patient_name", "game_type", "difficulty_level",
        "score", "accuracy", "reaction_time_ms", "mistake_count", "created_at",
    ])
    for s in sessions:
        writer.writerow([
            patient_id,
            patient.get("name", "Patient"),
            s.get("game_type"),
            s.get("difficulty_level"),
            s.get("score"),
            s.get("accuracy"),
            s.get("reaction_time_ms"),
            s.get("mistake_count"),
            s.get("created_at"),
        ])

    buf.seek(0)
    filename = f"memora_{patient_id}_cognitive.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/admin/overview")
async def admin_overview(admin: dict = Depends(require_admin)):
    """Admin-only: cross-patient counts for platform monitoring."""
    if db_module.is_supabase_configured():
        client = db_module.get_supabase_admin()
        try:
            patients = client.table("patients").select("id", count="exact").execute()
            users = client.table("profiles").select("id", count="exact").execute()
            sessions = client.table("cognitive_sessions").select("id", count="exact").execute()
            return {
                "total_patients": getattr(patients, "count", len(patients.data or [])),
                "total_users": getattr(users, "count", len(users.data or [])),
                "total_sessions": getattr(sessions, "count", len(sessions.data or [])),
            }
        except Exception:
            pass
    from backend.app.api.routes.patients import MOCK_PATIENTS
    from backend.app.api.routes.cognitive import COGNITIVE_HISTORY
    from backend.app.core.security import DEMO_USERS, _demo_seed_admin

    _demo_seed_admin()
    return {
        "total_patients": len(MOCK_PATIENTS),
        "total_users": len(DEMO_USERS),
        "total_sessions": len(COGNITIVE_HISTORY),
    }
