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


def test_patient_can_change_own_language():
    headers = _auth_headers("lang_self@test.local", "secret123", role="patient", full_name="Lang Self")
    patients = client.get("/api/patients", headers=headers).json()
    assert patients
    pid = patients[0]["id"]

    res = client.put(f"/api/patients/{pid}/language", json={"language_code": "hi-IN"}, headers=headers)
    assert res.status_code == 200, res.text
    assert res.json()["primary_language"] == "hi-IN"

    # The new language must be visible on subsequent fetches.
    after = client.get("/api/patients", headers=headers).json()
    assert after[0]["primary_language"] == "hi-IN"


def test_caregiver_can_change_patient_language():
    headers = _auth_headers("lang_cg@test.local", "secret123", full_name="Lang CG")
    created = client.post(
        "/api/patients",
        json={"name": "Lang Patient", "age": 70, "gender": "Female", "primary_language": "en-IN", "pin": "1234"},
        headers=headers,
    )
    pid = created.json()["id"]
    res = client.put(f"/api/patients/{pid}/language", json={"language_code": "ta-IN"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["primary_language"] == "ta-IN"


def test_language_update_rejects_unsupported_code():
    headers = _admin_headers()
    res = client.put("/api/patients/1/language", json={"language_code": "fr-FR"}, headers=headers)
    assert res.status_code == 422


def test_language_update_forbidden_for_stranger():
    owner = _auth_headers("lang_owner@test.local", "secret123", full_name="Lang Owner")
    stranger = _auth_headers("lang_stranger@test.local", "secret123", full_name="Lang Stranger")
    pid = client.post(
        "/api/patients",
        json={"name": "Guarded", "age": 70, "gender": "Female", "primary_language": "en-IN", "pin": "1234"},
        headers=owner,
    ).json()["id"]
    res = client.put(f"/api/patients/{pid}/language", json={"language_code": "ta-IN"}, headers=stranger)
    assert res.status_code == 403


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


def test_voice_accepts_recorded_audio_with_content_type():
    """Mobile records m4a; the route must accept the clip plus its container."""
    import base64

    headers = _admin_headers()
    clip = base64.b64encode(b"\x00\x00\x00\x18ftypM4A " + b"\x00" * 256).decode()
    response = client.post("/api/voice/interact", json={
        "patient_id": 1,
        "audio_base64": clip,
        "audio_content_type": "audio/m4a",
        "language_code": "ta-IN",
    }, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["reply_text"]


def test_voice_rejects_oversized_audio():
    import base64

    headers = _admin_headers()
    too_big = base64.b64encode(b"\x00" * (4 * 1024 * 1024 + 1)).decode()
    response = client.post("/api/voice/interact", json={
        "patient_id": 1,
        "audio_base64": too_big,
        "audio_content_type": "audio/m4a",
        "language_code": "ta-IN",
    }, headers=headers)
    assert response.status_code == 400


def test_audio_container_mapping():
    """Each client container maps to the filename + mime Saaras receives."""
    from backend.app.services.sarvam_service import SarvamAIService

    assert SarvamAIService._resolve_audio_upload("audio/m4a") == ("input.m4a", "audio/mp4")
    assert SarvamAIService._resolve_audio_upload("audio/webm;codecs=opus") == ("input.webm", "audio/webm")
    assert SarvamAIService._resolve_audio_upload("audio/3gpp") == ("input.3gp", "audio/3gpp")
    # Unknown or missing types fall back to WAV rather than failing the upload.
    assert SarvamAIService._resolve_audio_upload(None) == ("input.wav", "audio/wav")
    assert SarvamAIService._resolve_audio_upload("application/octet-stream") == ("input.wav", "audio/wav")


def test_voice_interact_bengali():
    headers = _admin_headers()
    response = client.post("/api/voice/interact", json={
        "patient_id": 1,
        "question_text": "আমার মেয়ে কে?",
        "language_code": "bn-IN"
    }, headers=headers)
    assert response.status_code == 200
    assert "অনিতা" in response.json()["reply_text"]


def test_voice_interact_assamese():
    headers = _admin_headers()
    response = client.post("/api/voice/interact", json={
        "patient_id": 1,
        "question_text": "মোৰ জীয়েক কোন?",
        "language_code": "as-IN"
    }, headers=headers)
    assert response.status_code == 200
    assert "অনিতা" in response.json()["reply_text"]


def test_sarvam_ner_templates_present():
    from backend.app.services.sarvam_service import LOCALIZED_TEMPLATES, MULTILINGUAL_INTENT_MAP

    assert "as-IN" in LOCALIZED_TEMPLATES
    assert "bn-IN" in LOCALIZED_TEMPLATES
    assert "as" in MULTILINGUAL_INTENT_MAP["food"]
    assert "bn" in MULTILINGUAL_INTENT_MAP["daughter_or_family"]
    # Fallback is localized, not English, for NER languages.
    assert LOCALIZED_TEMPLATES["as-IN"]["fallback"] != LOCALIZED_TEMPLATES["en-IN"]["fallback"]

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


def test_questions_localized_and_reject_unknown_language():
    headers = _admin_headers()

    gk = client.get("/api/cognitive/questions/gk?language_code=hi-IN", headers=headers)
    assert gk.status_code == 200, gk.text
    gk_data = gk.json()
    assert any("\u0900" <= ch <= "\u097f" for ch in gk_data["question"])
    assert gk_data["answer"] in gk_data["options"]

    att = client.get("/api/cognitive/questions/attention?language_code=ta-IN", headers=headers)
    assert att.status_code == 200, att.text
    att_data = att.json()
    assert any("\u0b80" <= ch <= "\u0bff" for ch in att_data["question"])
    assert att_data["answer"] in att_data["options"]

    assert client.get("/api/cognitive/questions/gk?language_code=fr-FR", headers=headers).status_code == 400
    assert client.get("/api/cognitive/questions/attention?language_code=xx-XX", headers=headers).status_code == 400


def test_photo_recognition_round_for_patient_with_memories():
    headers = _admin_headers()
    res = client.get("/api/cognitive/next-photo-game?patient_id=1", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["photo_url"]
    assert data["correct_title"] in data["options"]
    assert len(data["options"]) == 4


def test_photo_recognition_no_memories_returns_400():
    headers = _auth_headers("photonone@test.local", "secret123", full_name="Photo None")
    created = client.post(
        "/api/patients",
        json={"name": "No Memory", "age": 80, "gender": "Female", "primary_language": "en-IN", "pin": "1234"},
        headers=headers,
    )
    pid = created.json()["id"]
    res = client.get(f"/api/cognitive/next-photo-game?patient_id={pid}", headers=headers)
    assert res.status_code == 400


def test_log_session_accepts_photo_recognition_rejects_task_sequencing():
    headers = _admin_headers()
    base = {
        "patient_id": 1,
        "difficulty_level": 1,
        "score": 100,
        "accuracy": 1.0,
        "reaction_time_ms": 2000,
        "mistake_count": 0,
    }
    ok = client.post("/api/cognitive/log-session", json={**base, "game_type": "photo_recognition"}, headers=headers)
    assert ok.status_code == 200, ok.text

    bad = client.post("/api/cognitive/log-session", json={**base, "game_type": "task_sequencing"}, headers=headers)
    assert bad.status_code == 400
