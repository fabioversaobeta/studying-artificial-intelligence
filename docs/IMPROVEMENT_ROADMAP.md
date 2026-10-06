# Roadmap de Correções e Melhorias

Origem: análise técnica do projeto feita em 2026-10-06. Este arquivo é o
**tracker de execução** das correções e melhorias levantadas. Ele é
complementar ao `docs/ROADMAP.md` (que acompanha as *features de produto*);
aqui acompanhamos *dívida técnica, segurança, qualidade e prontidão de produção*.

Última atualização: 2026-10-06 (criação)

---

## Como usar este arquivo (leia antes de pegar um item)

Várias sessões do Claude Code vão trabalhar em paralelo. Para não colidirem:

1. **Escolha um item com status `TODO`** cujas dependências (`Depende de`)
   estejam `DONE`.
2. **Reivindique o item primeiro**: troque o status para `IN_PROGRESS`, preencha
   `Responsável` (nome/branch da sessão) e faça um commit só com essa mudança
   (`docs: claim item X`). Só então comece o trabalho.
3. **Trabalhe em uma branch própria** (`fix/<id>-<slug>`, ex.: `fix/C1-secret-key-guard`),
   idealmente em um git worktree separado. Não trabalhe direto na `master`.
4. **Respeite a coluna "Arquivos"**: ela lista o que o item toca. Dois itens
   `IN_PROGRESS` não devem tocar os mesmos arquivos. Se precisar tocar um
   arquivo fora da lista, anote no item e confira se alguém está nele.
5. **Ao terminar**: rode os quality gates do `CLAUDE.md`, marque o item como
   `DONE`, preencha `Commit/PR` e adicione uma linha ao "Log de progresso" no
   final. Mexa **apenas na sua linha** deste arquivo, para minimizar conflitos
   de merge.
6. **Se ficar bloqueado**, marque `BLOCKED` e escreva o motivo na coluna Notas.
7. Decisões arquiteturais novas vão para `docs/DECISIONS.md`; perguntas em
   aberto vão para `docs/PENDING.md`.
8. Cada item deve virar **commits pequenos e incrementais**, conforme a
   disciplina de commits do `CLAUDE.md`.

**Status válidos:** `TODO` · `IN_PROGRESS` · `BLOCKED` · `DONE` · `WONTDO`
**Prioridade:** `P0` fazer agora · `P1` curto prazo · `P2` médio prazo
**Esforço:** `S` (< 1h) · `M` (algumas horas) · `L` (uma sessão inteira ou mais)

## Progresso geral

| Fase | Itens | Concluídos |
|---|---|---|
| P0 — Fazer agora | 9 | 9 |
| P1 — Curto prazo | 16 | 13 |
| P2 — Médio prazo | 21 | 0 |

*(Atualize estes contadores quando concluir um item.)*

## Estado de referência (linha de base em 2026-10-06)

| Gate | Resultado |
|---|---|
| `pytest` | 51 passando |
| `mypy app` | limpo |
| `tsc` / `oxlint` / `npm run build` | limpos |
| `ruff check` | **48 erros** (todos em `alembic/`, 37 deles E501) |
| `ruff format --check` | **3 arquivos** a reformatar |
| Testes de frontend | inexistentes |
| CI | inexistente |

Meta deste roadmap: todos os gates verdes **e** rodando automaticamente em CI.

---

## Trilha A — Higiene do repositório e lint

Sem dependências entre si, exceto onde indicado. Ótima trilha para uma sessão rápida.

