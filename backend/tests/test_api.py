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


def _admin_headers():
    return _auth_headers("admin@memora.local", "admin123", role="admin", full_name="Admin")


def test_verify_pin_success():
    headers = _admin_headers()
    # legacy patient 1 PIN is 1234 in demo fallback; admin can access legacy rows
    response = client.post("/api/auth/verify-pin", json={"pin": "1234", "patient_id": 1}, headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_verify_pin_failure():
    headers = _admin_headers()
    response = client.post("/api/auth/verify-pin", json={"pin": "9999", "patient_id": 1}, headers=headers)
    assert response.status_code == 401
    assert "Incorrect" in response.json()["detail"]

def test_verify_pin_invalid_patient():
    headers = _admin_headers()
    response = client.post("/api/auth/verify-pin", json={"pin": "1234", "patient_id": 99999}, headers=headers)
    assert response.status_code == 404

def test_verify_pin_forbidden_patient():
    h1 = _auth_headers("pin_owner@test.local", "secret123", full_name="PIN Owner")
    h2 = _auth_headers("pin_stranger@test.local", "secret123", full_name="PIN Stranger")
    p1 = client.post(
        "/api/patients",
        json={"name": "PIN Patient", "age": 70, "gender": "Female", "primary_language": "en-IN", "pin": "4321"},
        headers=h1,
    )
    assert p1.status_code == 201, p1.text
    pid = p1.json()["id"]
    # Stranger gets 403, owner succeeds
    assert client.post("/api/auth/verify-pin", json={"pin": "4321", "patient_id": pid}, headers=h2).status_code == 403
    ok = client.post("/api/auth/verify-pin", json={"pin": "4321", "patient_id": pid}, headers=h1)
    assert ok.status_code == 200

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

def test_memories_crud_flow():
    headers = _admin_headers()
    # 1. List existing memories
    list_res = client.get("/api/memories?patient_id=1", headers=headers)
    assert list_res.status_code == 200

    # 2. Create a new memory
    create_res = client.post(
        "/api/memories",
        data={
            "patient_id": 1,
            "category": "Person",
            "title": "Dr. Varma",
            "details": "Family physician who visits on Sundays.",
            "relationship": "Doctor"
        },
        headers=headers,
    )
    assert create_res.status_code == 200
    new_memory = create_res.json()
    assert new_memory["title"] == "Dr. Varma"
    memory_id = new_memory["id"]

    # 3. Update the memory
    update_res = client.put(
        f"/api/memories/{memory_id}?patient_id=1",
        data={
            "title": "Dr. Varma (Physician)",
            "details": "Family physician who visits on Sunday mornings."
        },
        headers=headers,
    )
    assert update_res.status_code == 200
    updated_memory = update_res.json()
    assert updated_memory["title"] == "Dr. Varma (Physician)"

    # 4. Delete the memory
    delete_res = client.delete(f"/api/memories/{memory_id}?patient_id=1", headers=headers)
    assert delete_res.status_code == 200
    assert delete_res.json()["success"] is True

def test_tasks_crud_and_reset_flow():
    headers = _admin_headers()
    # 1. List tasks
    list_res = client.get("/api/routines/tasks?patient_id=1", headers=headers)
    assert list_res.status_code == 200

    # 2. Add a new task
    add_res = client.post(
        "/api/routines/tasks",
        json={
            "patient_id": 1,
            "title": "Evening Pranayama Breathing",
            "task_time": "18:00",
            "category": "Exercise"
        },
        headers=headers,
    )
    assert add_res.status_code == 200
    task_data = add_res.json()
    assert task_data["title"] == "Evening Pranayama Breathing"
    task_id = task_data["id"]
    assert task_data["done"] is False

    listed = client.get("/api/routines/tasks?patient_id=1", headers=headers)
    assert listed.status_code == 200
    assert any(t["id"] == task_id for t in listed.json())

    # 3. Toggle task completion
    toggle_res = client.post(f"/api/routines/tasks/{task_id}/toggle?patient_id=1", headers=headers)
    assert toggle_res.status_code == 200
    assert toggle_res.json()["done"] is True

    after_toggle = client.get("/api/routines/tasks?patient_id=1", headers=headers)
    matching = next(t for t in after_toggle.json() if t["id"] == task_id)
    assert matching["done"] is True

    # 4. Reset tasks for the day
    reset_res = client.post("/api/routines/tasks/reset?patient_id=1", headers=headers)
    assert reset_res.status_code == 200
    assert reset_res.json()["success"] is True

    after_reset = client.get("/api/routines/tasks?patient_id=1", headers=headers)
    matching = next(t for t in after_reset.json() if t["id"] == task_id)
    assert matching["done"] is False

    # 5. Delete task
    delete_res = client.delete(f"/api/routines/tasks/{task_id}?patient_id=1", headers=headers)
    assert delete_res.status_code == 200
    assert delete_res.json()["success"] is True

    after_delete = client.get("/api/routines/tasks?patient_id=1", headers=headers)
    assert all(t["id"] != task_id for t in after_delete.json())


def test_reminders_crud_enable_and_persistence():
    headers = _admin_headers()
    list_res = client.get("/api/routines/reminders?patient_id=1", headers=headers)
    assert list_res.status_code == 200

    create_res = client.post(
        "/api/routines/reminders",
        json={
            "patient_id": 1,
            "title": "Evening herbal tea",
            "reminder_time": "19:15",
            "frequency": "Daily",
            "category": "Food/Meal",
        },
        headers=headers,
    )
    assert create_res.status_code == 200
    reminder = create_res.json()
    reminder_id = reminder["id"]
    assert reminder["title"] == "Evening herbal tea"
    assert reminder["category"] == "Food/Meal"
    assert reminder["enabled"] is True
    assert reminder["done"] is False

    listed = client.get("/api/routines/reminders?patient_id=1", headers=headers)
    assert any(r["id"] == reminder_id for r in listed.json())

    update_res = client.put(
        f"/api/routines/reminders/{reminder_id}?patient_id=1",
        json={"title": "Evening herbal tea with honey", "reminder_time": "19:30"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Evening herbal tea with honey"

    after_update = client.get("/api/routines/reminders?patient_id=1", headers=headers)
    matching = next(r for r in after_update.json() if r["id"] == reminder_id)
    assert matching["title"] == "Evening herbal tea with honey"
    assert matching["reminder_time"].startswith("19:30")

    disable_res = client.post(f"/api/routines/reminders/{reminder_id}/toggle-enabled?patient_id=1", headers=headers)
    assert disable_res.status_code == 200
    assert disable_res.json()["enabled"] is False

    after_disable = client.get("/api/routines/reminders?patient_id=1", headers=headers)
    matching = next(r for r in after_disable.json() if r["id"] == reminder_id)
    assert matching["enabled"] is False

    enable_res = client.post(f"/api/routines/reminders/{reminder_id}/toggle-enabled?patient_id=1", headers=headers)
    assert enable_res.status_code == 200
    assert enable_res.json()["enabled"] is True

    toggle_done = client.post(f"/api/routines/reminders/{reminder_id}/toggle?patient_id=1", headers=headers)
    assert toggle_done.status_code == 200
    assert toggle_done.json()["done"] is True

    delete_res = client.delete(f"/api/routines/reminders/{reminder_id}?patient_id=1", headers=headers)
    assert delete_res.status_code == 200
    assert delete_res.json()["success"] is True

    after_delete = client.get("/api/routines/reminders?patient_id=1", headers=headers)
    assert all(r["id"] != reminder_id for r in after_delete.json())
