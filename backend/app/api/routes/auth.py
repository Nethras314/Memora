from fastapi import APIRouter, HTTPException, status, Depends
from backend.app.models.schemas import PINVerifyRequest, PINVerifyResponse
from backend.app.core.security import verify_pin
from backend.app.core.database import get_supabase
from backend.app.api.routes.patients import MOCK_PATIENTS

router = APIRouter(prefix="/auth", tags=["Authentication & Security"])

@router.post("/verify-pin", response_model=PINVerifyResponse)
async def verify_patient_pin(req: PINVerifyRequest, supabase = Depends(get_supabase)):
    """
    Secure server-side PIN verification for unlocking private memory bank.
    Protects elderly confidential details and family photos.
    Verifies against the specific patient's stored pin_hash in Supabase or patient store.
    """
    patient_id = req.patient_id
    stored_pin_hash = None

    # 1. Look up patient's PIN hash in Supabase
    if supabase:
        try:
            res = supabase.table("patients").select("id, pin_hash").eq("id", patient_id).single().execute()
            if res.data and "pin_hash" in res.data:
                stored_pin_hash = res.data["pin_hash"]
        except Exception:
            pass

    # 2. Fallback to mock store if database is not available or query returned nothing
    if stored_pin_hash is None:
        for p in MOCK_PATIENTS:
            if p["id"] == patient_id:
                stored_pin_hash = p.get("pin_hash", p.get("pin", "1234"))
                break

    if stored_pin_hash is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found."
        )

    is_valid = verify_pin(req.pin, str(stored_pin_hash))
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect 4-digit PIN. Please try again."
        )

    return PINVerifyResponse(
        success=True,
        message="PIN verified successfully. Memory bank unlocked."
    )
