from fastapi import APIRouter, HTTPException, Depends
import base64
from backend.app.models.schemas import VoiceInteractRequest, VoiceInteractResponse
from backend.app.services.sarvam_service import SarvamAIService
from backend.app.api.routes.memories import MOCK_MEMORIES
from backend.app.api.routes.routines import MOCK_REMINDERS
from backend.app.api.routes.patients import MOCK_PATIENTS

router = APIRouter(prefix="/voice", tags=["Voice & Sarvam AI"])

@router.post("/interact", response_model=VoiceInteractResponse)
async def voice_interaction(req: VoiceInteractRequest):
    """
    Handles natural voice or text conversations with MEMORA in Indian regional languages
    (Tamil, Hindi, Kannada, Telugu, English) powered by Sarvam AI (Saaras STT & Bulbul TTS).
    """
    patient = next((p for p in MOCK_PATIENTS if p["id"] == req.patient_id), MOCK_PATIENTS[0])
    patient_memories = [m for m in MOCK_MEMORIES if m["patient_id"] == req.patient_id]
    patient_reminders = [r for r in MOCK_REMINDERS if r["patient_id"] == req.patient_id]

    question_text = req.question_text

    # 1. Transcribe audio if base64 audio was provided
    if req.audio_base64:
        try:
            audio_bytes = base64.b64decode(req.audio_base64)
            transcription = await SarvamAIService.transcribe_audio(audio_bytes, req.language_code)
            question_text = transcription
        except Exception:
            question_text = req.question_text or "Who is my daughter?"
    elif not question_text:
        question_text = "Who is my daughter?"

    # 2. Multilingual Intent & Knowledge Lookup
    reply_text = SarvamAIService.resolve_conversational_reply(
        question_text=question_text,
        language_code=req.language_code,
        patient_name=patient["name"],
        memories=patient_memories,
        reminders=patient_reminders
    )

    # 3. Text-To-Speech Synthesis via Sarvam Bulbul:v1
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