| ID | Item | Prio | Esf. | Status | Responsável | Depende de | Arquivos | Commit/PR | Notas |
|---|---|---|---|---|---|---|---|---|---|
| A1 | Remover `start-here.txt` (25 kB, prompt pessoal), `second-here.txt` e `third-here.txt` (vazios) da raiz e do histórico futuro. Se o conteúdo for útil, mover para fora do repo. | P0 | S | DONE | S1 (`fix/s1-hygiene-lint`) | — | `start-here.txt`, `second-here.txt`, `third-here.txt` | 0a96430 | **Apagar autorizado pelo dono (2026-10-06)** — não precisa confirmar de novo. Apenas `git rm` dos 3 arquivos; não reescrever o histórico. |
| A2 | Mover o "Master Prompt" da raiz para `docs/archive/` com nome sem espaços/travessão e **atualizar a referência no `CLAUDE.md`** (seção "What this project is") e no `README.md`, se houver. | P0 | S | DONE | S1 (`fix/s1-hygiene-lint`) | — | `Claude Code — Master Prompt…md`, `CLAUDE.md`, `README.md` | 058c848 | Não quebrar o link citado no CLAUDE.md. |
| A3 | Zerar o ruff: excluir `alembic/versions/` do lint (`extend-exclude` no `pyproject.toml`) **ou** rodar `--fix`; rodar `ruff format` nos 3 arquivos pendentes (incl. `alembic/env.py`). | P0 | S | DONE | S1 (`fix/s1-hygiene-lint`) | — | `backend/pyproject.toml`, `backend/alembic/**` | 0adefbf | Recomendado: excluir migrations autogeradas do E501, e aplicar `--fix` no que for seguro. |
| A4 | Resolver o warning do `TestClient`/`httpx` (StarletteDeprecationWarning) conforme a recomendação do Starlette. | P2 | S | BLOCKED | | — | `backend/pyproject.toml` | | **Aguardando decisão do dono:** (1) instalar `httpx2>=2.13` no venv/dev deps (recomendação do Starlette; existe no PyPI, v2.0–2.13) ou (2) manter `httpx` e filtrar o warning em `filterwarnings`. A instalação foi negada pelo sistema de permissões na sessão S13. |
| A5 | Corrigir `docs/ROADMAP.md`: a linha "Backend lint/type-check clean (ruff + mypy)" estava incorreta. Só marcar como correta depois de A3. | P0 | S | DONE | S1 (`fix/s1-hygiene-lint`) | A3 | `docs/ROADMAP.md` | 03d9596 | |

## Trilha B — CI/CD

| ID | Item | Prio | Esf. | Status | Responsável | Depende de | Arquivos | Commit/PR | Notas |
|---|---|---|---|---|---|---|---|---|---|
| B1 | Criar GitHub Actions (`.github/workflows/ci.yml`) com dois jobs. **Backend:** serviço Postgres, `ruff check`, `ruff format --check`, `mypy app`, `alembic upgrade head` em banco limpo, `pytest`. **Frontend:** `npm ci`, `npm run lint`, `npm run typecheck`, `npm run build`. Rodar em PR e push na `master`. | P0 | M | DONE | S2 (`fix/s2-secret-guard-and-ci`) | A3 (para o CI já nascer verde) | `.github/workflows/ci.yml` | | Os testes usam `TEST_DATABASE_URL` (ver `tests/conftest.py`). Cachear pip/npm. |
| B2 | Ativar proteção de branch na `master` exigindo CI verde. | P1 | S | TODO | | B1 | (config do GitHub) | | Ação manual do dono no GitHub; a sessão apenas documenta o passo. |
| B3 | Adicionar teste de smoke de migração: `alembic upgrade head` + `alembic downgrade base` + `upgrade head` no CI. | P2 | S | IN_PROGRESS | S13b (`fix/s13b-ci-migrations-coverage`) | B1 | `.github/workflows/ci.yml` | | |

## Trilha C — Segurança e autenticação

Itens C1–C3 mexem em `core/` e `services/auth_service.py`; **fazer em sequência
ou combinar com cuidado** (ver coluna Arquivos).

