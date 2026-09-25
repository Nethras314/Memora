from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date as DateValue

# =========================================================
# AUTH / MULTI-USER SCHEMAS
# =========================================================
class SignupRequest(BaseModel):
    email: str = Field(..., example="caregiver@example.com")
    password: str = Field(..., min_length=6, example="secret123")
    full_name: str = Field(..., example="Anitha")
    role: str = Field("caregiver", example="caregiver")
    phone: Optional[str] = Field(None, example="8056962028")


class LoginRequest(BaseModel):
    email: str = Field(..., example="caregiver@example.com")
    password: str = Field(..., example="secret123")


class AuthUserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role: str
    linked_patient_id: Optional[int] = None


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserResponse


class AdminCreateUserRequest(SignupRequest):
    linked_patient_id: Optional[int] = None


class LinkPatientRequest(BaseModel):
    patient_id: int = Field(..., example=1)


# =========================================================
# PATIENT SCHEMAS
# =========================================================
class PatientBase(BaseModel):
    name: str = Field(..., example="Meenakshi")
    age: int = Field(..., ge=1, le=120, example=70)
    gender: str = Field(..., example="Female")
    phone: Optional[str] = Field(None, example="8056962028")
    primary_language: str = Field("en-IN", example="en-IN")

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
    caregiver_id: Optional[str] = None
    auth_user_id: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# =========================================================
# PIN & AUTH SCHEMAS
# =========================================================
class PINVerifyRequest(BaseModel):
    pin: str = Field(..., min_length=4, max_length=4, example="1234")
    patient_id: int = Field(default=1, example=1)

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

class MemoryUpdate(BaseModel):
    category: Optional[str] = None
    title: Optional[str] = None
    details: Optional[str] = None
    relationship: Optional[str] = None
    photo_url: Optional[str] = None

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
    date: Optional[DateValue] = None

    class Config:
        from_attributes = True

# =========================================================
# REMINDERS SCHEMAS
# =========================================================
class ReminderBase(BaseModel):
    title: str = Field(..., example="Take medicine")
    reminder_time: str = Field(..., example="14:00")
    frequency: str = Field("Daily", example="Daily")
    category: str = Field("Custom", example="Medicine")

class ReminderCreate(ReminderBase):
    patient_id: int = 1
    enabled: bool = True

class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    reminder_time: Optional[str] = None
    frequency: Optional[str] = None
    category: Optional[str] = None
    enabled: Optional[bool] = None
    done: Optional[bool] = None

class ReminderResponse(ReminderBase):
    id: int
    patient_id: int
    done: bool = False
    enabled: bool = True

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
    # Container the client recorded in (m4a from iOS/Android, webm from web),
    # so the STT provider receives a correctly labelled file.
    audio_content_type: Optional[str] = Field(None, example="audio/m4a")
    language_code: str = Field("ta-IN", example="ta-IN")  # as-IN, bn-IN, en-IN, hi-IN, ta-IN

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
