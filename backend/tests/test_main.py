"""
Automated tests: auth, report creation, hype uniqueness, duplicate thresholds,
priority engine, and safety-critical override.
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# In-memory SQLite for tests
TEST_DB = "sqlite:///./test_sos.db"
engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True, scope="function")
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides = {}


client = TestClient(app)


# ── Helpers ───────────────────────────────────────────────────────────────────

def register(email, password, role="student", name="Test User"):
    resp = client.post("/auth/register", json={
        "name": name, "email": email, "password": password, "role": role
    })
    return resp


def login(email, password):
    resp = client.post("/auth/login", json={"email": email, "password": password})
    return resp.json().get("access_token")


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ── Auth tests ────────────────────────────────────────────────────────────────

class TestAuth:
    def test_register_success(self):
        resp = register("a@test.com", "pass1234")
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["email"] == "a@test.com"

    def test_register_duplicate_email(self):
        register("dup@test.com", "pass1234")
        resp = register("dup@test.com", "pass1234")
        assert resp.status_code == 400

    def test_login_success(self):
        register("b@test.com", "pass1234")
        resp = client.post("/auth/login", json={"email": "b@test.com", "password": "pass1234"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self):
        register("c@test.com", "pass1234")
        resp = client.post("/auth/login", json={"email": "c@test.com", "password": "wrong"})
        assert resp.status_code == 401

    def test_get_me(self):
        register("d@test.com", "pass1234")
        token = login("d@test.com", "pass1234")
        resp = client.get("/auth/me", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.json()["email"] == "d@test.com"

    def test_protected_route_without_token(self):
        resp = client.get("/auth/me")
        assert resp.status_code == 401


# ── Report creation tests ─────────────────────────────────────────────────────

class TestReports:
    def test_create_report(self):
        register("reporter@test.com", "pass1234")
        token = login("reporter@test.com", "pass1234")
        resp = client.post(
            "/reports",
            data={"title": "Broken step", "building": "Block A", "description": "Step cracked"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "report" in data
        assert data["report"]["title"] == "Broken step"

    def test_create_report_unauthenticated(self):
        resp = client.post("/reports", data={"title": "test", "building": "Block A"})
        assert resp.status_code == 401

    def test_list_reports(self):
        register("lister@test.com", "pass1234")
        token = login("lister@test.com", "pass1234")
        resp = client.get("/reports", headers=auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_get_own_reports(self):
        register("own@test.com", "pass1234")
        token = login("own@test.com", "pass1234")
        client.post("/reports", data={"title": "My report", "building": "Block B"}, headers=auth_headers(token))
        resp = client.get("/reports/mine", headers=auth_headers(token))
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


# ── Hype uniqueness tests ─────────────────────────────────────────────────────

class TestHype:
    def _setup_report(self):
        register("owner@test.com", "pass1234", name="Owner")
        owner_token = login("owner@test.com", "pass1234")
        register("hyper@test.com", "pass1234", name="Hyper")
        hyper_token = login("hyper@test.com", "pass1234")

        resp = client.post(
            "/reports",
            data={"title": "Test hazard", "building": "Block A"},
            headers=auth_headers(owner_token),
        )
        report_id = resp.json()["report"]["id"]
        return report_id, owner_token, hyper_token

    def test_hype_once(self):
        report_id, _, hyper_token = self._setup_report()
        resp = client.post(f"/reports/{report_id}/hype", headers=auth_headers(hyper_token))
        assert resp.status_code == 200
        assert resp.json()["current_user_hyped"] is True

    def test_hype_twice_fails(self):
        report_id, _, hyper_token = self._setup_report()
        client.post(f"/reports/{report_id}/hype", headers=auth_headers(hyper_token))
        resp = client.post(f"/reports/{report_id}/hype", headers=auth_headers(hyper_token))
        assert resp.status_code == 400

    def test_cannot_hype_own_report(self):
        report_id, owner_token, _ = self._setup_report()
        resp = client.post(f"/reports/{report_id}/hype", headers=auth_headers(owner_token))
        assert resp.status_code == 400

    def test_unhype(self):
        report_id, _, hyper_token = self._setup_report()
        client.post(f"/reports/{report_id}/hype", headers=auth_headers(hyper_token))
        resp = client.delete(f"/reports/{report_id}/hype", headers=auth_headers(hyper_token))
        assert resp.status_code == 200
        assert resp.json()["current_user_hyped"] is False


# ── Priority engine unit tests ────────────────────────────────────────────────

class TestPriorityEngine:
    def test_severity_weight(self):
        from app.services.priority_engine import compute_priority
        from app.models import Report
        from datetime import datetime

        r = Report(severity=5, hype_count=0, recurrence_count=0, is_safety_critical=False,
                   created_at=datetime.utcnow(), building="A")
        bd = compute_priority(r, location_criticality=3)
        assert bd["final_score"] > 30  # High severity should score well

    def test_safety_critical_override(self):
        from app.services.priority_engine import compute_priority
        from app.models import Report
        from datetime import datetime

        r = Report(severity=1, hype_count=0, recurrence_count=0, is_safety_critical=True,
                   created_at=datetime.utcnow(), building="A")
        bd = compute_priority(r, location_criticality=1)
        assert bd["final_score"] >= 90
        assert bd["safety_critical_override"] is True

    def test_hype_cap(self):
        from app.services.priority_engine import _hype_norm, HYPE_CAP
        # Hype beyond cap should not increase score
        score_at_cap = _hype_norm(HYPE_CAP)
        score_beyond = _hype_norm(HYPE_CAP * 10)
        assert abs(score_at_cap - score_beyond) < 0.01  # Effectively the same


# ── Duplicate threshold unit test ─────────────────────────────────────────────

class TestDuplicateDetector:
    def test_cosine_similarity_identical(self):
        from app.services.duplicate_detector import _cosine_similarity
        v = [1.0, 2.0, 3.0]
        assert _cosine_similarity(v, v) == pytest.approx(1.0, abs=1e-5)

    def test_cosine_similarity_orthogonal(self):
        from app.services.duplicate_detector import _cosine_similarity
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert _cosine_similarity(a, b) == pytest.approx(0.0, abs=1e-5)

    def test_duplicate_threshold_constant(self):
        from app.services.duplicate_detector import DUPLICATE_THRESHOLD, POSSIBLE_THRESHOLD
        assert DUPLICATE_THRESHOLD == 0.85
        assert POSSIBLE_THRESHOLD == 0.70
        assert DUPLICATE_THRESHOLD > POSSIBLE_THRESHOLD
