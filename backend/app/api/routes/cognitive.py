from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from datetime import datetime
import random
from backend.app.models.schemas import CognitiveSessionCreate, CognitiveSessionResponse, DDANextGameResponse
from backend.app.services.dda_engine import DynamicDifficultyAdjustmentEngine
from backend.app.core.database import get_supabase

router = APIRouter(prefix="/cognitive", tags=["AI Cognitive Engine & DDA"])

# In-memory telemetry log for patient session history
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

# Clinical Question Banks for Dementia
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

@router.get("/next-game", response_model=DDANextGameResponse)
async def get_next_game_config(patient_id: int = 1, game_type: str = "sequence_memory"):
    """
    AI-Powered Dynamic Difficulty Adjustment (DDA).
    Analyzes patient's historical error rates and reaction latency to tune
    the exact symbol sequence, presentation duration, and option set.
    """
    patient_history = [s for s in COGNITIVE_HISTORY if s["patient_id"] == patient_id and s["game_type"] == game_type]
    
    # Run DDA Engine
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
async def log_session_telemetry(session: CognitiveSessionCreate, supabase = Depends(get_supabase)):
    """
    Records session metrics: accuracy, response latency (ms), mistakes.
    Feeds back into the DDA algorithm for longitudinal cognitive tracking.
    """
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

    if supabase:
        try:
            supabase.table("cognitive_sessions").insert(record).execute()
        except Exception:
            pass

    return record

@router.get("/questions/gk")
async def get_general_knowledge_question():
    """Returns a randomized general knowledge question adapted for dementia memory recall."""
    return random.choice(GK_BANK)

@router.get("/questions/attention")
async def get_attention_question():
    """Returns a randomized visual odd-one-out question to exercise focus."""
    return random.choice(ATTENTION_BANK)
