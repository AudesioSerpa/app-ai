# Facilita AI — PRD

## Problema original
Criar um PWA mobile-first em pt-BR chamado **Facilita AI** — central de ferramentas prontas de IA e utilidades para o dia a dia, sem exigir que o usuário saiba prompts. Slogan: "Sua IA para resolver o dia a dia.".

## Personas
- **Usuário casual mobile**: quer resolver algo rápido (responder WhatsApp, corrigir texto) sem cadastro.
- **Usuário recorrente**: cria conta para salvar histórico e favoritos, ganha benefícios extras.
- **Admin**: gerencia ferramentas, custos, publicidade e chaves de IA.

## Requisitos essenciais (estáticos)
- Mobile-first / PWA, pt-BR, navegação inferior fixa (Início, Ferramentas, Favoritos, Histórico, Perfil).
- Ferramentas prontas com um único botão de gerar.
- IA por trás do backend (nunca expor chaves).
- Login opcional; ferramentas locais funcionam sem consumir IA.
- Favoritos e histórico persistentes para usuários autenticados.
- Rate limit / créditos / painel admin previstos na arquitetura.

## Escopo MVP (11 ferramentas)
1. Responder WhatsApp • 2. Melhorar texto • 3. Corrigir português • 4. Resumir texto •
5. Criar e-mail • 6. Criar legenda • 7. Títulos para YouTube • 8. QR Code (local) •
9. Gerador de senhas (local) • 10. Calculadora de porcentagem (local) •
11. Gerador de imagens IA (fal.ai FLUX.1 Schnell).

## Stack
- Frontend: React 19 + React Router + Tailwind + shadcn + qrcode.react.
- Backend: FastAPI + Motor (MongoDB) + JWT + bcrypt + Emergent LLM (GPT-5.4 Mini).
- Auth: e-mail/senha (JWT). Google Auth previsto como toggle no painel (mock informativo).
- Deploy: supervisor + Kubernetes ingress (`/api` prefix).

## O que está implementado (Fev/2026)
- 11 ferramentas do MVP com UI mobile-first e tema escuro.
- **Gerador de Imagens IA (fal.ai FLUX.1 Schnell)**: `POST /api/generate-image` (backend guarda `FAL_KEY` em `backend/.env`), UI `/ferramenta/image_gen` com escolha de aspecto (1:1, 16:9, 9:16), download e compartilhar. Consome 1 uso/dia do free tier. Grava no histórico com `tool="image_gen"` e resultado (URL da imagem). **Fix 26/Fev/2026**: `App.js` linha 153 — slice da seção "Mais usadas" da Home atualizado de `slice(0,4)` → `slice(0,5)` para expor o novo card.
- Auth JWT (login/registro), seed do admin (`admin@facilita.ai` / `Facilita@123`).
- `/api/generate` roteia IA vs. locais (senha e %) e grava histórico completo (prompt+resultado).
- Favoritos sincronizados: hook usa localStorage + `/api/favorites` (GET/POST/DELETE) quando logado.
- Histórico com fetch autenticado, agrupamento por dia, reabrir em modal, copiar e excluir.
- QR Code corrigido (agora lê `fields.text`).
- **Monetização**: sistema centralizado (`isPremium()` no back respeita `expires_at`); `AdBanner` só aparece para plano grátis com `ads_enabled=true`; `UsageBadge` mostra usos restantes; modal amigável quando limite bate; página `/premium` com comparação Grátis vs Premium.
- **Painel administrativo visual em `/admin`** (protegido por role): sliders para limite grátis/premium e preço; switches para ads globais/banner/intersticial; busca de usuários por e-mail e botões para promover/rebaixar; 3 cards de stats. Sliders com debounce de 350ms.
- **Mercado Pago — Assinatura recorrente mensal (Preapproval)**: `POST /api/checkout/premium` cria preapproval sem plano fixo via SDK (`mercadopago==3.3.0`); frontend redireciona ao `subscriptions/checkout`. Após autorização, MP cobra R$ 9,90/mês automaticamente. `GET /api/subscription` mostra próxima cobrança e `POST /api/subscription/cancel` cancela self-service (mantém Premium até o fim do ciclo). Reuso de preapproval pending evita duplicatas.
- **Webhook seguro**: `POST /api/mercadopago/webhook` valida HMAC-SHA256 (manifest `id:{data.id};request-id:{req};ts:{ts};`) usando `MP_WEBHOOK_SECRET`. Trata `subscription_preapproval` (status sync) e `subscription_authorized_payment` (extend +30 dias idempotente via `processed_mp_events`).
- **Tolerância 3 dias**: `is_premium()` adiciona 3 dias ao `expires_at` quando `preapproval_status == "authorized"` — cobre falhas temporárias de cartão enquanto o MP faz retry. **GraceBanner** amigável no topo de Home, Perfil e Premium quando o usuário entra na tolerância (com contagem de dias restantes e link para atualizar cartão).
- **Painel de faturas**: `GET /api/subscription/invoices` consulta `/authorized_payments/search` do MP e retorna histórico do usuário; UI no `/perfil` mostra data, valor em BRL e status traduzido (Pago/Recusado/Aguardando/etc).
- Rate limit por dia: `/api/generate` retorna HTTP 402 quando usuário grátis passa do `free_daily_limit`.
- Placeholder de anúncio identificado + página de termos.

