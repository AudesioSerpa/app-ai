"""Iteration 8: BRT (America/Sao_Paulo) daily reset for AI usage."""
import os
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient
from zoneinfo import ZoneInfo

load_dotenv(Path(__file__).resolve().parents[2] / "frontend" / ".env")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

BRT = ZoneInfo("America/Sao_Paulo")

mongo = MongoClient(MONGO_URL)
db = mongo[DB_NAME]


def _brt_day_bounds_utc():
    now_brt = datetime.now(BRT)
    start_brt = now_brt.replace(hour=0, minute=0, second=0, microsecond=0)
    end_brt = start_brt + timedelta(days=1)
    return start_brt.astimezone(timezone.utc), end_brt.astimezone(timezone.utc)


def _register():
    email = f"TEST_brt_{uuid.uuid4().hex[:8]}@facilita.ai"
    r = requests.post(f"{API}/auth/register", json={"email": email, "password": "TestPass123", "name": "BRT"})
    assert r.status_code == 200, r.text
    return email, r.json()["token"], r.json()["user"]["id"]


def _hdr(tok):
    return {"Authorization": f"Bearer {tok}"}


def test_brt_bounds_are_24h_utc_window():
    """brt_day_bounds_utc should produce a 24h window that starts at BRT midnight expressed in UTC."""
    start, end = _brt_day_bounds_utc()
    assert (end - start) == timedelta(days=1)
    # BRT is currently UTC-3 (no DST in Brazil since 2019)
    # Start converted back to BRT must be exactly midnight
    start_in_brt = start.astimezone(BRT)
    assert start_in_brt.hour == 0 and start_in_brt.minute == 0 and start_in_brt.second == 0
    # And end must be next-day midnight BRT
    end_in_brt = end.astimezone(BRT)
    assert end_in_brt.hour == 0 and (end_in_brt - start_in_brt).days == 1


def test_records_before_brt_midnight_do_not_count():
    """Records with created_at just before BRT midnight (i.e., in BRT yesterday) must NOT count."""
    _, tok, uid = _register()
    start, _end = _brt_day_bounds_utc()

    # Insert 3 records 1 minute BEFORE current BRT day start (== BRT yesterday)
    yesterday_ts = (start - timedelta(minutes=1)).isoformat()
    for _ in range(3):
        db.usage.insert_one({
            "id": str(uuid.uuid4()),
            "tool": "correct_pt",
            "user_id": uid,
            "prompt": {"text": "old"},
            "result": "x",
            "created_at": yesterday_ts,
        })

    r = requests.get(f"{API}/me/usage", headers=_hdr(tok))
    assert r.status_code == 200
    data = r.json()
    assert data["used"] == 0, f"BRT-yesterday records should not count. Got used={data['used']}"
    assert data["remaining"] == data["limit"]


def test_records_after_brt_midnight_do_count():
    """Records with created_at just AFTER current BRT midnight must count."""
    _, tok, uid = _register()
    start, _end = _brt_day_bounds_utc()

    today_ts = (start + timedelta(minutes=1)).isoformat()
    for _ in range(3):
        db.usage.insert_one({
            "id": str(uuid.uuid4()),
            "tool": "correct_pt",
            "user_id": uid,
            "prompt": {"text": "today"},
            "result": "x",
            "created_at": today_ts,
        })

    r = requests.get(f"{API}/me/usage", headers=_hdr(tok))
    assert r.status_code == 200
    data = r.json()
    assert data["used"] == 3, f"BRT-today records should count. Got used={data['used']}"
    assert data["remaining"] == 0

    # 4th real call should be blocked
    r = requests.post(f"{API}/generate", headers=_hdr(tok),
                      json={"tool": "correct_pt", "payload": {"text": "block"}})
    assert r.status_code == 402


def test_reset_simulation_moving_records_to_brt_yesterday():
    """Do 3 real AI calls (limit reached), then manipulate created_at to BRT yesterday → reset simulated."""
    _, tok, uid = _register()
    for i in range(3):
        r = requests.post(f"{API}/generate", headers=_hdr(tok),
                          json={"tool": "correct_pt", "payload": {"text": f"real {i}"}})
        assert r.status_code == 200, r.text

    # Confirm limit reached
    r = requests.get(f"{API}/me/usage", headers=_hdr(tok))
    assert r.json()["used"] == 3
    r = requests.post(f"{API}/generate", headers=_hdr(tok),
                      json={"tool": "correct_pt", "payload": {"text": "over"}})
    assert r.status_code == 402

    # Move all 3 records to BRT yesterday (30h ago is guaranteed to be < BRT-today-start)
    start, _end = _brt_day_bounds_utc()
    yesterday_ts = (start - timedelta(hours=6)).isoformat()
    result = db.usage.update_many({"user_id": uid}, {"$set": {"created_at": yesterday_ts}})
    assert result.modified_count == 3

    # Now /me/usage must show reset
    r = requests.get(f"{API}/me/usage", headers=_hdr(tok))
    data = r.json()
    assert data["used"] == 0, f"Reset failed. Got used={data['used']}"
    assert data["remaining"] == 3

    # And a 4th generate should succeed
    r = requests.post(f"{API}/generate", headers=_hdr(tok),
                      json={"tool": "correct_pt", "payload": {"text": "new day"}})
    assert r.status_code == 200


def test_existing_records_in_current_brt_day_still_count():
    """Nenhuma regressão: records inseridos hoje via API (created_at UTC now) devem continuar contando."""
    _, tok, uid = _register()
    for i in range(2):
        r = requests.post(f"{API}/generate", headers=_hdr(tok),
                          json={"tool": "correct_pt", "payload": {"text": f"reg {i}"}})
        assert r.status_code == 200
    r = requests.get(f"{API}/me/usage", headers=_hdr(tok))
    assert r.json()["used"] == 2
    assert r.json()["remaining"] == 1


def teardown_module(module):
    # Cleanup TEST_brt_* users and their usage
    users = list(db.users.find({"email": {"$regex": "^TEST_brt_"}}, {"id": 1}))
    ids = [u["id"] for u in users]
    if ids:
        db.usage.delete_many({"user_id": {"$in": ids}})
        db.users.delete_many({"id": {"$in": ids}})
