from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from backend.app.core import database as db_module
from backend.app.core.access import DEMO_ACCESS_GRANTS, ensure_patient_access, list_accessible_patients
from backend.app.core.security import DEMO_USERS, _demo_seed_admin, get_current_user, normalize_role, require_admin
from backend.app.models.schemas import AccessGrantCreate, AccessGrantResponse

router = APIRouter(prefix="/grants", tags=["Doctor Access Grants"])


def _supabase():
    return db_module.get_supabase_admin() if db_module.is_supabase_configured() else None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _serialize(g: dict) -> AccessGrantResponse:
    return AccessGrantResponse(
        id=g["id"],
        patient_id=g["patient_id"],
        doctor_id=g.get("doctor_id"),
        granted_by=str(g.get("granted_by")) if g.get("granted_by") else None,
        reason=g.get("reason"),
        status=g.get("status", "active"),
        created_at=g.get("created_at"),
        revoked_at=g.get("revoked_at"),
    )


async def _doctor_exists(doctor_id: str) -> bool:
    admin = _supabase()
    if admin is not None:
        try:
            res = admin.table("profiles").select("id,role").eq("id", doctor_id).single().execute()
            return bool(res.data) and normalize_role(res.data.get("role")) == "doctor"
        except Exception:
            return False
    _demo_seed_admin()
    return any(
        u["id"] == doctor_id and normalize_role(u.get("role")) == "doctor"
        for u in DEMO_USERS.values()
    )


@router.get("", response_model=List[AccessGrantResponse])
async def list_grants(user: dict = Depends(get_current_user)):
    role = normalize_role(user.get("role"))
    admin = _supabase()
    if admin is not None:
        q = admin.table("access_grants").select("*").order("created_at", desc=True)
        if role == "admin":
            res = q.execute()
        elif role == "doctor":
            res = q.eq("doctor_id", user["id"]).execute()
        else:
            patients = await list_accessible_patients(user)
            ids = [p["id"] for p in patients]
            if not ids:
                return []
            res = q.in_("patient_id", ids).execute()
        return [_serialize(r) for r in (res.data or [])]

    _demo_seed_admin()
    if role == "admin":
        rows = list(DEMO_ACCESS_GRANTS)
    elif role == "doctor":
        rows = [g for g in DEMO_ACCESS_GRANTS if g.get("doctor_id") == user["id"]]
    else:
        patients = await list_accessible_patients(user)
        ids = {p["id"] for p in patients}
        rows = [g for g in DEMO_ACCESS_GRANTS if g.get("patient_id") in ids]
    return [_serialize(g) for g in rows]


@router.get("/doctors")
async def list_doctors(admin_user: dict = Depends(require_admin)):
    admin = _supabase()
    if admin is not None:
        try:
            res = admin.table("profiles").select("id,email,full_name,role").eq("role", "doctor").execute()
            return res.data or []
        except Exception:
            return []
    _demo_seed_admin()
    return [
        {"id": u["id"], "email": u["email"], "full_name": u.get("full_name"), "role": u["role"]}
        for u in DEMO_USERS.values()
        if normalize_role(u.get("role")) == "doctor"
    ]


@router.post("", response_model=AccessGrantResponse, status_code=201)
async def create_grant(payload: AccessGrantCreate, user: dict = Depends(get_current_user)):
    role = normalize_role(user.get("role"))
    if role == "doctor":
        raise HTTPException(status_code=403, detail="Doctors cannot grant themselves access.")
    await ensure_patient_access(user, payload.patient_id)
    if not await _doctor_exists(payload.doctor_id):
        raise HTTPException(status_code=404, detail="Doctor account not found.")

    admin = _supabase()
    record = {
        "patient_id": payload.patient_id,
        "doctor_id": payload.doctor_id,
        "granted_by": user["id"],
        "reason": payload.reason,
        "status": "active",
        "created_at": _now(),
        "revoked_at": None,
    }

    if admin is not None:
        try:
            existing = (
                admin.table("access_grants")
                .select("id")
                .eq("patient_id", payload.patient_id)
                .eq("doctor_id", payload.doctor_id)
                .execute()
            )
            if existing.data:
                gid = existing.data[0]["id"]
                res = (
                    admin.table("access_grants")
                    .update({"status": "active", "revoked_at": None, "granted_by": user["id"], "reason": payload.reason})
                    .eq("id", gid)
                    .execute()
                )
                return _serialize(res.data[0])
            res = admin.table("access_grants").insert(record).execute()
            return _serialize(res.data[0])
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to create grant: {exc}") from exc

    existing = next(
        (g for g in DEMO_ACCESS_GRANTS if g["patient_id"] == payload.patient_id and g["doctor_id"] == payload.doctor_id),
        None,
    )
    if existing:
        existing.update(status="active", revoked_at=None, granted_by=user["id"], reason=payload.reason)
        return _serialize(existing)

    gid = max([g["id"] for g in DEMO_ACCESS_GRANTS], default=0) + 1
    new_grant = {"id": gid, **record}
    DEMO_ACCESS_GRANTS.append(new_grant)
    return _serialize(new_grant)


@router.delete("/{grant_id}", response_model=AccessGrantResponse)
async def revoke_grant(grant_id: int, user: dict = Depends(get_current_user)):
    role = normalize_role(user.get("role"))
    if role == "doctor":
        raise HTTPException(status_code=403, detail="Doctors cannot revoke access grants.")
    admin = _supabase()

    if admin is not None:
        try:
            existing = admin.table("access_grants").select("*").eq("id", grant_id).single().execute()
            g = existing.data
        except Exception:
            g = None
        if not g:
            raise HTTPException(status_code=404, detail="Grant not found.")
        await ensure_patient_access(user, int(g["patient_id"]))
        res = admin.table("access_grants").update({"status": "revoked", "revoked_at": _now()}).eq("id", grant_id).execute()
        return _serialize(res.data[0])

    g = next((x for x in DEMO_ACCESS_GRANTS if x["id"] == grant_id), None)
    if not g:
        raise HTTPException(status_code=404, detail="Grant not found.")
    await ensure_patient_access(user, int(g["patient_id"]))
    g["status"] = "revoked"
    g["revoked_at"] = _now()
    return _serialize(g)
