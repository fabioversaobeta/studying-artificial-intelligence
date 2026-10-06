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

# ----------------------------------------------------------------------
# authentication-authorization
# ----------------------------------------------------------------------

_IDOR_CODE = """```python
@app.get("/invoices/{invoice_id}")
def get_invoice(
    invoice_id: UUID,
    user: User = Depends(current_user),  # raises 401 if not logged in
    db: Session = Depends(get_db),
):
    return db.get(Invoice, invoice_id)
```"""

_AUTH = "authentication-authorization"

AUTH_QUESTIONS: tuple[QuestionSeed, ...] = (
    _q(
        "authentication-authorization-q01",
        _AUTH,
        MC,
        EASY,
        ("d",),
        ("password-hashing", "argon2"),
        _t(
            "How should a backend store user passwords?",
            "Passwords must be stored with a deliberately slow, salted, one-way password "
            "hashing function (Argon2id, bcrypt, scrypt), so a leaked database is expensive "
            "to brute-force. Encryption is reversible, so whoever gets the key gets every "
            "password; fast general-purpose hashes (MD5, SHA-256) let attackers test billions "
            "of guesses per second; and Base64 is an encoding, not protection at all.",
            _options(
                "Encrypted with AES, so support staff can recover forgotten passwords.",
                "Hashed with a fast function such as SHA-256, because fast is better for "
                "login performance.",
                "Encoded with Base64, which makes them unreadable.",
                "Hashed with a slow, salted password-hashing algorithm such as Argon2id or "
                "bcrypt.",
            ),
        ),
        _t(
            "Como um backend deve armazenar as senhas dos usuários?",
            "Senhas devem ser armazenadas com uma função de hash de senhas deliberadamente "
            "lenta, com salt e de mão única (Argon2id, bcrypt, scrypt), para que um banco "
            "vazado seja caro de atacar por força bruta. Criptografia é reversível, então "
            "quem obtém a chave obtém todas as senhas; hashes rápidos de uso geral (MD5, "
            "SHA-256) permitem testar bilhões de palpites por segundo; e Base64 é uma "
            "codificação, não uma proteção.",
            _options(
                "Criptografadas com AES, para que o suporte possa recuperar senhas "
                "esquecidas.",
                "Com hash de uma função rápida como SHA-256, pois rápido é melhor para o "
                "desempenho do login.",
                "Codificadas em Base64, o que as torna ilegíveis.",
                "Com hash de um algoritmo lento e com salt, como Argon2id ou bcrypt.",
            ),
        ),
    ),
    _q(
        "authentication-authorization-q02",
        _AUTH,
        MC,
        EASY,
        ("c",),
        ("authentication", "authorization", "http-status-codes"),
        _t(
            "A user with a valid session tries to delete a project that belongs to another "
            "team, and the system decides they have no permission to do so. Which status "
            "code is the standard response?",
            "The caller is authenticated, but not allowed: that is `403 Forbidden`. `401` "
            "means the credentials are missing or invalid (authentication failed), `400` is "
            "for a malformed request, and `405` means the HTTP method is not supported on "
            "that route. (Some APIs deliberately answer `404` to avoid revealing that the "
            "resource exists, but `403` is the standard answer here.)",
            _options(
                "`401 Unauthorized`",
                "`400 Bad Request`",
                "`403 Forbidden`",
                "`405 Method Not Allowed`",
            ),
        ),
        _t(
            "Um usuário com sessão válida tenta excluir um projeto que pertence a outra "
            "equipe, e o sistema decide que ele não tem permissão. Qual é o status padrão "
            "da resposta?",
            "O chamador está autenticado, mas não autorizado: isso é `403 Forbidden`. `401` "
            "significa credenciais ausentes ou inválidas (falha de autenticação), `400` é "
            "para requisições malformadas e `405` indica que o método HTTP não é suportado "
            "na rota. (Algumas APIs respondem `404` de propósito para não revelar que o "
            "recurso existe, mas `403` é a resposta padrão aqui.)",
            _options(
                "`401 Unauthorized`",
                "`400 Bad Request`",
                "`403 Forbidden`",
                "`405 Method Not Allowed`",
            ),
        ),
    ),
    _q(
        "authentication-authorization-q03",
        _AUTH,
        MC,
        EASY,
        ("b",),
        ("jwt", "security-basics"),
        _t(
            "Which statement about a standard signed JWT is correct?",
            "A signed JWT has a Base64url-encoded header and payload plus a signature. The "
            "signature gives integrity (tampering is detected), not confidentiality: anyone "
            "who holds the token can decode and read the claims, so secrets must not go in "
            "them. The payload is not encrypted, the signature does not hide anything, and "
            "verification can be done locally with the key, with no call to the issuer on "
            "every request.",
            _options(
                "The payload is encrypted, so the client cannot read the claims.",
                "The payload is only encoded: anyone holding the token can read it, and the "
                "signature only protects against tampering.",
                "The signature makes the claims confidential.",
                "A server must call the issuer on every request to verify the token.",
            ),
        ),
        _t(
            "Qual afirmação sobre um JWT assinado padrão está correta?",
            "Um JWT assinado tem header e payload codificados em Base64url mais uma "
            "assinatura. A assinatura dá integridade (adulterações são detectadas), não "
            "confidencialidade: qualquer um que tenha o token pode decodificar e ler as "
            "claims, então segredos não devem ir nelas. O payload não é criptografado, a "
            "assinatura não esconde nada, e a verificação pode ser feita localmente com a "
            "chave, sem consultar o emissor a cada requisição.",
            _options(
                "O payload é criptografado, então o cliente não consegue ler as claims.",
                "O payload é apenas codificado: qualquer um com o token pode lê-lo, e a "
                "assinatura só protege contra adulteração.",
                "A assinatura torna as claims confidenciais.",
                "O servidor precisa consultar o emissor a cada requisição para verificar o "
                "token.",
            ),
        ),
    ),
    _q(
        "authentication-authorization-q04",
        _AUTH,
        MC,
        MEDIUM,
        ("d",),
        ("sessions", "jwt", "revocation"),
        _t(
            "After a password change, the product must immediately sign the user out of every "
            "device. Which approach makes that requirement simplest to satisfy?",
            "With server-side sessions, the server owns the state, so deleting the user's "
            "session records revokes access at once. A self-contained JWT stays valid until "
            "it expires, because nothing on the server says otherwise; longer lifetimes make "
            "that worse, a stronger signature algorithm does not change it, and where the "
            "token is stored in the browser is irrelevant to revocation. Stateless tokens "
            "need extra machinery (short expiry plus revocable refresh tokens, or a "
            "denylist) to approximate this.",
            _options(
                "Stateless JWT access tokens valid for 24 hours, with no server-side state.",
                "Stateless JWTs with longer lifetimes, so users rarely need to log in.",
                "Stateless JWTs signed with a stronger algorithm.",
                "Server-side sessions kept in a database or cache: delete all of the user's "
                "session records.",
            ),
        ),
        _t(
            "Depois de uma troca de senha, o produto precisa deslogar imediatamente o usuário "
            "de todos os dispositivos. Qual abordagem torna esse requisito mais simples de "
            "atender?",
            "Com sessões no servidor, o servidor é dono do estado, então apagar os registros "
            "de sessão do usuário revoga o acesso na hora. Um JWT autocontido continua "
            "válido até expirar, pois nada no servidor diz o contrário; vidas mais longas "
            "pioram isso, um algoritmo de assinatura mais forte não muda nada, e onde o "
            "token fica no navegador é irrelevante para a revogação. Tokens stateless "
            "exigem mecanismos extras (expiração curta com refresh tokens revogáveis, ou "
            "uma denylist) para aproximar isso.",
            _options(
                "Access tokens JWT stateless válidos por 24 horas, sem estado no servidor.",
                "JWTs stateless com vida mais longa, para que os usuários raramente precisem "
                "fazer login.",
                "JWTs stateless assinados com um algoritmo mais forte.",
                "Sessões no servidor guardadas em banco ou cache: apagar todos os registros "
                "de sessão do usuário.",
            ),
        ),
    ),
    _q(
        "authentication-authorization-q05",
        _AUTH,
        MC,
        MEDIUM,
        ("b",),
        ("oauth2", "pkce"),
        _t(
            "A single-page app (a public client that cannot keep a secret) signs users in "
            "through an OAuth 2.0 authorization server. Which flow is recommended?",
            "Authorization Code with PKCE: the app receives a short-lived code through the "
            "redirect and exchanges it using a one-time `code_verifier`, so an intercepted "
            "code is useless. The implicit flow exposes tokens in the redirect URL and is "
            "discouraged; the password grant makes the app handle the user's password, "
            "defeating delegation; and Client Credentials is for machine-to-machine calls "
            "with no user involved.",
            _options(
                "Implicit flow, returning the access token in the redirect URL fragment.",
                "Authorization Code flow with PKCE.",
                "Resource Owner Password Credentials, with the app collecting the username "
                "and password.",
                "Client Credentials, with a client secret embedded in the app bundle.",
            ),
        ),
        _t(
            "Uma single-page app (um cliente público que não consegue guardar segredo) "
            "autentica usuários por meio de um servidor de autorização OAuth 2.0. Qual fluxo "
            "é recomendado?",
            "Authorization Code com PKCE: o app recebe um code de curta duração pelo "
            "redirecionamento e o troca usando um `code_verifier` de uso único, então um "
            "code interceptado é inútil. O fluxo implicit expõe tokens na URL de "
            "redirecionamento e é desencorajado; o password grant faz o app lidar com a "
            "senha do usuário, anulando a delegação; e Client Credentials serve para "
            "chamadas máquina a máquina, sem usuário.",
            _options(
                "Fluxo implicit, devolvendo o access token no fragmento da URL de "
                "redirecionamento.",
                "Fluxo Authorization Code com PKCE.",
                "Resource Owner Password Credentials, com o app coletando usuário e senha.",
                "Client Credentials, com um client secret embutido no bundle do app.",
            ),
        ),
    ),
    _q(
        "authentication-authorization-q06",
        _AUTH,
        MC,
        MEDIUM,
        ("c",),
        ("oidc", "oauth2", "id-token"),
        _t(
            "What does OpenID Connect (OIDC) add on top of OAuth 2.0?",
            "OAuth 2.0 is about delegated authorization (access to resources), not about "
            "telling the client who the user is. OIDC adds an identity layer: the `openid` "
            "scope, an ID token (a JWT with claims about the authentication event and the "
            "user) and a standard userinfo endpoint. It does not replace the authorization "
            "code flow, and refresh tokens already exist in OAuth 2.0.",
            _options(
                "Encryption of all access tokens in transit and at rest.",
                "A new flow that replaces the authorization code flow.",
                "An identity layer: an ID token with claims about the authenticated user, "
                "the `openid` scope and a userinfo endpoint.",
                "Refresh tokens, which OAuth 2.0 does not support.",
            ),
        ),
        _t(
            "O que o OpenID Connect (OIDC) acrescenta ao OAuth 2.0?",
            "O OAuth 2.0 trata de autorização delegada (acesso a recursos), não de dizer ao "
            "cliente quem é o usuário. O OIDC acrescenta uma camada de identidade: o scope "
            "`openid`, um ID token (um JWT com claims sobre o evento de autenticação e o "
            "usuário) e um endpoint userinfo padronizado. Ele não substitui o fluxo "
            "authorization code, e refresh tokens já existem no OAuth 2.0.",
            _options(
                "Criptografia de todos os access tokens em trânsito e em repouso.",
                "Um novo fluxo que substitui o fluxo authorization code.",
                "Uma camada de identidade: um ID token com claims sobre o usuário "
                "autenticado, o scope `openid` e um endpoint userinfo.",
                "Refresh tokens, que o OAuth 2.0 não suporta.",
            ),
        ),
    ),
    _q(
        "authentication-authorization-q07",
        _AUTH,
        MS,
        MEDIUM,
        ("a", "c", "d"),
        ("jwt", "token-validation"),
        _t(
            "Your API receives a JWT access token from an external identity provider. Which "
            "checks must the API perform before trusting it? Select all that apply.",
            "Verify the signature with the key and algorithm the API expects (never let the "
            "token's own `alg` header decide, which is how `none` and key-confusion attacks "
            "work), reject expired tokens, and check that `iss` and `aud` identify the "
            "expected issuer and this API. Decoding the payload without verifying proves "
            "nothing, since anyone can forge a payload, and HTTPS only protects the "
            "transport, not the token's origin.",
            _options(
                "Verify the signature using the expected key and an allow-listed algorithm.",
                "Base64-decode the payload and trust the claims, since the request came over "
                "HTTPS.",
                "Reject the token if it is expired (`exp`) or not yet valid (`nbf`).",
                "Check that the issuer (`iss`) and audience (`aud`) match what the API "
                "expects.",
                "Accept whatever algorithm the token's `alg` header declares, for "
                "compatibility with any issuer.",
            ),
        ),
        _t(
            "Sua API recebe um access token JWT de um provedor de identidade externo. Quais "
            "verificações a API deve fazer antes de confiar nele? Selecione todas que se "
            "aplicam.",
            "Verificar a assinatura com a chave e o algoritmo que a API espera (nunca deixar "
            "o header `alg` do próprio token decidir, que é como funcionam os ataques com "
            "`none` e de confusão de chaves), rejeitar tokens expirados e checar se `iss` e "
            "`aud` identificam o emissor esperado e esta API. Decodificar o payload sem "
            "verificar não prova nada, pois qualquer um forja um payload, e o HTTPS protege "
            "só o transporte, não a origem do token.",
            _options(
                "Verificar a assinatura usando a chave esperada e um algoritmo de uma lista "
                "permitida.",
                "Decodificar o payload em Base64 e confiar nas claims, já que a requisição "
                "veio por HTTPS.",
                "Rejeitar o token se estiver expirado (`exp`) ou ainda não válido (`nbf`).",
                "Checar se o emissor (`iss`) e a audiência (`aud`) correspondem ao que a API "
                "espera.",
                "Aceitar o algoritmo que o header `alg` do token declarar, por "
                "compatibilidade com qualquer emissor.",
            ),
        ),
    ),
    _q(
        "authentication-authorization-q08",
        _AUTH,
        CODE,
        MEDIUM,
        ("b",),
        ("idor", "bola", "authorization"),
        _t(
            "This endpoint requires login. What vulnerability does it have?\n\n" + _IDOR_CODE,
            "Authentication only proves who the caller is. The handler never checks that the "
            "invoice belongs to that user (or tenant), so any logged-in user can read any "
            "invoice by guessing or obtaining its id: broken object-level authorization "
            "(IDOR/BOLA), a leading API vulnerability. The fix is an ownership or tenant "
            "check on every object access. Random UUIDs make guessing harder but are not an "
            "authorization control. There is no SQL injection here, and CSRF concerns "
            "state-changing requests.",
            _options(
                "None: because login is required, only legitimate users can reach it.",
                "Broken object-level authorization (IDOR): any logged-in user can fetch any "
                "invoice by id, since ownership is never checked.",
                "SQL injection through `invoice_id`.",
                "CSRF, because the endpoint answers a `GET` request.",
            ),
        ),
        _t(
            "Este endpoint exige login. Qual vulnerabilidade ele tem?\n\n" + _IDOR_CODE,
            "A autenticação só prova quem é o chamador. O handler nunca verifica se a fatura "
            "pertence àquele usuário (ou tenant), então qualquer usuário logado pode ler "
            "qualquer fatura adivinhando ou obtendo seu id: autorização quebrada em nível "
            "de objeto (IDOR/BOLA), uma das principais vulnerabilidades de API. A correção "
            "é uma checagem de propriedade ou de tenant em todo acesso a objeto. UUIDs "
            "aleatórios dificultam o palpite, mas não são um controle de autorização. Não há "
            "SQL injection aqui, e CSRF diz respeito a requisições que alteram estado.",
            _options(
                "Nenhuma: como o login é exigido, só usuários legítimos chegam a ele.",
                "Autorização quebrada em nível de objeto (IDOR): qualquer usuário logado "
                "pode buscar qualquer fatura pelo id, pois a propriedade nunca é verificada.",
                "SQL injection por meio de `invoice_id`.",
                "CSRF, porque o endpoint responde a uma requisição `GET`.",
            ),
        ),
    ),
    _q(
        "authentication-authorization-q09",
        _AUTH,
        MC,
        HARD,
        ("a",),
        ("xss", "csrf", "token-storage", "cookies"),
        _t(
            "A single-page app must keep a session credential in the browser. Which statement "
            "about the trade-offs is correct?",
            "A token in `localStorage` can be read by any script running on the page, so a "
            "single XSS bug lets an attacker exfiltrate it. An `HttpOnly` cookie cannot be "
            "read by JavaScript, but the browser attaches it automatically to requests, so "
            "you need CSRF defenses (`SameSite`, anti-CSRF tokens). HttpOnly is not immune to "
            "XSS, because injected script can still make authenticated requests from the "
            "victim's browser. The same-origin policy does not protect against scripts "
            "already running in your own origin, and tokens sent manually in an "
            "`Authorization` header are not exposed to CSRF.",
            _options(
                "A token in `localStorage` can be stolen by any injected script (XSS), while "
                "an `HttpOnly` cookie cannot be read by scripts but is sent automatically, "
                "so it needs CSRF protection.",
                "An `HttpOnly` cookie is immune to both XSS and CSRF, so it needs no further "
                "defenses.",
                "`localStorage` is protected by the same-origin policy, so XSS cannot read "
                "tokens stored there.",
                "A token sent in a manually set `Authorization` header is the one exposed to "
                "CSRF, because browsers attach it to every request.",
            ),
        ),
        _t(
            "Uma single-page app precisa guardar uma credencial de sessão no navegador. Qual "
            "afirmação sobre os trade-offs está correta?",
            "Um token no `localStorage` pode ser lido por qualquer script rodando na página, "
            "então um único bug de XSS permite que o atacante o exfiltre. Um cookie "
            "`HttpOnly` não pode ser lido por JavaScript, mas o navegador o anexa "
            "automaticamente às requisições, então são necessárias defesas contra CSRF "
            "(`SameSite`, tokens anti-CSRF). HttpOnly não é imune a XSS, pois um script "
            "injetado ainda pode fazer requisições autenticadas a partir do navegador da "
            "vítima. A same-origin policy não protege contra scripts que já rodam na sua "
            "própria origem, e tokens enviados manualmente em um header `Authorization` não "
            "ficam expostos a CSRF.",
            _options(
                "Um token no `localStorage` pode ser roubado por qualquer script injetado "
                "(XSS), enquanto um cookie `HttpOnly` não pode ser lido por scripts, mas é "
                "enviado automaticamente, então precisa de proteção contra CSRF.",
                "Um cookie `HttpOnly` é imune a XSS e a CSRF, então não precisa de mais "
                "nenhuma defesa.",
                "O `localStorage` é protegido pela same-origin policy, então XSS não "
                "consegue ler os tokens guardados nele.",
                "Um token enviado em um header `Authorization` definido manualmente é o que "
                "fica exposto a CSRF, porque os navegadores o anexam a toda requisição.",
            ),
        ),
    ),
    _q(
        "authentication-authorization-q10",
        _AUTH,
        SHORT,
        HARD,
        None,
        ("refresh-tokens", "token-rotation", "jwt"),
        _t(
            "Design the token strategy for a web app with a JSON API. How do you combine "
            "short-lived access tokens and refresh tokens, and how do you limit the damage "
            "if a refresh token is stolen?",
            "Self-check: did you mention (1) short-lived access tokens, (2) a long-lived, "
            "opaque refresh token stored hashed on the server, (3) rotation on every use, "
            "(4) reuse detection that revokes the whole token family, (5) safe client storage "
            "and (6) revocation on logout or password change?",
            model_answer="Issue a short-lived access token (for example 5 to 15 minutes, a "
            "JWT verified locally) and a longer-lived refresh token that is an opaque random "
            "value, stored hashed on the server, so it can be revoked. When the access token "
            "expires, the client calls the refresh endpoint and gets a new access token and a "
            "new refresh token (rotation); the old refresh token becomes invalid. If an "
            "already-used refresh token is presented again, treat it as theft: revoke the "
            "whole token family and force a new login. Keep the refresh token in an "
            "`HttpOnly`, `Secure`, `SameSite` cookie scoped to the refresh path, set an "
            "absolute lifetime, and revoke tokens on logout, password change or detected "
            "compromise. This bounds a stolen access token to minutes and makes stolen "
            "refresh tokens detectable.",
        ),
        _t(
            "Projete a estratégia de tokens de um app web com uma API JSON. Como você combina "
            "access tokens de vida curta e refresh tokens, e como limita o estrago se um "
            "refresh token for roubado?",
            "Autoavaliação: você mencionou (1) access tokens de vida curta, (2) um refresh "
            "token longo e opaco, guardado com hash no servidor, (3) rotação a cada uso, "
            "(4) detecção de reuso que revoga toda a família de tokens, (5) armazenamento "
            "seguro no cliente e (6) revogação no logout ou na troca de senha?",
            model_answer="Emitir um access token de vida curta (por exemplo 5 a 15 minutos, "
            "um JWT verificado localmente) e um refresh token de vida mais longa que é um "
            "valor aleatório opaco, guardado com hash no servidor, para que possa ser "
            "revogado. Quando o access token expira, o cliente chama o endpoint de refresh e "
            "recebe um novo access token e um novo refresh token (rotação); o refresh token "
            "antigo se torna inválido. Se um refresh token já usado for apresentado de novo, "
            "trata-se como roubo: revogar toda a família de tokens e exigir novo login. "
            "Guardar o refresh token em um cookie `HttpOnly`, `Secure` e `SameSite` restrito "
            "ao caminho de refresh, definir um tempo de vida absoluto e revogar tokens no "
            "logout, na troca de senha ou ao detectar comprometimento. Isso limita um access "
            "token roubado a minutos e torna detectável o roubo de refresh tokens.",
        ),
    ),
)

QUESTIONS: tuple[QuestionSeed, ...] = REST_QUESTIONS + AUTH_QUESTIONS

ASSESSMENTS: tuple[AssessmentSeed, ...] = ()

QUESTION_SET = SubjectQuestionSet(
    subject_slug="backend-engineering",
    questions=QUESTIONS,
    assessments=ASSESSMENTS,
)
