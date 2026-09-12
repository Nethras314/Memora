from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, time, date

# =========================================================
# PATIENT SCHEMAS
# =========================================================
class PatientBase(BaseModel):
    name: str = Field(..., example="Meenakshi")
    age: int = Field(..., ge=1, le=120, example=70)
    gender: str = Field(..., example="Female")
    phone: Optional[str] = Field(None, example="8056962028")
    primary_language: str = Field("ta-IN", example="ta-IN")

class PatientCreate(PatientBase):
    pin: str = Field(..., min_length=4, max_length=4, example="1234")

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    primary_language: Optional[str] = None

class PatientResponse(PatientBase):
    id: int
    caregiver_name: Optional[str] = "Anitha"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# =========================================================
# PIN & AUTH SCHEMAS
# =========================================================
class PINVerifyRequest(BaseModel):
    pin: str = Field(..., min_length=4, max_length=4, example="1234")

class PINVerifyResponse(BaseModel):
    success: bool
    message: str

# =========================================================
# MEMORY BANK SCHEMAS
# =========================================================
class MemoryBase(BaseModel):
    category: str = Field(..., example="Person")
    title: str = Field(..., example="Daughter")
    details: str = Field(..., example="Anitha is my eldest daughter who cares for me.")
    relationship: Optional[str] = Field(None, example="Daughter")
    photo_url: Optional[str] = None

class MemoryCreate(MemoryBase):
    patient_id: int = 1

class MemoryResponse(MemoryBase):
    id: int
    patient_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# =========================================================
# ROUTINE / TASKS SCHEMAS
# =========================================================
class TaskBase(BaseModel):
    title: str = Field(..., example="Morning Breakfast")
    task_time: str = Field(..., example="09:00")
    category: str = Field("Routine", example="Routine")

class TaskCreate(TaskBase):
    patient_id: int = 1

class TaskResponse(TaskBase):
    id: int
    patient_id: int
    done: bool = False
    date: Optional[date] = None

    class Config:
        from_attributes = True

# =========================================================
# REMINDERS SCHEMAS
# =========================================================
class ReminderBase(BaseModel):
    title: str = Field(..., example="Take medicine")
    reminder_time: str = Field(..., example="14:00")
    frequency: str = Field("Daily", example="Daily")

class ReminderCreate(ReminderBase):
    patient_id: int = 1

class ReminderResponse(ReminderBase):
    id: int
    patient_id: int
    done: bool = False

    class Config:
        from_attributes = True

# =========================================================
# COGNITIVE / DDA SCHEMAS
# =========================================================
class CognitiveSessionCreate(BaseModel):
    patient_id: int = 1
    game_type: str = Field("sequence_memory", example="sequence_memory")
    difficulty_level: int = Field(1, ge=1, le=10)
    score: int = Field(..., ge=0, le=100)
    accuracy: float = Field(..., ge=0.0, le=1.0)
    reaction_time_ms: int = Field(..., ge=100, example=2800)
    mistake_count: int = Field(0, ge=0)
    session_metadata: Optional[Dict[str, Any]] = None

class CognitiveSessionResponse(CognitiveSessionCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class DDANextGameResponse(BaseModel):
    game_type: str
    difficulty_level: int
    sequence: Optional[List[str]] = None
    options: Optional[List[str]] = None
    display_duration_ms: int
    guidance_cue: str

# =========================================================
# VOICE & SARVAM AI SCHEMAS
# =========================================================
class VoiceInteractRequest(BaseModel):
    patient_id: int = 1
    question_text: Optional[str] = None
    audio_base64: Optional[str] = None
    language_code: str = Field("ta-IN", example="ta-IN") # ta-IN, hi-IN, kn-IN, en-IN

class VoiceInteractResponse(BaseModel):
    transcription: str
    reply_text: str
    audio_base64: Optional[str] = None
    source: str # "sarvam_ai" or "local_nlu"

# =========================================================
# CAREGIVER ANALYTICS SCHEMAS
# =========================================================
class CaregiverAnalyticsResponse(BaseModel):
    patient_id: int
    patient_name: str
    routine_completion_pct: int
    completed_tasks: int
    total_tasks: int
    cognitive_stability_score: int # 0-100 score calculated from DDA telemetry
    recent_sessions_count: int
    recommended_focus: str
    cognitive_trend: List[Dict[str, Any]]
