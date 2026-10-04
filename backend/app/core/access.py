from typing import List, Optional

from fastapi import Depends, HTTPException, status

from backend.app.core import database as db_module
from backend.app.core.security import normalize_role


def _supabase() -> bool:
    return db_module.is_supabase_configured()


# In-memory access grants for the demo/offline fallback store.
DEMO_ACCESS_GRANTS: List[dict] = []


async def _granted_patient_ids(doctor_id: str) -> set:
    """Active patient ids a doctor has been explicitly granted access to."""
    admin = db_module.get_supabase_admin()
    if _supabase() and admin is not None:
        try:
            res = (
                admin.table("access_grants")
                .select("patient_id")
                .eq("doctor_id", doctor_id)
                .eq("status", "active")
                .execute()
            )
            return {int(r["patient_id"]) for r in (res.data or []) if r.get("patient_id") is not None}
        except Exception:
            return set()
    return {
        int(g["patient_id"])
        for g in DEMO_ACCESS_GRANTS
        if g.get("doctor_id") == doctor_id and g.get("status") == "active"
    }


async def fetch_profile(user_id: str) -> dict:
    admin = db_module.get_supabase_admin()
    if admin is None:
        return {}
    try:
        res = admin.table("profiles").select("*").eq("id", user_id).single().execute()
        return res.data or {}
    except Exception:
        return {}


async def list_accessible_patients(user: dict) -> List[dict]:
    role = normalize_role(user.get("role"))
    admin = db_module.get_supabase_admin()
    if _supabase() and admin is not None:
        try:
            if role == "admin":
                res = admin.table("patients").select("*").order("id").execute()
                return res.data or []
            if role == "doctor":
                granted = await _granted_patient_ids(user["id"])
                if not granted:
                    return []
                res = admin.table("patients").select("*").in_("id", list(granted)).order("id").execute()
                return res.data or []
            if role == "patient":
                profile = await fetch_profile(user["id"])
                linked = profile.get("linked_patient_id")
                rows = []
                try:
                    own = admin.table("patients").select("*").eq("auth_user_id", user["id"]).execute()
                    rows.extend(own.data or [])
                except Exception:
                    pass
                if linked:
                    try:
                        one = admin.table("patients").select("*").eq("id", linked).execute()
                        seen = {r.get("id") for r in rows}
                        for r in one.data or []:
                            if r.get("id") not in seen:
                                rows.append(r)
                    except Exception:
                        pass
                return rows
            res = admin.table("patients").select("*").eq("caregiver_id", user["id"]).order("id").execute()
            return res.data or []
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to load patients: {exc}",
            ) from exc

    # Fallback demo store (no Supabase keys): strict per-user isolation
    from backend.app.api.routes.patients import MOCK_PATIENTS
    from backend.app.core.security import DEMO_USERS, _demo_seed_admin

    _demo_seed_admin()
    if role == "admin":
        return list(MOCK_PATIENTS)
    if role == "doctor":
        granted = await _granted_patient_ids(user["id"])
        return [p for p in MOCK_PATIENTS if p.get("id") in granted]
    if role == "patient":
        linked = None
        for u in DEMO_USERS.values():
            if u["id"] == user["id"]:
                linked = u.get("linked_patient_id")
                break
        return [
            p for p in MOCK_PATIENTS
            if p.get("auth_user_id") == user["id"] or (linked is not None and p.get("id") == linked)
        ]
    # caregiver: only patients explicitly assigned to this login
    return [p for p in MOCK_PATIENTS if p.get("caregiver_id") == user["id"]]


async def ensure_patient_access(user: dict, patient_id: int) -> dict:
    patients = await list_accessible_patients(user)
    for p in patients:
        try:
            if int(p.get("id")) == int(patient_id):
                return p
        except (TypeError, ValueError):
            continue
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have access to this patient.",
    )


def can_write(user: dict) -> bool:
    return normalize_role(user.get("role")) in ("caregiver", "admin", "patient")
