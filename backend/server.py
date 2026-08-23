from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import secrets
import string
import re
import time
import hmac
import hashlib
import httpx
import mercadopago
from zoneinfo import ZoneInfo
from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Mercado Pago
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN", "")
MP_WEBHOOK_SECRET = os.environ.get("MP_WEBHOOK_SECRET", "")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
PREMIUM_PRICE_BRL = float(os.environ.get("PREMIUM_PRICE_BRL", "9.90"))
mp_sdk = mercadopago.SDK(MP_ACCESS_TOKEN) if MP_ACCESS_TOKEN else None

# Logging (needs to exist before route handlers reference it)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")
JWT_SECRET = os.environ["JWT_SECRET"]
MODEL = "gpt-5.4-mini"
AI_TOOLS = {"whatsapp", "improve_text", "correct_pt", "summarize", "create_email", "create_caption", "youtube_titles"}

class AuthInput(BaseModel):
    email: str
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(default="", max_length=80)

class GenerateInput(BaseModel):
    tool: str
    payload: Dict[str, Any]

class FavoriteInput(BaseModel):
    tool_id: str

class SettingsInput(BaseModel):
    free_daily_limit: Optional[int] = Field(default=None, ge=0, le=1000)
    premium_daily_limit: Optional[int] = Field(default=None, ge=0, le=100000)
    premium_price_brl: Optional[float] = Field(default=None, ge=0)
    ads_enabled: Optional[bool] = None
    banner_enabled: Optional[bool] = None
    interstitial_enabled: Optional[bool] = None

class SubscriptionInput(BaseModel):
    plan: str  # "free" | "premium"

DEFAULT_SETTINGS = {
    "id": "app_settings",
    "free_daily_limit": 3,
    "premium_daily_limit": 500,
    "premium_price_brl": float(os.environ.get("PREMIUM_PRICE_BRL", "9.90")),
    "ads_enabled": True,
    "banner_enabled": True,
    "interstitial_enabled": False,
}

async def get_settings():
    s = await db.settings.find_one({"id": "app_settings"}, {"_id": 0})
    if not s:
        await db.settings.insert_one(DEFAULT_SETTINGS.copy())
        return DEFAULT_SETTINGS.copy()
    return {**DEFAULT_SETTINGS, **s}

def is_premium(user):
    if not user: return False
    sub = user.get("subscription") or {}
    if sub.get("plan") not in {"premium", "canceled"}: return False
    exp = sub.get("expires_at")
    if not exp:
        return sub.get("plan") == "premium"  # concessão manual sem expiração
    try:
        expires = datetime.fromisoformat(exp)
    except Exception:
        return False
    now = datetime.now(timezone.utc)
    # Tolerância de 3 dias: se o MP ainda está autorizado a tentar cobrar, mantém acesso
    if sub.get("preapproval_status") == "authorized" and sub.get("plan") == "premium":
        expires = expires + timedelta(days=3)
    return expires > now

