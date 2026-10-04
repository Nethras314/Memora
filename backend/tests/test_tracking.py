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


def _create_patient(owner_headers, name):
    res = client.post(
        "/api/patients",
        json={"name": name, "age": 72, "gender": "Female", "primary_language": "en-IN", "pin": "1234"},
        headers=owner_headers,
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


def test_mood_log_crud_and_isolation():
    cg = _headers("mood_owner@test.local", "secret123", full_name="Mood Owner")
    pid = _create_patient(cg, "Mood Patient")

    res = client.post(
        "/api/tracking/mood",
        json={"patient_id": pid, "mood": "Agitated", "behavior_flags": ["sundowning"], "note": "afternoon"},
        headers=cg,
    )
    assert res.status_code == 201, res.text
    mid = res.json()["id"]
    assert res.json()["mood"] == "Agitated"
    assert res.json()["behavior_flags"] == ["sundowning"]

    listed = client.get(f"/api/tracking/mood?patient_id={pid}", headers=cg)
    assert listed.status_code == 200
    assert any(m["id"] == mid for m in listed.json())

    stranger = _headers("mood_stranger@test.local", "secret123", full_name="Mood Stranger")
    assert client.get(f"/api/tracking/mood?patient_id={pid}", headers=stranger).status_code == 403

    deleted = client.delete(f"/api/tracking/mood/{mid}?patient_id={pid}", headers=cg)
    assert deleted.status_code == 200


def test_patient_cannot_write_mood():
    ph = _headers("mood_patient@test.local", "secret123", role="patient", full_name="Mood Patient")
    patients = client.get("/api/patients", headers=ph).json()
    assert patients
    pid = patients[0]["id"]
    res = client.post("/api/tracking/mood", json={"patient_id": pid, "mood": "Calm"}, headers=ph)
    assert res.status_code == 403


def test_mood_rejects_invalid_value():
    cg = _headers("mood_invalid@test.local", "secret123", full_name="Mood Invalid")
    pid = _create_patient(cg, "Mood Invalid Patient")
    res = client.post("/api/tracking/mood", json={"patient_id": pid, "mood": "Ecstatic"}, headers=cg)
    assert res.status_code == 400


def test_clinical_notes_write_rules():
    admin = _admin()
    cg = _headers("note_cg@test.local", "secret123", full_name="Note CG")
    pid = _create_patient(cg, "Note Patient")

    # Caregiver cannot write clinical notes.
    assert client.post(
        "/api/tracking/notes",
        json={"patient_id": pid, "note_type": "general", "body": "hi"},
        headers=cg,
    ).status_code == 403

    # Admin (doctor/admin role) can write.
    res = client.post(
        "/api/tracking/notes",
        json={"patient_id": pid, "note_type": "assessment", "body": "Stable, mild memory decline."},
        headers=admin,
    )
    assert res.status_code == 201, res.text
    nid = res.json()["id"]
    assert res.json()["note_type"] == "assessment"

    # Caregiver can read own patient's notes.
    listed = client.get(f"/api/tracking/notes?patient_id={pid}", headers=cg)
    assert listed.status_code == 200
    assert any(n["id"] == nid for n in listed.json())

    stranger = _headers("note_stranger@test.local", "secret123", full_name="Note Stranger")
    assert client.get(f"/api/tracking/notes?patient_id={pid}", headers=stranger).status_code == 403


def test_clinical_note_rejects_invalid_type():
    admin = _admin()
    res = client.post(
        "/api/tracking/notes",
        json={"patient_id": 1, "note_type": "memo", "body": "x"},
        headers=admin,
    )
    assert res.status_code == 400
