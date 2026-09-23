from fastapi import APIRouter, HTTPException, Depends
from typing import List
from backend.app.models.schemas import PatientResponse, PatientCreate, PatientUpdate
from backend.app.core.database import get_supabase

router = APIRouter(prefix="/patients", tags=["Patients"])

# In-memory mock store for demo and testing without external db requirement
MOCK_PATIENTS = [
    {
        "id": 1,
        "name": "Meenakshi",
        "age": 70,
        "gender": "Female",
        "phone": "8056962028",
        "primary_language": "ta-IN",
        "caregiver_name": "Anitha",
        "pin_hash": "1234"
    },
    {
        "id": 2,
        "name": "Raman",
        "age": 75,
        "gender": "Male",
        "phone": "9000000000",
        "primary_language": "en-IN",
        "caregiver_name": "Kumar",
        "pin_hash": "1234"
    }
]

@router.get("", response_model=List[PatientResponse])
async def list_patients(supabase = Depends(get_supabase)):
    """
    Returns all patients managed by the caregiver. Supports true multi-patient environments.
    """
    if supabase:
        try:
            res = supabase.table("patients").select("*").execute()
            if res.data:
                return res.data
        except Exception:
            pass
    return MOCK_PATIENTS

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: int, supabase = Depends(get_supabase)):
    """
    Fetches the profile for a specific patient.
    """
    if supabase:
        try:
            res = supabase.table("patients").select("*").eq("id", patient_id).single().execute()
            if res.data:
                return res.data
        except Exception:
            pass
            
    for p in MOCK_PATIENTS:
        if p["id"] == patient_id:
            return p
    raise HTTPException(status_code=404, detail="Patient not found")

@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(patient_id: int, update: PatientUpdate, supabase = Depends(get_supabase)):
    """
    Updates patient details (name, age, phone, language preference).
    """
    for p in MOCK_PATIENTS:
        if p["id"] == patient_id:
            if update.name: p["name"] = update.name
            if update.age: p["age"] = update.age
            if update.gender: p["gender"] = update.gender
            if update.phone: p["phone"] = update.phone
            if update.primary_language: p["primary_language"] = update.primary_language
            return p
    raise HTTPException(status_code=404, detail="Patient not found")
