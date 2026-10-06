"""Question bank for the System Design subject (api-design, caching-strategies,
load-balancing and database-scaling, ten questions each, English + Brazilian
Portuguese).

Written by Claude (``source=ai_generated``) and awaiting the owner's review,
as decided in docs/PROPOSAL_TRACK_I.md (D6). Rules: ``validate.py``.
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
    options: tuple[str, ...] | None = None,
    model_answer: str | None = None,
) -> QuestionText:
    return QuestionText(
        prompt=prompt,
        explanation=explanation,
        options=_options(*options) if options is not None else None,
        model_answer=model_answer,
    )


def _q(
    code: str,
    competency: str,
    qtype: QuestionType,
    difficulty: QuestionDifficulty,
    correct: tuple[str, ...] | None,
    tags: tuple[str, ...],
    en: QuestionText,
    pt: QuestionText,
) -> QuestionSeed:
    return QuestionSeed(
        code=code,
        competency_slug=competency,
        type=qtype,
        difficulty=difficulty,
        correct=correct,
        tags=tags,
        source=AI,
        text={Language.EN: en, Language.PT_BR: pt},
    )


_OFFSET_FEED_CODE = """```python
feed = ["e", "d", "c", "b", "a"]   # newest first
page1 = feed[0:3]                  # GET /feed?limit=3&offset=0
feed.insert(0, "f")                # a new item is published
page2 = feed[3:6]                  # GET /feed?limit=3&offset=3
print(page1, page2)
```"""


# ----------------------------------------------------------------------
# api-design
# ----------------------------------------------------------------------
_API: tuple[QuestionSeed, ...] = (
    _q(
        "api-design-q01",
        "api-design",
        MC,
        EASY,
        ("b",),
        ("rest", "resources"),
        _t(
            "A client needs the orders that belong to user 42. Which endpoint design best "
            "follows REST resource modelling?",
            "REST puts nouns in the URL and lets the HTTP method carry the verb: "
            "`GET /users/42/orders` reads the orders sub-resource of a user. The other options "
            "smuggle a verb into the path (RPC style), and A and D also use `POST` for a pure "
            "read, which hides that the call is safe and makes it harder to cache.",
            (
                '`POST /getUserOrders` with `{"user_id": 42}` in the body',
                "`GET /users/42/orders`",
                "`GET /getOrders?user=42`",
                "`POST /users/42/fetchOrders`",
            ),
        ),
        _t(
            "Um cliente precisa dos pedidos do usuário 42. Qual desenho de endpoint segue melhor "
            "a modelagem de recursos do REST?",
            "No REST os substantivos ficam na URL e o método HTTP carrega o verbo: "
            "`GET /users/42/orders` lê o sub-recurso de pedidos de um usuário. As demais opções "
            "enfiam um verbo no caminho (estilo RPC), e A e D ainda usam `POST` para uma simples "
            "leitura, o que esconde que a chamada é segura e dificulta o cache.",
            (
                '`POST /getUserOrders` com `{"user_id": 42}` no corpo',
                "`GET /users/42/orders`",
                "`GET /getOrders?user=42`",
                "`POST /users/42/fetchOrders`",
            ),
        ),
    ),
    _q(
        "api-design-q02",
        "api-design",
        MC,
        EASY,
        ("c",),
        ("http-status-codes",),
        _t(
            "A request carries a valid token for user Ana, but Ana's role does not allow her to "
            "delete this project. Which status code should the API return?",
            "`403 Forbidden` means the caller is authenticated but not authorized. `401` would "
            "be right if the token were missing or invalid (the server does not know who is "
            "calling). `400` is for a malformed request and `409` for a conflict with the "
            "resource's current state; neither describes a permission problem.",
            (
                "`400 Bad Request`",
                "`401 Unauthorized`",
                "`403 Forbidden`",
                "`409 Conflict`",
            ),
        ),
        _t(
            "Uma requisição traz um token válido da usuária Ana, mas o papel dela não permite "
            "excluir este projeto. Qual status code a API deve retornar?",
            "`403 Forbidden` significa que o chamador está autenticado, mas não autorizado. "
            "`401` seria o correto se o token estivesse ausente ou inválido (o servidor não sabe "
            "quem está chamando). `400` é para requisição malformada e `409` para conflito com o "
            "estado atual do recurso; nenhum descreve um problema de permissão.",
            (
                "`400 Bad Request`",
                "`401 Unauthorized`",
                "`403 Forbidden`",
                "`409 Conflict`",
            ),
        ),
    ),
    _q(
        "api-design-q03",
        "api-design",
        MC,
        EASY,
        ("d",),
        ("idempotency", "http-methods"),
        _t(
            "A mobile client sends a request and the connection times out, so it cannot tell "
            "whether the server processed it. Which request is naturally safe to retry blindly?",
            "`PUT` replaces the whole resource with the representation sent, so repeating it "
            "leaves the same end state: it is idempotent by definition. Retrying `POST /orders` "
            "or `POST /payments` can create a second order or charge twice, and a `PATCH` that "
            'says "increment by 1" changes the result on every repetition.',
            (
                "`POST /orders` creating a new order",
                "`POST /payments` charging a card",
                '`PATCH /counters/7` with `{"increment": 1}`',
                "`PUT /users/42` with the full new representation of the user",
            ),
        ),
        _t(
            "Um cliente mobile envia uma requisição e a conexão expira (timeout), então ele não "
            "sabe se o servidor a processou. Qual requisição é naturalmente segura para "
            "reenviar às cegas?",
            "O `PUT` substitui o recurso inteiro pela representação enviada, então repeti-lo "
            "deixa o mesmo estado final: é idempotente por definição. Reenviar `POST /orders` "
            "ou `POST /payments` pode criar um segundo pedido ou cobrar duas vezes, e um `PATCH` "
            'que diz "incremente em 1" muda o resultado a cada repetição.',
            (
                "`POST /orders` criando um novo pedido",
                "`POST /payments` cobrando um cartão",
                '`PATCH /counters/7` com `{"increment": 1}`',
                "`PUT /users/42` com a nova representação completa do usuário",
            ),
        ),
    ),
    _q(
        "api-design-q04",
        "api-design",
        MC,
        MEDIUM,
        ("a",),
        ("pagination", "performance"),
        _t(
            "An API exposes a table of 50 million rows through `?limit=20&offset=N`, and clients "
            "that page deep get very slow responses. What is the main reason cursor pagination "
            "(`?after=<cursor>`) avoids this problem?",
            "With a large `OFFSET` the database still walks and discards every skipped row, so "
            "cost grows with how deep you page. A cursor encodes the last-seen sort key, so the "
            "query becomes `WHERE id > :last ORDER BY id LIMIT 20`: an index seek whose cost "
            "does not depend on depth. Offset queries can use indexes too (C is wrong), and "
            "cursors are sequential, so they give up jumping to an arbitrary page (D is "
            "backwards).",
            (
                "The database seeks straight to the last-seen key through an index, whereas a "
                "large offset makes it walk and discard all the skipped rows.",
                "Browsers cache cursor URLs, so deep pages are rarely requested from the server.",
                "Offset queries cannot use an index for the sort order, but cursor queries can.",
                "A cursor lets the client jump directly to page 5000, which offset does not "
                "allow.",
            ),
        ),
        _t(
            "Uma API expõe uma tabela de 50 milhões de linhas com `?limit=20&offset=N`, e "
            "clientes que paginam fundo recebem respostas muito lentas. Qual é a principal razão "
            "de a paginação por cursor (`?after=<cursor>`) evitar esse problema?",
            "Com um `OFFSET` grande o banco ainda percorre e descarta todas as linhas puladas, "
            "então o custo cresce com a profundidade da página. O cursor codifica a última chave "
            "de ordenação vista, e a consulta vira `WHERE id > :last ORDER BY id LIMIT 20`: uma "
            "busca por índice cujo custo não depende da profundidade. Consultas com offset também "
            "podem usar índices (C está errada) e o cursor é sequencial, abrindo mão de pular "
            "para uma página arbitrária (D está invertida).",
            (
                "O banco busca direto a última chave vista por meio de um índice, enquanto um "
                "offset grande o obriga a percorrer e descartar todas as linhas puladas.",
                "Os navegadores fazem cache das URLs com cursor, então páginas profundas "
                "raramente chegam ao servidor.",
                "Consultas com offset não conseguem usar índice para a ordenação, mas as com "
                "cursor conseguem.",
                "O cursor permite ao cliente saltar direto para a página 5000, o que o offset "
                "não permite.",
            ),
        ),
    ),
    _q(
        "api-design-q05",
        "api-design",
        CODE,
        MEDIUM,
        ("c",),
        ("pagination", "offset"),
        _t(
            "A client reads a newest-first feed with offset pagination. Between its two "
            "requests, a new item is published. What does the client receive?\n\n"
            + _OFFSET_FEED_CODE,
            "The new item `f` shifts every existing item one position down, so the item at "
            "offset 3 is now `c`, which the client already received on page 1. The output is "
            "`['e', 'd', 'c'] ['c', 'b', 'a']`: a duplicate. (A delete would do the opposite "
            "and make the client skip an item.) Cursor pagination avoids this because it is "
            "anchored to a value, not to a position.",
            (
                "`['e', 'd', 'c'] ['b', 'a']`: item `c` is skipped.",
                "`['e', 'd', 'c'] ['f', 'e', 'd']`: the new item shows up first.",
                "`['e', 'd', 'c'] ['c', 'b', 'a']`: item `c` appears on both pages.",
                "An `IndexError`, because the list changed size between the two reads.",
            ),
        ),
        _t(
            "Um cliente lê um feed do mais novo para o mais antigo com paginação por offset. "
            "Entre as duas requisições, um novo item é publicado. O que o cliente recebe?\n\n"
            + _OFFSET_FEED_CODE,
            "O novo item `f` empurra todos os itens existentes uma posição para baixo, então o "
            "item no offset 3 agora é `c`, que o cliente já recebeu na página 1. A saída é "
            "`['e', 'd', 'c'] ['c', 'b', 'a']`: um item duplicado. (Uma exclusão faria o "
            "oposto e o cliente pularia um item.) A paginação por cursor evita isso porque é "
            "ancorada em um valor, não em uma posição.",
            (
                "`['e', 'd', 'c'] ['b', 'a']`: o item `c` é pulado.",
                "`['e', 'd', 'c'] ['f', 'e', 'd']`: o novo item aparece primeiro.",
                "`['e', 'd', 'c'] ['c', 'b', 'a']`: o item `c` aparece nas duas páginas.",
                "Um `IndexError`, porque a lista mudou de tamanho entre as duas leituras.",
            ),
        ),
    ),
    _q(
        "api-design-q06",
        "api-design",
        MC,
        MEDIUM,
        ("d",),
        ("idempotency", "concurrency", "payments"),
        _t(
            "Two retries of the same `POST /payments`, carrying the same `Idempotency-Key`, hit "
            "two different servers a few milliseconds apart. Which server-side design reliably "
            "charges the card only once?",
            "The key must be reserved atomically, before the side effect, using something the "
            "database enforces (a unique constraint, a lock). The request that loses the race "
            "then waits for, or replays, the stored result. Look-up-then-charge (A) is a classic "
            "check-then-act race: both retries pass the check. Client-side waiting (B) cannot "
            "prevent two in-flight requests, and dropping requests by body hash (C) ignores the "
            "key and would also block legitimate repeated purchases.",
            (
                "Look the key up; if it is absent, charge the card and store the key and the "
                "response afterwards.",
                "Make the client wait 30 seconds before every retry.",
                "Drop any request whose body hash was seen in the last second.",
                "Reserve the key under a unique constraint in the same transaction that records "
                "the payment, and let the request that loses the race replay the stored result.",
            ),
        ),
        _t(
            "Dois reenvios do mesmo `POST /payments`, com o mesmo `Idempotency-Key`, chegam a "
            "dois servidores diferentes com poucos milissegundos de diferença. Qual desenho no "
            "servidor garante de forma confiável que o cartão seja cobrado só uma vez?",
            "A chave precisa ser reservada de forma atômica, antes do efeito colateral, usando "
            "algo que o banco garanta (constraint única, lock). A requisição que perde a corrida "
            "espera ou reaproveita o resultado armazenado. Consultar e depois cobrar (A) é uma "
            "race condition clássica de check-then-act: os dois reenvios passam na checagem. "
            "Esperar no cliente (B) não impede duas requisições em andamento, e descartar por "
            "hash do corpo (C) ignora a chave e bloquearia compras repetidas legítimas.",
            (
                "Consultar a chave; se ausente, cobrar o cartão e só depois gravar a chave e a "
                "resposta.",
                "Fazer o cliente esperar 30 segundos antes de cada reenvio.",
                "Descartar qualquer requisição cujo hash do corpo foi visto no último segundo.",
                "Reservar a chave com uma constraint única na mesma transação que registra o "
                "pagamento, e fazer a requisição que perde a corrida devolver o resultado "
                "armazenado.",
            ),
        ),
    ),
    _q(
        "api-design-q07",
        "api-design",
        MS,
        MEDIUM,
        ("a", "c", "e"),
        ("error-handling", "contracts"),
        _t(
            "Which of these are good practices for an API's error contract? Select all that "
            "apply.",
            "A stable machine-readable `code` lets clients branch on specific failures, a "
            "`request_id` ties a user's report to a server log line, and one envelope "
            "enforced by a global exception handler (even for unhandled 500s) spares clients "
            "from per-endpoint parsing. Returning `200 OK` with an error body hides failures "
            "from callers, load balancers and dashboards that only look at the status code, and "
            "leaking stack traces or SQL exposes internals without helping the client.",
            (
                "A stable, machine-readable error `code` (for example `insufficient_funds`).",
                "Return `200 OK` and put the error description in the body.",
                "A `request_id` in every error that correlates with server-side logs and traces.",
                "Include the stack trace and the failing SQL in the response to ease debugging.",
                "The same error envelope for every endpoint, enforced by one global exception "
                "handler.",
            ),
        ),
        _t(
            "Quais destas são boas práticas para o contrato de erros de uma API? Selecione "
            "todas que se aplicam.",
            "Um `code` estável e legível por máquina permite ao cliente tratar falhas "
            "específicas, um `request_id` liga o relato de um usuário a uma linha de log do "
            "servidor, e um único envelope imposto por um exception handler global (inclusive "
            "para 500s não tratados) poupa os clientes de parsing por endpoint. Retornar "
            "`200 OK` com o erro no corpo esconde a falha de chamadores, load balancers e "
            "dashboards que olham só o status code, e vazar stack trace ou SQL expõe detalhes "
            "internos sem ajudar o cliente.",
            (
                "Um `code` de erro estável e legível por máquina (por exemplo "
                "`insufficient_funds`).",
                "Retornar `200 OK` e colocar a descrição do erro no corpo.",
                "Um `request_id` em todo erro, correlacionado com logs e traces do servidor.",
                "Incluir o stack trace e o SQL que falhou na resposta para facilitar a "
                "depuração.",
                "O mesmo envelope de erro para todos os endpoints, imposto por um único "
                "exception handler global.",
            ),
        ),
    ),
    _q(
        "api-design-q08",
        "api-design",
        MC,
        MEDIUM,
        ("c",),
        ("versioning", "compatibility"),
        _t(
            "Your public API is served under `/v1`. Which change can ship **without** a new "
            "major version, because existing clients keep working?",
            "Adding a new optional field to a response is additive: clients that ignore it "
            "are unaffected. Renaming a field, changing a field's type, or making a previously "
            "optional request parameter required each break clients that were valid yesterday. "
            "Preferring additive changes is how teams avoid maintaining parallel API versions.",
            (
                "Renaming the response field `created` to `created_at`.",
                "Changing `id` from an integer to a string.",
                "Adding a new optional `nickname` field to the response.",
                "Making the previously optional `currency` request parameter required.",
            ),
        ),
        _t(
            "Sua API pública é servida em `/v1`. Qual mudança pode ser publicada **sem** uma "
            "nova versão maior, porque os clientes existentes continuam funcionando?",
            "Adicionar um novo campo opcional à resposta é uma mudança aditiva: clientes que o "
            "ignoram não são afetados. Renomear um campo, mudar o tipo de um campo ou tornar "
            "obrigatório um parâmetro antes opcional quebram clientes que eram válidos ontem. "
            "Preferir mudanças aditivas é como as equipes evitam manter versões paralelas da API.",
            (
                "Renomear o campo de resposta `created` para `created_at`.",
                "Mudar `id` de inteiro para string.",
                "Adicionar um novo campo opcional `nickname` à resposta.",
                "Tornar obrigatório o parâmetro de requisição `currency`, antes opcional.",
            ),
        ),
    ),
    _q(
        "api-design-q09",
        "api-design",
        MC,
        HARD,
        ("b",),
        ("pagination", "cursor", "ordering"),
        _t(
            "A feed is sorted by `created_at`. Its cursor holds the last row's `created_at`, and "
            "the next page runs `WHERE created_at > :cursor ORDER BY created_at LIMIT 20`. Bulk "
            "imports create many rows with the exact same timestamp, and users report items "
            "that never appear. What is the right fix?",
            "When several rows share a timestamp, a page boundary can fall in the middle of the "
            "tie, and `>` then skips the remaining tied rows. Add a unique tie-breaker to both "
            "the ordering and the cursor and compare the pair: "
            "`WHERE (created_at, id) > (:ts, :id) ORDER BY created_at, id`. `>=` (C) would "
            "repeat the last row and can loop forever if a whole page is tied, rounding "
            "timestamps (D) creates more ties, and going back to offset (A) brings back its "
            "cost and shifting problems.",
            (
                "Switch to `OFFSET`, so that position instead of the timestamp decides where "
                "each page starts.",
                "Order by `(created_at, id)` and put both values in the cursor, comparing them "
                "as a pair.",
                "Change `>` to `>=` so rows with the same timestamp are included.",
                "Round timestamps to whole seconds so ties become less frequent.",
            ),
        ),
        _t(
            "Um feed é ordenado por `created_at`. O cursor guarda o `created_at` da última "
            "linha, e a página seguinte executa `WHERE created_at > :cursor ORDER BY created_at "
            "LIMIT 20`. Importações em massa criam muitas linhas com exatamente o mesmo "
            "timestamp, e usuários relatam itens que nunca aparecem. Qual é a correção certa?",
            "Quando várias linhas têm o mesmo timestamp, o limite da página pode cair no meio do "
            "empate, e o `>` então pula as demais linhas empatadas. Adicione um desempate único "
            "à ordenação e ao cursor e compare o par: "
            "`WHERE (created_at, id) > (:ts, :id) ORDER BY created_at, id`. O `>=` (C) repetiria "
            "a última linha e pode entrar em loop se uma página inteira estiver empatada, "
            "arredondar timestamps (D) cria mais empates, e voltar ao offset (A) traz de volta "
            "o custo e o problema de deslocamento.",
            (
                "Voltar ao `OFFSET`, de modo que a posição, e não o timestamp, defina onde cada "
                "página começa.",
                "Ordenar por `(created_at, id)` e colocar os dois valores no cursor, comparando-os "
                "como um par.",
                "Trocar `>` por `>=` para incluir as linhas com o mesmo timestamp.",
                "Arredondar os timestamps para segundos inteiros, para que haja menos empates.",
            ),
        ),
    ),
    _q(
        "api-design-q10",
        "api-design",
        SHORT,
        HARD,
        None,
        ("idempotency", "retries", "design"),
        _t(
            "You are designing `POST /orders` for a mobile app on flaky networks. How do you make "
            "it safe to retry? Cover the mechanism, where the state lives, and the edge cases.",
            "Self-check: did you mention (1) a client-generated key per logical operation sent "
            "on every attempt, (2) atomic reservation with the side effect, (3) replaying the "
            "stored response, (4) rejecting the same key with a different body, and (5) key "
            "expiry?",
            model_answer="The client generates a unique key (for example a UUID) per logical "
            "order and sends it in an `Idempotency-Key` header on every attempt. The server "
            "reserves that key atomically with the side effect, for example a unique constraint "
            "on the key in the same transaction that inserts the order, so two concurrent "
            "retries cannot both create it. A repeated key returns the originally stored "
            "response (same status and body) instead of creating a second order. If the same "
            "key arrives with a different request body, it is a client bug and the server "
            "rejects it with 409 or 422 rather than silently reusing the old result. Stored keys "
            "expire after a window such as 24 hours to bound storage.",
        ),
        _t(
            "Você está desenhando o `POST /orders` para um app mobile em redes instáveis. Como "
            "torná-lo seguro para reenvio? Cubra o mecanismo, onde o estado fica e os casos de "
            "borda.",
            "Autoavaliação: você mencionou (1) uma chave gerada pelo cliente por operação lógica "
            "e enviada em toda tentativa, (2) a reserva atômica junto com o efeito colateral, "
            "(3) devolver a resposta armazenada, (4) rejeitar a mesma chave com corpo diferente "
            "e (5) a expiração das chaves?",
            model_answer="O cliente gera uma chave única (por exemplo um UUID) por pedido "
            "lógico e a envia no header `Idempotency-Key` em toda tentativa. O servidor reserva "
            "essa chave de forma atômica junto com o efeito colateral, por exemplo com uma "
            "constraint única na chave na mesma transação que insere o pedido, de modo que dois "
            "reenvios concorrentes não possam criá-lo ambos. Uma chave repetida devolve a "
            "resposta originalmente armazenada (mesmo status e corpo) em vez de criar um segundo "
            "pedido. Se a mesma chave chegar com um corpo diferente, é um bug do cliente e o "
            "servidor a rejeita com 409 ou 422, em vez de reaproveitar o resultado antigo em "
            "silêncio. As chaves guardadas expiram após uma janela, como 24 horas, para limitar "
            "o armazenamento.",
        ),
    ),
)


# --- caching-strategies: see below ---
_CACHE: tuple[QuestionSeed, ...] = ()
_LB: tuple[QuestionSeed, ...] = ()
_DB: tuple[QuestionSeed, ...] = ()


QUESTIONS: tuple[QuestionSeed, ...] = (*_API, *_CACHE, *_LB, *_DB)


ASSESSMENTS: tuple[AssessmentSeed, ...] = (
    AssessmentSeed(
        code="system-design-api-design-quiz",
        title="API Design Quiz",
        description="REST modelling, status codes, pagination, versioning and idempotent retries.",
        kind=AssessmentKind.COMPETENCY,
        competency_slug="api-design",
        translations={
            "pt-BR": {
                "title": "Quiz de Design de APIs",
                "description": "Modelagem REST, status codes, paginação, versionamento e "
                "reenvios idempotentes.",
            }
        },
    ),
)


QUESTION_SET = SubjectQuestionSet(
    subject_slug="system-design",
    questions=QUESTIONS,
    assessments=ASSESSMENTS,
)
