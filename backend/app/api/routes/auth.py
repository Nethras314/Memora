from fastapi import APIRouter, HTTPException, status
from backend.app.models.schemas import PINVerifyRequest, PINVerifyResponse
from backend.app.core.security import verify_pin

router = APIRouter(prefix="/auth", tags=["Authentication & Security"])

# Default hash for testing PIN '1234'
DEFAULT_PATIENT_PIN_HASH = "1234"

@router.post("/verify-pin", response_model=PINVerifyResponse)
async def verify_patient_pin(req: PINVerifyRequest):
    """
    Secure server-side PIN verification for unlocking private memory bank.
    Protects elderly confidential details and family photos.
    """
    is_valid = verify_pin(req.pin, DEFAULT_PATIENT_PIN_HASH)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect 4-digit PIN. Please try again."
        )
    return PINVerifyResponse(
        success=True,
        message="PIN verified successfully. Memory bank unlocked."
    )
