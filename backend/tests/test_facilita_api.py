"""Regression checks for health, auth, protected routes, and utility generation."""
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
pytestmark = pytest.mark.skipif(not BASE_URL, reason="REACT_APP_BACKEND_URL is not set")


@pytest.fixture
def session():
    return requests.Session()


@pytest.fixture
def admin_session(session):
    response = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@facilita.ai", "password": "Facilita@123", "name": ""
    }, timeout=20)
    assert response.status_code == 200, response.text
    session.headers["Authorization"] = f"Bearer {response.json()['token']}"
    return session


def test_health(session):
    response = session.get(f"{BASE_URL}/api/", timeout=20)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_google_is_explicitly_unconfigured(session):
    response = session.get(f"{BASE_URL}/api/auth/google", timeout=20)
    assert response.status_code == 200
    assert response.json()["configured"] is False


def test_utility_generation(session):
    password = session.post(f"{BASE_URL}/api/generate", json={
        "tool": "password_gen", "payload": {"length": 12, "letters": True, "numbers": True, "symbols": True}
    }, timeout=20)
    assert password.status_code == 200
    assert len(password.json()["result"]) == 12
    percentage = session.post(f"{BASE_URL}/api/generate", json={
        "tool": "percentage_calc", "payload": {"value": 500, "percentage": 20}
    }, timeout=20)
    assert percentage.status_code == 200
    assert percentage.json()["result"] == "100.00"


def test_admin_routes_and_favorites(admin_session):
    stats = admin_session.get(f"{BASE_URL}/api/admin/stats", timeout=20)
    assert stats.status_code == 200
    assert "users" in stats.json() and "generations" in stats.json()
    add = admin_session.post(f"{BASE_URL}/api/favorites", json={"tool_id": "whatsapp"}, timeout=20)
    assert add.status_code == 200 and add.json()["ok"] is True
    favorites = admin_session.get(f"{BASE_URL}/api/favorites", timeout=20)
    assert any(item["tool_id"] == "whatsapp" for item in favorites.json())
    assert admin_session.delete(f"{BASE_URL}/api/favorites/whatsapp", timeout=20).status_code == 200


def test_history_requires_auth(session):
    response = session.get(f"{BASE_URL}/api/history", timeout=20)
    assert response.status_code == 401


def test_history_list_and_delete(admin_session):
    # Create a usage record via password_gen? No, password_gen doesn't persist. Insert via correct_pt requires LLM.
    # Just verify list works and delete of unknown id returns ok
    hist = admin_session.get(f"{BASE_URL}/api/history", timeout=20)
    assert hist.status_code == 200
    assert isinstance(hist.json(), list)
    # Delete a fake id should still return ok (idempotent)
    d = admin_session.delete(f"{BASE_URL}/api/history/nonexistent-id", timeout=20)
    assert d.status_code == 200
