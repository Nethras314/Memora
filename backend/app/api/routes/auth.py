import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.core import database as db_module
from backend.app.core.security import (
    DEMO_USERS,
    SELF_SIGNUP_ROLES,
    _demo_seed_admin,
    _hash_password,
    _verify_password,
    create_demo_token,
    get_current_user,
    normalize_role,
    require_admin,
    verify_pin,
)
from backend.app.models.schemas import (
    AdminCreateUserRequest,
    AuthTokenResponse,
    AuthUserResponse,
    LinkPatientRequest,
    LoginRequest,
    PINVerifyRequest,
    PINVerifyResponse,
    SignupRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication & Users"])

# Legacy demo PIN (kept for existing tests / fallback)
DEFAULT_PATIENT_PIN_HASH = "1234"


def _profile_to_user(user_id: str, email: str, profile: dict) -> AuthUserResponse:
    return AuthUserResponse(
        id=user_id,
        email=email,
        full_name=profile.get("full_name"),
        role=normalize_role(profile.get("role")),
        linked_patient_id=profile.get("linked_patient_id"),
    )


async def _get_profile(user_id: str) -> dict:
    admin = db_module.get_supabase_admin()
    if admin is None:
        return {}
    try:
        res = admin.table("profiles").select("*").eq("id", user_id).single().execute()
        return res.data or {}
    except Exception:
        return {}


@router.post("/signup", response_model=AuthTokenResponse, status_code=201)
async def signup(req: SignupRequest):
    role = normalize_role(req.role)
    if role not in SELF_SIGNUP_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public signup is allowed for patient and caregiver only. Ask an admin for staff accounts.",
        )
    email = req.email.strip().lower()

    if db_module.is_supabase_configured():
        anon = db_module.supabase_client
        admin = db_module.get_supabase_admin()
        try:
            res = anon.auth.sign_up(
                {
                    "email": email,
                    "password": req.password,
                    "options": {"data": {"full_name": req.full_name, "role": role}},
                }
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Signup failed: {exc}") from exc
        supa_user = getattr(res, "user", None)
        session = getattr(res, "session", None)
        if supa_user is None:
            raise HTTPException(status_code=400, detail="Signup failed. Email may already be registered.")
        user_id = getattr(supa_user, "id", None) or (supa_user.get("id") if isinstance(supa_user, dict) else None)
        if admin is not None and user_id:
            try:
                admin.table("profiles").upsert(
                    {
                        "id": user_id,
                        "email": email,
                        "full_name": req.full_name,
                        "phone": req.phone,
                        "role": role,
                    }
                ).execute()
            except Exception:
                pass
        token = getattr(session, "access_token", None) or (session.get("access_token") if isinstance(session, dict) else None)
        if not token:
            # Email confirmation required — user must confirm then login.
            raise HTTPException(
                status_code=202,
                detail="Account created. Please confirm your email, then sign in.",
            )
        profile = await _get_profile(user_id)
        return AuthTokenResponse(
            access_token=token,
            user=_profile_to_user(user_id, email, {**profile, "role": role, "full_name": req.full_name}),
        )

    # Demo fallback (local dev / tests, no Supabase keys)
    _demo_seed_admin()
    if email in DEMO_USERS:
        raise HTTPException(status_code=400, detail="Email already registered. Please sign in.")
    user_id = f"demo-{uuid.uuid4().hex[:8]}"
    DEMO_USERS[email] = {
        "id": user_id,
        "email": email,
        "password_hash": _hash_password(req.password),
        "full_name": req.full_name,
        "phone": req.phone,
        "role": role,
        "linked_patient_id": None,
    }
    if role == "patient":
        from backend.app.api.routes.patients import MOCK_PATIENTS

        new_id = max([p["id"] for p in MOCK_PATIENTS], default=0) + 1
        MOCK_PATIENTS.append(
            {
                "id": new_id,
                "name": req.full_name,
                "age": 70,
                "gender": "Other",
                "phone": req.phone or "",
                "primary_language": "en-IN",
                "caregiver_name": "",
                "caregiver_id": None,
                "auth_user_id": user_id,
                "pin_hash": "1234",
            }
        )
        DEMO_USERS[email]["linked_patient_id"] = new_id
    token = create_demo_token(user_id, email, role)
    u = DEMO_USERS[email]
    return AuthTokenResponse(
        access_token=token,
        user=AuthUserResponse(
            id=user_id, email=email, full_name=u["full_name"], role=role,
            linked_patient_id=u.get("linked_patient_id"),
        ),
    )


@router.post("/login", response_model=AuthTokenResponse)
async def login(req: LoginRequest):
    email = req.email.strip().lower()
    if db_module.is_supabase_configured():
        anon = db_module.supabase_client
        try:
            res = anon.auth.sign_in_with_password({"email": email, "password": req.password})
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid email or password.") from None
        session = getattr(res, "session", None)
        supa_user = getattr(res, "user", None)
        token = getattr(session, "access_token", None) if session else None
        if isinstance(session, dict):
            token = session.get("access_token")
        if not token or supa_user is None:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        user_id = getattr(supa_user, "id", None) or (supa_user.get("id") if isinstance(supa_user, dict) else None)
        meta_email = getattr(supa_user, "email", email)
        profile = await _get_profile(user_id)
        role = normalize_role(profile.get("role") or "caregiver")
        return AuthTokenResponse(
            access_token=token,
            user=_profile_to_user(user_id, meta_email or email, profile),
        )

    _demo_seed_admin()
    user = DEMO_USERS.get(email)
    if not user or not _verify_password(req.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = create_demo_token(user["id"], email, user["role"])
    return AuthTokenResponse(
        access_token=token,
        user=AuthUserResponse(
            id=user["id"], email=email, full_name=user.get("full_name"),
            role=user["role"], linked_patient_id=user.get("linked_patient_id"),
        ),
    )


@router.get("/me", response_model=AuthUserResponse)
async def me(user: dict = Depends(get_current_user)):
    if db_module.is_supabase_configured():
        profile = await _get_profile(user["id"])
        if profile:
            return _profile_to_user(user["id"], profile.get("email", user.get("email", "")), profile)
    else:
        for u in DEMO_USERS.values():
            if u["id"] == user["id"]:
                return AuthUserResponse(
                    id=u["id"], email=u["email"], full_name=u.get("full_name"),
                    role=u["role"], linked_patient_id=u.get("linked_patient_id"),
                )
    return AuthUserResponse(
        id=user["id"], email=user.get("email", ""), full_name=None,
        role=user.get("role", "caregiver"), linked_patient_id=None,
    )


@router.post("/link-patient")
async def link_patient(req: LinkPatientRequest, user: dict = Depends(get_current_user)):
    """Patient links own login to a patient row; caregiver claims a patient; admin links anyone."""
    role = normalize_role(user.get("role"))

    if db_module.is_supabase_configured():
        admin = db_module.get_supabase_admin()
        try:
            prow = admin.table("patients").select("*").eq("id", req.patient_id).single().execute()
        except Exception:
            raise HTTPException(status_code=404, detail="Patient not found.")
        patient = prow.data or {}
        if role == "patient":
            try:
                admin.table("patients").update({"auth_user_id": user["id"]}).eq("id", req.patient_id).execute()
                admin.table("profiles").update({"linked_patient_id": req.patient_id}).eq("id", user["id"]).execute()
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"Link failed: {exc}") from exc
        elif role == "caregiver":
            if patient.get("caregiver_id") and patient.get("caregiver_id") != user["id"]:
                raise HTTPException(status_code=403, detail="Patient is already assigned to another caregiver.")
            try:
                admin.table("patients").update({"caregiver_id": user["id"]}).eq("id", req.patient_id).execute()
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"Link failed: {exc}") from exc
        else:  # admin / doctor pass-through (admin enforced at route level below for others)
            if role not in ("admin", "doctor"):
                raise HTTPException(status_code=403, detail="Not allowed.")
        return {"success": True, "patient_id": req.patient_id}

    # Demo fallback
    from backend.app.api.routes.patients import MOCK_PATIENTS

    target = next((p for p in MOCK_PATIENTS if p["id"] == req.patient_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Patient not found.")
    if role == "patient":
        target["auth_user_id"] = user["id"]
        for u in DEMO_USERS.values():
            if u["id"] == user["id"]:
                u["linked_patient_id"] = req.patient_id
    elif role == "caregiver":
        target["caregiver_id"] = user["id"]
    elif role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed.")
    return {"success": True, "patient_id": req.patient_id}


@router.post("/verify-pin", response_model=PINVerifyResponse)
async def verify_patient_pin(req: PINVerifyRequest, user: dict = Depends(get_current_user)):
    """
    Secure server-side PIN verification for unlocking private memory bank.
    Requires login, checks the caller may access this patient, then verifies
    against the specific patient's stored pin_hash.
    Returns 404 when the patient does not exist at all.
    """
    from backend.app.core.access import ensure_patient_access, list_accessible_patients

    patient_id = int(req.patient_id or 1)
    try:
        patient = await ensure_patient_access(user, patient_id)
    except HTTPException as exc:
        if exc.status_code == 403 and normalize_role(user.get("role")) == "admin":
            # Admins can see every patient, so 403 here means the row is missing.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found.",
            ) from exc
        raise
    stored = patient.get("pin_hash")
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )
    if not verify_pin(req.pin, str(stored)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect 4-digit PIN. Please try again.",
        )
    return PINVerifyResponse(success=True, message="PIN verified successfully. Memory bank unlocked.")


