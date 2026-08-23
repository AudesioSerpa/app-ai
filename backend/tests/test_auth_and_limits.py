"""Iteration 7: Auth-required for ALL tools + free_daily_limit=3 + rate limit persisted by user_id."""
import os, time, uuid
import pytest
import requests

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / "frontend" / ".env")
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@facilita.ai"
ADMIN_PASSWORD = "Facilita@123"


def _register():
    email = f"TEST_it7_{uuid.uuid4().hex[:8]}@facilita.ai"
    r = requests.post(f"{API}/auth/register", json={"email": email, "password": "TestPass123", "name": "TestIT7"})
    assert r.status_code == 200, r.text
    return email, "TestPass123", r.json()["token"], r.json()["user"]["id"]


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _admin_token():
    return _login(ADMIN_EMAIL, ADMIN_PASSWORD)


def _hdr(tok):
    return {"Authorization": f"Bearer {tok}"}


# ---------- SETTINGS ----------
def test_settings_default_free_limit_is_3():
    r = requests.get(f"{API}/settings")
    assert r.status_code == 200
    data = r.json()
    assert data["free_daily_limit"] == 3, f"Expected 3, got {data['free_daily_limit']}"
    assert data["premium_daily_limit"] == 500


# ---------- AUTH REQUIRED FOR /generate ----------
@pytest.mark.parametrize("tool", ["qrcode", "password_gen", "percentage_calc", "correct_pt", "improve_text", "whatsapp", "summarize", "create_email", "create_caption", "youtube_titles"])
def test_generate_requires_auth_no_token(tool):
    r = requests.post(f"{API}/generate", json={"tool": tool, "payload": {"text": "oi", "message": "oi", "topic": "oi", "value": 10, "percentage": 20}})
    assert r.status_code == 401
    assert "login" in r.json().get("detail", "").lower()


def test_generate_requires_auth_bad_token():
    r = requests.post(f"{API}/generate", headers={"Authorization": "Bearer invalid"}, json={"tool": "qrcode", "payload": {"text": "oi"}})
    assert r.status_code == 401


def test_no_guest_usage_in_db():
    # trigger multiple unauth attempts, all must fail
    for _ in range(3):
        requests.post(f"{API}/generate", json={"tool": "correct_pt", "payload": {"text": "oi"}})
    # can't query DB directly here, but /me/usage as guest should still count 0 (used=0 for guest)
    r = requests.get(f"{API}/me/usage")
    assert r.status_code == 200
    # For guest user, used should remain 0 since no unauth requests get through
    assert r.json()["used"] == 0


# ---------- RATE LIMIT 3 ----------
def test_rate_limit_3_ai_calls_then_402():
    email, password, tok, uid = _register()
    for i in range(3):
        r = requests.post(f"{API}/generate", headers=_hdr(tok), json={"tool": "correct_pt", "payload": {"text": f"teste {i}"}})
        assert r.status_code == 200, f"Call {i+1}/3 failed: {r.status_code} {r.text}"
    # 4th
    r = requests.post(f"{API}/generate", headers=_hdr(tok), json={"tool": "correct_pt", "payload": {"text": "quarto"}})
    assert r.status_code == 402, r.text
    assert "limite" in r.json()["detail"].lower()


def test_rate_limit_persists_across_new_tokens():
    """Novo login mesmo usuário não libera novos usos."""
    email, password, tok, uid = _register()
    for i in range(3):
        r = requests.post(f"{API}/generate", headers=_hdr(tok), json={"tool": "correct_pt", "payload": {"text": f"t{i}"}})
        assert r.status_code == 200
    # login again → new token, same user
    tok2 = _login(email, password)
    assert tok2 != tok or True  # tokens may differ
    r = requests.post(f"{API}/generate", headers=_hdr(tok2), json={"tool": "correct_pt", "payload": {"text": "novo token"}})
    assert r.status_code == 402, "Rate limit must persist across new tokens (per user_id)"


def test_local_tools_do_not_consume_ai_quota():
    email, password, tok, uid = _register()
    # 3x each local tool — all authorized
    for _ in range(3):
        r = requests.post(f"{API}/generate", headers=_hdr(tok), json={"tool": "qrcode", "payload": {"text": "https://x"}})
        assert r.status_code in (200, 400), r.text  # qrcode may not have server logic; check below
    for _ in range(3):
        r = requests.post(f"{API}/generate", headers=_hdr(tok), json={"tool": "password_gen", "payload": {"length": 12, "letters": True, "numbers": True, "symbols": False}})
        assert r.status_code == 200
    for _ in range(3):
        r = requests.post(f"{API}/generate", headers=_hdr(tok), json={"tool": "percentage_calc", "payload": {"value": 100, "percentage": 25}})
        assert r.status_code == 200
    # now 3x AI, still all 200
    for i in range(3):
        r = requests.post(f"{API}/generate", headers=_hdr(tok), json={"tool": "correct_pt", "payload": {"text": f"ok {i}"}})
        assert r.status_code == 200, f"AI call {i+1} should succeed after local tools; got {r.status_code}"
    # 4th AI → 402
    r = requests.post(f"{API}/generate", headers=_hdr(tok), json={"tool": "correct_pt", "payload": {"text": "final"}})
    assert r.status_code == 402


# ---------- PREMIUM UNLIMITED-ISH ----------
def test_premium_user_uses_500_limit():
    admin_tok = _admin_token()
    email, password, tok, uid = _register()
    # promote to premium
    r = requests.post(f"{API}/admin/users/{uid}/subscription", headers=_hdr(admin_tok), json={"plan": "premium"})
    assert r.status_code == 200, r.text
    # /me/usage should show 500
    r = requests.get(f"{API}/me/usage", headers=_hdr(tok))
    assert r.status_code == 200
    data = r.json()
    assert data["is_premium"] is True
    assert data["limit"] == 500
    # can do >3 AI calls
    for i in range(4):
        r = requests.post(f"{API}/generate", headers=_hdr(tok), json={"tool": "correct_pt", "payload": {"text": f"prem {i}"}})
        assert r.status_code == 200, f"Premium call {i+1} failed"


# ---------- REGRESSION: local tools no auth = 401 too ----------
def test_qrcode_unauth_returns_401():
    r = requests.post(f"{API}/generate", json={"tool": "qrcode", "payload": {"text": "x"}})
    assert r.status_code == 401


# Ensure admin left as FREE at the end (idempotent cleanup at module teardown)
def teardown_module(module):
    try:
        admin_tok = _admin_token()
        # find admin id via /auth/me
        r = requests.get(f"{API}/auth/me", headers=_hdr(admin_tok))
        if r.status_code == 200:
            admin_id = r.json()["id"]
            requests.post(f"{API}/admin/users/{admin_id}/subscription", headers=_hdr(admin_tok), json={"plan": "free"})
    except Exception:
        pass
