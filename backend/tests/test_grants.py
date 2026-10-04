from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core import database as db_module

# Force demo-mode store for deterministic tests even if env keys exist.
db_module.supabase_client = None
db_module.supabase_admin_client = None
db_module.is_supabase_configured = lambda: False

client = TestClient(app)


def _headers(email: str, password: str, role: str = "caregiver", full_name: str = "Tester"):
    if not (email == "admin@memora.local" and role == "admin"):
        client.post(
            "/api/auth/signup",
            json={"email": email, "password": password, "full_name": full_name, "role": role},
        )
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _admin():
    return _headers("admin@memora.local", "admin123", role="admin", full_name="Admin")


def _make_doctor(email: str):
    admin = _admin()
    created = client.post(
        "/api/auth/admin/users",
        json={"email": email, "password": "secret123", "full_name": "Dr. Varma", "role": "doctor"},
        headers=admin,
    )
    assert created.status_code == 201, created.text
    doctor_id = created.json()["id"]
    login = client.post("/api/auth/login", json={"email": email, "password": "secret123"})
    assert login.status_code == 200, login.text
    doc_h = {"Authorization": f"Bearer {login.json()['access_token']}"}
    return admin, doctor_id, doc_h


def test_doctor_access_requires_grant():
    admin, doctor_id, doc_h = _make_doctor("doc_grant@test.local")

    # No grants yet: doctor sees no patients and cannot read analytics.
    patients = client.get("/api/patients", headers=doc_h)
    assert patients.status_code == 200
    assert all(p["id"] != 1 for p in patients.json())
    assert client.get("/api/caregiver/analytics?patient_id=1", headers=doc_h).status_code == 403

    # Admin grants access to patient 1.
    grant = client.post(
        "/api/grants",
        json={"patient_id": 1, "doctor_id": doctor_id, "reason": "Treating physician"},
        headers=admin,
    )
    assert grant.status_code == 201, grant.text
    gid = grant.json()["id"]
    assert grant.json()["status"] == "active"

    # Doctor now sees patient 1 and can read analytics.
    patients2 = client.get("/api/patients", headers=doc_h)
    assert any(p["id"] == 1 for p in patients2.json())
    assert client.get("/api/caregiver/analytics?patient_id=1", headers=doc_h).status_code == 200

    # Revoke -> forbidden again.
    rev = client.delete(f"/api/grants/{gid}", headers=admin)
    assert rev.status_code == 200
    assert client.get("/api/caregiver/analytics?patient_id=1", headers=doc_h).status_code == 403


def test_doctor_cannot_grant_self():
    _, _, doc_h = _make_doctor("doc_selfgrant@test.local")
    res = client.post(
        "/api/grants",
        json={"patient_id": 1, "doctor_id": "someone", "reason": "x"},
        headers=doc_h,
    )
    assert res.status_code == 403


def test_grant_requires_valid_doctor():
    admin = _admin()
    res = client.post(
        "/api/grants",
        json={"patient_id": 1, "doctor_id": "nonexistent-doctor", "reason": "x"},
        headers=admin,
    )
    assert res.status_code == 404


def test_grant_revoked_by_unauthorized_caregiver():
    admin, doctor_id, _ = _make_doctor("doc_revoke@test.local")
    grant = client.post(
        "/api/grants",
        json={"patient_id": 1, "doctor_id": doctor_id, "reason": "x"},
        headers=admin,
    )
    gid = grant.json()["id"]

    stranger = _headers("revoke_stranger@test.local", "secret123", full_name="Stranger CG")
    assert client.delete(f"/api/grants/{gid}", headers=stranger).status_code == 403


def test_list_grants_returns_own_for_doctor():
    admin, doctor_id, doc_h = _make_doctor("doc_listgrants@test.local")
    client.post("/api/grants", json={"patient_id": 1, "doctor_id": doctor_id, "reason": "x"}, headers=admin)
    res = client.get("/api/grants", headers=doc_h)
    assert res.status_code == 200
    rows = res.json()
    assert any(r["doctor_id"] == doctor_id and r["patient_id"] == 1 for r in rows)
