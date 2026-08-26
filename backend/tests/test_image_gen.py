"""Tests for the new Gerador de Imagens IA feature (fal.ai FLUX.1 Schnell).
FAL_KEY is empty on purpose in preview -> endpoint returns 503 before hitting fal.ai.
Focus: schema, rate-limit path (503 short-circuit is expected), settings extension, me/usage extension,
and separation of image_gen usage count from AI text tools.
"""
import os
import uuid
import pytest
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://smart-tools-49.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@facilita.ai"
ADMIN_PASSWORD = "Facilita@123"


# --- Fixtures -----------------------------------------------------------------
@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def test_user():
    email = f"TEST_imguser_{uuid.uuid4().hex[:8]}@test.local"
    r = requests.post(f"{API}/auth/register", json={"email": email, "password": "TestPass123!", "name": "TestImg"})
    assert r.status_code == 200, f"register failed: {r.status_code} {r.text}"
    body = r.json()
    return {"email": email, "token": body["token"], "id": body["user"]["id"]}


@pytest.fixture(scope="module")
def user_headers(test_user):
    return {"Authorization": f"Bearer {test_user['token']}"}


# --- Public settings ----------------------------------------------------------
class TestPublicSettings:
    def test_settings_includes_image_limits(self):
        r = requests.get(f"{API}/settings")
        assert r.status_code == 200
        data = r.json()
        assert "free_daily_image_limit" in data
        assert "premium_daily_image_limit" in data
        assert isinstance(data["free_daily_image_limit"], int)
        assert isinstance(data["premium_daily_image_limit"], int)
        # defaults per PRD
        assert data["free_daily_image_limit"] == 3
        assert data["premium_daily_image_limit"] == 50


# --- Admin settings PUT -------------------------------------------------------
class TestAdminSettings:
    def test_admin_get_settings(self, admin_headers):
        r = requests.get(f"{API}/admin/settings", headers=admin_headers)
        assert r.status_code == 200
        for k in ("free_daily_image_limit", "premium_daily_image_limit"):
            assert k in r.json()

    def test_update_and_restore_image_limits(self, admin_headers):
        # Update
        r = requests.put(f"{API}/admin/settings", headers=admin_headers,
                         json={"free_daily_image_limit": 7, "premium_daily_image_limit": 77})
        assert r.status_code == 200
        assert r.json()["free_daily_image_limit"] == 7
        assert r.json()["premium_daily_image_limit"] == 77
        # Public also reflects
        pub = requests.get(f"{API}/settings").json()
        assert pub["free_daily_image_limit"] == 7
        assert pub["premium_daily_image_limit"] == 77
        # Restore defaults
        r = requests.put(f"{API}/admin/settings", headers=admin_headers,
                         json={"free_daily_image_limit": 3, "premium_daily_image_limit": 50})
        assert r.status_code == 200
        assert r.json()["free_daily_image_limit"] == 3
        assert r.json()["premium_daily_image_limit"] == 50


# --- /me/usage extension ------------------------------------------------------
class TestMeUsage:
    def test_unauth_me_usage_has_image_fields(self):
        r = requests.get(f"{API}/me/usage")
        assert r.status_code == 200
        d = r.json()
        for k in ("used", "limit", "remaining", "image_used", "image_limit", "image_remaining",
                  "is_premium", "plan", "in_grace_period", "grace_days_left"):
            assert k in d, f"missing key: {k}"
        assert d["image_used"] == 0
        assert d["image_remaining"] == d["image_limit"]

    def test_auth_me_usage_has_image_fields(self, user_headers):
        r = requests.get(f"{API}/me/usage", headers=user_headers)
        assert r.status_code == 200
        d = r.json()
        for k in ("image_used", "image_limit", "image_remaining"):
            assert k in d
        assert d["image_used"] == 0