def compute_grace(user):
    """Retorna {in_grace_period, grace_days_left} indicando se o usuário está no período de tolerância de 3 dias."""
    if not user: return {"in_grace_period": False, "grace_days_left": 0}
    sub = user.get("subscription") or {}
    if sub.get("plan") != "premium" or sub.get("preapproval_status") != "authorized":
        return {"in_grace_period": False, "grace_days_left": 0}
    exp = sub.get("expires_at")
    if not exp: return {"in_grace_period": False, "grace_days_left": 0}
    try:
        expires = datetime.fromisoformat(exp)
    except Exception:
        return {"in_grace_period": False, "grace_days_left": 0}
    now = datetime.now(timezone.utc)
    if now < expires: return {"in_grace_period": False, "grace_days_left": 0}
    grace_end = expires + timedelta(days=3)
    if now < grace_end:
        secs = (grace_end - now).total_seconds()
        return {"in_grace_period": True, "grace_days_left": max(1, int(secs // 86400) + (1 if secs % 86400 else 0))}
    return {"in_grace_period": False, "grace_days_left": 0}

def today_iso_prefix():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

BRT_TZ = ZoneInfo("America/Sao_Paulo")

def brt_day_bounds_utc():
    """Retorna (início, fim) do dia atual no fuso America/Sao_Paulo em ISO UTC."""
    now_brt = datetime.now(BRT_TZ)
    start_brt = now_brt.replace(hour=0, minute=0, second=0, microsecond=0)
    end_brt = start_brt + timedelta(days=1)
    return start_brt.astimezone(timezone.utc).isoformat(), end_brt.astimezone(timezone.utc).isoformat()

async def count_today_ai_usage(user_id: str) -> int:
    start, end = brt_day_bounds_utc()
    return await db.usage.count_documents({
        "user_id": user_id,
        "tool": {"$in": list(AI_TOOLS)},
        "created_at": {"$gte": start, "$lt": end},
    })

def token_for(user):
    return jwt.encode({"sub": user["id"], "email": user["email"], "role": user.get("role", "user")}, JWT_SECRET, algorithm="HS256")

async def current_user(authorization: Optional[str] = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        data = jwt.decode(authorization.split(" ", 1)[1], JWT_SECRET, algorithms=["HS256"])
        return await db.users.find_one({"id": data["sub"]}, {"_id": 0, "password": 0})
    except Exception:
        return None

async def required_user(user=Depends(current_user)):
    if not user:
        raise HTTPException(401, "Faça login para continuar")
    return user

@app.on_event("startup")
async def seed_admin():
    existing = await db.users.find_one({"email": "admin@facilita.ai"})
    if not existing:
        await db.users.insert_one({"id": str(uuid.uuid4()), "email": "admin@facilita.ai", "name": "Admin Facilita", "password": bcrypt.hashpw(b"Facilita@123", bcrypt.gensalt()).decode(), "role": "admin", "created_at": datetime.now(timezone.utc).isoformat()})
    # Migração: se o limite grátis ainda é o antigo padrão de 10, atualiza para 3
    doc = await db.settings.find_one({"id": "app_settings"})
    if doc and doc.get("free_daily_limit") == 10:
        await db.settings.update_one({"id": "app_settings"}, {"$set": {"free_daily_limit": 3}})


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Facilita AI API", "status": "ok"}

@api_router.post("/auth/register")
async def register(input: AuthInput):
    email = input.email.strip().lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email): raise HTTPException(400, "Informe um e-mail válido")
    if await db.users.find_one({"email": email}): raise HTTPException(409, "Este e-mail já está cadastrado")
    user = {"id": str(uuid.uuid4()), "email": email, "name": input.name.strip() or email.split("@")[0], "password": bcrypt.hashpw(input.password.encode(), bcrypt.gensalt()).decode(), "role": "user", "subscription": {"plan": "free"}, "created_at": datetime.now(timezone.utc).isoformat()}
    await db.users.insert_one(user.copy())
    return {"token": token_for(user), "user": {k: user[k] for k in ("id", "email", "name", "role", "subscription")}}

@api_router.post("/auth/login")
async def login(input: AuthInput):
    user = await db.users.find_one({"email": input.email.strip().lower()})
    if not user or not bcrypt.checkpw(input.password.encode(), user.get("password", "").encode()): raise HTTPException(401, "E-mail ou senha incorretos")
    safe = {k: user.get(k) for k in ("id", "email", "name", "role", "subscription")}
    return {"token": token_for(user), "user": safe}

@api_router.get("/auth/me")
async def me(user=Depends(required_user)): return user

@api_router.get("/auth/google")
async def google_auth():
    return {"configured": False, "message": "Login Google será conectado no painel administrativo."}

def prompt_for(tool, p):
    prompts = {
        "whatsapp": f"Gere 3 respostas diferentes em português do Brasil para esta mensagem: {p.get('message','')}. Tom: {p.get('tone','Amigável')}. Retorne apenas 3 opções numeradas.",
        "improve_text": f"Melhore este texto em português do Brasil, mantendo significado. Direção: {p.get('mode','Deixar mais claro')}. Retorne apenas o texto final: {p.get('text','')}",
        "correct_pt": f"Corrija ortografia, pontuação, concordância e gramática sem mudar o sentido. Retorne apenas o texto corrigido: {p.get('text','')}",
        "summarize": f"Resuma em português do Brasil no formato {p.get('mode','Resumo normal')}. Texto: {p.get('text','')}",
        "create_email": f"Crie um e-mail em português do Brasil sobre {p.get('topic','')}, estilo {p.get('style','Profissional')}. Retorne assunto e corpo bem separados.",
        "create_caption": f"Crie 3 legendas em português do Brasil para {p.get('platform','Instagram')} sobre: {p.get('topic','')}. Preferência: {p.get('style','Normal')}, {p.get('emoji','Com emojis')}. Retorne numeradas.",
        "youtube_titles": f"Crie 10 títulos atraentes em português do Brasil para YouTube sobre: {p.get('topic','')}. Retorne apenas uma lista numerada."
    }
    return prompts.get(tool, "Responda em português do Brasil de forma útil.")

async def ai_generate(tool, payload):
    key = os.environ.get("EMERGENT_LLM_KEY")
    if not key: raise HTTPException(503, "IA ainda não configurada no painel administrativo")
    chat = LlmChat(api_key=key, session_id=str(uuid.uuid4()), system_message="Você é o Facilita AI. Seja claro, útil e natural em pt-BR.").with_model("openai", MODEL)
    chunks = []
    async for event in chat.stream_message(UserMessage(text=prompt_for(tool, payload))):
        if isinstance(event, TextDelta): chunks.append(event.content)
    return "".join(chunks).strip()

@api_router.post("/generate")
async def generate(input: GenerateInput, user=Depends(required_user)):
    if input.tool not in AI_TOOLS and input.tool not in {"qrcode", "password_gen", "percentage_calc"}: raise HTTPException(400, "Ferramenta inválida")
    if input.tool in AI_TOOLS:
        settings = await get_settings()
        user_id = user["id"]
        limit = settings["premium_daily_limit"] if is_premium(user) else settings["free_daily_limit"]
        used = await count_today_ai_usage(user_id)
        if used >= limit:
            raise HTTPException(402, "Você atingiu o limite gratuito de IA de hoje. Assine o Premium para continuar." if not is_premium(user) else "Limite diário atingido.")
        text = await ai_generate(input.tool, input.payload)
        record = {"id": str(uuid.uuid4()), "tool": input.tool, "user_id": user_id, "prompt": input.payload, "result": text, "created_at": datetime.now(timezone.utc).isoformat()}
        await db.usage.insert_one(record)
    elif input.tool == "password_gen":
        p=input.payload; chars=(string.ascii_letters if p.get("letters", True) else "")+(string.digits if p.get("numbers", True) else "")+(string.punctuation if p.get("symbols", True) else "")
        text=''.join(secrets.choice(chars or string.ascii_letters) for _ in range(max(6, min(64, int(p.get("length", 16))))) )
    else:
        p=input.payload; value=float(p.get("value", 0)); percentage=float(p.get("percentage", 0)); text=f"{value * percentage / 100:.2f}"
    return {"result": text, "tool": input.tool}

@api_router.get("/favorites")
async def favorites(user=Depends(required_user)):
    return await db.favorites.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)

@api_router.post("/favorites")
async def add_favorite(input: FavoriteInput, user=Depends(required_user)):
    await db.favorites.update_one({"user_id": user["id"], "tool_id": input.tool_id}, {"$set": {"user_id": user["id"], "tool_id": input.tool_id}}, upsert=True)
    return {"ok": True}

@api_router.delete("/favorites/{tool_id}")
async def remove_favorite(tool_id: str, user=Depends(required_user)):
    await db.favorites.delete_one({"user_id": user["id"], "tool_id": tool_id}); return {"ok": True}

@api_router.get("/history")
async def history(user=Depends(required_user)):
    return await db.usage.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)

@api_router.delete("/history/{item_id}")
async def remove_history(item_id: str, user=Depends(required_user)):
    await db.usage.delete_one({"id": item_id, "user_id": user["id"]}); return {"ok": True}

@api_router.get("/admin/stats")
async def admin_stats(user=Depends(required_user)):
    if user.get("role") != "admin": raise HTTPException(403, "Acesso restrito")
    return {"users": await db.users.count_documents({}), "generations": await db.usage.count_documents({}), "tools": await db.usage.aggregate([{"$group":{"_id":"$tool","count":{"$sum":1}}}]).to_list(20)}

@api_router.get("/settings")
async def public_settings():
    s = await get_settings()
    return {k: s[k] for k in ("free_daily_limit","premium_daily_limit","premium_price_brl","ads_enabled","banner_enabled","interstitial_enabled")}

@api_router.get("/admin/settings")
async def admin_get_settings(user=Depends(required_user)):
    if user.get("role") != "admin": raise HTTPException(403, "Acesso restrito")
    return await get_settings()

@api_router.put("/admin/settings")
async def admin_update_settings(input: SettingsInput, user=Depends(required_user)):
    if user.get("role") != "admin": raise HTTPException(403, "Acesso restrito")
    updates = {k: v for k, v in input.model_dump().items() if v is not None}
    if updates:
        await db.settings.update_one({"id": "app_settings"}, {"$set": updates}, upsert=True)
    return await get_settings()

@api_router.get("/me/usage")
async def me_usage(user=Depends(current_user)):
    settings = await get_settings()
    premium = is_premium(user)
    limit = settings["premium_daily_limit"] if premium else settings["free_daily_limit"]
    if not user:
        # /api/generate exige login, então visitantes nunca acumulam uso — retorno 0/limit direto
        return {"used": 0, "limit": limit, "remaining": limit, "is_premium": False, "plan": "free", "in_grace_period": False, "grace_days_left": 0}
    used = await count_today_ai_usage(user["id"])
    grace = compute_grace(user)
    return {"used": used, "limit": limit, "remaining": max(0, limit - used), "is_premium": premium, "plan": "premium" if premium else "free", **grace}

@api_router.post("/admin/users/{user_id}/subscription")
async def set_subscription(user_id: str, input: SubscriptionInput, user=Depends(required_user)):
    if user.get("role") != "admin": raise HTTPException(403, "Acesso restrito")
    if input.plan not in {"free", "premium"}: raise HTTPException(400, "Plano inválido")
    await db.users.update_one({"id": user_id}, {"$set": {"subscription": {"plan": input.plan, "updated_at": datetime.now(timezone.utc).isoformat()}}})
    fresh = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not fresh: raise HTTPException(404, "Usuário não encontrado")
    return {"user": fresh}

@api_router.post("/checkout/premium")
async def checkout_premium(user=Depends(required_user)):
    """Cria uma assinatura recorrente mensal (Mercado Pago Preapproval)."""
    if not mp_sdk:
        raise HTTPException(503, "Pagamento não configurado. Adicione MP_ACCESS_TOKEN no painel administrativo.")
    base = PUBLIC_BASE_URL or ""
    # Se o usuário já tem uma assinatura em andamento, reaproveita
    existing = user.get("subscription") or {}
    existing_id = existing.get("preapproval_id")
    if existing_id and existing.get("preapproval_status") in {"pending", "authorized"}:
        try:
            current = mp_sdk.preapproval().get(existing_id)
            if current.get("status", 500) < 300:
                data = current.get("response") or {}
                if data.get("status") in {"pending", "authorized"} and data.get("init_point"):
                    return {"preapproval_id": data["id"], "init_point": data["init_point"], "reused": True}
        except Exception:
            logger.exception("Falha ao consultar preapproval existente")

    body = {
        "reason": "Facilita AI Premium",
        "external_reference": str(user["id"]),
        "payer_email": user["email"],
        "back_url": f"{base}/premium",
        "auto_recurring": {
            "frequency": 1,
            "frequency_type": "months",
            "transaction_amount": float(PREMIUM_PRICE_BRL),
            "currency_id": "BRL",
        },
        "status": "pending",
    }
    try:
        result = mp_sdk.preapproval().create(body)
        pref = result.get("response") or {}
        if not pref.get("id"): raise Exception(str(result))
    except Exception:
        logger.exception("Falha ao criar preapproval MP")
        raise HTTPException(502, "Não foi possível iniciar a assinatura. Tente novamente.")

    await db.users.update_one({"id": user["id"]}, {"$set": {
        "subscription": {**(existing if existing else {}),
            "preapproval_id": pref["id"],
            "preapproval_status": pref.get("status", "pending"),
            "activated_by": "mercadopago_recurring",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    }})
    return {"preapproval_id": pref["id"], "init_point": pref.get("init_point")}


async def extend_premium_one_cycle(user_id: str, preapproval_id: str, payment_id: str):
    """Estende Premium em +30 dias a partir do maior entre agora e expires_at atual. Idempotente."""
    event_key = f"authorized_payment:{payment_id}"
    try:
        await db.processed_mp_events.insert_one({"_id": event_key, "user_id": user_id, "processed_at": datetime.now(timezone.utc).isoformat()})
    except Exception:  # DuplicateKeyError → já processado
        return False
    user = await db.users.find_one({"id": user_id}) or {}
    sub = user.get("subscription") or {}
    now = datetime.now(timezone.utc)
    base = now
    try:
        if sub.get("expires_at"):
            base = max(datetime.fromisoformat(sub["expires_at"]), now)
    except Exception:
        pass
    new_expires = (base + timedelta(days=30)).isoformat()
    await db.users.update_one({"id": user_id}, {"$set": {"subscription": {
        "plan": "premium",
        "expires_at": new_expires,
        "activated_by": "mercadopago_recurring",
        "preapproval_id": preapproval_id,
        "preapproval_status": "authorized",
        "last_payment_id": str(payment_id),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }}})
    return True


def valid_mp_signature(headers: Dict[str, str], data_id: Optional[str]) -> bool:
    if not MP_WEBHOOK_SECRET: return True  # sandbox / secret não configurado
    signature = headers.get("x-signature") or headers.get("X-Signature")
    request_id = headers.get("x-request-id") or headers.get("X-Request-Id")
    if not signature or not request_id or not data_id: return False
    parts = dict(p.strip().split("=", 1) for p in signature.split(",") if "=" in p)
    ts, received = parts.get("ts"), parts.get("v1")
    if not ts or not received: return False
    try:
        # ts vem em milissegundos ou segundos; tenta ambos
        ts_int = int(ts)
        seconds = ts_int / 1000 if ts_int > 10_000_000_000 else ts_int
        if abs(time.time() - seconds) > 5*60: return False
    except ValueError:
        return False
    manifest = f"id:{data_id.lower()};request-id:{request_id};ts:{ts};"
    expected = hmac.new(MP_WEBHOOK_SECRET.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received)


async def _fetch_authorized_payment(auth_pay_id: str):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"https://api.mercadopago.com/authorized_payments/{auth_pay_id}",
            headers={"Authorization": f"Bearer {MP_ACCESS_TOKEN}"},
        )
    if r.status_code >= 300: return None
    return r.json()


@api_router.post("/mercadopago/webhook")
async def mercadopago_webhook(request: Request):
    if not mp_sdk: return {"received": False}
    body = {}
    try: body = await request.json()
    except Exception: pass
    query = dict(request.query_params)
    data_id = query.get("data.id") or str((body.get("data") or {}).get("id") or "")
    event_type = query.get("type") or body.get("type") or body.get("topic")
    if not data_id: return {"received": True}
    if not valid_mp_signature(dict(request.headers), data_id):
        raise HTTPException(401, "assinatura inválida")

    try:
        if event_type == "subscription_preapproval":
            r = mp_sdk.preapproval().get(data_id)
            pre = r.get("response") or {}
            user_id = pre.get("external_reference")
            status = pre.get("status")
            if user_id:
                await db.users.update_one(
                    {"id": user_id, "subscription.preapproval_id": data_id},
                    {"$set": {"subscription.preapproval_status": status, "subscription.updated_at": datetime.now(timezone.utc).isoformat()}},
                )
                # Se cancelado, marca plano como canceled (mantém expires_at até vencer naturalmente)
                if status == "canceled":
                    await db.users.update_one({"id": user_id}, {"$set": {"subscription.plan": "canceled"}})
        elif event_type == "subscription_authorized_payment":
            invoice = await _fetch_authorized_payment(data_id)
            if invoice:
                payment = invoice.get("payment") or {}
                preapproval_id = str(invoice.get("preapproval_id") or "")
                pre_status = invoice.get("payment_type_id")  # not needed here
                # Busca usuário via preapproval_id
                target = await db.users.find_one({"subscription.preapproval_id": preapproval_id})
                if target and payment.get("status") == "approved":
                    await extend_premium_one_cycle(target["id"], preapproval_id, str(payment.get("id") or invoice.get("id")))
                elif target:
                    # Cobrança falhou/pendente: apenas registra tentativa (tolerância cobre)
                    await db.billing_events.update_one(
                        {"_id": f"invoice:{invoice.get('id')}"},
                        {"$set": {"invoice": invoice, "status": payment.get("status") or "pending", "user_id": target["id"], "updated_at": datetime.now(timezone.utc).isoformat()}},
                        upsert=True,
                    )
        # ignore other event types
    except HTTPException: raise
    except Exception:
        logger.exception("Erro no webhook MP")
    return {"received": True}


@api_router.get("/subscription")
async def my_subscription(user=Depends(required_user)):
    """Retorna o status atual da assinatura do usuário. Reconcilia com MP se possível."""
    sub = user.get("subscription") or {}
    pre_id = sub.get("preapproval_id")
    if pre_id and mp_sdk:
        try:
            r = mp_sdk.preapproval().get(pre_id)
            data = r.get("response") or {}
            status = data.get("status")
            if status and status != sub.get("preapproval_status"):
                await db.users.update_one({"id": user["id"]}, {"$set": {"subscription.preapproval_status": status, "subscription.next_payment_date": data.get("next_payment_date")}})
                sub["preapproval_status"] = status
                sub["next_payment_date"] = data.get("next_payment_date")
        except Exception:
            logger.exception("Falha ao reconciliar assinatura MP")
    return {
        "plan": sub.get("plan", "free"),
        "expires_at": sub.get("expires_at"),
        "preapproval_id": pre_id,
        "preapproval_status": sub.get("preapproval_status"),
        "next_payment_date": sub.get("next_payment_date"),
        "is_premium": is_premium({**user, "subscription": sub}),
        **compute_grace({**user, "subscription": sub}),
    }


@api_router.get("/subscription/invoices")
async def list_invoices(user=Depends(required_user)):
    """Retorna o histórico de cobranças (authorized_payments) do usuário no Mercado Pago."""
    sub = user.get("subscription") or {}
    pre_id = sub.get("preapproval_id")
    if not pre_id or not MP_ACCESS_TOKEN:
        return {"invoices": []}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://api.mercadopago.com/authorized_payments/search",
                params={"preapproval_id": pre_id, "limit": 20, "sort": "date_created:desc"},
                headers={"Authorization": f"Bearer {MP_ACCESS_TOKEN}"},
            )
        if r.status_code >= 300:
            return {"invoices": []}
        data = r.json()
        results = data.get("results", [])
    except Exception:
        logger.exception("Falha ao listar faturas MP")
        return {"invoices": []}
    invoices = []
    for inv in results:
        payment = inv.get("payment") or {}
        invoices.append({
            "id": str(inv.get("id")),
            "amount": inv.get("transaction_amount") or (payment.get("transaction_amount") or 0),
            "currency": inv.get("currency_id") or "BRL",
            "status": payment.get("status") or inv.get("status") or "pending",
            "date": inv.get("date_created") or payment.get("date_approved") or payment.get("date_created"),
            "period_start": inv.get("debit_date"),
        })
    return {"invoices": invoices}


