from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_list_patients():
    response = client.get("/api/patients")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert data[0]["name"] == "Meenakshi"
    assert data[1]["name"] == "Raman"

def test_verify_pin_success():
    response = client.post("/api/auth/verify-pin", json={"pin": "1234"})
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_verify_pin_failure():
    response = client.post("/api/auth/verify-pin", json={"pin": "9999"})
    assert response.status_code == 401

def test_dda_next_game():
    response = client.get("/api/cognitive/next-game?patient_id=1")
    assert response.status_code == 200
    data = response.json()
    assert "sequence" in data
    assert "options" in data
    assert data["difficulty_level"] >= 1

def test_caregiver_analytics():
    response = client.get("/api/caregiver/analytics?patient_id=1")
    assert response.status_code == 200
    data = response.json()
    assert "cognitive_stability_score" in data
    assert "routine_completion_pct" in data

def test_voice_interact_tamil():
    response = client.post("/api/voice/interact", json={
        "patient_id": 1,
        "question_text": "என் மகள் யார்?",
        "language_code": "ta-IN"
    })
    assert response.status_code == 200
    data = response.json()
    assert "அனிதா" in data["reply_text"]