| ID | Item | Prio | Esf. | Status | Responsável | Depende de | Arquivos | Commit/PR | Notas |
|---|---|---|---|---|---|---|---|---|---|
| C1 | **Falhar o boot em produção** se `secret_key` for o valor default (ou curto demais) ou se `debug=True`. Default de `debug` deve ser seguro. Atualizar `.env.example` e `docs/DEPLOYMENT.md`. Cobrir com testes. | P0 | S | DONE | S2 (`fix/s2-secret-guard-and-ci`) | — | `backend/app/core/config.py`, `backend/.env.example`, `docs/DEPLOYMENT.md`, novo teste | | Risco atual: sem a env var, qualquer um forja JWT. |
| C2 | **Rate limiting** em `/auth/login`, `/auth/register` e `/auth/refresh` (ex.: `slowapi`, por IP e/ou por e-mail). Limites configuráveis via env. Retornar 429 no formato de erro padrão. | P1 | M | DONE | S7 (`fix/s7-auth-hardening`) | — | `backend/app/main.py`, `backend/app/api/v1/auth.py`, `backend/pyproject.toml`, `backend/app/core/config.py` | 60f5eb7 | Atrás de proxy (Railway), usar o IP correto (`X-Forwarded-For`). |
| C3 | **Rotação de refresh token + revogação**: adicionar claim `jti`; refresh usado fica inválido; endpoint `POST /auth/logout` revoga o par; denylist/tabela em Postgres (sem Redis). Nova migration. Atualizar o frontend para chamar o logout. | P1 | L | IN_PROGRESS | S12 (`fix/s12-token-rotation`) | C1 | `backend/app/core/security.py`, `backend/app/services/auth_service.py`, `backend/app/api/deps.py`, `backend/app/api/v1/auth.py`, `backend/app/models/user.py`, nova migration, `frontend/src/services/auth-service.ts`, `frontend/src/features/auth/*` | | Resolve também o item de `docs/PENDING.md` "Token revocation". Registrar a decisão em `DECISIONS.md`. Considerar reduzir o access token de 24h para ~15–60 min. |
| C4 | **Política de cadastro**: flag `REGISTRATION_ENABLED` e/ou código de convite, para o deploy público não aceitar signups arbitrários. | P1 | S | DONE | S7 (`fix/s7-auth-hardening`) | — | `backend/app/core/config.py`, `backend/app/services/auth_service.py`, `backend/app/api/v1/auth.py`, `frontend/src/pages/register-page.tsx` | 60f5eb7, 77feace | Conflita com C2/C3 em `auth.py` — combinar ordem. |
| C5 | **Decisão sobre armazenamento de tokens no frontend** (localStorage vs cookie httpOnly + CSRF). Se mantiver localStorage, documentar o risco e adicionar CSP/headers de segurança (Vercel `headers`). | P2 | M | TODO | | C3 | `frontend/vercel.json`, `frontend/src/lib/token-storage.ts`, `docs/DECISIONS.md` | | Hoje não há `dangerouslySetInnerHTML`/`rehype-raw` (verificado), então o risco é baixo, mas o refresh dura 30 dias. |
| C6 | Revisar CORS para produção (origens explícitas via env; `allow_methods`/`allow_headers` restritos em vez de `*`). | P1 | S | DONE | S7 (`fix/s7-auth-hardening`) | — | `backend/app/main.py`, `backend/app/core/config.py` | 0d81d42 | Conflita com C2 em `main.py`. |

## Trilha D — Robustez do backend

