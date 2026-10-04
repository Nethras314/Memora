from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core import database as db_module

# Force demo-mode store for deterministic tests even if env keys exist.
db_module.supabase_client = None
db_module.supabase_admin_client = None
db_module.is_supabase_configured = lambda: False

from backend.app.services import analytics_service as svc

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


def _session(accuracy, latency, days_ago=0, game_type="sequence_memory", score=80):
    return {
        "id": 1,
        "patient_id": 1,
        "game_type": game_type,
        "difficulty_level": 1,
        "score": score,
        "accuracy": accuracy,
        "reaction_time_ms": latency,
        "mistake_count": 0,
        "created_at": datetime.now() - timedelta(days=days_ago),
    }


# ---------------------------------------------------------------------------
# Pure metric-spine unit tests
# ---------------------------------------------------------------------------
def test_composite_renormalizes_on_single_domain():
    idx, insufficient, w = svc.composite_index(80.0, None, None, None)
    assert idx == 80.0
    assert insufficient is True
    assert w["games"] == 1.0


def test_composite_full_domains_weighted():
    idx, insufficient, w = svc.composite_index(80.0, 50.0, 100.0, 90.0)
    assert insufficient is False
    # 0.50*80 + 0.20*50 + 0.15*100 + 0.15*90 = 40 + 10 + 15 + 13.5 = 78.5
    assert idx == 78.5
    assert abs(sum(w.values()) - 1.0) < 1e-9


def test_rag_thresholds():
    assert svc.rag_status(90) == "green"
    assert svc.rag_status(70) == "amber"
    assert svc.rag_status(50) == "red"
    assert svc.rag_status(None) == "amber"


def test_domain_breakdown_memory_from_accuracy():
    sessions = [
        _session(0.9, 3000, game_type="sequence_memory"),
        _session(0.7, 3000, game_type="sequence_memory"),
    ]
    breakdown = svc.domain_breakdown(sessions, [], [], [])
    memory = next(d for d in breakdown if d["domain"] == "memory")
    assert memory["score"] == 80.0
    assert memory["sample_count"] == 2


def test_decline_velocity_negative_for_declining():
    base = datetime.now().date()
    series = []
    for i in range(10):
        series.append({
            "date": base - timedelta(days=(10 - i)),
            "index": 90.0 - i * 2,
            "score": 90 - i,
            "latency_ms": 3000,
        })
    v = svc.decline_velocity(series)
    assert v is not None and v < 0


def test_index_delta_recent_vs_prior():
    base = datetime.now().date()
    series = []
    for d in range(28, 7, -1):  # prior 21 days, index 80
        series.append({"date": base - timedelta(days=d), "index": 80.0, "score": 80, "latency_ms": 3000})
    for d in range(7, 0, -1):  # recent 7 days, index 70
        series.append({"date": base - timedelta(days=d), "index": 70.0, "score": 70, "latency_ms": 3000})
    assert svc.index_delta(series) == -10.0


# ---------------------------------------------------------------------------
# Endpoint smoke tests
# ---------------------------------------------------------------------------
def test_glance_endpoint():
    h = _admin()
    res = client.get("/api/caregiver/glance?patient_id=1", headers=h)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "status" in data
    assert "index" in data
    assert "routine_pct" in data
    assert data["status"] in ("green", "amber", "red")


def test_trend_endpoint_validates_window():
    h = _admin()
    ok = client.get("/api/caregiver/trend?patient_id=1&window_days=30", headers=h)
    assert ok.status_code == 200
    assert isinstance(ok.json(), list)

    assert client.get("/api/caregiver/trend?patient_id=1&window_days=45", headers=h).status_code == 400


def test_export_csv():
    h = _admin()
    res = client.get("/api/caregiver/export?patient_id=1&format=csv", headers=h)
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "patient_id" in res.text


def test_patients_summary_admin():
    h = _admin()
    res = client.get("/api/caregiver/patients/summary", headers=h)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_analytics_includes_new_fields():
    h = _admin()
    res = client.get("/api/caregiver/analytics?patient_id=1", headers=h)
    assert res.status_code == 200
    data = res.json()
    for key in ("index", "status", "domain_breakdown", "weights", "trend_30d", "index_delta"):
        assert key in data
    assert data["status"] in ("green", "amber", "red")
    assert data["weights"]["games"] > 0
