# Proposta — Trilha I (produto alinhado às entrevistas)

Status: **APROVADA pelo dono em 2026-10-06 — Fase 1 iniciada (I2 + I1 + J6).** Decisões do dono no §3.1.
Data: 2026-10-06. Relacionada a `docs/IMPROVEMENT_ROADMAP.md` (itens I1–I5),
`docs/PRODUCT.md`, `docs/PENDING.md` e ao brief original arquivado em
`docs/archive/master-prompt-learning-platform.md`.

## 1. Objetivo

Transformar a plataforma de "registro de estudo com gamificação" em uma
ferramenta de **preparação ativa para entrevistas técnicas internacionais**:
perguntas reais, correção com feedback, simulação de entrevista e uma
recomendação diária do que estudar. Tudo respeitando os princípios do
produto: *conteúdo é dado*, *XP ≠ mastery*, *transparente > esperto*,
*um v1 real em vez de um completo fake*.

## 2. Princípios de design para esta trilha

1. **IA como camada substituível.** Nenhum SDK de provedor fora de
   `app/services/ai/`. Interface estreita, provider real + provider *fake*
   determinístico para testes (a suíte nunca chama rede).
2. **O que pode ser determinístico, é.** Banco de questões (I2) e
   recomendação (I3) funcionam **sem LLM** na primeira versão. A IA entra onde
   agrega algo que regra não faz: avaliar respostas abertas e conduzir uma
   entrevista.
3. **IA nunca concede XP ou mastery sozinha antes de ser validada.** Um
   avaliador LLM só passa a alimentar XP/mastery depois de passar por um
   *golden dataset* de regressão (já previsto em `docs/PENDING.md`). Até lá, o
   resultado é *feedback consultivo* e o usuário confirma o resultado.
4. **Entrada do usuário é dado, não instrução** (prompt injection):
   respostas e descrições de vaga vão em campos delimitados, saída do modelo é
   validada contra um schema estrito antes de ser usada.
5. **Custo e privacidade controlados:** teto de gasto/limite de chamadas por
   usuário/dia, timeout e retry limitados, logs sem o conteúdo das respostas
   (só ids, tamanhos, latência, tokens).
6. **Conteúdo gerado por IA entra por revisão humana:** perguntas geradas
   por LLM viram *seeds* revisados pelo dono (conteúdo é dado versionado), não
   são geradas em tempo de execução para o aluno.

## 3. Decisões que preciso de você (bloqueiam o início)

| # | Decisão | Minha recomendação |
|---|---|---|
| D1 | **Provedor de LLM** | Claude (API da Anthropic) como primeiro provider, atrás da abstração; modelo configurável por env. |
| D2 | **Orçamento/teto** de uso de IA (por dia/mês) | Teto diário configurável, padrão baixo; ao estourar, a feature degrada para "feedback indisponível" sem quebrar o fluxo. |
| D3 | **Idiomas** de questões e entrevista | Conteúdo técnico em **inglês** (alvo: vagas internacionais) com interface em inglês; opção de explicações em pt-BR no mentor. |
| D4 | **Assessments alimentam o mastery?** | Sim: o sinal *Practice* (35 pts) passa a considerar *challenges + quizzes*, mantendo o total em 100 e a fórmula documentada em `DOMAIN.md`. |
| D5 | **XP de quiz** | XP só na 1ª aprovação por questão/assessment (mesma regra anti-farm dos challenges); tentativas repetidas contam para mastery, não para XP. |
| D6 | **Quem escreve as questões** | Eu gero rascunhos por competência em lotes; você revisa antes de entrar nos seeds. Definir meta inicial (ex.: 8–12 questões/competência nas 30 competências). |
| D7 | **Chave de API** | Fica só em variável de ambiente (nunca no repo); você a fornece na hora de habilitar o provider real. Antes disso tudo roda com o provider fake. |


### 3.1 Decisões do dono (2026-10-06)

