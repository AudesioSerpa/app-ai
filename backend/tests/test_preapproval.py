"""Backend tests for Mercado Pago Preapproval migration (iteration 5)."""
import os
import time
import uuid
import hmac
import hashlib
from datetime import datetime, timezone, timedelta

import pytest
import requests
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path

# Load backend .env to get MONGO_URL / secret (backend/.env is the source of truth)
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if os.environ.get("REACT_APP_BACKEND_URL") else None
if not BASE_URL:
    # fallback to frontend .env
    load_dotenv(Path(__file__).resolve().parents[2] / "frontend" / ".env")
    BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")

MP_WEBHOOK_SECRET = os.environ.get("MP_WEBHOOK_SECRET", "")
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

ADMIN_EMAIL = "admin@facilita.ai"
ADMIN_PASSWORD = "Facilita@123"


# ---------- helpers ----------
def _register():
    email = f"TEST_pre_{uuid.uuid4().hex[:8]}@example.com"
    r = requests.post(f"{BASE_URL}/api/auth/register", json={"email": email, "password": "Passw0rd!", "name": "Pre Tester"})
    assert r.status_code == 200, r.text
    return email, r.json()["token"], r.json()["user"]["id"]


def _login(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _auth(t):
    return {"Authorization": f"Bearer {t}"}


def _sign(data_id: str, request_id: str, ts: str) -> str:
    manifest = f"id:{data_id.lower()};request-id:{request_id};ts:{ts};"
    return hmac.new(MP_WEBHOOK_SECRET.encode(), manifest.encode(), hashlib.sha256).hexdigest()


# ---------- Preapproval creation & reuse ----------
class TestCheckoutPreapproval:
    def test_creates_preapproval(self):
        _, token, _ = _register()
        r = requests.post(f"{BASE_URL}/api/checkout/premium", headers=_auth(token))
        assert r.status_code == 200, r.text
        data = r.json()
        assert "preapproval_id" in data and data["preapproval_id"]
        assert "init_point" in data and data["init_point"].startswith("https://www.mercadopago.com.br/subscriptions/checkout?preapproval_id=")

    def test_reuses_pending_preapproval(self):
        _, token, _ = _register()
        r1 = requests.post(f"{BASE_URL}/api/checkout/premium", headers=_auth(token))
        assert r1.status_code == 200
        first_id = r1.json()["preapproval_id"]
        r2 = requests.post(f"{BASE_URL}/api/checkout/premium", headers=_auth(token))
        assert r2.status_code == 200
        # should be reused OR return same id
        assert r2.json()["preapproval_id"] == first_id or r2.json().get("reused") is True


# ---------- GET /api/subscription ----------
class TestGetSubscription:
    def test_unauth_401(self):
        r = requests.get(f"{BASE_URL}/api/subscription")
        assert r.status_code == 401

    def test_free_user_defaults(self):
        _, token, _ = _register()
        r = requests.get(f"{BASE_URL}/api/subscription", headers=_auth(token))
        assert r.status_code == 200
        d = r.json()
        assert d["plan"] == "free"
        assert d["is_premium"] is False
        assert d["preapproval_id"] is None

    def test_after_checkout_has_preapproval(self):
        _, token, _ = _register()
        c = requests.post(f"{BASE_URL}/api/checkout/premium", headers=_auth(token))
        assert c.status_code == 200
        r = requests.get(f"{BASE_URL}/api/subscription", headers=_auth(token))
        assert r.status_code == 200
        d = r.json()
        assert d["preapproval_id"] == c.json()["preapproval_id"]
        assert d["preapproval_status"] in {"pending", "authorized"}


# ---------- Cancel ----------
class TestCancelSubscription:
    def test_cancel_without_preapproval_404(self):
        _, token, _ = _register()
        r = requests.post(f"{BASE_URL}/api/subscription/cancel", headers=_auth(token))
        assert r.status_code == 404

    def test_cancel_after_checkout(self):
        _, token, _ = _register()
        requests.post(f"{BASE_URL}/api/checkout/premium", headers=_auth(token))
        r = requests.post(f"{BASE_URL}/api/subscription/cancel", headers=_auth(token))
        # MP may accept cancel of a pending preapproval; accept 200 or 502 (MP quirk)
        assert r.status_code in (200, 502), r.text
        if r.status_code == 200:
            g = requests.get(f"{BASE_URL}/api/subscription", headers=_auth(token))
            assert g.status_code == 200
            assert g.json()["preapproval_status"] in {"cancelled", "canceled"}
            assert g.json()["plan"] == "canceled"


# ---------- Webhook HMAC ----------
class TestWebhookHMAC:
    def test_invalid_signature_401(self):
        r = requests.post(
            f"{BASE_URL}/api/mercadopago/webhook?type=subscription_preapproval&data.id=fake",
            headers={"x-signature": "ts=1,v1=deadbeef", "x-request-id": "req-1"},
            json={"type": "subscription_preapproval", "data": {"id": "fake"}},
        )
        assert r.status_code == 401
        assert "assinatura" in r.text.lower() or "inv" in r.text.lower()

    def test_no_signature_401(self):
        r = requests.post(
            f"{BASE_URL}/api/mercadopago/webhook?type=subscription_preapproval&data.id=fake",
            json={"type": "subscription_preapproval", "data": {"id": "fake"}},
        )
        assert r.status_code == 401

    def test_valid_signature_returns_200(self):
        assert MP_WEBHOOK_SECRET, "MP_WEBHOOK_SECRET must be set"
        data_id = "fake"
        req_id = "req-test-" + uuid.uuid4().hex[:6]
        ts = str(int(time.time()))
        v1 = _sign(data_id, req_id, ts)
        r = requests.post(
            f"{BASE_URL}/api/mercadopago/webhook?type=subscription_preapproval&data.id={data_id}",
            headers={"x-signature": f"ts={ts},v1={v1}", "x-request-id": req_id, "Content-Type": "application/json"},
            json={"type": "subscription_preapproval", "data": {"id": data_id}},
        )
        assert r.status_code == 200, r.text
        assert r.json().get("received") is True


# ---------- Grace 3 days ----------
class TestGrace3Days:
    def _set_sub(self, user_id, sub):
        c = MongoClient(MONGO_URL)
        try:
            c[DB_NAME].users.update_one({"id": user_id}, {"$set": {"subscription": sub}})
        finally:
            c.close()

    def test_grace_within_3_days(self):
        _, token, user_id = _register()
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        self._set_sub(user_id, {
            "plan": "premium",
            "expires_at": yesterday,
            "preapproval_id": "fake-pre",
            "preapproval_status": "authorized",
        })
        r = requests.get(f"{BASE_URL}/api/me/usage", headers=_auth(token))
        assert r.status_code == 200
        assert r.json()["is_premium"] is True, r.json()

    def test_grace_beyond_3_days(self):
        _, token, user_id = _register()
        four_days_ago = (datetime.now(timezone.utc) - timedelta(days=4)).isoformat()
        self._set_sub(user_id, {
            "plan": "premium",
            "expires_at": four_days_ago,
            "preapproval_id": "fake-pre",
            "preapproval_status": "authorized",
        })
        r = requests.get(f"{BASE_URL}/api/me/usage", headers=_auth(token))
        assert r.status_code == 200
        assert r.json()["is_premium"] is False, r.json()


# ---------- Regression ----------
class TestRegression:
    def test_admin_login_and_stats(self):
        tok = _login(ADMIN_EMAIL, ADMIN_PASSWORD)
        r = requests.get(f"{BASE_URL}/api/admin/stats", headers=_auth(tok))
        assert r.status_code == 200
        assert "users" in r.json()

    def test_public_settings(self):
        r = requests.get(f"{BASE_URL}/api/settings")
        assert r.status_code == 200
        assert "free_daily_limit" in r.json()

    def test_generate_password_no_auth(self):
        r = requests.post(f"{BASE_URL}/api/generate", json={"tool": "password_gen", "payload": {"length": 12}})
        assert r.status_code == 200
        assert isinstance(r.json().get("result"), str)
