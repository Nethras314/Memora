from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from backend.app.models.schemas import CaregiverAnalyticsResponse
from backend.app.api.routes.patients import MOCK_PATIENTS
from backend.app.api.routes.routines import MOCK_TASKS
from backend.app.api.routes.cognitive import COGNITIVE_HISTORY
from backend.app.services.dda_engine import DynamicDifficultyAdjustmentEngine
from backend.app.core.database import get_supabase

router = APIRouter(prefix="/caregiver", tags=["Caregiver Dashboard"])

@router.get("/analytics", response_model=CaregiverAnalyticsResponse)
async def get_caregiver_analytics(patient_id: int = 1, supabase = Depends(get_supabase)):
    """
    Computes real-time progress metrics and clinical cognitive stability trends
    for family caregivers and attending physicians.
    """
    patient = next((p for p in MOCK_PATIENTS if p["id"] == patient_id), MOCK_PATIENTS[0])
    
    # Task completion analytics
    patient_tasks = [t for t in MOCK_TASKS if t["patient_id"] == patient_id]
    total_tasks = len(patient_tasks)
    completed_tasks = sum(1 for t in patient_tasks if t["done"])
    completion_pct = int((completed_tasks / total_tasks) * 100) if total_tasks else 0

    # Cognitive Telemetry Analysis
    patient_sessions = [s for s in COGNITIVE_HISTORY if s["patient_id"] == patient_id]
    stability_score = DynamicDifficultyAdjustmentEngine.calculate_cognitive_stability_score(patient_sessions)

    # Historical trend points for chart
    trend = []
    for s in patient_sessions[-7:]:
        trend.append({
            "session_id": s["id"],
            "date": s["created_at"].strftime("%d %b"),
            "score": s["score"],
            "latency_sec": round(s["reaction_time_ms"] / 1000, 1),
            "level": s["difficulty_level"]
        })

    focus = "Routine adherence is high. Continue stimulating memory with morning symbol sequences."
    if stability_score < 60:
        focus = "Slight increase in reaction latency detected. Suggest gentle breathing and familiar music."

    return CaregiverAnalyticsResponse(
        patient_id=patient_id,
        patient_name=patient["name"],
        routine_completion_pct=completion_pct,
        completed_tasks=completed_tasks,
        total_tasks=total_tasks,
        cognitive_stability_score=stability_score,
        recent_sessions_count=len(patient_sessions),
        recommended_focus=focus,
        cognitive_trend=trend
    )