| # | Decisão final |
|---|---|
| D1 | **API do Claude (Anthropic)**. A chave (`ANTHROPIC_API_KEY`) será preenchida pelo dono nas variáveis de ambiente do Railway; nunca vai para o repo. Até lá, tudo roda com o provider *fake*. |
| D2 | **Sem teto de orçamento no primeiro momento**: o dono vai medir o uso em produção. Mantemos apenas a *medição* (`ai_usage`: tokens, latência, custo estimado) e um teto **opcional e desligado por padrão** (configurável por env) para poder ligar depois sem mudar código. |
| D3 | **Idioma escolhido pelo usuário, inglês como padrão** (`en`, com `pt-BR` disponível). Vale para o conteúdo (questões, explicações), para o mentor/avaliador de IA e para a simulação de entrevista. A localização das *strings da interface* é um item separado (J7), fora da Fase 1. |
| D4 | Assessments alimentam o sinal *Practice* do mastery (recomendação aceita; fórmula exata definida pelo I2 e documentada em `DOMAIN.md`). |
| D5 | **XP: o dono delegou; decisão registrada abaixo.** |
| D6 | **As questões são escritas pela IA** (Claude), em lote, por matéria, nos dois idiomas, entrando como seeds marcados `source=ai_generated`, com validação automática de estrutura e consistência. |

**Regra de XP adotada (D5)** — projetada para recompensar *atividade genuína* sem
permitir farm nem premiar chute, mantendo XP separado de mastery:
1. XP só é concedido ao **finalizar** uma tentativa e somente se a nota for ≥ ao
   limiar de aprovação do assessment (padrão 70%). Chutar uma questão solta não paga nada.
2. Numa tentativa aprovada, o XP é a soma do `xp_value` (por dificuldade:
   fácil/médio/difícil) apenas das questões acertadas **pela primeira vez na vida do usuário**,
   mais um bônus de conclusão **na primeira aprovação** daquele assessment.
3. Tentativas repetidas **não** rendem XP de questões já pagas nem novo bônus; elas contam
   para o **mastery** (que mede conhecimento) e para o streak/quests normalmente.
4. O total é naturalmente limitado pelo tamanho do banco de questões (não há farm infinito);
   o ledger registra a fonte `assessment` e o `reference_id` da tentativa.
5. **Sem estorno** de XP em nenhum caso (mesma decisão do D6/delete).

## 4. Escopo por item

### I2 — Assessments / banco de questões (sem IA)
- **Modelo (aditivo):** `Question` (competência, tipo: `multiple_choice` |
  `multi_select` | `short_answer` | `code_reading`, enunciado markdown,
  opções, resposta/explicação, dificuldade, tags, `source`), `Assessment`
  (conjunto de questões: por competência, por trilha ou "misto"),
  `AssessmentAttempt` e `QuestionResponse` (resposta, correta?, tempo).
- **Correção determinística** para múltipla escolha/multi-select; respostas
  abertas ficam `pending_review` até existir o avaliador (I5) ou
  auto-avaliação guiada (mostrar a resposta-modelo e o usuário marca).
- **API:** iniciar tentativa, responder, finalizar, histórico, estatísticas por
  competência. Paginação já padronizada (D5 concluído).
- **Integração:** mastery (D4), XP (D5), achievements/quests (novos critérios,
  ex. `assessments_passed_count`), spaced repetition (questão errada vira
  revisão da competência).
- **Frontend:** tela de quiz (uma questão por vez, teclado acessível), resultado
  com explicações, histórico.
- **Tamanho:** L. **Dependências:** nenhuma (já pode começar). Migração própria.

### I1 — Camada `ai_service` provider-agnóstica
- Interface `AIProvider` (ex.: `complete(messages, *, schema, max_tokens)`
  com saída estruturada), `ClaudeProvider`, `FakeProvider` (respostas
  determinísticas por fixture), configuração por env (provider, modelo, chave,
  timeout, teto diário).
- Guardrails do §2 implementados **uma vez** aqui: validação de schema,
  limite de tokens, medição de custo/uso (tabela `ai_usage` simples),
  tratamento de falha/timeout, `request_id` propagado (reaproveita H2).
- **Sem feature de produto ainda**: apenas a fundação + testes + um endpoint
  interno de saúde ("provider configurado?") para validar a integração.
- **Tamanho:** M–L. **Dependências:** D1, D2, D7 (para o provider real; o fake
  não precisa). Pode ser feito **em paralelo** com I2.

### I3 — Recomendação "o que estudar hoje" (regra, sem LLM)
- Serviço determinístico e explicável: combina revisões vencidas (SRS),
  competências `learning` com maior queda de retenção, próxima competência
  `available` em uma learning path ativa e metas com prazo próximo. Cada
  sugestão devolve o **motivo** ("porque…"), em linha com *transparente > esperto*.
- Endpoint `GET /recommendations/today` + card no dashboard.
- Versão futura opcional: o mentor (I1) reescreve a explicação em linguagem
  natural, mas a *decisão* continua sendo da regra.