## Backlog priorizado
### P0
- PWA manifest + ícones + Open Graph.
- Rate limit real por usuário/IP e limite diário.
- Sistema de créditos com decremento por ferramenta (config no admin).

### P1
- Google Auth real (arquitetura já prevista).
- Painel admin completo (CRUD de ferramentas, custos, ads, IA keys).
- Ferramentas "Em breve" prometidas: transcrição de áudio, tradutor, currículo, desconto, juros, compressão de imagem.

### P2
- Premium (arquitetura + gateway).
- AdBanner/Interstitial/Rewarded reais.
- Analytics events (tool_opened, generation_completed, etc.).
- SEO + URLs amigáveis por ferramenta (`/responder-whatsapp` etc.).

## Regras de segurança
- Nunca expor `EMERGENT_LLM_KEY` no frontend.
- Todo texto passa pelo backend; validar tamanho no `GenerateInput`.
- CORS restrito via env; JWT com segredo em env.

## Credenciais de teste
Ver `/app/memory/test_credentials.md`.

## Update Fev/2026 — Gerador de Áudio + Sistema Central de Custos
### Nova ferramenta: audio_gen (ElevenLabs Flash v2.5, pt-BR)
- `POST /api/generate-audio` — retorna MP3 binário; SEM armazenamento (histórico grava apenas texto, voz, chars, duração e custos).
- Voz padrão: `HOfBIVLhom4mc9WvXfyH` (Andrea Lot — feminina pt-BR). Modelo: `eleven_flash_v2_5`.
- Fluxo: contar chars → estimar seg (15 chars/s) → validar limite/generation → **reservar** no `db.usage` com status `reserved` → chamar ElevenLabs → sucesso: `commit` com duração real (mutagen) e chars cobrados (header `character-cost`); falha: **delete** (estorno integral).
- Chave: `ELEVENLABS_API_KEY` lida **APENAS** via `os.environ.get`. Nunca em `.env`, git, frontend, APK ou logs. Configurar via Emergent → Gerenciar implantação → Segredos → Chaves personalizadas.

