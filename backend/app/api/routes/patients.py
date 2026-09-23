from typing import List

from fastapi import APIRouter, Depends, HTTPException

from backend.app.core import database as db_module
from backend.app.core.access import ensure_patient_access, list_accessible_patients
from backend.app.core.security import get_current_user, normalize_role
from backend.app.models.schemas import PatientCreate, PatientResponse, PatientUpdate

router = APIRouter(prefix="/patients", tags=["Patients"])

# Fallback store for local demo / tests (used only when Supabase is not configured)
MOCK_PATIENTS = [
    {
        "id": 1,
        "name": "Meenakshi",
        "age": 70,
        "gender": "Female",
        "phone": "8056962028",
        "primary_language": "ta-IN",
        "caregiver_name": "Anitha",
        "caregiver_id": None,
        "auth_user_id": None,
        "pin_hash": "1234",
    },
    {
        "id": 2,
        "name": "Raman",
        "age": 75,
        "gender": "Male",
        "phone": "9000000000",
        "primary_language": "en-IN",
        "caregiver_name": "Kumar",
        "caregiver_id": None,
        "auth_user_id": None,
        "pin_hash": "1234",
    }
]


def _row_to_response(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "name": row.get("name"),
        "age": row.get("age"),
        "gender": row.get("gender"),
        "phone": row.get("phone"),
        "primary_language": row.get("primary_language") or "en-IN",
        "caregiver_name": row.get("caregiver_name"),
        "caregiver_id": str(row.get("caregiver_id")) if row.get("caregiver_id") else None,
        "auth_user_id": str(row.get("auth_user_id")) if row.get("auth_user_id") else None,
    }


@router.get("", response_model=List[PatientResponse])
async def list_patients(user: dict = Depends(get_current_user)):
    rows = await list_accessible_patients(user)
    return [_row_to_response(r) for r in rows]


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: int, user: dict = Depends(get_current_user)):
    row = await ensure_patient_access(user, patient_id)
    return _row_to_response(row)


@router.post("", response_model=PatientResponse, status_code=201)
async def create_patient(payload: PatientCreate, user: dict = Depends(get_current_user)):
    role = normalize_role(user.get("role"))
    if role not in ("caregiver", "admin"):
        raise HTTPException(status_code=403, detail="Only caregivers or admins can register patients.")
    from backend.app.core.security import hash_pin

    if db_module.is_supabase_configured():
        admin = db_module.get_supabase_admin()
        data = {
            "name": payload.name,
            "age": payload.age,
            "gender": payload.gender,
            "phone": payload.phone,
            "primary_language": payload.primary_language or "en-IN",
            "pin_hash": hash_pin(payload.pin),
            "caregiver_id": None if role == "admin" else user["id"],
        }
        try:
            res = admin.table("patients").insert(data).execute()
            row = (res.data or [data])[0]
            return _row_to_response(row)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to create patient: {exc}") from exc

    new_id = max([p["id"] for p in MOCK_PATIENTS], default=0) + 1
    row = {
        "id": new_id,
        "name": payload.name,
        "age": payload.age,
        "gender": payload.gender,
        "phone": payload.phone or "",
        "primary_language": payload.primary_language or "en-IN",
        "caregiver_name": "",
        "caregiver_id": None if role == "admin" else user["id"],
        "auth_user_id": None,
        "pin_hash": hash_pin(payload.pin),
    }
    MOCK_PATIENTS.append(row)
    return _row_to_response(row)


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(patient_id: int, update: PatientUpdate, user: dict = Depends(get_current_user)):
    role = normalize_role(user.get("role"))
    if role == "patient":
        raise HTTPException(status_code=403, detail="Patients cannot edit clinical records. Ask your caregiver.")
    await ensure_patient_access(user, patient_id)
    patch = {k: v for k, v in update.model_dump().items() if v is not None}
    if db_module.is_supabase_configured():
        admin = db_module.get_supabase_admin()
        try:
            res = admin.table("patients").update(patch).eq("id", patient_id).execute()
            row = (res.data or [{}])[0] or await ensure_patient_access(user, patient_id)
            return _row_to_response(row)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Update failed: {exc}") from exc
    for p in MOCK_PATIENTS:
        if p["id"] == patient_id:
            p.update(patch)
            return _row_to_response(p)
    raise HTTPException(status_code=404, detail="Patient not found")
