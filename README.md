# Facilita AI

App mobile-first em pt-BR com ferramentas prontas de IA para o dia a dia.
Stack: **React 19 + Tailwind** (frontend) · **FastAPI + MongoDB** (backend) ·
**Mercado Pago Preapproval** (assinatura recorrente Premium) · **Capacitor 6** (Android wrapper).

## Estrutura

```
/app
├── frontend/         → React (PWA/mobile-first)
├── backend/          → FastAPI + Motor + JWT + MP + emergentintegrations
├── mobile/           → Capacitor Android (wrapper WebView → produção)
├── .github/workflows → CI que gera APK debug + AAB release
└── memory/PRD.md     → Documento vivo do produto
```

## Variáveis de ambiente

**Nunca commite `.env`.** Copie os exemplos abaixo para `backend/.env` e `frontend/.env`.

### `backend/.env`
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="facilita_ai"
CORS_ORIGINS="*"
EMERGENT_LLM_KEY="sk-emergent-..."
JWT_SECRET="troque-por-uma-string-longa-aleatoria"
MP_ACCESS_TOKEN="APP_USR-...-..."
MP_WEBHOOK_SECRET="chave-hex-do-painel-do-mercado-pago"
PUBLIC_BASE_URL="https://seu-dominio.com"
PREMIUM_PRICE_BRL="9.90"
```

### `frontend/.env`
```env
REACT_APP_BACKEND_URL=https://seu-dominio.com
```

## Rodar local

```bash
# backend
cd backend && pip install -r requirements.txt && uvicorn server:app --reload --port 8001

# frontend
cd frontend && yarn install && yarn start
```

## Gerar APK/AAB Android

Ver `mobile/README.md`. Resumo: rode o workflow **Android build (Facilita AI)** em
GitHub Actions e baixe os artifacts.

## Credenciais de demonstração
Admin: `admin@facilita.ai` / `Facilita@123` (seed no startup).
