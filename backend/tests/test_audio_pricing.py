"""Tests for audio_gen (503 without ELEVENLABS_API_KEY), /api/pricing, /api/me/usage, image validation."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://smart-tools-49.preview.emergentagent.com").rstrip("/")


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "admin@facilita.ai", "password": "Facilita@123"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["user"]["role"] == "admin"
    return d["token"]


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ---------------- ROOT / HEALTH ----------------
def test_root_ok():
    r = requests.get(f"{BASE_URL}/api/")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


# ---------------- /api/pricing ----------------
def test_pricing_public_snapshot():
    r = requests.get(f"{BASE_URL}/api/pricing")
    assert r.status_code == 200
    d = r.json()
    assert d["usd_to_brl"] == 5.10
    assert d["fx_safety_buffer"] == 0.10
    assert d["target_gross_margin"] == 0.70
    assert d["mp_fee_rate"] == 0.05
    assert d["audio"]["model"] == "eleven_flash_v2_5"
    assert d["audio"]["usd_per_char"] == 0.00005
    assert d["audio"]["free_daily_seconds"] == 60
    assert d["audio"]["free_max_seconds_per_gen"] == 60
    assert d["image"]["usd_per_image"] == 0.003
    assert d["image"]["max_prompt_chars"] == 1000
    # No secret keys exposed
    body = r.text
    for forbidden in ("ELEVENLABS_API_KEY", "FAL_KEY", "MP_ACCESS_TOKEN", "JWT_SECRET"):
        assert forbidden not in body


# ---------------- /api/me/usage ----------------
def test_me_usage_anonymous_has_audio_fields():
    r = requests.get(f"{BASE_URL}/api/me/usage")
    assert r.status_code == 200
    d = r.json()
    for k in ("audio_used_seconds", "audio_limit_seconds", "audio_remaining_seconds", "audio_max_seconds_per_gen"):
        assert k in d
    assert d["audio_limit_seconds"] == 60
    assert d["audio_max_seconds_per_gen"] == 60


def test_me_usage_authenticated_free_limits(auth_headers):
    r = requests.get(f"{BASE_URL}/api/me/usage", headers=auth_headers)
    assert r.status_code == 200
    d = r.json()
    # Admin is not premium by default
    assert d["audio_limit_seconds"] in (60, 300)  # 60 if free, 300 if premium
    assert d["audio_max_seconds_per_gen"] == 60
    assert isinstance(d["audio_used_seconds"], (int, float))


# ---------------- /api/generate-audio without ELEVENLABS_API_KEY ----------------
def test_generate_audio_no_key_returns_503(auth_headers):
    # Snapshot audio_used_seconds BEFORE
    before = requests.get(f"{BASE_URL}/api/me/usage", headers=auth_headers).json()["audio_used_seconds"]

    r = requests.post(f"{BASE_URL}/api/generate-audio", json={"text": "Olá, teste de áudio."}, headers=auth_headers)
    assert r.status_code == 503, f"Expected 503 without ELEVENLABS_API_KEY, got {r.status_code}: {r.text}"
    detail = r.json().get("detail", "")
    assert "Geração de áudio não configurada" in detail or "não configurada" in detail.lower()
    # No secret in response body
    body = r.text
    key_value = os.environ.get("ELEVENLABS_API_KEY", "")
    if key_value:
        assert key_value not in body

    # Verify no reservation created
    after = requests.get(f"{BASE_URL}/api/me/usage", headers=auth_headers).json()["audio_used_seconds"]
    assert after == before, f"audio_used_seconds changed! before={before} after={after}"


def test_generate_audio_empty_text_rejected(auth_headers):
    r = requests.post(f"{BASE_URL}/api/generate-audio", json={"text": ""}, headers=auth_headers)
    assert r.status_code in (400, 422), r.text


def test_generate_audio_without_jwt_returns_401():
    r = requests.post(f"{BASE_URL}/api/generate-audio", json={"text": "teste"})
    assert r.status_code == 401


def test_generate_audio_too_long_text(auth_headers):
    # 3001 chars — pydantic max_length=3000 should reject as 422 (before hitting endpoint logic)
    text = "a" * 3001
    r = requests.post(f"{BASE_URL}/api/generate-audio", json={"text": text}, headers=auth_headers)
    # Pydantic validation returns 422; endpoint's own check returns 413
    assert r.status_code in (413, 422), r.text


# ---------------- /api/generate-image validation ----------------
def test_generate_image_prompt_too_short(auth_headers):
    r = requests.post(f"{BASE_URL}/api/generate-image", json={"prompt": "hi"}, headers=auth_headers)
    assert r.status_code == 422


def test_generate_image_prompt_too_long(auth_headers):
    r = requests.post(f"{BASE_URL}/api/generate-image", json={"prompt": "a" * 1001}, headers=auth_headers)
    assert r.status_code == 422


def test_generate_image_prompt_999_accepted_validation(auth_headers):
    # 999 chars is accepted by pydantic; won't call fal if FAL_KEY missing → could be 503 or 200/502.
    # We just verify it is NOT 422 (validation passed).
    r = requests.post(f"{BASE_URL}/api/generate-image", json={"prompt": "a" * 999}, headers=auth_headers)
    assert r.status_code != 422, f"999 chars should not be rejected by validation, got {r.status_code}: {r.text}"


# ---------------- Auth ----------------
def test_admin_login_returns_role_admin():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "admin@facilita.ai", "password": "Facilita@123"})
    assert r.status_code == 200
    d = r.json()
    assert d["user"]["role"] == "admin"
    assert isinstance(d["token"], str) and len(d["token"]) > 20
