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
- Painel admin básico via `/api/admin/stats` (usuários, gerações, top ferramentas).
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
