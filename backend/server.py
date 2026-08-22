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
import mercadopago
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
    "free_daily_limit": 10,
    "premium_daily_limit": 500,
    "premium_price_brl": 19.90,
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
    if sub.get("plan") != "premium": return False
    exp = sub.get("expires_at")
    if not exp: return True  # sem expiração (concedido manualmente pelo admin)
    try:
        return datetime.fromisoformat(exp) > datetime.now(timezone.utc)
    except Exception:
        return False

def today_iso_prefix():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

async def count_today_ai_usage(user_id: str) -> int:
    prefix = today_iso_prefix()
    return await db.usage.count_documents({
        "user_id": user_id,
        "tool": {"$in": list(AI_TOOLS)},
        "created_at": {"$regex": f"^{prefix}"},
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
async def generate(input: GenerateInput, user=Depends(current_user)):
    if input.tool not in AI_TOOLS and input.tool not in {"qrcode", "password_gen", "percentage_calc"}: raise HTTPException(400, "Ferramenta inválida")
    if input.tool in AI_TOOLS:
        settings = await get_settings()
        user_id = user["id"] if user else "guest"
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
    user_id = user["id"] if user else "guest"
    used = await count_today_ai_usage(user_id)
    return {"used": used, "limit": limit, "remaining": max(0, limit - used), "is_premium": premium, "plan": "premium" if premium else "free"}

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
    if not mp_sdk:
        raise HTTPException(503, "Pagamento não configurado. Adicione MP_ACCESS_TOKEN no painel administrativo.")
    intent_id = f"premium-{user['id']}-{int(time.time_ns())}"[:64]
    base = PUBLIC_BASE_URL or ""
    preference = {
        "items": [{
            "id": "premium-30d",
            "title": "Facilita AI Premium — 30 dias",
            "description": "Acesso Premium por 30 dias (sem anúncios + IA ampliada)",
            "quantity": 1,
            "currency_id": "BRL",
            "unit_price": float(PREMIUM_PRICE_BRL),
        }],
        "external_reference": intent_id,
        "metadata": {"user_id": str(user["id"]), "product": "premium_30d"},
        "back_urls": {
            "success": f"{base}/premium",
            "failure": f"{base}/premium",
            "pending": f"{base}/premium",
        },
        "auto_return": "approved",
        "notification_url": f"{base}/api/mercadopago/webhook",
        "statement_descriptor": "FACILITA AI",
    }
    try:
        result = mp_sdk.preference().create(preference)
        pref = result.get("response") or {}
        if not pref.get("id"): raise Exception(str(result))
    except Exception as e:
        logger.exception("Falha ao criar preferência MP")
        raise HTTPException(502, "Não foi possível iniciar o pagamento. Tente novamente.")
    await db.payment_intents.insert_one({
        "id": intent_id,
        "user_id": user["id"],
        "preference_id": pref["id"],
        "payment_id": None,
        "status": "created",
        "amount": float(PREMIUM_PRICE_BRL),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"preference_id": pref["id"], "init_point": pref.get("init_point"), "external_reference": intent_id}


async def activate_premium_30_days(user_id: str, payment_id: str):
    # Idempotente: se este payment_id já ativou, não estende novamente
    existing = await db.premium_grants.find_one({"payment_id": payment_id})
    if existing: return
    expires = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    await db.users.update_one({"id": user_id}, {"$set": {"subscription": {"plan": "premium", "expires_at": expires, "activated_by": "mercadopago", "payment_id": payment_id, "updated_at": datetime.now(timezone.utc).isoformat()}}})
    await db.premium_grants.insert_one({"payment_id": payment_id, "user_id": user_id, "expires_at": expires, "created_at": datetime.now(timezone.utc).isoformat()})


def valid_mp_signature(signature: Optional[str], request_id: Optional[str], payment_id: Optional[str]) -> bool:
    if not MP_WEBHOOK_SECRET: return True  # em ambiente sem secret configurado, aceita (uso apenas em teste sandbox)
    if not signature or not request_id or not payment_id: return False
    parts = dict(p.split("=", 1) for p in signature.split(",") if "=" in p)
    ts, received = parts.get("ts"), parts.get("v1")
    if not ts or not received: return False
    try:
        if abs(time.time() - int(ts)/1000) > 5*60: return False
    except ValueError:
        return False
    manifest = f"id:{payment_id};request-id:{request_id};ts:{ts};"
    expected = hmac.new(MP_WEBHOOK_SECRET.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received)


@api_router.post("/mercadopago/webhook")
async def mercadopago_webhook(request: Request):
    if not mp_sdk: return {"received": False}
    body = {}
    try: body = await request.json()
    except Exception: pass
    query = dict(request.query_params)
    payment_id = query.get("data.id") or str((body.get("data") or {}).get("id") or "")
    event_type = query.get("type") or body.get("type")
    if event_type and event_type != "payment": return {"received": True}
    if not payment_id: return {"received": True}
    if not valid_mp_signature(request.headers.get("x-signature"), request.headers.get("x-request-id"), payment_id):
        raise HTTPException(401, "assinatura inválida")
    try:
        result = mp_sdk.payment().get(payment_id)
        payment = result.get("response") or {}
    except Exception:
        logger.exception("Falha ao consultar pagamento MP")
        return {"received": True}
    reference = payment.get("external_reference")
    intent = await db.payment_intents.find_one({"id": reference})
    if not intent: return {"received": True}
    status = payment.get("status")
    await db.payment_intents.update_one({"id": reference}, {"$set": {"payment_id": str(payment.get("id")), "status": status}})
    if status == "approved":
        await activate_premium_30_days(intent["user_id"], str(payment["id"]))
    return {"received": True}


@api_router.get("/payments/{payment_id}")
async def payment_status(payment_id: str, user=Depends(required_user)):
    if not mp_sdk: raise HTTPException(503, "Pagamento não configurado")
    # Consulta MP e reconcilia
    try:
        result = mp_sdk.payment().get(payment_id)
        payment = result.get("response") or {}
    except Exception:
        raise HTTPException(502, "Falha ao consultar pagamento")
    reference = payment.get("external_reference")
    intent = await db.payment_intents.find_one({"id": reference, "user_id": user["id"]})
    if not intent: raise HTTPException(404, "Pagamento não encontrado")
    status = payment.get("status")
    await db.payment_intents.update_one({"id": reference}, {"$set": {"payment_id": str(payment.get("id")), "status": status}})
    if status == "approved":
        await activate_premium_30_days(user["id"], str(payment["id"]))
    return {"id": str(payment.get("id")), "status": status, "status_detail": payment.get("status_detail")}


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