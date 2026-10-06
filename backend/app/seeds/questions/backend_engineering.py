"""Question bank for the Backend Engineering subject: rest-api-design,
authentication-authorization, postgresql-fundamentals and
event-driven-architecture (about ten questions each, English + Brazilian
Portuguese).

Written by Claude (``source=ai_generated``) and awaiting the owner's review,
as decided in docs/PROPOSAL_TRACK_I.md (D6). Rules: ``validate.py``. Every SQL
snippet and every PostgreSQL behavior described here (isolation, locking,
planner choices) was executed against a real PostgreSQL 16 database.
"""

from app.models.assessment import (
    AssessmentKind,
    QuestionDifficulty,
    QuestionSource,
    QuestionType,
)
from app.models.user import Language
from app.seeds.questions.types import (
    AssessmentSeed,
    OptionSeed,
    QuestionSeed,
    QuestionText,
    SubjectQuestionSet,
)

EASY = QuestionDifficulty.EASY
MEDIUM = QuestionDifficulty.MEDIUM
HARD = QuestionDifficulty.HARD
MC = QuestionType.MULTIPLE_CHOICE
MS = QuestionType.MULTI_SELECT
CODE = QuestionType.CODE_READING
SHORT = QuestionType.SHORT_ANSWER
AI = QuestionSource.AI_GENERATED


def _options(*texts: str) -> tuple[OptionSeed, ...]:
    """_options("text a", "text b", ...) -> options with ids a, b, c..."""
    return tuple(OptionSeed(id=chr(ord("a") + i), text=text) for i, text in enumerate(texts))


def _t(
    prompt: str,
    explanation: str,
    options: tuple[OptionSeed, ...] | None = None,
    model_answer: str | None = None,
) -> QuestionText:
    return QuestionText(
        prompt=prompt, explanation=explanation, options=options, model_answer=model_answer
    )


def _q(
    code: str,
    competency: str,
    type_: QuestionType,
    difficulty: QuestionDifficulty,
    correct: tuple[str, ...] | None,
    tags: tuple[str, ...],
    en: QuestionText,
    pt: QuestionText,
) -> QuestionSeed:
    return QuestionSeed(
        code=code,
        competency_slug=competency,
        type=type_,
        difficulty=difficulty,
        correct=correct,
        tags=tags,
        source=AI,
        text={Language.EN: en, Language.PT_BR: pt},
    )


# ----------------------------------------------------------------------
# rest-api-design
# ----------------------------------------------------------------------

_KEYSET_BUG_SQL = """```sql
-- page 1
SELECT id, created_at FROM posts
ORDER BY created_at DESC LIMIT 20;

-- page 2 (:last_created_at = created_at of the last row of page 1)
SELECT id, created_at FROM posts
WHERE created_at < :last_created_at
ORDER BY created_at DESC LIMIT 20;
```"""

_ASYNC_DB_CODE = """```python
@app.get("/reports/{report_id}")
async def get_report(report_id: UUID, db: Session = Depends(get_db)):
    return db.get(Report, report_id)  # synchronous SQLAlchemy session
```"""

_REST = "rest-api-design"