| ID | Item | Prio | Esf. | Status | Responsável | Depende de | Arquivos | Commit/PR | Notas |
|---|---|---|---|---|---|---|---|---|---|
| D1 | Tratar `IntegrityError` → 409 (race condition no registro com e-mail duplicado) e adicionar um handler global para exceções não tratadas (500 com corpo padrão `{error:{code,message}}`, sem vazar stack). Teste da corrida. | P0 | S | DONE | S3 (`fix/s3-error-handling-health`) | — | `backend/app/main.py`, `backend/app/core/exceptions.py`, `backend/app/services/auth_service.py`, novo teste | 0d8c244 | Conflita com C2/C6 em `main.py` — coordenar. |
| D2 | `/health/ready` deve devolver **503** (não 500) quando o banco falhar, e usar a dependência `get_db` em vez de `SessionLocal` manual. | P0 | S | DONE | S3 (`fix/s3-error-handling-health`) | — | `backend/app/main.py`, novo teste | 0d8c244 | |
| D5 | **Paginação** (`limit`/`offset` ou cursor, com teto máximo) nas listagens: study sessions, XP awards, goals, reviews, submissions. Schema de resposta consistente. | P1 | M | DONE | S9 (`fix/s9-pagination`) | — | `backend/app/api/v1/*.py`, `backend/app/repositories/*.py`, `backend/app/schemas/*.py`, `docs/API.md` | 9f1e08f | Contrato do corpo inalterado (array); total no header `X-Total-Count`. Frontend (G1–G3) pode adotar `limit`/`offset`. |
| D3 | Corrigir a recursão `award_xp` ↔ `check_and_award_achievements`: atualizar `earned_codes` dentro do loop / tornar a avaliação iterativa e idempotente. Teste com duas conquistas desbloqueadas na mesma passada. | P1 | M | DONE | S8 (`fix/s8-gamification`) | — | `backend/app/services/gamification_service.py`, `backend/tests/` | ba1b72e | **Bug real confirmado pela S5** (teste `xfail(strict=True)` em `tests/test_gamification_service.py::TestAchievements::test_two_achievements_unlock_in_the_same_pass`): o loop usa um snapshot de `earned_codes`; quando a conquista A paga XP, o `award_xp` reentra e concede B; o loop externo chega em B com snapshot velho e viola `uq_user_achievement` (500). Correção: reler `earned_codes` dentro do loop (ou pagar XP após o loop e reavaliar) e adicionar `order_by` em `list_achievements`. Ao corrigir, **remover o marcador xfail**. |
| D4 | **Tirar efeito colateral do `GET`** das quests: concluir quests em evento (quando o XP é concedido) e deixar `GET /quests` somente leitura. Atualizar `DECISIONS.md` (a decisão atual diz o contrário). | P1 | M | DONE | S8 (`fix/s8-gamification`) | D3 (mesmo serviço) | `backend/app/services/quest_service.py`, `backend/app/services/gamification_service.py`, `backend/app/api/v1/gamification.py`, `docs/DECISIONS.md` | 86e0912 | |
| D6 | Adicionar `DELETE` para goals e study sessions (e ao `apiClient.delete` no frontend). Decidir se deletar sessão estorna XP/mastery (provavelmente **não** — soft delete ou bloquear). | P2 | M | TODO | | — | `backend/app/api/v1/goals.py`, `backend/app/api/v1/study_sessions.py`, `backend/app/services/learning_service.py`, `frontend/src/services/api-client.ts` | | Registrar a decisão sobre XP em `DECISIONS.md`. |
| D7 | Separar migração/seed do boot do servidor (`railway.toml` roda `alembic upgrade head` + seeds a cada start). Usar um release/pre-deploy command ou um passo único para evitar corrida com múltiplas réplicas. | P2 | S | TODO | | H1 | `backend/railway.toml`, `docs/DEPLOYMENT.md` | | Só vale mexer depois do deploy real. |

## Trilha E — Performance

| ID | Item | Prio | Esf. | Status | Responsável | Depende de | Arquivos | Commit/PR | Notas |
|---|---|---|---|---|---|---|---|---|---|
| E1 | **Eliminar N+1** em `learning_service`: `_competency_with_state` (3–4 queries por competência + loop de pré-requisitos) e `list_subjects` (1 query por subject). Carregar mastery, minutos e pré-requisitos em lote (`IN`), por subject/usuário. Manter o contrato da API; adicionar teste que conta queries. | P1 | M | DONE | S6 (`fix/s6-n-plus-one`) | — | `backend/app/services/learning_service.py`, `backend/app/repositories/{learning_catalog,mastery,study}_repository.py`, `backend/tests/` | de8d0b9 | Hoje funciona (30 competências), mas não escala. Verificar também `dashboard_service`. |
| E2 | Índices: revisar queries mais frequentes (por `user_id` + data/competência) e adicionar índices ausentes via migration. | P2 | S | TODO | | E1 | nova migration, `backend/app/models/*.py` | | Medir com `EXPLAIN` antes. |

## Trilha F — Testes