- **Tamanho:** M. **Dependências:** G1/G3 e J2 (concluídos/em andamento);
  melhor depois de I2 para incluir "faça um quiz de X".

### I5 — Correção automática (LLM-as-judge) de respostas abertas/challenges
- Avaliador com **rubrica por questão/challenge** (critérios, pesos, exemplos
  de resposta forte/fraca) em dados; saída estruturada `{score, critérios,
  feedback, confiança}`.
- **Golden dataset** versionado (respostas rotuladas por você) + suíte de
  avaliação offline (concordância do juiz com os rótulos) com um piso
  mínimo antes de ligar qualquer efeito em XP/mastery. Até lá: modo
  *consultivo* (mostra nota sugerida, usuário confirma).
- Defesas: prompt injection, respostas vazias/gaming, consistência (mesma
  resposta → nota estável; amostragem repetida).
- **Tamanho:** L. **Dependências:** I1, I2 (formato de resposta/rubrica) e o
  golden dataset (trabalho seu + meu).

### I4 — Simulação de entrevista
- Modelo `InterviewSession` + `InterviewTurn`: tipos *coding*, *system
  design*, *behavioral*, *AI/ML*; roteiro por banco de perguntas (dados), com
  follow-ups conduzidos pelo mentor (I1) e **encerramento com relatório**:
  pontos fortes, lacunas, competências a reforçar (alimenta I3 e SRS).
- Formato textual no v1 (sem voz); *timer* e modo "sem ajuda" opcionais;
  rubrica por tipo; nada de XP automático até o juiz estar validado (I5).
- **Tamanho:** L (o maior). **Dependências:** I1, I2; idealmente I5.

### (Opcional, fora da lista original) — Career readiness vs. job description
Prevista em `PRODUCT.md`: colar uma vaga, extrair competências exigidas e
comparar com o mastery atual (lacunas → recomendações). Só depois de I1/I3.
Proponho **adiar** e decidir após a Fase 3.

## 5. Ordem proposta e paralelização

| Fase | Itens | Em paralelo? | Resultado entregue |
|---|---|---|---|
| 1 | **I2** (assessments) + **I1** (fundação de IA, provider fake) | Sim — arquivos disjuntos | Quizzes reais funcionando; base de IA testável sem custo |
| 2 | **I3** (recomendação por regra) | Depois de I2 | Dashboard diz o que estudar hoje, com motivo |
| 3 | **I5** (juiz) — começa pelo golden dataset | Depois de I1+I2 | Feedback de respostas abertas (consultivo → confiável) |
| 4 | **I4** (simulação de entrevista) | Depois de I1+I2(+I5) | Entrevista guiada com relatório |
| 5 | Career readiness (opcional) | Depois de I3 | Lacunas vs. vaga |

Justificativa: I2 entrega valor imediato **sem custo nem risco de IA**; I1
em paralelo prepara o terreno; I3 colhe os dados dos dois; I5 e I4 são as
peças de maior risco (qualidade do juiz) e ficam por último, com o golden
dataset como porta de qualidade.

## 6. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Juiz LLM inconsistente ou "bonzinho" | Rubrica explícita, golden dataset, piso de concordância, modo consultivo até passar |
| Custo imprevisível | Teto diário, `ai_usage`, degradação graciosa, modelo configurável |
| Vazamento de dados pessoais em prompts/logs | Logs só com metadados; nenhum dado de conta no prompt; chave só em env |
| Prompt injection via resposta do usuário | Delimitação, validação de schema, nunca executar saída do modelo |
| Farm de XP com quizzes | Regra D5 (XP só na 1ª aprovação) + teto por dia |
| Qualidade das questões geradas | Revisão humana obrigatória antes de entrar nos seeds |
| Escopo (I4/I5 são grandes) | Entrega incremental por fase; cada fase é útil sozinha |

## 7. Definição de pronto por fase
Gates do `CLAUDE.md` (ruff, mypy, pytest com cobertura ≥ 80%, frontend
test/lint/typecheck/build, migrações ida-e-volta), docs atualizados
(`DOMAIN.md`, `API.md`, `DECISIONS.md`), nenhuma chamada de rede na suíte e
verificação manual do fluxo no navegador.

## 8. O que preciso para começar
Aprovação do escopo/ordem e respostas D1–D7. Com D1/D2/D7 ainda abertas, já é
possível iniciar a **Fase 1 parcial**: I2 completo e I1 com provider fake.
