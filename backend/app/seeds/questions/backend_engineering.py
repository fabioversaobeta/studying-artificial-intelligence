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
                "`200 OK` with no further information, since the request succeeded.",
                "`202 Accepted`, because creating a resource is always asynchronous and may "
                "still fail later.",
                "`201 Created`, with the new resource's URL in a `Location` header.",
                "`204 No Content`, because the client already knows everything it sent.",
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
                "`200 OK` sem mais informações, já que a requisição deu certo.",
                "`202 Accepted`, porque criar um recurso é sempre assíncrono e ainda pode "
                "falhar depois.",
                "`201 Created`, com a URL do novo recurso no header `Location`.",
                "`204 No Content`, porque o cliente já sabe tudo o que enviou.",
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
                '`POST /payments` with `{"amount": 50}` to charge the customer',
                "`PUT /users/42` with the full new representation of the user",
                "`POST /emails/send` with a recipient, a subject and a body, to be delivered",
                '`PATCH /counters/7` with `{"increment": 1}` to add one to the total',
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
                '`POST /payments` com `{"amount": 50}` para cobrar o cliente',
                "`PUT /users/42` com a nova representação completa do usuário",
                "`POST /emails/send` com destinatário, assunto e corpo, para ser entregue",
                '`PATCH /counters/7` com `{"increment": 1}` para somar um ao total',
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
            '`{"age": "abc"}`. What does FastAPI return by default?',
            "FastAPI validates the body before your handler runs and answers "
            "`422 Unprocessable Entity` with a structured list of errors (location, message, "
            "type). The handler is never called, so there is no `500`, and `404` is about a "
            "missing resource, not a malformed field. A `400` is a legitimate choice in "
            "other designs, but it is not the framework default.",
            _options(
                "`422 Unprocessable Entity`, with details of the invalid field.",
                "`400 Bad Request` with a generic message saying the request is invalid.",
                "`500 Internal Server Error`, because the handler crashes on the value.",
                "`404 Not Found`, because the body does not match the route.",
            ),
        ),
        _t(
            "Um endpoint declara um modelo Pydantic de corpo com `age: int`, e um cliente "
            'envia `{"age": "abc"}`. O que o FastAPI retorna por padrão?',
            "O FastAPI valida o corpo antes de executar o handler e responde "
            "`422 Unprocessable Entity` com uma lista estruturada de erros (localização, "
            "mensagem, tipo). O handler nunca é chamado, então não há `500`, e `404` trata de "
            "recurso inexistente, não de campo malformado. Um `400` é uma escolha legítima em "
            "outros designs, mas não é o padrão do framework.",
            _options(
                "`422 Unprocessable Entity`, com detalhes do campo inválido.",
                "`400 Bad Request` com uma mensagem genérica dizendo que a requisição é "
                "inválida.",
                "`500 Internal Server Error`, porque o handler quebra com o valor.",
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
                "It cannot be combined with a sort order, so the feed order is undefined.",
                "It forces the client to know the total number of rows before asking for any "
                "page.",
                "Inserts and deletes between requests can duplicate or skip items, and large "
                "offsets get slower.",
                "It returns rows in a non-deterministic order even when the query has an "
                "`ORDER BY` on a unique column.",
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
                "Não pode ser combinada com uma ordenação, então a ordem do feed fica "
                "indefinida.",
                "Obriga o cliente a conhecer o número total de linhas antes de pedir qualquer "
                "página.",
                "Inserções e remoções entre requisições podem duplicar ou pular itens, e "
                "offsets grandes ficam mais lentos.",
                "Devolve as linhas em ordem não determinística mesmo quando a consulta tem "
                "`ORDER BY` em uma coluna única.",
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
                "Return an `ETag` on `GET`, require it in an `If-Match` header on updates, and "
                "answer `412 Precondition Failed` on a mismatch.",
                "Use `PATCH` instead of `PUT`, because `PATCH` updates are atomic and can never "
                "overwrite another client's change in the meantime.",
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
                "atualizações e responder `412 Precondition Failed` se divergir.",
                "Usar `PATCH` em vez de `PUT`, porque atualizações `PATCH` são atômicas e "
                "nunca sobrescrevem a mudança de outro cliente nesse meio-tempo.",
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
                "Rate-limit the endpoint so that retries arriving too soon are rejected.",
                "Change the endpoint to `GET` with query parameters, because `GET` requests "
                "are always safe to retry.",
                "Return `200` immediately and process the transfer in the background, so a "
                "retry finds it already queued.",
                "Require a client-generated `Idempotency-Key` and return the stored result "
                "when the key repeats.",
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
                "Aplicar rate limit ao endpoint para que as novas tentativas que chegarem "
                "cedo demais sejam rejeitadas.",
                "Trocar o endpoint para `GET` com parâmetros de consulta, porque requisições "
                "`GET` são sempre seguras para repetir.",
                "Retornar `200` imediatamente e processar a transferência em segundo plano, "
                "de modo que uma nova tentativa a encontre já enfileirada.",
                "Exigir uma `Idempotency-Key` gerada pelo cliente e devolver o resultado "
                "guardado quando a chave se repetir.",
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
            'A real test pins down behavior: the exact response shape (not just "some keys '
            'exist"), known seeded data with the expected default order and consistent '
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
            '"algumas chaves existem"), dados conhecidos com a ordem padrão esperada e '
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
                "`Depends` cannot be used in an `async def` handler, so it raises a `SyntaxError`.",
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
                "Hashed with a slow, salted password-hashing algorithm such as Argon2id or bcrypt.",
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
                "Criptografadas com AES, para que o suporte possa recuperar senhas esquecidas.",
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
                "O servidor precisa consultar o emissor a cada requisição para verificar o token.",
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
                "Check that the issuer (`iss`) and audience (`aud`) match what the API expects.",
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

# ----------------------------------------------------------------------
# postgresql-fundamentals
# ----------------------------------------------------------------------

_COMPOSITE_INDEX_SQL = """```sql
CREATE INDEX events_user_created ON events (user_id, created_at);

-- Query 1
SELECT * FROM events WHERE user_id = 5 ORDER BY created_at DESC LIMIT 10;

-- Query 2
SELECT * FROM events WHERE created_at > now() - interval '1 minute';
```"""

_LOWER_EMAIL_SQL = """```sql
-- users(id serial PRIMARY KEY, email text UNIQUE), about 100,000 rows
EXPLAIN SELECT * FROM users WHERE lower(email) = 'user5@example.com';
```

```text
Seq Scan on users  (cost=0.00..2235.00 rows=500 width=25)
  Filter: (lower(email) = 'user5@example.com'::text)
```"""

_NOT_IN_SQL = """```sql
-- users(id), orders(id, user_id); guest orders have user_id = NULL
-- and the table contains at least one such row.
SELECT id FROM users
WHERE id NOT IN (SELECT user_id FROM orders);
```"""

_PG = "postgresql-fundamentals"

PG_QUESTIONS: tuple[QuestionSeed, ...] = (
    _q(
        "postgresql-fundamentals-q01",
        _PG,
        MC,
        EASY,
        ("c",),
        ("sql", "null"),
        _t(
            "The `users` table has a nullable column `nickname`. Which query returns the "
            "users that have no nickname?",
            '`NULL` means "unknown or missing", and any comparison with `NULL` using `=` '
            "yields `NULL` (not true), so `nickname = NULL` matches no rows at all, even "
            "when nicknames are missing. The correct test is `IS NULL`. An empty string is a "
            "real value different from `NULL`, and `==` is not SQL.",
            _options(
                "`SELECT * FROM users WHERE nickname = NULL;`",
                "`SELECT * FROM users WHERE nickname = '';`",
                "`SELECT * FROM users WHERE nickname IS NULL;`",
                "`SELECT * FROM users WHERE nickname == NULL;`",
            ),
        ),
        _t(
            "A tabela `users` tem uma coluna anulável `nickname`. Qual consulta retorna os "
            "usuários que não têm apelido?",
            '`NULL` significa "desconhecido ou ausente", e qualquer comparação com `NULL` '
            "usando `=` resulta em `NULL` (não verdadeiro), então `nickname = NULL` não "
            "retorna nenhuma linha, mesmo quando há apelidos ausentes. O teste correto é "
            "`IS NULL`. Uma string vazia é um valor real, diferente de `NULL`, e `==` não é "
            "SQL.",
            _options(
                "`SELECT * FROM users WHERE nickname = NULL;`",
                "`SELECT * FROM users WHERE nickname = '';`",
                "`SELECT * FROM users WHERE nickname IS NULL;`",
                "`SELECT * FROM users WHERE nickname == NULL;`",
            ),
        ),
    ),
    _q(
        "postgresql-fundamentals-q02",
        _PG,
        MC,
        EASY,
        ("a",),
        ("sql", "joins"),
        _t(
            "With tables `users(id)` and `orders(id, user_id)`, which query lists the users "
            "who have never placed an order?",
            "A `LEFT JOIN` keeps every user and fills the order columns with `NULL` when "
            "there is no match, so filtering `o.id IS NULL` leaves exactly the users without "
            "orders. With an `INNER JOIN` unmatched users are discarded before the filter, so "
            "the result is always empty. `LEFT JOIN ... IS NOT NULL` returns the opposite "
            "set (users with orders), and the last option does not even involve the users "
            "table.",
            _options(
                "`SELECT u.id FROM users u LEFT JOIN orders o ON o.user_id = u.id WHERE o.id "
                "IS NULL;`",
                "`SELECT u.id FROM users u JOIN orders o ON o.user_id = u.id WHERE o.id IS NULL;`",
                "`SELECT u.id FROM users u LEFT JOIN orders o ON o.user_id = u.id WHERE o.id "
                "IS NOT NULL;`",
                "`SELECT user_id FROM orders WHERE user_id IS NULL;`",
            ),
        ),
        _t(
            "Com as tabelas `users(id)` e `orders(id, user_id)`, qual consulta lista os "
            "usuários que nunca fizeram um pedido?",
            "Um `LEFT JOIN` mantém todos os usuários e preenche as colunas do pedido com "
            "`NULL` quando não há correspondência, então filtrar `o.id IS NULL` deixa "
            "exatamente os usuários sem pedidos. Com um `INNER JOIN`, usuários sem "
            "correspondência são descartados antes do filtro, e o resultado é sempre vazio. "
            "`LEFT JOIN ... IS NOT NULL` retorna o conjunto oposto (usuários com pedidos), "
            "e a última opção nem envolve a tabela de usuários.",
            _options(
                "`SELECT u.id FROM users u LEFT JOIN orders o ON o.user_id = u.id WHERE o.id "
                "IS NULL;`",
                "`SELECT u.id FROM users u JOIN orders o ON o.user_id = u.id WHERE o.id IS NULL;`",
                "`SELECT u.id FROM users u LEFT JOIN orders o ON o.user_id = u.id WHERE o.id "
                "IS NOT NULL;`",
                "`SELECT user_id FROM orders WHERE user_id IS NULL;`",
            ),
        ),
    ),
    _q(
        "postgresql-fundamentals-q03",
        _PG,
        MC,
        EASY,
        ("b",),
        ("indexes", "write-cost"),
        _t(
            "What is the main cost of adding an index to a table?",
            "An index is a separate data structure: it takes disk space, and every `INSERT`, "
            "`UPDATE` of an indexed column and `DELETE` must also maintain it, so writes get "
            "slower. That is why you index for the queries you actually run, not every "
            "column. Indexes do not slow down reads, do not force rows into index order "
            "on disk, do not make the table read-only and do not prevent duplicates (only "
            "`UNIQUE` indexes do that, by design).",
            _options(
                "Reads on that table become slower.",
                "Extra storage, plus every write must also update the index, which makes "
                "writes slower.",
                "The table can no longer contain duplicate rows.",
                "The table becomes read-only while the index exists.",
            ),
        ),
        _t(
            "Qual é o principal custo de adicionar um índice a uma tabela?",
            "Um índice é uma estrutura de dados separada: ocupa espaço em disco, e todo "
            "`INSERT`, `UPDATE` de coluna indexada e `DELETE` também precisa mantê-lo, então "
            "as escritas ficam mais lentas. Por isso se indexa para as consultas que "
            "realmente existem, não todas as colunas. Índices não deixam as leituras mais "
            "lentas, não forçam as linhas a ficar em ordem no disco, não tornam a tabela "
            "somente leitura e não impedem duplicatas (só índices `UNIQUE` fazem isso, "
            "por definição).",
            _options(
                "As leituras nessa tabela ficam mais lentas.",
                "Espaço extra de armazenamento, e toda escrita também precisa atualizar o "
                "índice, o que a deixa mais lenta.",
                "A tabela não pode mais conter linhas duplicadas.",
                "A tabela fica somente leitura enquanto o índice existir.",
            ),
        ),
    ),
    _q(
        "postgresql-fundamentals-q04",
        _PG,
        CODE,
        MEDIUM,
        ("c",),
        ("indexes", "composite-index", "explain"),
        _t(
            "Given this composite index, which statement is correct?\n\n" + _COMPOSITE_INDEX_SQL,
            "A B-tree on `(user_id, created_at)` is sorted by `user_id` first and, inside "
            "each user, by `created_at`. Query 1 can seek straight to `user_id = 5` and read "
            "rows already in `created_at` order (backwards), so it needs no separate sort "
            "and stops after 10 rows. Query 2 filters only on the second column, so the "
            "index cannot be used as an efficient seek on it (a separate index on "
            "`created_at` would be needed). Mentioning an indexed column is not enough: "
            "column order matters, and `LIMIT` does not disable indexes.",
            _options(
                "Both queries use the index equally well, because both mention indexed columns.",
                "Query 2 uses the index, but Query 1 does not because `ORDER BY` always needs "
                "a separate sort.",
                "Query 1 can seek by `user_id` and read rows already ordered by `created_at`; "
                "Query 2 filters only on the second column, so it cannot use the index as an "
                "efficient seek.",
                "Neither can use it, because indexes are ignored when `LIMIT` is present.",
            ),
        ),
        _t(
            "Dado este índice composto, qual afirmação está correta?\n\n" + _COMPOSITE_INDEX_SQL,
            "Uma B-tree em `(user_id, created_at)` é ordenada primeiro por `user_id` e, "
            "dentro de cada usuário, por `created_at`. A Query 1 pode ir direto a "
            "`user_id = 5` e ler as linhas já em ordem de `created_at` (de trás para "
            "frente), então não precisa de ordenação separada e para após 10 linhas. A "
            "Query 2 filtra apenas pela segunda coluna, então o índice não pode ser usado "
            "como uma busca eficiente nela (seria preciso um índice separado em "
            "`created_at`). Citar uma coluna indexada não basta: a ordem das colunas "
            "importa, e `LIMIT` não desativa índices.",
            _options(
                "Ambas as consultas usam o índice igualmente bem, pois ambas citam colunas "
                "indexadas.",
                "A Query 2 usa o índice, mas a Query 1 não, pois `ORDER BY` sempre exige uma "
                "ordenação separada.",
                "A Query 1 pode buscar por `user_id` e ler linhas já ordenadas por "
                "`created_at`; a Query 2 filtra só pela segunda coluna, então não consegue "
                "usar o índice como busca eficiente.",
                "Nenhuma pode usá-lo, porque índices são ignorados quando há `LIMIT`.",
            ),
        ),
    ),
    _q(
        "postgresql-fundamentals-q05",
        _PG,
        MC,
        MEDIUM,
        ("b",),
        ("isolation", "read-committed", "mvcc"),
        _t(
            "In PostgreSQL's default isolation level, a transaction runs the same `SELECT` "
            "twice. Between the two statements, another transaction commits an `UPDATE` to "
            "one of the matching rows. What happens?",
            "The default is `READ COMMITTED`: each statement gets a fresh snapshot, so the "
            "second `SELECT` sees the newly committed value (a non-repeatable read). Reading "
            "the same value twice requires `REPEATABLE READ` or higher. Under MVCC, plain "
            "reads never block on writers, and no serialization error is raised at this "
            "level for this scenario.",
            _options(
                "Both reads return the same data, because the transaction keeps one snapshot "
                "from its first statement.",
                "The second read sees the new committed value, because each statement takes "
                "a new snapshot.",
                "The second read blocks until the other transaction's session is closed.",
                "The second read fails with a serialization error.",
            ),
        ),
        _t(
            "No nível de isolamento padrão do PostgreSQL, uma transação executa o mesmo "
            "`SELECT` duas vezes. Entre os dois comandos, outra transação faz commit de um "
            "`UPDATE` em uma das linhas retornadas. O que acontece?",
            "O padrão é `READ COMMITTED`: cada comando recebe um snapshot novo, então o "
            "segundo `SELECT` vê o valor recém-commitado (uma non-repeatable read). Ler o "
            "mesmo valor duas vezes exige `REPEATABLE READ` ou superior. No MVCC, leituras "
            "simples não bloqueiam por causa de escritores, e nenhum erro de serialização é "
            "lançado nesse nível para este cenário.",
            _options(
                "As duas leituras retornam os mesmos dados, pois a transação mantém um único "
                "snapshot desde o primeiro comando.",
                "A segunda leitura vê o novo valor commitado, pois cada comando obtém um "
                "snapshot novo.",
                "A segunda leitura bloqueia até a sessão da outra transação ser encerrada.",
                "A segunda leitura falha com um erro de serialização.",
            ),
        ),
    ),
    _q(
        "postgresql-fundamentals-q06",
        _PG,
        MS,
        MEDIUM,
        ("a", "c", "d"),
        ("transactions", "lost-update", "locking"),
        _t(
            "Many requests increment `accounts.balance` for the same row concurrently, at "
            "PostgreSQL's default isolation level. Which approaches avoid lost updates? "
            "Select all that apply.",
            "A single `UPDATE ... SET balance = balance + 10` is atomic: the row lock "
            "serializes the writers and each one re-reads the latest value. `SELECT ... FOR "
            "UPDATE` makes the second transaction wait for the first to finish before "
            "reading. Under `REPEATABLE READ`, the second writer gets a serialization error "
            "and must retry. Reading the value in the application and writing back a computed "
            "one is the lost-update race itself, and wrapping a plain `SELECT` and `UPDATE` "
            "in `BEGIN`/`COMMIT` at the default level does not change that, since the plain "
            "read takes no lock.",
            _options(
                "A single statement: `UPDATE accounts SET balance = balance + 10 WHERE id = 1`.",
                "`SELECT balance` in the application, add 10, then `UPDATE accounts SET "
                "balance = <computed value>`.",
                "Inside a transaction, `SELECT balance ... FOR UPDATE`, then update the row.",
                "Run the transaction at `REPEATABLE READ` and retry it when a serialization "
                "failure occurs.",
                "Wrap the plain `SELECT` and the `UPDATE` in `BEGIN`/`COMMIT` at the default "
                "isolation level.",
            ),
        ),
        _t(
            "Muitas requisições incrementam `accounts.balance` da mesma linha ao mesmo "
            "tempo, no nível de isolamento padrão do PostgreSQL. Quais abordagens evitam "
            "lost updates? Selecione todas que se aplicam.",
            "Um único `UPDATE ... SET balance = balance + 10` é atômico: o lock da linha "
            "serializa os escritores e cada um relê o valor mais recente. `SELECT ... FOR "
            "UPDATE` faz a segunda transação esperar a primeira terminar antes de ler. Em "
            "`REPEATABLE READ`, o segundo escritor recebe um erro de serialização e precisa "
            "tentar de novo. Ler o valor na aplicação e gravar de volta um valor calculado é "
            "a própria race do lost update, e envolver um `SELECT` simples e o `UPDATE` em "
            "`BEGIN`/`COMMIT` no nível padrão não muda isso, pois a leitura simples não "
            "toma lock.",
            _options(
                "Um único comando: `UPDATE accounts SET balance = balance + 10 WHERE id = 1`.",
                "`SELECT balance` na aplicação, somar 10 e então `UPDATE accounts SET "
                "balance = <valor calculado>`.",
                "Dentro de uma transação, `SELECT balance ... FOR UPDATE` e depois atualizar "
                "a linha.",
                "Executar a transação em `REPEATABLE READ` e repeti-la quando ocorrer uma "
                "falha de serialização.",
                "Envolver o `SELECT` simples e o `UPDATE` em `BEGIN`/`COMMIT` no nível de "
                "isolamento padrão.",
            ),
        ),
    ),
    _q(
        "postgresql-fundamentals-q07",
        _PG,
        CODE,
        MEDIUM,
        ("d",),
        ("indexes", "explain", "expression-index"),
        _t(
            "The `email` column is `UNIQUE` (so it has an index), yet this query does a "
            "sequential scan. What is the reason and the usual fix?\n\n" + _LOWER_EMAIL_SQL,
            "The index is on `email`, but the query filters on the expression `lower(email)`, "
            "a different value the plain index cannot answer. The fix is an expression index, "
            "`CREATE INDEX ON users (lower(email))` (or a case-insensitive type such as "
            "`citext`). Unique indexes do serve equality lookups, text columns are indexable, "
            "and `EXPLAIN` does not need any special data type.",
            _options(
                "`UNIQUE` indexes cannot be used for equality lookups.",
                "PostgreSQL never uses indexes on `text` columns.",
                "`EXPLAIN` disables index usage; the real query would use the index.",
                "The filter applies `lower()` to the column, so the index on `email` cannot "
                "be used; create an expression index on `lower(email)`.",
            ),
        ),
        _t(
            "A coluna `email` é `UNIQUE` (logo, tem um índice), mas esta consulta faz uma "
            "varredura sequencial. Qual é o motivo e a correção usual?\n\n" + _LOWER_EMAIL_SQL,
            "O índice é sobre `email`, mas a consulta filtra pela expressão `lower(email)`, "
            "um valor diferente que o índice simples não consegue responder. A correção é "
            "um índice de expressão, `CREATE INDEX ON users (lower(email))` (ou um tipo "
            "insensível a maiúsculas, como `citext`). Índices únicos servem, sim, para buscas "
            "de igualdade, colunas `text` podem ser indexadas, e o `EXPLAIN` não exige "
            "nenhum tipo de dado especial.",
            _options(
                "Índices `UNIQUE` não podem ser usados em buscas de igualdade.",
                "O PostgreSQL nunca usa índices em colunas `text`.",
                "O `EXPLAIN` desativa o uso de índices; a consulta real usaria o índice.",
                "O filtro aplica `lower()` à coluna, então o índice em `email` não pode ser "
                "usado; crie um índice de expressão em `lower(email)`.",
            ),
        ),
    ),
    _q(
        "postgresql-fundamentals-q08",
        _PG,
        CODE,
        MEDIUM,
        ("c",),
        ("sql", "null", "subqueries"),
        _t(
            "What does this query return?\n\n" + _NOT_IN_SQL,
            "`id NOT IN (...)` expands to `id <> v1 AND id <> v2 AND ...`. When one of the "
            "values is `NULL`, `id <> NULL` is unknown, so the whole condition can never be "
            "true and the query returns no rows at all, instead of the users without "
            "orders. The robust forms are `NOT EXISTS (SELECT 1 FROM orders o WHERE "
            "o.user_id = u.id)` or a `LEFT JOIN ... IS NULL` anti-join.",
            _options(
                "The users that have no orders; the `NULL` row is simply ignored.",
                "Every user, since `NULL` matches nothing.",
                "No rows at all, because the comparison with `NULL` makes the condition "
                "unknown for every user.",
                "An error, because `NOT IN` does not accept subqueries with `NULL`.",
            ),
        ),
        _t(
            "O que esta consulta retorna?\n\n" + _NOT_IN_SQL,
            "`id NOT IN (...)` se expande para `id <> v1 AND id <> v2 AND ...`. Quando um dos "
            "valores é `NULL`, `id <> NULL` é desconhecido, então a condição inteira nunca "
            "pode ser verdadeira e a consulta não retorna nenhuma linha, em vez dos usuários "
            "sem pedidos. As formas robustas são `NOT EXISTS (SELECT 1 FROM orders o WHERE "
            "o.user_id = u.id)` ou um anti-join com `LEFT JOIN ... IS NULL`.",
            _options(
                "Os usuários sem pedidos; a linha com `NULL` é simplesmente ignorada.",
                "Todos os usuários, pois `NULL` não casa com nada.",
                "Nenhuma linha, pois a comparação com `NULL` torna a condição desconhecida "
                "para todos os usuários.",
                "Um erro, pois `NOT IN` não aceita subconsultas com `NULL`.",
            ),
        ),
    ),
    _q(
        "postgresql-fundamentals-q09",
        _PG,
        SHORT,
        HARD,
        None,
        ("isolation", "write-skew", "serializable"),
        _t(
            "A hospital rule says at least one doctor must stay on call. Two transactions run "
            "at `REPEATABLE READ`: each counts the doctors on call, sees two, and then sets "
            "its own doctor (a different row in each) to off call. Both commit and nobody is "
            "left on call. Why did this happen and how do you prevent it?",
            "Self-check: did you mention (1) write skew under snapshot isolation, (2) that "
            "the transactions update different rows so there is no write-write conflict, "
            "(3) `SERIALIZABLE` with retry on serialization failure, and (4) an alternative "
            "such as explicit locking of the rows that were read?",
            model_answer="This is write skew. At `REPEATABLE READ` each transaction works on "
            "its own snapshot, where both doctors are still on call. They write to different "
            "rows, so PostgreSQL sees no write-write conflict and both commits succeed, even "
            "though together they violate the invariant. Fixes: run the transaction at "
            "`SERIALIZABLE`, where PostgreSQL detects the read-write dependency cycle and "
            "aborts one transaction with a serialization failure (SQLSTATE 40001), which the "
            "application must retry; or make the read lock what it depends on, for example "
            "`SELECT ... FOR UPDATE` on all on-call rows (or on a shared parent row), so the "
            "transactions serialize.",
        ),
        _t(
            "Uma regra de um hospital diz que pelo menos um médico deve ficar de plantão. "
            "Duas transações rodam em `REPEATABLE READ`: cada uma conta os médicos de "
            "plantão, vê dois e então marca o seu próprio médico (uma linha diferente em "
            "cada) como fora de plantão. Ambas fazem commit e ninguém fica de plantão. Por "
            "que isso aconteceu e como evitar?",
            "Autoavaliação: você mencionou (1) write skew sob snapshot isolation, (2) que as "
            "transações atualizam linhas diferentes, então não há conflito escrita-escrita, "
            "(3) `SERIALIZABLE` com nova tentativa após falha de serialização e (4) uma "
            "alternativa como bloquear explicitamente as linhas lidas?",
            model_answer="Isso é write skew. Em `REPEATABLE READ`, cada transação trabalha "
            "em seu próprio snapshot, no qual os dois médicos ainda estão de plantão. Elas "
            "escrevem em linhas diferentes, então o PostgreSQL não vê conflito "
            "escrita-escrita e os dois commits têm sucesso, embora juntos violem a "
            "invariante. Correções: executar a transação em `SERIALIZABLE`, onde o "
            "PostgreSQL detecta o ciclo de dependências leitura-escrita e aborta uma das "
            "transações com falha de serialização (SQLSTATE 40001), que a aplicação deve "
            "repetir; ou fazer a leitura bloquear aquilo de que depende, por exemplo "
            "`SELECT ... FOR UPDATE` em todas as linhas de plantão (ou em uma linha pai "
            "compartilhada), de modo que as transações se serializem.",
        ),
    ),
    _q(
        "postgresql-fundamentals-q10",
        _PG,
        MC,
        HARD,
        ("a",),
        ("transactions", "deadlock", "locking"),
        _t(
            "Transaction T1 updates row A and then row B. Concurrently, T2 updates row B and "
            "then row A, and the two interleave so each holds one lock and waits for the "
            "other. What happens in PostgreSQL, and what is the standard prevention?",
            "PostgreSQL's deadlock detector finds the wait cycle (after `deadlock_timeout`, "
            "one second by default), aborts one of the transactions with a `deadlock "
            "detected` error and lets the other proceed; the application should retry the "
            "victim. The standard prevention is to acquire locks in a consistent order in "
            "all code paths. MVCC does not let writers on the same row run in parallel, "
            "transactions do not wait forever, and a locked row is never silently skipped by "
            "a plain `UPDATE`.",
            _options(
                "One transaction is aborted with a deadlock error and the other continues; "
                "prevent it by always locking rows in the same order.",
                "Both wait forever, because PostgreSQL has no deadlock detection; prevent it "
                "with a longer `statement_timeout`.",
                "Both succeed, since MVCC lets writers update the same rows without "
                "blocking each other.",
                "Each `UPDATE` silently skips the row locked by the other transaction.",
            ),
        ),
        _t(
            "A transação T1 atualiza a linha A e depois a linha B. Ao mesmo tempo, T2 "
            "atualiza a linha B e depois a A, e as duas se intercalam de modo que cada uma "
            "segura um lock e espera pelo outro. O que acontece no PostgreSQL e qual é a "
            "prevenção padrão?",
            "O detector de deadlocks do PostgreSQL encontra o ciclo de espera (após "
            "`deadlock_timeout`, um segundo por padrão), aborta uma das transações com o "
            "erro `deadlock detected` e deixa a outra seguir; a aplicação deve repetir a "
            "vítima. A prevenção padrão é adquirir locks em uma ordem consistente em todos "
            "os caminhos de código. O MVCC não deixa escritores da mesma linha rodarem em "
            "paralelo, transações não esperam para sempre, e uma linha bloqueada nunca é "
            "silenciosamente ignorada por um `UPDATE` simples.",
            _options(
                "Uma transação é abortada com erro de deadlock e a outra continua; evita-se "
                "isso bloqueando sempre as linhas na mesma ordem.",
                "Ambas esperam para sempre, pois o PostgreSQL não detecta deadlocks; evita-se "
                "com um `statement_timeout` maior.",
                "Ambas têm sucesso, pois o MVCC permite que escritores atualizem as mesmas "
                "linhas sem bloquear uns aos outros.",
                "Cada `UPDATE` ignora silenciosamente a linha bloqueada pela outra transação.",
            ),
        ),
    ),
)

# ----------------------------------------------------------------------
# event-driven-architecture
# ----------------------------------------------------------------------

_DUAL_WRITE_CODE = """```python
def place_order(db, broker, data):
    order = Order(**data)
    db.add(order)
    db.commit()
    broker.publish("order.placed", {"order_id": str(order.id)})
    return order
```"""

_DEDUP_CONSUMER_CODE = """```python
def handle(message):
    with db.begin():
        inserted = db.execute(
            "INSERT INTO processed_messages (message_id) VALUES (:id) "
            "ON CONFLICT DO NOTHING",
            {"id": message.id},
        ).rowcount
        if inserted == 0:
            return  # already processed
        record_charge(db, message.payload)  # writes to the same database
```"""

_EDA = "event-driven-architecture"

EDA_QUESTIONS: tuple[QuestionSeed, ...] = (
    _q(
        "event-driven-architecture-q01",
        _EDA,
        MC,
        EASY,
        ("c",),
        ("queues", "pub-sub"),
        _t(
            "What is the key difference between a work queue with competing consumers and a "
            "pub/sub topic?",
            "In a work queue, each message is delivered to just one of the competing "
            "consumers, which is how you spread work across workers. In pub/sub, every "
            "subscriber receives its own copy of each message, so billing, analytics and "
            "notifications can all react to the same event. Both are asynchronous, and both "
            "can be durable, so those are not the distinguishing factors.",
            _options(
                "A work queue is synchronous, while pub/sub is asynchronous.",
                "Pub/sub messages are never persisted, while queue messages always are.",
                "In a work queue each message is handled by one consumer; in pub/sub each "
                "subscriber receives its own copy of every message.",
                "A work queue can have only one consumer, while pub/sub has many.",
            ),
        ),
        _t(
            "Qual é a principal diferença entre uma fila de trabalho com consumidores "
            "concorrentes e um tópico pub/sub?",
            "Em uma fila de trabalho, cada mensagem é entregue a apenas um dos consumidores "
            "concorrentes, e é assim que se distribui trabalho entre workers. No pub/sub, "
            "cada assinante recebe sua própria cópia de cada mensagem, então faturamento, "
            "analytics e notificações podem reagir ao mesmo evento. Ambos são assíncronos e "
            "ambos podem ser duráveis, então esses não são os fatores que os distinguem.",
            _options(
                "Uma fila de trabalho é síncrona, enquanto o pub/sub é assíncrono.",
                "Mensagens de pub/sub nunca são persistidas, enquanto as de fila sempre são.",
                "Em uma fila de trabalho cada mensagem é tratada por um consumidor; no "
                "pub/sub cada assinante recebe sua própria cópia de toda mensagem.",
                "Uma fila de trabalho só pode ter um consumidor, enquanto o pub/sub tem vários.",
            ),
        ),
    ),
    _q(
        "event-driven-architecture-q02",
        _EDA,
        MC,
        EASY,
        ("d",),
        ("delivery-guarantees", "idempotency"),
        _t(
            "A broker offers at-least-once delivery. What must the consumer be designed for?",
            "At-least-once means a message is never silently lost, but it can be delivered "
            "more than once (for example after a consumer crash before the acknowledgement, "
            "or an acknowledgement timeout). The consumer must therefore be idempotent: "
            "processing the same message twice must have the same effect as processing it "
            "once. Duplicates are expected, loss is not allowed by the guarantee, and global "
            "ordering is not part of it.",
            _options(
                "Messages are never duplicated, so no special handling is needed.",
                "Messages may be lost, so the consumer must poll the database as a backup.",
                "Messages always arrive in the global order they were published.",
                "The same message may arrive more than once, so processing must be idempotent.",
            ),
        ),
        _t(
            "Um broker oferece entrega at-least-once. Para o que o consumidor deve ser projetado?",
            "At-least-once significa que uma mensagem nunca se perde silenciosamente, mas "
            "pode ser entregue mais de uma vez (por exemplo, após uma queda do consumidor "
            "antes do acknowledgement, ou um timeout do acknowledgement). Portanto o "
            "consumidor deve ser idempotente: processar a mesma mensagem duas vezes deve ter "
            "o mesmo efeito que processá-la uma vez. Duplicatas são esperadas, a perda não é "
            "permitida pela garantia, e ordenação global não faz parte dela.",
            _options(
                "As mensagens nunca são duplicadas, então nenhum tratamento especial é necessário.",
                "As mensagens podem se perder, então o consumidor deve consultar o banco "
                "como reserva.",
                "As mensagens sempre chegam na ordem global em que foram publicadas.",
                "A mesma mensagem pode chegar mais de uma vez, então o processamento deve ser "
                "idempotente.",
            ),
        ),
    ),
    _q(
        "event-driven-architecture-q03",
        _EDA,
        MC,
        EASY,
        ("a",),
        ("decoupling", "message-queues"),
        _t(
            "The order service publishes an `OrderPlaced` message to a broker, and the email "
            "service consumes it, instead of the order service calling the email service over "
            "HTTP. What is the main benefit?",
            "The services are decoupled in time: if the email service is slow or down, "
            "orders still succeed and the messages wait in the queue until it recovers, and "
            "traffic spikes are absorbed by the queue. It does not give exactly-once "
            "delivery, it does not remove the need for failure handling (retries, duplicates, "
            "dead letters), and the email is sent later, not before the order response.",
            _options(
                "Order processing keeps working when the email service is slow or down, and "
                "the queue absorbs traffic spikes.",
                "It guarantees that each email is sent exactly once.",
                "It removes the need to handle failures in the email service.",
                "The email is guaranteed to be sent before the order response returns.",
            ),
        ),
        _t(
            "O serviço de pedidos publica uma mensagem `OrderPlaced` em um broker, e o "
            "serviço de e-mail a consome, em vez de o serviço de pedidos chamar o de e-mail "
            "por HTTP. Qual é o principal benefício?",
            "Os serviços ficam desacoplados no tempo: se o serviço de e-mail estiver lento "
            "ou fora do ar, os pedidos continuam funcionando e as mensagens esperam na fila "
            "até ele se recuperar, e picos de tráfego são absorvidos pela fila. Isso não dá "
            "entrega exactly-once, não elimina a necessidade de tratar falhas (retries, "
            "duplicatas, dead letters), e o e-mail é enviado depois, não antes da resposta "
            "do pedido.",
            _options(
                "O processamento de pedidos continua funcionando quando o serviço de e-mail "
                "está lento ou fora do ar, e a fila absorve picos de tráfego.",
                "Garante que cada e-mail seja enviado exatamente uma vez.",
                "Elimina a necessidade de tratar falhas no serviço de e-mail.",
                "O e-mail é garantidamente enviado antes de a resposta do pedido retornar.",
            ),
        ),
    ),
    _q(
        "event-driven-architecture-q04",
        _EDA,
        MC,
        MEDIUM,
        ("b",),
        ("exactly-once", "delivery-guarantees"),
        _t(
            'Which statement about "exactly-once delivery" across a network and '
            "independent systems is the most accurate?",
            "Over an unreliable network, a sender cannot know whether a lost acknowledgement "
            "means the message was lost or only the reply, so true exactly-once delivery is "
            "not generally achievable end to end. In practice you get exactly-once effects "
            "by combining at-least-once delivery with idempotent (or transactional) "
            "processing. Acknowledgements alone do not deduplicate, retrying an at-most-once "
            "sender produces at-least-once, and acknowledging before processing risks "
            "losing the message on a crash.",
            _options(
                "Any broker provides it once acknowledgements are enabled.",
                "It is not generally achievable end to end; in practice you combine "
                "at-least-once delivery with idempotent processing to get exactly-once "
                "effects.",
                "At-most-once delivery plus retries on the sender gives exactly-once.",
                "Acknowledging each message before processing it guarantees exactly-once "
                "processing.",
            ),
        ),
        _t(
            'Qual afirmação sobre "entrega exactly-once" através de uma rede e de sistemas '
            "independentes é a mais precisa?",
            "Em uma rede não confiável, o remetente não sabe se um acknowledgement perdido "
            "significa que a mensagem se perdeu ou apenas a resposta, então a entrega "
            "exactly-once verdadeira geralmente não é alcançável de ponta a ponta. Na "
            "prática, obtêm-se efeitos exactly-once combinando entrega at-least-once com "
            "processamento idempotente (ou transacional). Acknowledgements sozinhos não "
            "deduplicam, repetir um remetente at-most-once produz at-least-once, e dar "
            "acknowledge antes de processar arrisca perder a mensagem em uma queda.",
            _options(
                "Qualquer broker a fornece quando os acknowledgements estão habilitados.",
                "Geralmente não é alcançável de ponta a ponta; na prática combina-se "
                "entrega at-least-once com processamento idempotente para obter efeitos "
                "exactly-once.",
                "Entrega at-most-once mais retries no remetente resulta em exactly-once.",
                "Dar acknowledge em cada mensagem antes de processá-la garante "
                "processamento exactly-once.",
            ),
        ),
    ),
    _q(
        "event-driven-architecture-q05",
        _EDA,
        CODE,
        MEDIUM,
        ("a",),
        ("dual-write", "outbox", "reliability"),
        _t(
            "What is the reliability problem in this code?\n\n" + _DUAL_WRITE_CODE,
            "This is the dual-write problem: the database and the broker are two systems "
            "that cannot be updated atomically. If the process crashes or the broker is "
            "unavailable after `commit()` but before `publish()` succeeds, the order exists "
            "and no event is ever sent. The commit has already happened, so nothing rolls "
            "back, and publishing after the commit does not by itself duplicate events. The "
            "usual fix is the transactional outbox.",
            _options(
                "A crash or broker failure after the commit leaves a saved order whose event "
                "is never published.",
                "Publishing after the commit makes the event be delivered twice.",
                "If `publish` fails, the already committed transaction is rolled back "
                "automatically.",
                "`broker.publish` is blocked until the database replicas catch up.",
            ),
        ),
        _t(
            "Qual é o problema de confiabilidade neste código?\n\n" + _DUAL_WRITE_CODE,
            "Este é o problema do dual-write: o banco de dados e o broker são dois sistemas "
            "que não podem ser atualizados atomicamente. Se o processo cair ou o broker "
            "estiver indisponível depois do `commit()` mas antes de o `publish()` ter "
            "sucesso, o pedido existe e nenhum evento é enviado. O commit já aconteceu, "
            "então nada é revertido, e publicar após o commit não duplica eventos por si só. "
            "A correção usual é o transactional outbox.",
            _options(
                "Uma queda ou falha do broker após o commit deixa um pedido salvo cujo "
                "evento nunca é publicado.",
                "Publicar após o commit faz o evento ser entregue duas vezes.",
                "Se o `publish` falhar, a transação já commitada é revertida automaticamente.",
                "`broker.publish` fica bloqueado até as réplicas do banco o alcançarem.",
            ),
        ),
    ),
    _q(
        "event-driven-architecture-q06",
        _EDA,
        MC,
        MEDIUM,
        ("d",),
        ("outbox", "reliability"),
        _t(
            "Which description matches the transactional outbox pattern?",
            "In the outbox pattern the business change and the event row are written in the "
            "same local database transaction, so either both exist or neither does. A relay "
            "process then reads unsent rows and publishes them to the broker, marking them "
            "sent; this gives at-least-once publishing, so consumers must still be "
            "idempotent. Publishing first and writing later reintroduces the dual-write "
            "gap, in-memory buffers lose events on a crash, and distributed two-phase commit "
            "is a different (and heavier) technique.",
            _options(
                "Publish to the broker first, then write to the database, retrying forever "
                "if the write fails.",
                "Keep events in an in-memory list and flush them to the broker every few seconds.",
                "Run a distributed two-phase commit between the database and the broker for "
                "every request.",
                "Insert the event into an outbox table in the same transaction as the state "
                "change; a separate relay publishes the rows and marks them as sent.",
            ),
        ),
        _t(
            "Qual descrição corresponde ao padrão transactional outbox?",
            "No padrão outbox, a mudança de negócio e a linha do evento são gravadas na "
            "mesma transação local do banco, então ou existem as duas ou nenhuma. Um "
            "processo relay lê então as linhas não enviadas e as publica no broker, "
            "marcando-as como enviadas; isso dá publicação at-least-once, então os "
            "consumidores ainda precisam ser idempotentes. Publicar primeiro e gravar depois "
            "reintroduz a lacuna do dual-write, buffers em memória perdem eventos em uma "
            "queda, e two-phase commit distribuído é uma técnica diferente (e mais pesada).",
            _options(
                "Publicar no broker primeiro e depois gravar no banco, repetindo para sempre "
                "se a gravação falhar.",
                "Manter os eventos em uma lista em memória e descarregá-los no broker a cada "
                "alguns segundos.",
                "Executar um two-phase commit distribuído entre o banco e o broker em toda "
                "requisição.",
                "Inserir o evento em uma tabela outbox na mesma transação da mudança de "
                "estado; um relay separado publica as linhas e as marca como enviadas.",
            ),
        ),
    ),
    _q(
        "event-driven-architecture-q07",
        _EDA,
        CODE,
        MEDIUM,
        ("b",),
        ("idempotent-consumer", "deduplication", "sql"),
        _t(
            "The broker redelivers message `m1` after a first attempt that had already "
            "committed. What happens in this handler?\n\n" + _DEDUP_CONSUMER_CODE,
            "The first delivery inserts `m1` into `processed_messages` (rowcount 1) and "
            "records the charge, committing both together. On redelivery, `ON CONFLICT DO "
            "NOTHING` inserts nothing (rowcount 0) and the handler returns without charging "
            "again. Because the dedup row and the side effect share one transaction, a "
            "crash before commit rolls back both and the retry starts clean. A conflict does "
            "not raise an error, and the insert does not wait for anything to be removed.",
            _options(
                "The insert succeeds again and the customer is charged twice.",
                "The insert affects 0 rows, so the handler returns without charging again.",
                "`ON CONFLICT` raises an exception and the message goes to a dead-letter queue.",
                "The insert waits until the earlier `processed_messages` row is deleted.",
            ),
        ),
        _t(
            "O broker reentrega a mensagem `m1` após uma primeira tentativa que já havia "
            "feito commit. O que acontece neste handler?\n\n" + _DEDUP_CONSUMER_CODE,
            "A primeira entrega insere `m1` em `processed_messages` (rowcount 1) e registra "
            "a cobrança, fazendo commit dos dois juntos. Na reentrega, `ON CONFLICT DO "
            "NOTHING` não insere nada (rowcount 0) e o handler retorna sem cobrar de novo. "
            "Como a linha de deduplicação e o efeito colateral compartilham uma transação, "
            "uma queda antes do commit desfaz ambos e a nova tentativa começa limpa. Um "
            "conflito não lança erro, e o insert não espera nada ser removido.",
            _options(
                "O insert tem sucesso de novo e o cliente é cobrado duas vezes.",
                "O insert afeta 0 linhas, então o handler retorna sem cobrar de novo.",
                "`ON CONFLICT` lança uma exceção e a mensagem vai para uma dead-letter queue.",
                "O insert espera até a linha anterior de `processed_messages` ser apagada.",
            ),
        ),
    ),
    _q(
        "event-driven-architecture-q08",
        _EDA,
        MS,
        MEDIUM,
        ("a", "c", "d"),
        ("consumers", "acknowledgements", "dead-letter-queue"),
        _t(
            "Which practices are sound for a consumer working with an at-least-once broker? "
            "Select all that apply.",
            "Acknowledge only after the work has been done (or durably recorded), so a "
            "crash leads to redelivery rather than loss. Send messages that keep failing to a "
            "dead-letter queue after bounded retries, so one poison message does not block "
            "the rest. Deduplicate with a unique message id or business key, because "
            "duplicates will happen. Acknowledging on receipt turns the guarantee into "
            "at-most-once (a crash loses the message), and ordering across queues or "
            "partitions is not guaranteed.",
            _options(
                "Acknowledge a message only after it has been processed successfully.",
                "Acknowledge as soon as the message is received, to avoid any redelivery.",
                "Move a message that keeps failing to a dead-letter queue after a bounded "
                "number of retries.",
                "Deduplicate using a unique message id or a business key.",
                "Assume messages in different partitions or queues are processed in the "
                "order they were published.",
            ),
        ),
        _t(
            "Quais práticas são adequadas para um consumidor que trabalha com um broker "
            "at-least-once? Selecione todas que se aplicam.",
            "Dar acknowledge apenas depois de o trabalho ter sido feito (ou registrado de "
            "forma durável), para que uma queda leve à reentrega e não à perda. Enviar "
            "mensagens que continuam falhando para uma dead-letter queue após um número "
            "limitado de tentativas, para que uma poison message não bloqueie as demais. "
            "Deduplicar com um id único de mensagem ou uma chave de negócio, pois "
            "duplicatas vão acontecer. Dar acknowledge ao receber transforma a garantia em "
            "at-most-once (uma queda perde a mensagem), e a ordenação entre filas ou "
            "partições não é garantida.",
            _options(
                "Dar acknowledge em uma mensagem somente depois de processá-la com sucesso.",
                "Dar acknowledge assim que a mensagem for recebida, para evitar qualquer "
                "reentrega.",
                "Mover para uma dead-letter queue a mensagem que continua falhando após um "
                "número limitado de tentativas.",
                "Deduplicar usando um id único de mensagem ou uma chave de negócio.",
                "Supor que mensagens de partições ou filas diferentes são processadas na "
                "ordem em que foram publicadas.",
            ),
        ),
    ),
    _q(
        "event-driven-architecture-q09",
        _EDA,
        MC,
        HARD,
        ("c",),
        ("ordering", "partitioning", "scalability"),
        _t(
            "A topic is split into partitions for throughput. The events of one order "
            "(`Created`, `Paid`, `Shipped`) must be processed in order, but different orders "
            "may be processed in parallel. What is the standard design?",
            "Ordering is guaranteed only within a partition. Publishing with the order id as "
            "the partition (ordering) key sends all events of one order to the same "
            "partition, where a single consumer in the group processes them sequentially, "
            "while different orders spread across partitions and run in parallel. Random "
            "keys lose per-order ordering, sleeping in the consumer is a fragile guess about "
            "timing, and a single partition gives up the parallelism you wanted.",
            _options(
                "Use random keys for an even spread and let the consumers sort events by "
                "timestamp.",
                "Use a single partition for the whole topic and a single consumer.",
                "Publish with the order id as the partition key, so all events of an order "
                "land in the same partition and are consumed in sequence.",
                "Make the consumer sleep a few seconds when it receives `Paid` before `Created`.",
            ),
        ),
        _t(
            "Um tópico é dividido em partições para ganhar vazão. Os eventos de um pedido "
            "(`Created`, `Paid`, `Shipped`) precisam ser processados em ordem, mas pedidos "
            "diferentes podem ser processados em paralelo. Qual é o design padrão?",
            "A ordem só é garantida dentro de uma partição. Publicar com o id do pedido como "
            "chave de partição (ordenação) envia todos os eventos de um pedido para a mesma "
            "partição, onde um único consumidor do grupo os processa em sequência, enquanto "
            "pedidos diferentes se espalham pelas partições e rodam em paralelo. Chaves "
            "aleatórias perdem a ordem por pedido, dormir no consumidor é um palpite frágil "
            "sobre tempo, e uma única partição abre mão do paralelismo desejado.",
            _options(
                "Usar chaves aleatórias para uma distribuição uniforme e deixar os "
                "consumidores ordenarem os eventos por timestamp.",
                "Usar uma única partição para o tópico inteiro e um único consumidor.",
                "Publicar com o id do pedido como chave de partição, de modo que todos os "
                "eventos de um pedido caiam na mesma partição e sejam consumidos em "
                "sequência.",
                "Fazer o consumidor dormir alguns segundos ao receber `Paid` antes de `Created`.",
            ),
        ),
    ),
    _q(
        "event-driven-architecture-q10",
        _EDA,
        SHORT,
        HARD,
        None,
        ("outbox", "idempotent-consumer", "reliability", "design"),
        _t(
            "Design the flow between an Order service and a Payment service so that an order "
            "is never saved without its `OrderPlaced` event being eventually published, and "
            "the customer is never charged twice, even with crashes and redeliveries. Which "
            "components and guarantees do you use?",
            "Self-check: did you mention (1) the transactional outbox written in the same "
            "transaction as the order, (2) a relay that publishes with at-least-once "
            "semantics, (3) an idempotent consumer with deduplication by event id in the same "
            "transaction as the charge, (4) acknowledging after processing, and (5) retries "
            "with a dead-letter queue and monitoring?",
            model_answer="Producer side: in one database transaction, save the order and "
            "insert an `OrderPlaced` row (with a unique event id) into an outbox table. A "
            "relay process (polling or log-based change data capture) publishes unsent rows "
            "to the broker and marks them sent. That gives at-least-once publishing with no "
            "dual-write gap, but duplicates are possible. Consumer side: Payment acknowledges "
            "a message only after processing, and processes idempotently: in one transaction "
            "it inserts the event id into a processed-messages table (primary key) and "
            "records the charge; a conflict means a duplicate, so it skips the work. For "
            "the external payment provider call, pass an idempotency key derived from the "
            "event or order id. Add bounded retries with backoff, a dead-letter queue for "
            "poison messages, and monitoring of outbox lag and queue depth. Result: "
            "at-least-once delivery plus idempotent processing gives exactly-once effects.",
        ),
        _t(
            "Projete o fluxo entre um serviço de Pedidos e um serviço de Pagamentos de modo "
            "que um pedido nunca seja salvo sem que seu evento `OrderPlaced` seja "
            "eventualmente publicado e que o cliente nunca seja cobrado duas vezes, mesmo "
            "com quedas e reentregas. Quais componentes e garantias você usa?",
            "Autoavaliação: você mencionou (1) o transactional outbox gravado na mesma "
            "transação do pedido, (2) um relay que publica com semântica at-least-once, "
            "(3) um consumidor idempotente com deduplicação por id de evento na mesma "
            "transação da cobrança, (4) acknowledge após o processamento e (5) retries com "
            "dead-letter queue e monitoramento?",
            model_answer="Lado produtor: em uma única transação do banco, salvar o pedido e "
            "inserir uma linha `OrderPlaced` (com um id de evento único) em uma tabela "
            "outbox. Um processo relay (polling ou change data capture baseado em log) "
            "publica as linhas não enviadas no broker e as marca como enviadas. Isso dá "
            "publicação at-least-once sem a lacuna do dual-write, mas duplicatas são "
            "possíveis. Lado consumidor: Pagamentos dá acknowledge somente após processar, e "
            "processa de forma idempotente: em uma transação insere o id do evento em uma "
            "tabela de mensagens processadas (chave primária) e registra a cobrança; um "
            "conflito indica duplicata, então pula o trabalho. Na chamada ao provedor de "
            "pagamento externo, usar uma chave de idempotência derivada do id do evento ou "
            "do pedido. Acrescentar retries limitados com backoff, uma dead-letter queue "
            "para poison messages e monitoramento do atraso da outbox e da profundidade da "
            "fila. Resultado: entrega at-least-once mais processamento idempotente dá "
            "efeitos exactly-once.",
        ),
    ),
)

QUESTIONS: tuple[QuestionSeed, ...] = REST_QUESTIONS + AUTH_QUESTIONS + PG_QUESTIONS + EDA_QUESTIONS

ASSESSMENTS: tuple[AssessmentSeed, ...] = (
    AssessmentSeed(
        code="rest-api-design-quiz",
        title="REST API Implementation Quiz",
        description="Status codes, idempotency, pagination, concurrency control and testing.",
        kind=AssessmentKind.COMPETENCY,
        competency_slug="rest-api-design",
        translations={
            "pt-BR": {
                "title": "Quiz de Implementação de APIs REST",
                "description": "Status codes, idempotência, paginação, controle de "
                "concorrência e testes.",
            }
        },
    ),
    AssessmentSeed(
        code="authentication-authorization-quiz",
        title="Authentication & Authorization Quiz",
        description="Password hashing, sessions vs JWTs, OAuth2/OIDC, IDOR, XSS and CSRF.",
        kind=AssessmentKind.COMPETENCY,
        competency_slug="authentication-authorization",
        translations={
            "pt-BR": {
                "title": "Quiz de Autenticação e Autorização",
                "description": "Hash de senhas, sessões vs JWTs, OAuth2/OIDC, IDOR, XSS e CSRF.",
            }
        },
    ),
    AssessmentSeed(
        code="postgresql-fundamentals-quiz",
        title="PostgreSQL Fundamentals Quiz",
        description="NULLs, joins, indexes, EXPLAIN, isolation levels, locking and deadlocks.",
        kind=AssessmentKind.COMPETENCY,
        competency_slug="postgresql-fundamentals",
        translations={
            "pt-BR": {
                "title": "Quiz de Fundamentos de PostgreSQL",
                "description": "NULLs, joins, índices, EXPLAIN, níveis de isolamento, locks e "
                "deadlocks.",
            }
        },
    ),
    AssessmentSeed(
        code="event-driven-architecture-quiz",
        title="Event-Driven Architecture Quiz",
        description="Queues, pub/sub, delivery guarantees, outbox and idempotent consumers.",
        kind=AssessmentKind.COMPETENCY,
        competency_slug="event-driven-architecture",
        translations={
            "pt-BR": {
                "title": "Quiz de Arquitetura Orientada a Eventos",
                "description": "Filas, pub/sub, garantias de entrega, outbox e consumidores "
                "idempotentes.",
            }
        },
    ),
    AssessmentSeed(
        code="backend-engineering-checkpoint",
        title="Backend Engineering Checkpoint",
        description="A mixed check across APIs, auth, PostgreSQL and event-driven design.",
        kind=AssessmentKind.MIXED,
        question_codes=(
            "rest-api-design-q02",
            "rest-api-design-q05",
            "rest-api-design-q07",
            "authentication-authorization-q05",
            "authentication-authorization-q08",
            "postgresql-fundamentals-q05",
            "postgresql-fundamentals-q06",
            "event-driven-architecture-q02",
            "event-driven-architecture-q05",
            "event-driven-architecture-q06",
        ),
        translations={
            "pt-BR": {
                "title": "Checkpoint de Engenharia de Backend",
                "description": "Uma verificação mista entre APIs, autenticação, PostgreSQL e "
                "design orientado a eventos.",
            }
        },
        pass_threshold=75,
        completion_bonus_xp=40,
    ),
)

QUESTION_SET = SubjectQuestionSet(
    subject_slug="backend-engineering",
    questions=QUESTIONS,
    assessments=ASSESSMENTS,
)