| ID | Item | Prio | Esf. | Status | Responsável | Depende de | Arquivos | Commit/PR | Notas |
|---|---|---|---|---|---|---|---|---|---|
| F1 | **Infra de testes do frontend**: Vitest + Testing Library + jsdom; script `npm test`; integrar ao CI (B1). Primeiros testes: `api-client` (refresh dedup em 401 concorrentes, retry único, limpeza de tokens), `protected-route`, `token-storage`. | P0 | M | DONE | S4 (`fix/s4-frontend-tests`) | — | `frontend/package.json`, `frontend/vite.config.ts`, `frontend/src/**/*.test.ts(x)` | `6a1358b`..`42dfaab` (branch `fix/s4-frontend-tests`) | Maior risco de regressão hoje. |
| F2 | Testes de frontend das páginas principais (login/registro, dashboard, goals) com a API mockada (MSW ou fetch mock). | P1 | M | DONE | S10 (`fix/s10-frontend-page-tests`) | F1 | `frontend/src/pages/*.test.tsx` | | 12984e4 |
| F3 | Backend: testes dedicados para `challenge_service` (XP só na 1ª aprovação), `quest_service`, `review_service` (SM-2 via API), `dashboard_service`, `gamification_service` (streak em virada de dia, conquistas). | P1 | M | DONE | S5 (`fix/s5-backend-tests`) | — | `backend/tests/**` | `444d509`..`b0d5919` | Só adiciona arquivos novos → baixo risco de conflito. Achado: bug de conquistas duplicadas (ver xfail em `test_gamification_service.py`); novo helper `tests/factories.py`. |
| F4 | Testes de autorização: um usuário não acessa/altera dados de outro (goals, sessions, submissions, reviews). | P1 | S | DONE | S5 (`fix/s5-backend-tests`) | — | `backend/tests/test_authorization.py` | `88f54a8` | |
| F5 | Medir cobertura (`pytest-cov`) e definir um piso mínimo no CI. | P2 | S | IN_PROGRESS | S13b (`fix/s13b-ci-migrations-coverage`) | B1, F3 | `backend/pyproject.toml`, `.github/workflows/ci.yml` | | |

## Trilha G — Funcionalidades de frontend (backend já pronto)

| ID | Item | Prio | Esf. | Status | Responsável | Depende de | Arquivos | Commit/PR | Notas |
|---|---|---|---|---|---|---|---|---|---|
| G1 | **UI de revisão espaçada**: página com a fila de `GET /reviews/due` e envio de recall (`quality` 0–5) em `POST /reviews/{id}/recall`; estado vazio; atalho no dashboard. | P1 | M | DONE | S11 (`fix/s11-frontend-screens`) | — | `frontend/src/pages/reviews-page.tsx` (novo), `frontend/src/services/learning-service.ts`, `frontend/src/types/api.ts`, `frontend/src/routes/router.tsx`, `frontend/src/layouts/app-layout.tsx` | d0842bd | É o diferencial de retenção do produto. |
| G2 | **UI de conquistas e quests** (`/gamification/achievements`, `/gamification/quests`): progresso, desbloqueadas vs bloqueadas. | P1 | M | DONE | S11 (`fix/s11-frontend-screens`) | D4 (idealmente) | `frontend/src/pages/achievements-page.tsx` (novo), `frontend/src/services/gamification-service.ts`, `frontend/src/types/api.ts`, `frontend/src/routes/router.tsx`, `frontend/src/layouts/app-layout.tsx` | d3f0755 | Pode começar antes de D4; o contrato não muda. |
| G3 | **UI de learning paths** (`/learning-paths`): listagem e detalhe, com progresso por etapa. | P1 | M | DONE | S11 (`fix/s11-frontend-screens`) | — | `frontend/src/pages/learning-paths-page.tsx` (novo), `frontend/src/services/learning-service.ts`, `frontend/src/types/api.ts`, `frontend/src/routes/router.tsx`, `frontend/src/layouts/app-layout.tsx` | e77c3ea | Sem "progresso por etapa" (maestria por competência exigiria N chamadas); links levam à matéria. G1/G2/G3 colidem em `router.tsx`, `app-layout.tsx` e `types/api.ts` — são edições pequenas, mas **faça rebase frequente**. |
| G4 | Tratamento global de erros no frontend: Error Boundary, toasts de erro de API, estados de loading/erro consistentes (`use-async`). | P2 | M | IN_PROGRESS | S14 (`fix/s14-frontend-quality`) | — | `frontend/src/app/app.tsx`, `frontend/src/hooks/use-async.ts`, `frontend/src/components/ui/*` | | |
| G5 | Revisão de acessibilidade (WCAG AA): foco, contraste do tema escuro, labels, navegação por teclado. | P2 | M | IN_PROGRESS | S14 (`fix/s14-frontend-quality`) | — | `frontend/src/**` | | Usar a skill `design:accessibility-review`. |

