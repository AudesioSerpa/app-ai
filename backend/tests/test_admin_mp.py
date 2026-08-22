"""Backend tests for iteration 4: Admin panel + Mercado Pago integration."""
import os
import uuid
import requests
import pytest
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
pytestmark = pytest.mark.skipif(not BASE_URL, reason="REACT_APP_BACKEND_URL is not set")

ADMIN = {"email": "admin@facilita.ai", "password": "Facilita@123"}


def _login(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password, "name": ""}, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture(scope="module")
def admin_headers():
    tok = _login(ADMIN["email"], ADMIN["password"])["token"]
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(scope="module")
def user_ctx():
    email = f"test_mp_{uuid.uuid4().hex[:8]}@facilita.ai"
    r = requests.post(f"{BASE_URL}/api/auth/register", json={"email": email, "password": "Test@12345", "name": "MP User"}, timeout=20)
    assert r.status_code == 200, r.text
    d = r.json()
    return {"id": d["user"]["id"], "email": email, "token": d["token"], "headers": {"Authorization": f"Bearer {d['token']}"}}


# ---------- Mercado Pago ----------

def test_checkout_premium_creates_preference(user_ctx):
    r = requests.post(f"{BASE_URL}/api/checkout/premium", headers=user_ctx["headers"], timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("preference_id"), data
    assert data.get("external_reference"), data
    init_point = data.get("init_point") or ""
    assert "mercadopago" in init_point, f"init_point should be a MP url: {init_point}"


def test_checkout_premium_requires_auth():
    r = requests.post(f"{BASE_URL}/api/checkout/premium", timeout=20)
    assert r.status_code == 401, r.text


def test_payment_status_requires_auth():
    r = requests.get(f"{BASE_URL}/api/payments/999999", timeout=20)
    assert r.status_code == 401, r.text


def test_payment_status_unknown_id(user_ctx):
    # Fictitious payment_id: should NOT crash and return 502/404
    r = requests.get(f"{BASE_URL}/api/payments/000000000", headers=user_ctx["headers"], timeout=30)
    assert r.status_code in (404, 502), f"expected 404/502, got {r.status_code}: {r.text}"


def test_webhook_no_auth_required():
    # Webhook must accept POST without auth; with empty MP_WEBHOOK_SECRET should return received
    body = {"type": "payment", "data": {"id": "999999"}}
    r = requests.post(f"{BASE_URL}/api/mercadopago/webhook", json=body, timeout=30)
    # 200 with {received:true} or {received:false} if mp not configured; must NOT be 401
    assert r.status_code == 200, r.text
    j = r.json()
    assert "received" in j


def test_webhook_ignores_non_payment_events():
    r = requests.post(f"{BASE_URL}/api/mercadopago/webhook", json={"type": "test", "data": {"id": "1"}}, timeout=20)
    assert r.status_code == 200
    assert r.json().get("received") is True


# ---------- Admin users ----------

def test_admin_users_list(admin_headers):
    r = requests.get(f"{BASE_URL}/api/admin/users", headers=admin_headers, timeout=20)
    assert r.status_code == 200, r.text
    users = r.json()
    assert isinstance(users, list) and len(users) > 0
    # no password/_id leakage
    for u in users:
        assert "password" not in u
        assert "_id" not in u


def test_admin_users_search(admin_headers):
    r = requests.get(f"{BASE_URL}/api/admin/users", params={"search": "admin"}, headers=admin_headers, timeout=20)
    assert r.status_code == 200
    users = r.json()
    emails = [u["email"] for u in users]
    assert any("admin@facilita.ai" == e for e in emails), emails


def test_admin_users_forbidden_for_non_admin(user_ctx):
    r = requests.get(f"{BASE_URL}/api/admin/users", headers=user_ctx["headers"], timeout=20)
    assert r.status_code == 403


# ---------- Premium expiry semantics ----------

def test_premium_no_expiry_is_premium(admin_headers, user_ctx):
    # Grant premium (no expires_at) via admin endpoint
    r = requests.post(f"{BASE_URL}/api/admin/users/{user_ctx['id']}/subscription", headers=admin_headers, json={"plan": "premium"}, timeout=20)
    assert r.status_code == 200, r.text
    # Verify /me/usage reports is_premium=true
    r2 = requests.get(f"{BASE_URL}/api/me/usage", headers=user_ctx["headers"], timeout=20)
    assert r2.status_code == 200
    assert r2.json().get("is_premium") is True


def test_premium_expired_reports_free(admin_headers, user_ctx):
    # Directly manipulate DB via mongo -- do it through admin endpoint isn't possible, so use pymongo
    import pymongo
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "test_database")
    cli = pymongo.MongoClient(mongo_url)
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    cli[db_name].users.update_one({"id": user_ctx["id"]}, {"$set": {"subscription": {"plan": "premium", "expires_at": past}}})
    r = requests.get(f"{BASE_URL}/api/me/usage", headers=user_ctx["headers"], timeout=20)
    assert r.status_code == 200
    data = r.json()
    assert data.get("is_premium") is False, data
    assert data.get("plan") == "free"
    # cleanup: reset to free
    cli[db_name].users.update_one({"id": user_ctx["id"]}, {"$set": {"subscription": {"plan": "free"}}})


# ---------- Cleanup: keep admin as free (already free) ----------

def test_cleanup_admin_stays_free(admin_headers):
    r = requests.get(f"{BASE_URL}/api/admin/users", params={"search": "admin@facilita.ai"}, headers=admin_headers, timeout=20)
    assert r.status_code == 200
    admin = next((u for u in r.json() if u["email"] == "admin@facilita.ai"), None)
    assert admin is not None
    sub = admin.get("subscription") or {}
    assert sub.get("plan") != "premium", f"admin should stay free, got {sub}"
