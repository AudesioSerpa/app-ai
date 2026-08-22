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

## Escopo MVP (10 ferramentas)
1. Responder WhatsApp • 2. Melhorar texto • 3. Corrigir português • 4. Resumir texto •
5. Criar e-mail • 6. Criar legenda • 7. Títulos para YouTube • 8. QR Code (local) •
9. Gerador de senhas (local) • 10. Calculadora de porcentagem (local).

## Stack
- Frontend: React 19 + React Router + Tailwind + shadcn + qrcode.react.
- Backend: FastAPI + Motor (MongoDB) + JWT + bcrypt + Emergent LLM (GPT-5.4 Mini).
- Auth: e-mail/senha (JWT). Google Auth previsto como toggle no painel (mock informativo).
- Deploy: supervisor + Kubernetes ingress (`/api` prefix).

## O que está implementado (Fev/2026)
- 10 ferramentas do MVP com UI mobile-first e tema escuro.
- Auth JWT (login/registro), seed do admin (`admin@facilita.ai` / `Facilita@123`).
- `/api/generate` roteia IA vs. locais (senha e %) e grava histórico completo (prompt+resultado).
- Favoritos sincronizados: hook usa localStorage + `/api/favorites` (GET/POST/DELETE) quando logado.
- Histórico com fetch autenticado, agrupamento por dia, reabrir em modal, copiar e excluir.
- QR Code corrigido (agora lê `fields.text`).
- **Monetização**: sistema centralizado (`isPremium()` no back respeita `expires_at`); `AdBanner` só aparece para plano grátis com `ads_enabled=true`; `UsageBadge` mostra usos restantes; modal amigável quando limite bate; página `/premium` com comparação Grátis vs Premium.
- **Painel administrativo visual em `/admin`** (protegido por role): sliders para limite grátis/premium e preço; switches para ads globais/banner/intersticial; busca de usuários por e-mail e botões para promover/rebaixar; 3 cards de stats. Sliders com debounce de 350ms.
- **Mercado Pago — Assinatura recorrente mensal (Preapproval)**: `POST /api/checkout/premium` cria preapproval sem plano fixo via SDK (`mercadopago==3.3.0`); frontend redireciona ao `subscriptions/checkout`. Após autorização, MP cobra R$ 9,90/mês automaticamente. `GET /api/subscription` mostra próxima cobrança e `POST /api/subscription/cancel` cancela self-service (mantém Premium até o fim do ciclo). Reuso de preapproval pending evita duplicatas.
- **Webhook seguro**: `POST /api/mercadopago/webhook` valida HMAC-SHA256 (manifest `id:{data.id};request-id:{req};ts:{ts};`) usando `MP_WEBHOOK_SECRET`. Trata `subscription_preapproval` (status sync) e `subscription_authorized_payment` (extend +30 dias idempotente via `processed_mp_events`).
- **Tolerância 3 dias**: `is_premium()` adiciona 3 dias ao `expires_at` quando `preapproval_status == "authorized"` — cobre falhas temporárias de cartão enquanto o MP faz retry.
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
