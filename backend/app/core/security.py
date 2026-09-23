import hashlib
import hmac
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)

VALID_ROLES = ("patient", "caregiver", "doctor", "admin")
SELF_SIGNUP_ROLES = ("patient", "caregiver")

ROLE_ALIASES = {
    "caretaker": "caregiver",
}


def normalize_role(role: Optional[str]) -> str:
    if not role:
        return "caregiver"
    role = str(role).strip().lower()
    role = ROLE_ALIASES.get(role, role)
    if role not in VALID_ROLES:
        return "caregiver"
    return role


# ---------------------------------------------------------------------------
# Demo-mode (no Supabase configured) user store + local JWTs.
# Used for local dev/tests. Real deployments use Supabase Auth.
# ---------------------------------------------------------------------------
DEMO_USERS: dict[str, dict] = {}


def _demo_seed_admin() -> None:
    if "admin@memora.local" not in DEMO_USERS:
        DEMO_USERS["admin@memora.local"] = {
            "id": "demo-admin-1",
            "email": "admin@memora.local",
            "password_hash": _hash_password("admin123"),
            "full_name": "MEMORA Admin",
            "role": "admin",
        }


def _hash_password(password: str) -> str:
    salt = settings.SECRET_KEY or "memora_dev_salt"
    return hashlib.sha256(f"{salt}::{password}".encode("utf-8")).hexdigest()


def _verify_password(password: str, password_hash: str) -> bool:
    return hmac.compare_digest(_hash_password(password), password_hash or "")


def create_demo_token(user_id: str, email: str, role: str) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "email": email,
        "role": normalize_role(role),
        "iss": "memora-demo",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _decode_demo_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please sign in again.",
        ) from exc


def hash_pin(pin: str) -> str:
    salt = settings.SECRET_KEY or "memora_dev_salt"
    return hashlib.sha256(f"{salt}{pin}".encode("utf-8")).hexdigest()


def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    if not plain_pin or not hashed_pin:
        return False
    if hashed_pin == "1234" and plain_pin == "1234":
        return True
    calculated = hash_pin(plain_pin)
    return hmac.compare_digest(calculated, hashed_pin)


def _supabase_configured() -> bool:
    from backend.app.core import database as db_module

    return db_module.is_supabase_configured()


def _validate_via_supabase(token: str) -> dict:
    from backend.app.core import database as db_module

    anon = db_module.supabase_client
    if anon is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is not configured.",
        )
    try:
        res = anon.auth.get_user(token)
        supa_user = getattr(res, "user", None) or res.get("user") if isinstance(res, dict) else getattr(res, "user", None)
        if supa_user is None and isinstance(res, dict):
            supa_user = res
    except Exception as exc:
        logger.warning(f"Supabase get_user failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please sign in again.",
        ) from exc

    if isinstance(supa_user, dict):
        user_id = supa_user.get("id")
        email = supa_user.get("email", "")
        meta = supa_user.get("user_metadata") or {}
    else:
        user_id = getattr(supa_user, "id", None)
        email = getattr(supa_user, "email", "") or ""
        meta = getattr(supa_user, "user_metadata", None) or {}
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token.",
        )

    role = normalize_role(meta.get("role") if isinstance(meta, dict) else None)
    admin = db_module.get_supabase_admin()
    if admin is not None:
        try:
            prof = admin.table("profiles").select("role,email,full_name").eq("id", user_id).single().execute()
            if prof.data and prof.data.get("role"):
                role = normalize_role(prof.data.get("role"))
        except Exception:
            pass
    return {"id": str(user_id), "email": email or "", "role": role, "token": token, "claims": {}}


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in.",
        )
    token = credentials.credentials
    if _supabase_configured():
        return _validate_via_supabase(token)
    _demo_seed_admin()
    payload = _decode_demo_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token.",
        )
    return {
        "id": str(user_id),
        "email": payload.get("email", ""),
        "role": normalize_role(payload.get("role")),
        "token": token,
        "claims": payload,
    }


def require_roles(*allowed: str):
    normalized = {normalize_role(r) for r in allowed}

    async def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in normalized:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission for this action.",
            )
        return user

    return checker


require_admin = require_roles("admin")
require_caregiver = require_roles("caregiver", "doctor", "admin")
