"""Backend tests for Grace Period + Invoices (iteration 6)."""
import os
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if os.environ.get("REACT_APP_BACKEND_URL") else None
if not BASE_URL:
    load_dotenv(Path(__file__).resolve().parents[2] / "frontend" / ".env")
    BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]


def _register():
    email = f"TEST_gr_{uuid.uuid4().hex[:8]}@example.com"
    r = requests.post(f"{BASE_URL}/api/auth/register", json={"email": email, "password": "Passw0rd!", "name": "Grace T"})
    assert r.status_code == 200, r.text
    return email, r.json()["token"], r.json()["user"]["id"]


def _auth(t):
    return {"Authorization": f"Bearer {t}"}


def _set_sub(user_id, sub):
    c = MongoClient(MONGO_URL)
    try:
        c[DB_NAME].users.update_one({"id": user_id}, {"$set": {"subscription": sub}})
    finally:
        c.close()


class TestGraceFieldsFree:
    def test_usage_free_user_grace_fields(self):
        _, token, _ = _register()
        r = requests.get(f"{BASE_URL}/api/me/usage", headers=_auth(token))
        assert r.status_code == 200
        d = r.json()
        assert d["in_grace_period"] is False
        assert d["grace_days_left"] == 0

    def test_subscription_free_user_grace_fields(self):
        _, token, _ = _register()
        r = requests.get(f"{BASE_URL}/api/subscription", headers=_auth(token))
        assert r.status_code == 200
        d = r.json()
        assert d["in_grace_period"] is False
        assert d["grace_days_left"] == 0
        assert d["plan"] == "free"


class TestGracePeriodStates:
    def test_authorized_expired_yesterday_in_grace(self):
        _, token, user_id = _register()
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        _set_sub(user_id, {"plan": "premium", "expires_at": yesterday, "preapproval_id": "fake", "preapproval_status": "authorized"})
        r = requests.get(f"{BASE_URL}/api/me/usage", headers=_auth(token))
        d = r.json()
        assert d["in_grace_period"] is True, d
        assert d["grace_days_left"] in (1, 2, 3), d  # ~2 days left
        # /api/subscription
        r2 = requests.get(f"{BASE_URL}/api/subscription", headers=_auth(token))
        assert r2.json()["in_grace_period"] is True

    def test_authorized_expired_4_days_ago_out_of_grace(self):
        _, token, user_id = _register()
        four = (datetime.now(timezone.utc) - timedelta(days=4)).isoformat()
        _set_sub(user_id, {"plan": "premium", "expires_at": four, "preapproval_id": "fake", "preapproval_status": "authorized"})
        r = requests.get(f"{BASE_URL}/api/me/usage", headers=_auth(token))
        d = r.json()
        assert d["in_grace_period"] is False, d
        assert d["grace_days_left"] == 0

    def test_not_authorized_no_grace_even_recent(self):
        _, token, user_id = _register()
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        _set_sub(user_id, {"plan": "premium", "expires_at": yesterday, "preapproval_id": "fake", "preapproval_status": "pending"})
        r = requests.get(f"{BASE_URL}/api/me/usage", headers=_auth(token))
        d = r.json()
        assert d["in_grace_period"] is False, d


class TestInvoices:
    def test_unauth_401(self):
        r = requests.get(f"{BASE_URL}/api/subscription/invoices")
        assert r.status_code == 401

    def test_no_preapproval_returns_empty(self):
        _, token, _ = _register()
        r = requests.get(f"{BASE_URL}/api/subscription/invoices", headers=_auth(token))
        assert r.status_code == 200
        assert r.json() == {"invoices": []}

    def test_after_checkout_returns_array(self):
        _, token, _ = _register()
        c = requests.post(f"{BASE_URL}/api/checkout/premium", headers=_auth(token))
        assert c.status_code == 200, c.text
        r = requests.get(f"{BASE_URL}/api/subscription/invoices", headers=_auth(token))
        assert r.status_code == 200
        d = r.json()
        assert "invoices" in d
        assert isinstance(d["invoices"], list)


class TestRegression:
    def test_public_settings(self):
        r = requests.get(f"{BASE_URL}/api/settings")
        assert r.status_code == 200

    def test_admin_login(self):
        r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "admin@facilita.ai", "password": "Facilita@123"})
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "admin"