## Trilha H — Deploy e observabilidade

| ID | Item | Prio | Esf. | Status | Responsável | Depende de | Arquivos | Commit/PR | Notas |
|---|---|---|---|---|---|---|---|---|---|
| H1 | **Deploy real (ADIADO até o fim do roadmap)** em Railway (backend + Postgres) e Vercel (frontend), seguindo `docs/DEPLOYMENT.md`; verificar o fluxo completo em produção; corrigir o doc com o que for diferente da prática. | P1 | L | TODO | | C1, C6, D2 | `docs/DEPLOYMENT.md`, configs de deploy | | **Decisão do dono (2026-10-06): o deploy só acontece quando todo o resto deste roadmap estiver concluído.** Não iniciar antes. Requer ações do dono (contas/segredos); a sessão guia e verifica, sem inserir credenciais. |
| H2 | Observabilidade mínima: `request_id` nos logs (middleware), logging estruturado e Sentry (opcional, via DSN em env). | P2 | M | IN_PROGRESS | S15 (`fix/s15-observability`) | H1 | `backend/app/main.py`, `backend/app/core/`, `backend/pyproject.toml` | | Conflita com outros itens em `main.py`. |
| H3 | Backup/restore do Postgres de produção documentado (Railway) e teste de restauração. | P2 | S | TODO | | H1 | `docs/DEPLOYMENT.md` | | |

## Trilha I — Produto (alinhado ao objetivo de entrevistas)

Itens maiores; cada um merece um plano próprio e entrada em `docs/DECISIONS.md`
antes de codar. Não iniciar antes das trilhas P0/P1 críticas (C, D, F1) estarem
estáveis.

| ID | Item | Prio | Esf. | Status | Responsável | Depende de | Arquivos | Commit/PR | Notas |
|---|---|---|---|---|---|---|---|---|---|
| I1 | **Camada `ai_service` provider-agnóstica** (interface + 1 provider Claude + fake para testes), sem SDK de provider fora dela. Base do AI Mentor e do grader. | P2 | L | TODO | | — | `backend/app/services/ai_service.py` (novo), `backend/app/core/config.py` | | Ver `docs/PENDING.md`. Se usar a API da Anthropic, carregar a skill `claude-api`. |
| I2 | **Assessments / banco de questões** (`Assessment`, `Question`, tentativas, alimentando mastery). | P2 | L | TODO | | — | modelos, migration, services, API, seeds | | Aditivo; nada do schema atual muda. |
| I3 | **Motor de recomendação** "o que estudar hoje" (revisões vencidas + competências desbloqueadas + metas). | P2 | L | TODO | | G1, G3 | novo service/endpoint/UI | | |
| I4 | **Simulação de entrevista** (`InterviewSession`, sessões guiadas, pontuação). | P2 | L | TODO | | I1, I2 | modelos, services, API, UI | | |
| I5 | **Correção automática de challenges** (LLM-as-judge) com dataset dourado de regressão antes de conceder XP automaticamente. | P2 | L | TODO | | I1 | `challenge_service.py`, testes de avaliação | | Ver `docs/PENDING.md`. |

---

## Trilha J — Itens descobertos durante a execução

Surgiram nos relatórios das sessões (S5, S9, S11, S7). Mesmo formato das trilhas acima.

