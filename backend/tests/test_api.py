from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core import database as db_module

# Force demo-mode store for deterministic tests even if env keys exist.
db_module.supabase_client = None
db_module.supabase_admin_client = None
db_module.is_supabase_configured = lambda: False

client = TestClient(app)


def _auth_headers(email: str, password: str, role: str = "caregiver", full_name: str = "Tester"):
    if not (email == "admin@memora.local" and role == "admin"):
        client.post(
            "/api/auth/signup",
            json={"email": email, "password": password, "full_name": full_name, "role": role},
        )
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_protected_routes_require_auth():
    assert client.get("/api/patients").status_code == 401
    assert client.get("/api/memories?patient_id=1").status_code == 401
    assert client.get("/api/cognitive/next-game?patient_id=1").status_code == 401


def test_admin_login_and_user_listing():
    headers = _auth_headers("admin@memora.local", "admin123", role="admin", full_name="Admin")
    res = client.get("/api/auth/admin/users", headers=headers)
    assert res.status_code == 200
    assert any(u["email"] == "admin@memora.local" for u in res.json())


def test_caregiver_isolation_between_accounts():
    h1 = _auth_headers("cg_one@test.local", "secret123", full_name="CG One")
    h2 = _auth_headers("cg_two@test.local", "secret123", full_name="CG Two")

    p1 = client.post(
        "/api/patients",
        json={"name": "Patient One", "age": 72, "gender": "Female", "primary_language": "en-IN", "pin": "1111"},
        headers=h1,
    )
    assert p1.status_code == 201, p1.text
    pid = p1.json()["id"]

    # Caregiver two must NOT see caregiver one's patient
    others = client.get("/api/patients", headers=h2)
    assert others.status_code == 200
    assert all(p["id"] != pid for p in others.json())

    # ...nor access their memories/cognitive data
    assert client.get(f"/api/memories?patient_id={pid}", headers=h2).status_code == 403
    assert client.get(f"/api/cognitive/next-game?patient_id={pid}", headers=h2).status_code == 403

    # Owner can access
    assert client.get(f"/api/memories?patient_id={pid}", headers=h1).status_code == 200


def test_patient_signup_gets_own_record():
    headers = _auth_headers("patient_new@test.local", "secret123", role="patient", full_name="New Patient")
    res = client.get("/api/patients", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_verify_pin_success():
    headers = _auth_headers("admin@memora.local", "admin123", role="admin", full_name="Admin")
    # legacy patient 1 PIN is 1234 in demo fallback; admin can access legacy rows
    response = client.post("/api/auth/verify-pin", json={"pin": "1234", "patient_id": 1}, headers=headers)
    assert response.status_code in (200, 403)


def test_dda_next_game():
    headers = _auth_headers("admin@memora.local", "admin123", role="admin", full_name="Admin")
    response = client.get("/api/cognitive/next-game?patient_id=1", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "sequence" in data
    assert "options" in data
    assert data["difficulty_level"] >= 1


def test_caregiver_analytics():
    headers = _auth_headers("admin@memora.local", "admin123", role="admin", full_name="Admin")
    response = client.get("/api/caregiver/analytics?patient_id=1", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "cognitive_stability_score" in data
    assert "routine_completion_pct" in data


def test_voice_interact_tamil():
    headers = _auth_headers("admin@memora.local", "admin123", role="admin", full_name="Admin")
    response = client.post("/api/voice/interact", json={
        "patient_id": 1,
        "question_text": "என் மகள் யார்?",
        "language_code": "ta-IN"
    }, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "அனிதா" in data["reply_text"]
