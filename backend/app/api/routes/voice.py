import base64

from fastapi import APIRouter, Depends, HTTPException

from backend.app.core import database as db_module
from backend.app.core.access import ensure_patient_access
from backend.app.core.security import get_current_user
from backend.app.models.schemas import VoiceInteractRequest, VoiceInteractResponse
from backend.app.services.sarvam_service import SarvamAIService
from backend.app.api.routes.routines import load_patient_reminders

router = APIRouter(prefix="/voice", tags=["Voice & Sarvam AI"])

MAX_AUDIO_BYTES = 4 * 1024 * 1024


def _memories_for(patient_id: int):
    if db_module.is_supabase_configured():
        try:
            admin = db_module.get_supabase_admin()
            res = admin.table("memories").select("*").eq("patient_id", patient_id).execute()
            return res.data or []
        except Exception:
            pass
    from backend.app.api.routes.memories import MOCK_MEMORIES

    return [m for m in MOCK_MEMORIES if m["patient_id"] == patient_id]


def _reminders_for(patient_id: int):
    if db_module.is_supabase_configured():
        try:
            admin = db_module.get_supabase_admin()
            rows = load_patient_reminders(patient_id, admin)
            return [r for r in rows if r.get("enabled", True)]
        except Exception:
            pass
    from backend.app.api.routes.routines import MOCK_REMINDERS

    return [r for r in MOCK_REMINDERS if r["patient_id"] == patient_id]


def _patient_name(patient_id: int, user: dict) -> str:
    name = "friend"
    try:
        from backend.app.api.routes.patients import MOCK_PATIENTS

        row = next((p for p in MOCK_PATIENTS if p["id"] == patient_id), None)
        if row:
            name = row.get("name", name)
    except Exception:
        pass
    return name


@router.post("/interact", response_model=VoiceInteractResponse)
async def voice_interaction(req: VoiceInteractRequest, user: dict = Depends(get_current_user)):
    """
    Handles natural voice or text conversations with MEMORA in Indian regional languages
    (Tamil, Hindi, Kannada, Telugu, English) powered by Sarvam AI (Saaras STT & Bulbul TTS).
    """
    patient = await ensure_patient_access(user, req.patient_id)
    patient_memories = _memories_for(req.patient_id)
    patient_reminders = _reminders_for(req.patient_id)

    question_text = req.question_text

    if req.audio_base64:
        try:
            audio_bytes = base64.b64decode(req.audio_base64)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid audio payload.")
        if len(audio_bytes) > MAX_AUDIO_BYTES:
            raise HTTPException(status_code=400, detail="Voice clip too large. Keep it under 30 seconds.")
        try:
            transcription = await SarvamAIService.transcribe_audio(
                audio_bytes, req.language_code, req.audio_content_type
            )
            question_text = transcription
        except Exception:
            question_text = req.question_text or "Who is my daughter?"
    elif not question_text:
        question_text = "Who is my daughter?"

    reply_text = SarvamAIService.resolve_conversational_reply(
        question_text=question_text,
        language_code=req.language_code,
        patient_name=patient.get("name") or _patient_name(req.patient_id, user),
        memories=patient_memories,
        reminders=patient_reminders
    )

    audio_stream = await SarvamAIService.synthesize_speech(
        text=reply_text,
        target_language_code=req.language_code
    )

    return VoiceInteractResponse(
        transcription=question_text,
        reply_text=reply_text,
        audio_base64=audio_stream,
        source="sarvam_ai" if audio_stream else "local_nlu"
    )