| ID | Item | Prio | Esf. | Status | Responsável | Depende de | Arquivos | Commit/PR | Notas |
|---|---|---|---|---|---|---|---|---|---|
| J1 | Incluir nome da competência e da matéria no payload de `GET /reviews/due` e remover o `competency-index.ts` do frontend (hoje faz N+1 chamadas a `/subjects` e `/subjects/{id}`). | P2 | S | TODO | | — | `backend/app/schemas/learning.py`, `backend/app/services/review_service.py`, `backend/app/repositories/review_repository.py`, `frontend/src/features/learning/competency-index.ts`, `frontend/src/pages/reviews-page.tsx` | | Achado da S11. Mudança aditiva no contrato. |
| J2 | Progresso por etapa nas learning paths: expor a maestria do usuário por etapa em `GET /learning-paths/{slug}` e mostrar na UI (o G3 entregou sem progresso). | P2 | M | TODO | | — | `backend/app/api/v1/learning_paths.py`, `backend/app/schemas/learning.py`, `backend/app/services/learning_service.py`, `frontend/src/pages/learning-path-detail-page.tsx` | | Achado da S11. Reaproveitar o carregamento em lote do E1. |
| J3 | Usar a paginação (`limit`/`offset`, `X-Total-Count`) no frontend: "carregar mais" em goals, sessões de estudo e revisões. | P2 | M | IN_PROGRESS | S14 (`fix/s14-frontend-quality`) | — | `frontend/src/services/*.ts`, `frontend/src/pages/goals-page.tsx`, `frontend/src/pages/reviews-page.tsx` | | O D5 manteve o corpo como array; falta consumir o header. |
| J4 | **Decisão do dono**: sessões de estudo < 10 min dão 0 XP e não contam no streak (ver `docs/PENDING.md`). Implementar a opção escolhida. | P2 | S | BLOCKED | | decisão do dono | `backend/app/services/learning_service.py`, `backend/app/services/gamification_service.py` | | Bloqueado até o dono escolher (a/b/c em PENDING.md). |
| J5 | Rate limiter em memória é por processo (S7): se houver mais de 1 worker/réplica, mover o estado para Postgres/Redis. No deploy, definir `TRUST_PROXY_HEADERS=true` na Railway. | P2 | M | TODO | | H1 | `backend/app/core/rate_limit.py`, `docs/DEPLOYMENT.md` | | Só relevante se escalar para mais de 1 instância; o `TRUST_PROXY_HEADERS` entra no passo do deploy. |

## Mapa de conflitos (para quem coordena as sessões)

Arquivos com maior chance de edição simultânea. Se dois itens abaixo estiverem
`IN_PROGRESS` ao mesmo tempo, as sessões devem fazer rebase frequente.

| Arquivo | Itens que o tocam |
|---|---|
| `backend/app/main.py` | C2, C6, D1, D2, H2 |
| `backend/app/core/config.py` | C1, C2, C4, C6, I1 |
| `backend/app/api/v1/auth.py` / `auth_service.py` | C2, C3, C4, D1 |
| `backend/app/services/gamification_service.py` | D3, D4 |
| `backend/pyproject.toml` | A3, A4, C2, F5, H2 |
| `.github/workflows/ci.yml` | B1, B3, F1, F5 |
| `frontend/src/routes/router.tsx`, `layouts/app-layout.tsx`, `types/api.ts` | G1, G2, G3 |
| `docs/DEPLOYMENT.md` | C1, D7, H1, H3 |

### Sugestão de paralelização inicial (sem sobreposição de arquivos)

| Sessão | Itens | Observação |
|---|---|---|
| 1 | A1, A2, A3, A5 | Higiene + lint; destrava o CI |
| 2 | C1, depois B1 | Segredo seguro, depois CI |
| 3 | D1 + D2 (juntos) | Ambos em `main.py`; uma sessão só |
| 4 | F1 | Infra de testes do frontend |
| 5 | F3 + F4 | Só arquivos novos em `backend/tests/` |
| 6 | E1 | Performance em `learning_service` e repositories |

---

## Log de progresso

*Uma linha por item concluído, do mais recente para o mais antigo. Formato:
`AAAA-MM-DD — ID — resumo — commit/PR`*

