from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from backend.app.core import database as db_module
from backend.app.core.access import ensure_patient_access
from backend.app.core.security import get_current_user, normalize_role, require_admin
from backend.app.models.schemas import CaregiverAnalyticsResponse
from backend.app.services.dda_engine import DynamicDifficultyAdjustmentEngine

router = APIRouter(prefix="/caregiver", tags=["Caregiver Dashboard"])


def _tasks_for(patient_id: int) -> List[Dict[str, Any]]:
    if db_module.is_supabase_configured():
        try:
            from backend.app.api.routes.routines import load_patient_tasks

            return load_patient_tasks(patient_id, db_module.get_supabase_admin())
        except Exception:
            pass
    from backend.app.api.routes.routines import MOCK_TASKS

    return [t for t in MOCK_TASKS if t["patient_id"] == patient_id]


def _sessions_for(patient_id: int) -> List[Dict[str, Any]]:
    if db_module.is_supabase_configured():
        try:
            admin = db_module.get_supabase_admin()
            res = (
                admin.table("cognitive_sessions")
                .select("*")
                .eq("patient_id", patient_id)
                .order("created_at", desc=False)
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
    from backend.app.api.routes.cognitive import COGNITIVE_HISTORY

    return [s for s in COGNITIVE_HISTORY if s["patient_id"] == patient_id]


@router.get("/analytics", response_model=CaregiverAnalyticsResponse)
async def get_caregiver_analytics(patient_id: int = 1, user: dict = Depends(get_current_user)):
    """
    Computes real-time progress metrics and clinical cognitive stability trends
    for family caregivers and attending physicians.
    """
    role = normalize_role(user.get("role"))
    if role not in ("caregiver", "doctor", "admin"):
        # Patients may view their own summary via the same endpoint
        if role != "patient":
            from fastapi import HTTPException

            raise HTTPException(status_code=403, detail="Caregiver access required.")
    patient = await ensure_patient_access(user, patient_id)

    # Task completion analytics from persisted routine tasks
    patient_tasks = _tasks_for(patient_id)
    total_tasks = len(patient_tasks)
    completed_tasks = sum(1 for t in patient_tasks if t.get("done"))
    completion_pct = int((completed_tasks / total_tasks) * 100) if total_tasks else 0

    patient_sessions = _sessions_for(patient_id)
    stability_score = DynamicDifficultyAdjustmentEngine.calculate_cognitive_stability_score(patient_sessions)

    trend = []
    for s in patient_sessions[-7:]:
        created = s.get("created_at")
        if isinstance(created, datetime):
            label = created.strftime("%d %b")
        else:
            label = str(created or "")
        trend.append({
            "session_id": s.get("id"),
            "date": label,
            "score": s.get("score", 0),
            "latency_sec": round((s.get("reaction_time_ms") or 0) / 1000, 1),
            "level": s.get("difficulty_level", 1)
        })

    focus = "Routine adherence is high. Continue stimulating memory with morning symbol sequences."
    if stability_score < 60:
        focus = "Slight increase in reaction latency detected. Suggest gentle breathing and familiar music."

    return CaregiverAnalyticsResponse(
        patient_id=patient_id,
        patient_name=patient.get("name", "Patient"),
        routine_completion_pct=completion_pct,
        completed_tasks=completed_tasks,
        total_tasks=total_tasks,
        cognitive_stability_score=stability_score,
        recent_sessions_count=len(patient_sessions),
        recommended_focus=focus,
        cognitive_trend=trend
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
