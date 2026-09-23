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
    response = client.post("/api/auth/verify-pin", json={"pin": "1234", "patient_id": 1})
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_verify_pin_failure():
    response = client.post("/api/auth/verify-pin", json={"pin": "9999", "patient_id": 1})
    assert response.status_code == 401
    assert "Incorrect" in response.json()["detail"]

def test_verify_pin_invalid_patient():
    response = client.post("/api/auth/verify-pin", json={"pin": "1234", "patient_id": 99999})
    assert response.status_code == 404

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

def test_memories_crud_flow():
    # 1. List existing memories
    list_res = client.get("/api/memories?patient_id=1")
    assert list_res.status_code == 200
    initial_count = len(list_res.json())

    # 2. Create a new memory
    create_res = client.post(
        "/api/memories",
        data={
            "patient_id": 1,
            "category": "Person",
            "title": "Dr. Varma",
            "details": "Family physician who visits on Sundays.",
            "relationship": "Doctor"
        }
    )
    assert create_res.status_code == 200
    new_memory = create_res.json()
    assert new_memory["title"] == "Dr. Varma"
    memory_id = new_memory["id"]

    # 3. Update the memory
    update_res = client.put(
        f"/api/memories/{memory_id}",
        data={
            "title": "Dr. Varma (Physician)",
            "details": "Family physician who visits on Sunday mornings."
        }
    )
    assert update_res.status_code == 200
    updated_memory = update_res.json()
    assert updated_memory["title"] == "Dr. Varma (Physician)"

    # 4. Delete the memory
    delete_res = client.delete(f"/api/memories/{memory_id}")
    assert delete_res.status_code == 200
    assert delete_res.json()["success"] is True

def test_tasks_crud_and_reset_flow():
    # 1. List tasks
    list_res = client.get("/api/routines/tasks?patient_id=1")
    assert list_res.status_code == 200

    # 2. Add a new task
    add_res = client.post(
        "/api/routines/tasks",
        json={
            "patient_id": 1,
            "title": "Evening Pranayama Breathing",
            "task_time": "18:00",
            "category": "Exercise"
        }
    )
    assert add_res.status_code == 200
    task_data = add_res.json()
    assert task_data["title"] == "Evening Pranayama Breathing"
    task_id = task_data["id"]
    assert task_data["done"] is False

    listed = client.get("/api/routines/tasks?patient_id=1")
    assert listed.status_code == 200
    assert any(t["id"] == task_id for t in listed.json())

    # 3. Toggle task completion
    toggle_res = client.post(f"/api/routines/tasks/{task_id}/toggle")
    assert toggle_res.status_code == 200
    assert toggle_res.json()["done"] is True

    after_toggle = client.get("/api/routines/tasks?patient_id=1")
    matching = next(t for t in after_toggle.json() if t["id"] == task_id)
    assert matching["done"] is True

    # 4. Reset tasks for the day
    reset_res = client.post("/api/routines/tasks/reset?patient_id=1")
    assert reset_res.status_code == 200
    assert reset_res.json()["success"] is True

    after_reset = client.get("/api/routines/tasks?patient_id=1")
    matching = next(t for t in after_reset.json() if t["id"] == task_id)
    assert matching["done"] is False

    # 5. Delete task
    delete_res = client.delete(f"/api/routines/tasks/{task_id}")
    assert delete_res.status_code == 200
    assert delete_res.json()["success"] is True

    after_delete = client.get("/api/routines/tasks?patient_id=1")
    assert all(t["id"] != task_id for t in after_delete.json())