- 2026-10-06 — C2 — rate limiting em memória (por IP; login também por e-mail) em login/register/refresh, 429 padronizado + Retry-After; X-Forwarded-For só com TRUST_PROXY_HEADERS — `60f5eb7`
- 2026-10-06 — C4 — `REGISTRATION_ENABLED` e `REGISTRATION_INVITE_CODE`; `GET /auth/registration-info`; campo de convite na register-page — `60f5eb7`, `77feace`
- 2026-10-06 — C6 — CORS com métodos/headers restritos, origens via JSON ou CSV, `*` rejeitado em produção — `0d81d42`
- 2026-10-06 — D5 — paginação limit/offset (default 50, máx 200) + X-Total-Count em study-sessions, goals e reviews/due; corpo segue array; XP awards/submissions não têm endpoint de listagem — 9f1e08f
- 2026-10-06 — F2 — testes de frontend (Vitest + fetch mock) para auth-context, login, register, dashboard, goals, subjects e subject-detail (43 testes novos) — 12984e4
- 2026-10-06 — G3 — páginas de learning paths (lista + detalhe por slug) com link para a matéria de cada etapa — e77c3ea
- 2026-10-06 — G2 — página de conquistas (desbloqueadas vs bloqueadas) e quests com barra de progresso — d3f0755
- 2026-10-06 — G1 — página de revisões (fila de vencidas, recall 0–5, próximo intervalo) + atalho no dashboard — d0842bd
- 2026-10-06 — D4 — quests completam em evento (`settle_rewards`); `GET /gamification/quests` é somente leitura; DECISIONS.md atualizado — 86e0912
- 2026-10-06 — D3 — `settle_rewards` iterativo e idempotente (sem recursão/snapshot velho), `order_by` em achievements/quests, xfail removido — ba1b72e
- 2026-10-06 — F3 + F4 — testes dedicados de challenge/quest/review/dashboard/gamification e `test_authorization.py` (+130 testes, 1 xfail estrito documentando bug de conquistas duplicadas) — `444d509`..`88f54a8`
- 2026-10-06 — F1 — Vitest + Testing Library + jsdom; testes de api-client, token-storage e protected-route (20 testes); corrigido crash do api-client com corpo de erro sem `error` — `6a1358b`..`42dfaab`
- 2026-10-06 — E1 — N+1 eliminado em learning_service (queries em lote; detalhe 62→5, lista 10→4 em 15 competências); testes de caracterização e contagem de queries — de8d0b9
- 2026-10-06 — D1 — `IntegrityError` no registro vira 409; handler global devolve 500 padronizado sem stack (FastAPI sem `debug`) — 0d8c244
- 2026-10-06 — D2 — `/health/ready` usa `get_db` e devolve 503 `{"status":"unavailable"}` quando o banco falha — 0d8c244
- 2026-10-06 — A5 — ROADMAP.md: linha de lint/type-check corrigida e verificada — 03d9596
- 2026-10-06 — A3 — ruff check/format zerados; alembic/versions excluído do lint via extend-exclude — 0adefbf
- 2026-10-06 — A2 — Master Prompt movido para docs/archive/master-prompt-learning-platform.md; CLAUDE.md atualizado — 058c848
- 2026-10-06 — A1 — start/second/third-here.txt removidos — 0a96430
- 2026-10-06 — B1 — CI no GitHub Actions (backend + frontend, Postgres, cache pip/npm); ruff pode ficar vermelho até S1/A3 ser mergeada — 17de298
- 2026-10-06 — C1 — boot falha em produção com secret_key default/curta (<32) ou debug=True; debug agora default False — 9a1c7ec
- 2026-10-06 — (roadmap criado a partir da análise técnica; nenhum item executado ainda)
- 2026-10-06 — wave 3 iniciada: S12 (C3), S13 (A4,B3,F5), S14 (G4,G5,J3), S15 (H2) reivindicadas; Trilha J criada com itens descobertos (J1–J5)
- 2026-10-06 — wave 2 iniciada: S7 (C2,C4,C6), S8 (D3,D4), S9 (D5), S10 (F2), S11 (G1,G2,G3) reivindicadas em lote pelo coordenador
- 2026-10-06 — decisões do dono: A1 autorizado; deploy (H1) adiado para o fim; sessões S1–S6 iniciadas (reivindicadas em lote pelo coordenador)
