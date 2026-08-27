"""
Testes da carteira FASE 2 — executa contra Mongo real de dev.
Rode com: cd /app/backend && python -m pytest tests/test_wallet.py -v
"""
import os, asyncio, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
import pytest
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

@pytest.fixture
def db():
    client = AsyncIOMotorClient(MONGO_URL)
    yield client[DB_NAME]
    client.close()

async def _fresh_user(db, credits: int = 10000) -> str:
    uid = str(uuid.uuid4())
    await db.users.insert_one({"id": uid, "email": f"wt_{uid[:6]}@t.ai", "credit_balance": credits, "role": "user"})
    return uid

async def _cleanup(db, uid: str):
    await db.users.delete_one({"id": uid})
    await db.wallet_ledger.delete_many({"user_id": uid})

def test_reserve_ok_and_release(db):
    async def run():
        from wallet import WalletService
        w = WalletService(db)
        uid = await _fresh_user(db, 1000)
        try:
            r = await w.reserve_atomic(user_id=uid, credits=300, tool="audio_gen", reference_id="ref1")
            assert r is not None
            assert r["balance_after"] == 700
            # release
            await w.release_reserve(user_id=uid, credits=300, tool="audio_gen", reference_id="ref1")
            bal = await w.get_balance(uid)
            assert bal == 1000, f"esperado 1000, got {bal}"
        finally:
            await _cleanup(db, uid)
    asyncio.get_event_loop().run_until_complete(run())

def test_reserve_insufficient(db):
    async def run():
        from wallet import WalletService
        w = WalletService(db)
        uid = await _fresh_user(db, 100)
        try:
            r = await w.reserve_atomic(user_id=uid, credits=500, tool="audio_gen", reference_id="ref2")
            assert r is None
            bal = await w.get_balance(uid)
            assert bal == 100  # nunca negativo
        finally:
            await _cleanup(db, uid)
    asyncio.get_event_loop().run_until_complete(run())

def test_concurrent_reserve_no_double_spend(db):
    async def run():
        from wallet import WalletService
        w = WalletService(db)
        uid = await _fresh_user(db, 1000)
        try:
            # 4 requisições simultâneas de 400 cada — só 2 podem ganhar (800), 2 devem falhar
            results = await asyncio.gather(*[
                w.reserve_atomic(user_id=uid, credits=400, tool="audio_gen", reference_id=f"c{i}")
                for i in range(4)
            ])
            successes = [r for r in results if r is not None]
            failures = [r for r in results if r is None]
            assert len(successes) == 2, f"esperado 2 sucessos, got {len(successes)}"
            assert len(failures) == 2
            bal = await w.get_balance(uid)
            assert bal == 200, f"esperado 200 (1000 - 2*400), got {bal}"
        finally:
            await _cleanup(db, uid)
    asyncio.get_event_loop().run_until_complete(run())

def test_commit_adjusts_reserve(db):
    async def run():
        from wallet import WalletService
        w = WalletService(db)
        uid = await _fresh_user(db, 1000)
        try:
            await w.reserve_atomic(user_id=uid, credits=500, tool="audio_gen", reference_id="ref3")
            # consumo real foi menor (300) → devolve 200
            await w.commit_reserve(user_id=uid, reserved_credits=500, actual_credits=300,
                                    tool="audio_gen", provider="elevenlabs", reference_id="ref3")
            bal = await w.get_balance(uid)
            assert bal == 700, f"esperado 700 (1000 - 300 real), got {bal}"
        finally:
            await _cleanup(db, uid)
    asyncio.get_event_loop().run_until_complete(run())

def test_purchase_idempotent(db):
    async def run():
        from wallet import WalletService
        w = WalletService(db)
        uid = await _fresh_user(db, 0)
        try:
            r1 = await w.credit_purchase(user_id=uid, credits=15000, payment_id="mp_pay_123",
                                          package_id="pkg_popular", price_brl=29.90)
            assert r1 is not None
            r2 = await w.credit_purchase(user_id=uid, credits=15000, payment_id="mp_pay_123",
                                          package_id="pkg_popular", price_brl=29.90)
            assert r2 is None  # duplicado
            bal = await w.get_balance(uid)
            assert bal == 15000, f"esperado 15000 (única compra), got {bal}"
        finally:
            await _cleanup(db, uid)
    asyncio.get_event_loop().run_until_complete(run())

def test_simulate_does_not_alter_balance(db):
    async def run():
        from wallet import WalletService
        w = WalletService(db)
        uid = await _fresh_user(db, 5000)
        try:
            await w.simulate_consume(user_id=uid, credits=100, tool="image_gen",
                                     provider="fal_ai", estimated_cost_usd=0.003,
                                     real_cost_usd=0.003, provider_usage={"aspect_ratio":"1:1"},
                                     reference_id="sim1")
            bal = await w.get_balance(uid)
            assert bal == 5000  # simulation NUNCA altera saldo real
            entry = await db.wallet_ledger.find_one({"reference_id": "sim1"})
            assert entry["mode"] == "simulation"
        finally:
            await _cleanup(db, uid)
    asyncio.get_event_loop().run_until_complete(run())