REST_QUESTIONS: tuple[QuestionSeed, ...] = (
    _q(
        "rest-api-design-q01",
        _REST,
        MC,
        EASY,
        ("c",),
        ("http-status-codes", "rest"),
        _t(
            "A client sends `POST /projects` with a valid body and the server creates the "
            "project synchronously. Which response is the most precise?",
            "`201 Created` says that a new resource now exists, and the `Location` header "
            "tells the client where to find it. A plain `200` works but carries less meaning, "
            "`202 Accepted` means the work was only queued and is not finished, and `204` "
            "would hide server-generated fields such as the new `id`.",
            _options(
                "`200 OK` with no further information.",
                "`202 Accepted`, because creation is always asynchronous.",
                "`201 Created`, with the new resource's URL in a `Location` header and "
                "usually its representation in the body.",
                "`204 No Content`, because the client already knows what it sent.",
            ),
        ),
        _t(
            "Um cliente envia `POST /projects` com um corpo válido e o servidor cria o "
            "projeto de forma síncrona. Qual resposta é a mais precisa?",
            "`201 Created` informa que um novo recurso passou a existir, e o header "
            "`Location` indica onde encontrá-lo. Um `200` simples funciona, mas diz menos; "
            "`202 Accepted` significa que o trabalho apenas foi enfileirado e não terminou; "
            "e `204` esconderia campos gerados pelo servidor, como o novo `id`.",
            _options(
                "`200 OK` sem mais informações.",
                "`202 Accepted`, porque a criação é sempre assíncrona.",
                "`201 Created`, com a URL do novo recurso no header `Location` e, em geral, "
                "sua representação no corpo.",
                "`204 No Content`, porque o cliente já sabe o que enviou.",
            ),
        ),
    ),
    _q(
        "rest-api-design-q02",
        _REST,
        MC,
        EASY,
        ("b",),
        ("idempotency", "http-methods"),
        _t(
            "A mobile client sends a request, the connection times out, and the client cannot "
            "know whether the server processed it. Which request can it retry automatically "
            "without any extra deduplication mechanism?",
            "`PUT` replaces the resource with the given full representation, so repeating it "
            "leaves the same final state: it is idempotent by definition. `POST` that creates "
            "or triggers something (a payment, an email) is not idempotent, and a `PATCH` "
            "that applies a relative change such as an increment would be applied twice.",
            _options(
                "`POST /payments` with `{\"amount\": 50}`",
                "`PUT /users/42` with the full new representation of the user",
                "`POST /emails/send` with a recipient and a body",
                "`PATCH /counters/7` with `{\"increment\": 1}`",
            ),
        ),
        _t(
            "Um cliente mobile envia uma requisição, a conexão expira por timeout e ele não "
            "tem como saber se o servidor a processou. Qual requisição pode ser repetida "
            "automaticamente sem nenhum mecanismo extra de deduplicação?",
            "`PUT` substitui o recurso pela representação completa enviada, então repeti-lo "
            "deixa o mesmo estado final: é idempotente por definição. Um `POST` que cria ou "
            "dispara algo (um pagamento, um e-mail) não é idempotente, e um `PATCH` que aplica "
            "uma mudança relativa, como um incremento, seria aplicado duas vezes.",
            _options(
                "`POST /payments` com `{\"amount\": 50}`",
                "`PUT /users/42` com a nova representação completa do usuário",
                "`POST /emails/send` com destinatário e corpo",
                "`PATCH /counters/7` com `{\"increment\": 1}`",
            ),
        ),
    ),
    _q(
        "rest-api-design-q03",
        _REST,
        MC,
        EASY,
        ("a",),
        ("fastapi", "validation"),
        _t(
            "An endpoint declares a Pydantic body model with `age: int`, and a client sends "
            "`{\"age\": \"abc\"}`. What does FastAPI return by default?",
            "FastAPI validates the body before your handler runs and answers "
            "`422 Unprocessable Entity` with a structured list of errors (location, message, "
            "type). The handler is never called, so there is no `500`, and `404` is about a "
            "missing resource, not a malformed field. A `400` is a legitimate choice in "
            "other designs, but it is not the framework default.",
            _options(
                "`422 Unprocessable Entity`, with details about the invalid field.",
                "`400 Bad Request` with a generic message.",
                "`500 Internal Server Error`, because the handler crashes.",
                "`404 Not Found`, because the body does not match the route.",
            ),
        ),
        _t(
            "Um endpoint declara um modelo Pydantic de corpo com `age: int`, e um cliente "
            "envia `{\"age\": \"abc\"}`. O que o FastAPI retorna por padrão?",
            "O FastAPI valida o corpo antes de executar o handler e responde "
            "`422 Unprocessable Entity` com uma lista estruturada de erros (localização, "
            "mensagem, tipo). O handler nunca é chamado, então não há `500`, e `404` trata de "
            "recurso inexistente, não de campo malformado. Um `400` é uma escolha legítima em "
            "outros designs, mas não é o padrão do framework.",
            _options(
                "`422 Unprocessable Entity`, com detalhes sobre o campo inválido.",
                "`400 Bad Request` com uma mensagem genérica.",
                "`500 Internal Server Error`, porque o handler quebra.",
                "`404 Not Found`, porque o corpo não corresponde à rota.",
            ),
        ),
    ),
    _q(
        "rest-api-design-q04",
        _REST,
        MC,
        MEDIUM,
        ("c",),
        ("pagination", "offset"),
        _t(
            "A feed endpoint uses `?page=N&page_size=20` (offset pagination) while new posts "
            "are inserted all the time. Which problem is inherent to this approach?",
            "With offset pagination, every insert or delete between two requests shifts the "
            "rows, so a client can see the same item twice or miss one entirely. Deep offsets "
            "are also slow because the database still has to walk past all the skipped rows. "
            "Offset works fine with sorting, does not need a total count, and returns rows in "
            "the order requested.",
            _options(
                "It cannot be combined with a sort order.",
                "It forces the client to know the total number of rows first.",
                "Inserts and deletes between requests can cause duplicated or skipped items, "
                "and large offsets get slower because earlier rows must still be skipped.",
                "It returns rows in a non-deterministic order even with `ORDER BY`.",
            ),
        ),
        _t(
            "Um endpoint de feed usa `?page=N&page_size=20` (paginação por offset) enquanto "
            "novos posts são inseridos o tempo todo. Qual problema é inerente a essa "
            "abordagem?",
            "Na paginação por offset, toda inserção ou remoção entre duas requisições desloca "
            "as linhas, então o cliente pode ver o mesmo item duas vezes ou perder um. "
            "Offsets grandes também são lentos, pois o banco ainda precisa percorrer todas as "
            "linhas ignoradas. O offset funciona bem com ordenação, não exige contagem total "
            "e devolve as linhas na ordem pedida.",
            _options(
                "Não pode ser combinada com uma ordenação.",
                "Obriga o cliente a conhecer antes o número total de linhas.",
                "Inserções e remoções entre requisições podem duplicar ou pular itens, e "
                "offsets grandes ficam mais lentos porque as linhas anteriores ainda precisam "
                "ser ignoradas.",
                "Devolve as linhas em ordem não determinística mesmo com `ORDER BY`.",
            ),
        ),
    ),
    _q(
        "rest-api-design-q05",
        _REST,
        CODE,
        MEDIUM,
        ("b",),
        ("pagination", "keyset", "sql"),
        _t(
            "This keyset (cursor) pagination only uses `created_at` as the cursor. What is "
            "the bug?\n\n" + _KEYSET_BUG_SQL,
            "Timestamps are not unique. If several posts share the `created_at` of the last "
            "row of page 1 and some of them did not fit in that page, the strict `<` in "
            "page 2 skips them forever (and their relative order is not deterministic). The "
            "fix is a unique tiebreaker in both the `ORDER BY` and the predicate: "
            "`WHERE (created_at, id) < (:last_created_at, :last_id) ORDER BY created_at DESC, "
            "id DESC`. Using `>` would go in the wrong direction for a descending sort.",
            _options(
                "Nothing: this is the standard, correct way to paginate with a cursor.",
                "Rows that share the last timestamp but were not on page 1 are skipped; the "
                "sort key needs a unique tiebreaker such as `id`.",
                "`:last_created_at` is not allowed in SQL, so the query cannot run.",
                "The `<` should be `>` because the sort is descending.",
            ),
        ),
        _t(
            "Esta paginação por keyset (cursor) usa apenas `created_at` como cursor. Qual é o "
            "bug?\n\n" + _KEYSET_BUG_SQL,
            "Timestamps não são únicos. Se vários posts compartilham o `created_at` da última "
            "linha da página 1 e alguns não couberam nela, o `<` estrito da página 2 os pula "
            "para sempre (e a ordem relativa entre eles não é determinística). A correção é "
            "um desempate único tanto no `ORDER BY` quanto no predicado: "
            "`WHERE (created_at, id) < (:last_created_at, :last_id) ORDER BY created_at DESC, "
            "id DESC`. Usar `>` iria na direção errada para uma ordenação decrescente.",
            _options(
                "Nada: esta é a forma padrão e correta de paginar com cursor.",
                "Linhas que compartilham o último timestamp mas não estavam na página 1 são "
                "puladas; a chave de ordenação precisa de um desempate único, como `id`.",
                "`:last_created_at` não é permitido em SQL, então a consulta não executa.",
                "O `<` deveria ser `>` porque a ordenação é decrescente.",
            ),
        ),
    ),
    _q(
        "rest-api-design-q06",
        _REST,
        MC,
        HARD,
        ("a",),
        ("etag", "optimistic-concurrency", "http-caching"),
        _t(
            "Two clients load the same document, both edit it, and both send `PUT`. The second "
            "request silently overwrites the first one's changes. Which HTTP-native mechanism "
            "prevents this lost update?",
            "Optimistic concurrency: return an `ETag` on `GET`, require the client to send it "
            "back in `If-Match` on the update, and reject a mismatch with "
            "`412 Precondition Failed`, so the second client must re-fetch and merge. `PATCH` "
            "is not inherently safer, `no-store` does not stop a client from editing the "
            "copy it already holds, and TLS protects transport, not concurrent writers.",
            _options(
                "Return an `ETag` on `GET`, require it in an `If-Match` header on updates and "
                "answer `412 Precondition Failed` when it no longer matches.",
                "Use `PATCH` instead of `PUT`, because `PATCH` updates are atomic and can never "
                "overwrite another client's change.",
                "Serve the API only over HTTPS, so concurrent requests are serialized.",
                "Send `Cache-Control: no-store` on the `GET` response so clients never hold a "
                "stale copy.",
            ),
        ),
        _t(
            "Dois clientes carregam o mesmo documento, ambos o editam e ambos enviam `PUT`. A "
            "segunda requisição sobrescreve silenciosamente as mudanças da primeira. Qual "
            "mecanismo nativo do HTTP evita essa atualização perdida (lost update)?",
            "Controle de concorrência otimista: devolver um `ETag` no `GET`, exigir que o "
            "cliente o envie de volta em `If-Match` na atualização e rejeitar divergências "
            "com `412 Precondition Failed`, de modo que o segundo cliente precise buscar de "
            "novo e mesclar. `PATCH` não é inerentemente mais seguro, `no-store` não impede "
            "que o cliente edite a cópia que já tem, e TLS protege o transporte, não "
            "escritores concorrentes.",
            _options(
                "Devolver um `ETag` no `GET`, exigi-lo em um header `If-Match` nas "
                "atualizações e responder `412 Precondition Failed` quando ele não bater mais.",
                "Usar `PATCH` em vez de `PUT`, porque atualizações `PATCH` são atômicas e "
                "nunca sobrescrevem a mudança de outro cliente.",
                "Servir a API somente por HTTPS, de modo que requisições concorrentes sejam "
                "serializadas.",
                "Enviar `Cache-Control: no-store` na resposta do `GET` para que os clientes "
                "nunca guardem uma cópia desatualizada.",
            ),
        ),
    ),
    _q(
        "rest-api-design-q07",
        _REST,
        MC,
        MEDIUM,
        ("d",),
        ("idempotency-key", "reliability"),
        _t(
            "A client retries `POST /transfers` after a timeout, and the first attempt had in "
            "fact succeeded. Which design prevents a duplicate transfer?",
            "The client generates a unique `Idempotency-Key` for each logical operation and "
            "reuses it on retries. The server stores the key (with a unique constraint, "
            "atomically with the operation) together with the response, and replays that "
            "stored response for a repeated key. Rate limiting does not detect duplicates, "
            "`GET` must be free of side effects, and processing later does not stop the "
            "retry from being enqueued twice.",
            _options(
                "Rate-limit the endpoint so retries are rejected.",
                "Change the endpoint to `GET`, because `GET` requests are safe to retry.",
                "Return `200` immediately and process the transfer in the background.",
                "Require a client-generated `Idempotency-Key`, store it with the result under a "
                "unique constraint, and return the stored result when the key repeats.",
            ),
        ),
        _t(
            "Um cliente repete `POST /transfers` após um timeout, e a primeira tentativa, na "
            "verdade, tinha funcionado. Qual design evita uma transferência duplicada?",
            "O cliente gera uma `Idempotency-Key` única para cada operação lógica e a reutiliza "
            "nas novas tentativas. O servidor guarda a chave (com uma constraint de unicidade, "
            "atomicamente com a operação) junto com a resposta e reenvia essa resposta "
            "guardada quando a chave se repete. Rate limiting não detecta duplicatas, `GET` "
            "deve ser livre de efeitos colaterais, e processar depois não impede que a nova "
            "tentativa seja enfileirada duas vezes.",
            _options(
                "Aplicar rate limit ao endpoint para que as novas tentativas sejam rejeitadas.",
                "Trocar o endpoint para `GET`, porque requisições `GET` são seguras para "
                "repetir.",
                "Retornar `200` imediatamente e processar a transferência em segundo plano.",
                "Exigir uma `Idempotency-Key` gerada pelo cliente, guardá-la com o resultado "
                "sob uma constraint de unicidade e devolver o resultado guardado quando a "
                "chave se repetir.",
            ),
        ),
    ),
    _q(
        "rest-api-design-q08",
        _REST,
        MS,
        MEDIUM,
        ("a", "c", "e"),
        ("testing", "api-tests"),
        _t(
            "Which of these make a test of a list endpoint (`GET /items`) meaningfully "
            "strong? Select all that apply.",
            "A real test pins down behavior: the exact response shape (not just \"some keys "
            "exist\"), known seeded data with the expected default order and consistent "
            "pagination metadata, and the edge cases (empty result, last page, invalid "
            "parameters). Asserting only `200` passes for almost any body, and skipping "
            "invalid input leaves exactly the paths where APIs break.",
            _options(
                "Assert that the response has exactly the documented fields and types.",
                "Assert only that the status code is `200`; the framework validates the rest.",
                "Seed known rows and assert the default sort order and that the pagination "
                "metadata matches the data.",
                "Test only the happy path; invalid input is the validation library's job.",
                "Cover edge cases: an empty result, the last page, and invalid or "
                "out-of-range parameters.",
            ),
        ),
        _t(
            "Quais destes tornam o teste de um endpoint de listagem (`GET /items`) "
            "realmente forte? Selecione todos que se aplicam.",
            "Um teste de verdade fixa o comportamento: o formato exato da resposta (não só "
            "\"algumas chaves existem\"), dados conhecidos com a ordem padrão esperada e "
            "metadados de paginação consistentes, e os casos de borda (resultado vazio, "
            "última página, parâmetros inválidos). Verificar só o `200` passa para quase "
            "qualquer corpo, e ignorar entradas inválidas deixa justamente os caminhos onde "
            "as APIs quebram.",
            _options(
                "Verificar que a resposta tem exatamente os campos e tipos documentados.",
                "Verificar apenas que o status é `200`; o framework valida o resto.",
                "Criar linhas conhecidas e verificar a ordenação padrão e se os metadados de "
                "paginação batem com os dados.",
                "Testar só o caminho feliz; a entrada inválida é trabalho da biblioteca de "
                "validação.",
                "Cobrir casos de borda: resultado vazio, última página e parâmetros inválidos "
                "ou fora do intervalo.",
            ),
        ),
    ),
    _q(
        "rest-api-design-q09",
        _REST,
        CODE,
        MEDIUM,
        ("b",),
        ("fastapi", "async", "event-loop"),
        _t(
            "What is the problem with this FastAPI handler?\n\n" + _ASYNC_DB_CODE,
            "A handler declared with `async def` runs directly on the event loop thread. The "
            "synchronous SQLAlchemy call blocks that thread while the query runs, so every "
            "other request waits. Declaring the handler as a plain `def` makes FastAPI run it "
            "in its thread pool (or you can use an async driver with `await`). FastAPI does "
            "not move `async def` handlers to threads, `Depends` works in both kinds, and a "
            "synchronous call does not return an awaitable.",
            _options(
                "Nothing: FastAPI always runs `async def` handlers in a thread pool.",
                "The blocking database call stalls the event loop, delaying all other "
                "requests; use a plain `def` handler or an async driver with `await`.",
                "`Depends` cannot be used in an `async def` handler, so it raises a "
                "`SyntaxError`.",
                "`db.get(...)` returns a coroutine that FastAPI awaits automatically.",
            ),
        ),
        _t(
            "Qual é o problema deste handler do FastAPI?\n\n" + _ASYNC_DB_CODE,
            "Um handler declarado com `async def` roda diretamente na thread do event loop. A "
            "chamada síncrona do SQLAlchemy bloqueia essa thread enquanto a consulta executa, "
            "então todas as outras requisições esperam. Declarar o handler como um `def` "
            "simples faz o FastAPI executá-lo em seu thread pool (ou você pode usar um driver "
            "assíncrono com `await`). O FastAPI não move handlers `async def` para threads, "
            "`Depends` funciona nos dois tipos, e uma chamada síncrona não devolve um "
            "awaitable.",
            _options(
                "Nenhum: o FastAPI sempre executa handlers `async def` em um thread pool.",
                "A chamada bloqueante ao banco trava o event loop e atrasa todas as outras "
                "requisições; use um handler `def` simples ou um driver assíncrono com "
                "`await`.",
                "`Depends` não pode ser usado em handler `async def`, então lança um "
                "`SyntaxError`.",
                "`db.get(...)` devolve uma corrotina que o FastAPI aguarda automaticamente.",
            ),
        ),
    ),
    _q(
        "rest-api-design-q10",
        _REST,
        SHORT,
        HARD,
        None,
        ("pagination", "api-design", "cursor"),
        _t(
            "You must design `GET /orders` for a table with hundreds of millions of rows, "
            "sorted newest first, with clients that scroll infinitely. Describe your "
            "pagination design and its trade-offs.",
            "Self-check: did you mention (1) keyset/cursor pagination instead of offset, "
            "(2) a deterministic sort with a unique tiebreaker, (3) an index that matches the "
            "sort, (4) an opaque cursor and a `next_cursor` in the response, and (5) the "
            "trade-offs (no jump to page N, expensive or omitted total count)?",
            model_answer="Use keyset (cursor) pagination. Sort by a deterministic key such as "
            "`(created_at DESC, id DESC)`, where `id` is a unique tiebreaker, and fetch the "
            "next page with `WHERE (created_at, id) < (:last_created_at, :last_id) ... LIMIT "
            "n`. Back it with a composite index on the same columns and order, so each page "
            "is an index range scan whose cost does not grow with depth, unlike `OFFSET`. "
            "Return an opaque, encoded `next_cursor` (and a `limit`, capped server-side) "
            "instead of page numbers, and `null` when there are no more rows. Fetching "
            "`limit + 1` rows tells you whether another page exists. Trade-offs: clients "
            "cannot jump to an arbitrary page, a total count is expensive (so omit it or "
            "make it approximate), and changing the sort order requires a matching index and "
            "cursor format. In exchange, results stay stable under concurrent inserts.",
        ),
        _t(
            "Você precisa projetar `GET /orders` para uma tabela com centenas de milhões de "
            "linhas, ordenada da mais recente para a mais antiga, com clientes que fazem "
            "scroll infinito. Descreva seu design de paginação e os trade-offs.",
            "Autoavaliação: você mencionou (1) paginação por keyset/cursor em vez de offset, "
            "(2) uma ordenação determinística com desempate único, (3) um índice compatível "
            "com a ordenação, (4) um cursor opaco e um `next_cursor` na resposta e (5) os "
            "trade-offs (sem pular para a página N, contagem total cara ou omitida)?",
            model_answer="Usar paginação por keyset (cursor). Ordenar por uma chave "
            "determinística como `(created_at DESC, id DESC)`, onde `id` é um desempate único, "
            "e buscar a próxima página com `WHERE (created_at, id) < (:last_created_at, "
            ":last_id) ... LIMIT n`. Apoiar isso com um índice composto nas mesmas colunas e "
            "ordem, de modo que cada página seja uma varredura de intervalo no índice cujo "
            "custo não cresce com a profundidade, ao contrário do `OFFSET`. Devolver um "
            "`next_cursor` opaco e codificado (e um `limit`, com teto no servidor) em vez de "
            "números de página, e `null` quando não houver mais linhas. Buscar `limit + 1` "
            "linhas indica se existe outra página. Trade-offs: o cliente não pode pular para "
            "uma página arbitrária, a contagem total é cara (omiti-la ou torná-la "
            "aproximada) e mudar a ordenação exige um índice e um formato de cursor "
            "correspondentes. Em troca, os resultados ficam estáveis com inserções "
            "concorrentes.",
        ),
    ),
)

QUESTIONS: tuple[QuestionSeed, ...] = REST_QUESTIONS

ASSESSMENTS: tuple[AssessmentSeed, ...] = ()

QUESTION_SET = SubjectQuestionSet(
    subject_slug="backend-engineering",
    questions=QUESTIONS,
    assessments=ASSESSMENTS,
)