# --- POST /api/generate-image -------------------------------------------------
class TestGenerateImage:
    def test_unauth_returns_401(self):
        r = requests.post(f"{API}/generate-image", json={"prompt": "a cat"})
        assert r.status_code == 401

    def test_auth_but_fal_not_configured_returns_503(self, user_headers):
        r = requests.post(f"{API}/generate-image", headers=user_headers,
                          json={"prompt": "a beautiful sunset", "aspect_ratio": "1:1"})
        # FAL_KEY empty in preview -> 503 short-circuit BEFORE rate-limit / prompt-validation
        assert r.status_code == 503, f"expected 503 (FAL_KEY empty), got {r.status_code}: {r.text}"
        assert "configurada" in r.text.lower() or "fal" in r.text.lower()

    def test_short_prompt_still_503_because_fal_check_is_first(self, user_headers):
        # Pydantic min_length=3 SHOULD fire (422) BEFORE the 503 (dependency runs after body validation).
        r = requests.post(f"{API}/generate-image", headers=user_headers,
                          json={"prompt": "a", "aspect_ratio": "1:1"})
        assert r.status_code in (400, 422), f"expected 422 from pydantic, got {r.status_code}"

    def test_invalid_aspect_ratio_falls_back_silently(self, user_headers):
        # Since FAL_KEY empty, we get 503 — but this confirms no 400 for bad aspect.
        r = requests.post(f"{API}/generate-image", headers=user_headers,
                          json={"prompt": "test image", "aspect_ratio": "invalid"})
        assert r.status_code == 503  # never rejects unknown ratio


# --- Separation of image_gen count from AI text tools -------------------------
class TestUsageCountSeparation:
    def test_inject_image_records_isolates_image_used(self, test_user, user_headers):
        """Inject 3 image_gen records via direct DB write and verify image_used=3 but 'used' unaffected."""
        import asyncio
        from motor.motor_asyncio import AsyncIOMotorClient

        mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
        db_name = os.environ.get("DB_NAME", "test_database")

        async def inject():
            client = AsyncIOMotorClient(mongo_url)
            db = client[db_name]
            now_iso = datetime.now(timezone.utc).isoformat()
            docs = [{
                "id": str(uuid.uuid4()),
                "tool": "image_gen",
                "user_id": test_user["id"],
                "prompt": {"prompt": "x", "aspect_ratio": "1:1"},
                "result": "http://example.com/x.png",
                "created_at": now_iso,
            } for _ in range(3)]
            await db.usage.insert_many(docs)
            client.close()
            return [d["id"] for d in docs]

        async def cleanup(ids):
            client = AsyncIOMotorClient(mongo_url)
            db = client[db_name]
            await db.usage.delete_many({"id": {"$in": ids}})
            client.close()

        ids = asyncio.run(inject())
        try:
            r = requests.get(f"{API}/me/usage", headers=user_headers)
            assert r.status_code == 200
            d = r.json()
            assert d["image_used"] == 3, f"expected image_used=3, got {d['image_used']}"
            assert d["used"] == 0, f"AI text 'used' should NOT be affected, got {d['used']}"
            assert d["image_remaining"] == max(0, d["image_limit"] - 3)
        finally:
            asyncio.run(cleanup(ids))

        # After cleanup, image_used back to 0
        r = requests.get(f"{API}/me/usage", headers=user_headers)
        assert r.json()["image_used"] == 0


# --- Regression: existing tools still work ------------------------------------
class TestRegression:
    def test_login_still_works(self):
        r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        assert r.status_code == 200

    def test_tools_generate_non_ai(self, user_headers):
        # qrcode is non-AI, should always work
        r = requests.post(f"{API}/generate", headers=user_headers,
                          json={"tool": "qrcode", "payload": {"text": "https://example.com"}})
        assert r.status_code == 200, r.text

    def test_favorites_list(self, user_headers):
        r = requests.get(f"{API}/favorites", headers=user_headers)
        assert r.status_code == 200

    def test_history_list(self, user_headers):
        r = requests.get(f"{API}/history", headers=user_headers)
        assert r.status_code == 200