### Novo módulo `/app/backend/pricing.py` — `AI_PRICING`
- Fórmula margem BRUTA (não markup): `preco = custo / (1 - target_gross_margin)`
- Defaults: `usd_to_brl=5.10`, `fx_safety_buffer=0.10`, `target_gross_margin=0.70`, `mp_fee_rate=0.05`
- Áudio: `usd_per_char=0.00005`, Free 60s/dia (60s por gen), Premium 300s/dia (60s por gen) — **nunca ilimitado**.
- Imagem: `usd_per_image=0.003`, Free 3/dia, Prompt máx **1000 chars** (era 500).
- Texto: `provider_prepaid=true` (Emergent LLM), Free 3/dia.
- Endpoint público de leitura: `GET /api/pricing` (snapshot sem segredos).

### Registros de custo em cada geração (para coletar dados antes de vender pacotes)
- Imagem: `cost.api_usd`, `cost.api_brl_protected`, `cost.min_sale_price_brl`, `cost.min_sale_price_brl_with_mp_fee`
- Áudio: `cost.estimated_api_usd`, `cost.real_api_usd`, `cost.real_api_brl_protected`, `cost.real_min_sale_brl` + `duration_estimated_seconds`, `duration_real_seconds`, `prompt.chars_sent`, `prompt.chars_billed`

### Testes (iteration_14): 12/12 backend, 6/6 frontend — todos passam.

## Update Fev/2026 — Correções Gerador de Áudio v2
- **Bug SDK ElevenLabs 2.65**: `with_raw_response.convert()` é `@contextmanager` — precisa `with ... as raw:` + `b"".join(raw.data)`. Corrigido, sem mais `TypeError`.
- **Cloudflare 502 hijack**: trocado status de erro `502 → 503` para dependência externa; Cloudflare passa JSON pt-BR ao invés da página HTML dele.
- **RCA contagem "cobrados"**: header `character-cost` da ElevenLabs = CRÉDITOS consumidos (Flash v2.5 dá 50% desconto: 500 chars = 250 créditos). Não é literalmente "caracteres". Renomeado no UI/DB: `chars_billed` → `credits_billed`; cost calculation agora usa `len(text) × usd_per_char` (taxa efetiva já discontada), evitando subestimar custo.
- **Meta display** (novo layout em grid): Voz · Duração real · Caracteres enviados · Créditos ElevenLabs (só se header presente) · Custo estimado · Custo real.
- **Escolha de voz**: novo `GET /api/voices` — cache Mongo `voices_cache` (TTL 24h) → refresh live ElevenLabs → fallback estático (só Andrea). Admin: `POST /api/admin/voices/refresh`. Frontend: seção "Escolha uma voz" com filtros Todas/Femininas/Masculinas, cards com nome/gênero/idioma/descrição, botão ▶ Ouvir (usa `preview_url` — não consome limite diário), botão Selecionar, "Voz selecionada: X" antes do Gerar.

## Update Fev/2026 — FASE 1 Auditoria Carteira Universal
### Fix vozes (só 1 aparecia)
- **RCA**: filtro `_is_ptbr(labels)` descartava 99% das vozes porque `labels.language` da ElevenLabs raramente vem preenchido em vozes premade; e Flash v2.5 é multilíngue — descartar por metadata é errado.
- **Correção**: substituído filtro dinâmico por **lista curada manual** (`CURATED_PTBR_VOICES`) com 9 vozes premade conhecidas boas em pt-BR (4 F, 5 M). Backend enriquece `preview_url` via live API quando disponível; se falhar, retorna lista curada sem preview.

### Fix reconhecimento Premium
- **RCA**: backend SEMPRE reconheceu Premium corretamente (validado: Free→Premium 60s→300s em `/api/me/usage` sem re-login). O problema era o **frontend** lendo `subscription.plan` do localStorage, que não sincroniza quando o admin promove alguém externamente.
- **Correção**: `useUsage()` agora sincroniza `subscription.plan` do backend no `localStorage.facilita_user` em cada refresh. `AdBanner` usa `usage.is_premium` (fresh) em vez de `isPremium()` (stale).

### Aprovação pendente
Auditoria Carteira Universal de Créditos entregue ao dono do produto — não implementar até aprovação explícita.
