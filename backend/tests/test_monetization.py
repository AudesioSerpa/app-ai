"""Backend tests for monetization: settings, usage, rate-limit, checkout, subscription."""
import os
import uuid
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
pytestmark = pytest.mark.skipif(not BASE_URL, reason="REACT_APP_BACKEND_URL is not set")

ADMIN = {"email": "admin@facilita.ai", "password": "Facilita@123", "name": ""}


def _login(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password, "name": ""}, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture(scope="module")
def admin_token():
    return _login(ADMIN["email"], ADMIN["password"])["token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def test_user():
    """Create a fresh user for rate-limit / subscription tests."""
    email = f"test_mon_{uuid.uuid4().hex[:8]}@facilita.ai"
    r = requests.post(f"{BASE_URL}/api/auth/register", json={"email": email, "password": "Test@12345", "name": "Test Mon"}, timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    return {"id": data["user"]["id"], "email": email, "token": data["token"], "headers": {"Authorization": f"Bearer {data['token']}"}}


@pytest.fixture(autouse=True)
def _restore_default_limit(admin_headers):
    yield
    # Always reset free_daily_limit to 10 after every test
    requests.put(f"{BASE_URL}/api/admin/settings", headers=admin_headers, json={"free_daily_limit": 10}, timeout=20)


# ---------- Public settings ----------

def test_public_settings_no_auth():
    r = requests.get(f"{BASE_URL}/api/settings", timeout=20)
    assert r.status_code == 200
    data = r.json()
    for k in ("free_daily_limit", "premium_daily_limit", "premium_price_brl", "ads_enabled", "banner_enabled", "interstitial_enabled"):
        assert k in data


# ---------- Admin settings guard ----------

def test_admin_settings_requires_admin(test_user):
    r = requests.get(f"{BASE_URL}/api/admin/settings", headers=test_user["headers"], timeout=20)
    assert r.status_code == 403


def test_admin_settings_get_ok(admin_headers):
    r = requests.get(f"{BASE_URL}/api/admin/settings", headers=admin_headers, timeout=20)
    assert r.status_code == 200
    assert r.json()["free_daily_limit"] == 10  # default


def test_admin_settings_put_reflects_in_public(admin_headers):
    r = requests.put(f"{BASE_URL}/api/admin/settings", headers=admin_headers, json={"free_daily_limit": 3}, timeout=20)
    assert r.status_code == 200
    assert r.json()["free_daily_limit"] == 3
    pub = requests.get(f"{BASE_URL}/api/settings", timeout=20).json()
    assert pub["free_daily_limit"] == 3


# ---------- /me/usage ----------

def test_usage_guest():
    r = requests.get(f"{BASE_URL}/api/me/usage", timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert d["is_premium"] is False
    assert d["plan"] == "free"
    for k in ("used", "limit", "remaining"): assert k in d


def test_usage_authenticated(test_user):
    r = requests.get(f"{BASE_URL}/api/me/usage", headers=test_user["headers"], timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert d["plan"] == "free"
    assert d["is_premium"] is False


# ---------- Checkout ----------

def test_checkout_returns_preference(test_user):
    # Iteration 4: real MP checkout now returns preference_id + init_point
    r = requests.post(f"{BASE_URL}/api/checkout/premium", headers=test_user["headers"], timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("preference_id")
    assert "mercadopago" in (d.get("init_point") or "")


# ---------- Admin subscription control ----------

def test_admin_subscription_requires_admin(test_user):
    r = requests.post(
        f"{BASE_URL}/api/admin/users/{test_user['id']}/subscription",
        headers=test_user["headers"], json={"plan": "premium"}, timeout=20
    )
    assert r.status_code == 403


# ---------- Rate limit + upgrade ----------

def test_rate_limit_then_premium_bypass(admin_headers):
    # Fresh user
    email = f"test_rl_{uuid.uuid4().hex[:8]}@facilita.ai"
    reg = requests.post(f"{BASE_URL}/api/auth/register", json={"email": email, "password": "Test@12345", "name": "RL"}, timeout=20)
    assert reg.status_code == 200
    uid = reg.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {reg.json()['token']}"}

    # Set limit to 1
    requests.put(f"{BASE_URL}/api/admin/settings", headers=admin_headers, json={"free_daily_limit": 1}, timeout=20)

    payload = {"tool": "correct_pt", "payload": {"text": "ola mundo, tudo bem"}}
    # First call may succeed or 503 if LLM not configured. Accept either 200 or 503; both increment nothing extra beyond 200.
    r1 = requests.post(f"{BASE_URL}/api/generate", headers=headers, json=payload, timeout=60)
    assert r1.status_code in (200, 503), r1.text
    if r1.status_code == 503:
        pytest.skip("LLM not configured; cannot exercise rate limit path meaningfully")

    # Second call should be 402
    r2 = requests.post(f"{BASE_URL}/api/generate", headers=headers, json=payload, timeout=60)
    assert r2.status_code == 402, r2.text
    assert "limite" in r2.json().get("detail", "").lower()

    # Upgrade to premium via admin
    up = requests.post(
        f"{BASE_URL}/api/admin/users/{uid}/subscription",
        headers=admin_headers, json={"plan": "premium"}, timeout=20
    )
    assert up.status_code == 200
    assert up.json()["user"]["subscription"]["plan"] == "premium"

    # Now generation should work again (200 or 503 if LLM flake, but not 402)
    r3 = requests.post(f"{BASE_URL}/api/generate", headers=headers, json=payload, timeout=60)
    assert r3.status_code in (200, 503), r3.text
    assert r3.status_code != 402


# ---------- Regression: login returns subscription ----------

def test_login_returns_subscription_for_new_user(test_user):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": test_user["email"], "password": "Test@12345", "name": ""}, timeout=20)
    assert r.status_code == 200
    assert "subscription" in r.json()["user"]