# ---------------------------------------------------------------------------
# Admin user management
# ---------------------------------------------------------------------------
@router.get("/admin/users", response_model=List[AuthUserResponse])
async def admin_list_users(admin: dict = Depends(require_admin)):
    if db_module.is_supabase_configured():
        client = db_module.get_supabase_admin()
        try:
            res = client.table("profiles").select("*").order("created_at", desc=True).execute()
            return [
                AuthUserResponse(
                    id=r["id"], email=r.get("email", ""), full_name=r.get("full_name"),
                    role=normalize_role(r.get("role")), linked_patient_id=r.get("linked_patient_id"),
                )
                for r in (res.data or [])
            ]
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to list users: {exc}") from exc
    _demo_seed_admin()
    return [
        AuthUserResponse(
            id=u["id"], email=u["email"], full_name=u.get("full_name"),
            role=u["role"], linked_patient_id=u.get("linked_patient_id"),
        )
        for u in DEMO_USERS.values()
    ]


@router.post("/admin/users", response_model=AuthUserResponse, status_code=201)
async def admin_create_user(req: AdminCreateUserRequest, admin: dict = Depends(require_admin)):
    role = normalize_role(req.role)
    email = req.email.strip().lower()
    if db_module.is_supabase_configured():
        client = db_module.get_supabase_admin()
        try:
            created = client.auth.admin.create_user(
                {
                    "email": email,
                    "password": req.password,
                    "email_confirm": True,
                    "user_metadata": {"full_name": req.full_name, "role": role},
                }
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Create user failed: {exc}") from exc
        new_user = getattr(created, "user", created)
        user_id = getattr(new_user, "id", None) or (new_user.get("id") if isinstance(new_user, dict) else None)
        try:
            client.table("profiles").upsert(
                {
                    "id": user_id, "email": email, "full_name": req.full_name,
                    "phone": req.phone, "role": role, "linked_patient_id": req.linked_patient_id,
                }
            ).execute()
        except Exception:
            pass
        return AuthUserResponse(id=user_id, email=email, full_name=req.full_name, role=role,
                                linked_patient_id=req.linked_patient_id)
    _demo_seed_admin()
    if email in DEMO_USERS:
        raise HTTPException(status_code=400, detail="Email already exists.")
    import uuid as _uuid

    user_id = f"demo-{_uuid.uuid4().hex[:8]}"
    DEMO_USERS[email] = {
        "id": user_id, "email": email, "password_hash": _hash_password(req.password),
        "full_name": req.full_name, "phone": req.phone, "role": role,
        "linked_patient_id": req.linked_patient_id,
    }
    return AuthUserResponse(id=user_id, email=email, full_name=req.full_name, role=role,
                            linked_patient_id=req.linked_patient_id)