@api_router.post("/subscription/cancel")
async def cancel_subscription(user=Depends(required_user)):
    """Cancela a assinatura recorrente do usuário no Mercado Pago."""
    sub = user.get("subscription") or {}
    pre_id = sub.get("preapproval_id")
    if not pre_id: raise HTTPException(404, "Você não possui uma assinatura ativa para cancelar.")
    if not mp_sdk: raise HTTPException(503, "Pagamento não configurado.")
    try:
        r = mp_sdk.preapproval().update(pre_id, {"status": "cancelled"})
    except Exception:
        logger.exception("Falha ao cancelar preapproval")
        raise HTTPException(502, "Não foi possível cancelar agora. Tente novamente.")
    if r.get("status", 500) >= 300:
        # Fallback: alguns endpoints antigos aceitam grafias diferentes
        try:
            r = mp_sdk.preapproval().update(pre_id, {"status": "canceled"})
        except Exception:
            r = {"status": 502}
    if r.get("status", 500) >= 300:
        raise HTTPException(502, "Não foi possível cancelar agora.")
    await db.users.update_one({"id": user["id"]}, {"$set": {
        "subscription.plan": "canceled",
        "subscription.preapproval_status": "cancelled",
        "subscription.updated_at": datetime.now(timezone.utc).isoformat(),
    }})
    return {"ok": True, "message": "Assinatura cancelada. Seu Premium fica ativo até o fim do ciclo pago."}


@api_router.get("/admin/users")
async def admin_users(search: Optional[str] = None, user=Depends(required_user)):
    if user.get("role") != "admin": raise HTTPException(403, "Acesso restrito")
    q = {}
    if search:
        q = {"email": {"$regex": re.escape(search), "$options": "i"}}
    users = await db.users.find(q, {"_id": 0, "password": 0}).sort("created_at", -1).to_list(50)
    return users

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
# (logger is defined near the top so route handlers can reference it safely.)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()