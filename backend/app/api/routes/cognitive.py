from datetime import datetime
import random
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from backend.app.core import database as db_module
from backend.app.core.access import ensure_patient_access
from backend.app.core.security import get_current_user
from backend.app.models.schemas import (
    CognitiveSessionCreate,
    CognitiveSessionResponse,
    DDANextGameResponse,
)
from backend.app.services.dda_engine import DynamicDifficultyAdjustmentEngine

router = APIRouter(prefix="/cognitive", tags=["AI Cognitive Engine & DDA"])

# Fallback telemetry (demo/tests only; Supabase is source of truth when configured)
COGNITIVE_HISTORY: List[Dict[str, Any]] = [
    {
        "id": 1,
        "patient_id": 1,
        "game_type": "sequence_memory",
        "difficulty_level": 1,
        "score": 100,
        "accuracy": 1.0,
        "reaction_time_ms": 3200,
        "mistake_count": 0,
        "created_at": datetime.now()
    },
    {
        "id": 2,
        "patient_id": 1,
        "game_type": "sequence_memory",
        "difficulty_level": 2,
        "score": 90,
        "accuracy": 0.9,
        "reaction_time_ms": 3400,
        "mistake_count": 1,
        "created_at": datetime.now()
    }
]

GK_BANK = [
    {
        "question": "Which planet is known as the Red Planet?",
        "options": ["Earth", "Mars", "Venus"],
        "answer": "Mars",
        "hint": "It appears reddish in the night sky."
    },
    {
        "question": "What is the capital of India?",
        "options": ["Mumbai", "New Delhi", "Chennai"],
        "answer": "New Delhi",
        "hint": "Located in the north of India."
    },
    {
        "question": "Which animal is known as the King of the Jungle?",
        "options": ["Elephant", "Lion", "Tiger"],
        "answer": "Lion",
        "hint": "It has a large mane."
    }
]

ATTENTION_BANK = [
    {
        "question": "Which one is different from the others?",
        "options": ["🍎 Apple", "🍌 Banana", "🚗 Car"],
        "answer": "🚗 Car",
        "explanation": "Car is a vehicle, while Apple and Banana are fruits."
    },
    {
        "question": "Which one does not belong here?",
        "options": ["🐶 Dog", "🐱 Cat", "🪑 Chair"],
        "answer": "🪑 Chair",
        "explanation": "Chair is furniture, while Dog and Cat are animals."
    },
    {
        "question": "Spot the odd item:",
        "options": ["☕ Tea Cup", "🥄 Spoon", "🌻 Flower"],
        "answer": "🌻 Flower",
        "explanation": "Flower is a plant, while Cup and Spoon are kitchen utensils."
    }
]

ALLOWED_GAMES = {"sequence_memory", "general_knowledge", "odd_one_out", "task_sequencing"}


def _history_for(patient_id: int, game_type: str) -> List[Dict[str, Any]]:
    if db_module.is_supabase_configured():
        try:
            admin = db_module.get_supabase_admin()
            res = (
                admin.table("cognitive_sessions")
                .select("*")
                .eq("patient_id", patient_id)
                .eq("game_type", game_type)
                .order("created_at", desc=False)
                .limit(20)
                .execute()
            )
            return res.data or []
        except Exception:
            pass
    return [s for s in COGNITIVE_HISTORY if s["patient_id"] == patient_id and s["game_type"] == game_type]


@router.get("/next-game", response_model=DDANextGameResponse)
async def get_next_game_config(
    patient_id: int = 1, game_type: str = "sequence_memory",
    user: dict = Depends(get_current_user),
):
    await ensure_patient_access(user, patient_id)
    if game_type not in ALLOWED_GAMES:
        raise HTTPException(status_code=400, detail="Unknown game type.")
    patient_history = _history_for(patient_id, game_type)
    params = DynamicDifficultyAdjustmentEngine.evaluate_next_parameters(patient_history)
    return DDANextGameResponse(
        game_type=game_type,
        difficulty_level=params["difficulty_level"],
        sequence=params["sequence"],
        options=params["options"],
        display_duration_ms=params["display_duration_ms"],
        guidance_cue=params["guidance_cue"]
    )


@router.post("/log-session", response_model=CognitiveSessionResponse)
async def log_session_telemetry(session: CognitiveSessionCreate, user: dict = Depends(get_current_user)):
    await ensure_patient_access(user, session.patient_id)
    if session.game_type not in ALLOWED_GAMES:
        raise HTTPException(status_code=400, detail="Unknown game type.")
    record = {
        "id": len(COGNITIVE_HISTORY) + 1,
        "patient_id": session.patient_id,
        "game_type": session.game_type,
        "difficulty_level": session.difficulty_level,
        "score": session.score,
        "accuracy": session.accuracy,
        "reaction_time_ms": session.reaction_time_ms,
        "mistake_count": session.mistake_count,
        "session_metadata": session.session_metadata or {},
        "created_at": datetime.now()
    }
    COGNITIVE_HISTORY.append(record)

    if db_module.is_supabase_configured():
        try:
            admin = db_module.get_supabase_admin()
            payload = {k: v for k, v in record.items() if k != "id"}
            if isinstance(payload.get("created_at"), datetime):
                payload["created_at"] = payload["created_at"].isoformat()
            res = admin.table("cognitive_sessions").insert(payload).execute()
            if res.data:
                saved = res.data[0]
                if isinstance(saved.get("created_at"), str):
                    try:
                        saved["created_at"] = datetime.fromisoformat(saved["created_at"])
                    except ValueError:
                        saved["created_at"] = record["created_at"]
                return saved
        except Exception:
            pass

    return record


@router.get("/questions/gk")
async def get_general_knowledge_question(user: dict = Depends(get_current_user)):
    return random.choice(GK_BANK)


@router.get("/questions/attention")
async def get_attention_question(user: dict = Depends(get_current_user)):
    return random.choice(ATTENTION_BANK)
