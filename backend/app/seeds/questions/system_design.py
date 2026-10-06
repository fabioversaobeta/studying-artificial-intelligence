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
                "A cursor lets the client jump directly to page 5000, which offset does not allow.",
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
            "Which of these are good practices for an API's error contract? Select all that apply.",
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
                "Incluir o stack trace e o SQL que falhou na resposta para facilitar a depuração.",
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


# ----------------------------------------------------------------------
# caching-strategies
# ----------------------------------------------------------------------
_STALE_READ_CODE = """```python
cache = {}
db = {"price": 10}

def read_price():
    if "price" not in cache:
        cache["price"] = db["price"]
    return cache["price"]

def write_price(value):
    db["price"] = value

print(read_price())
write_price(20)
print(read_price())
```"""

_CACHE: tuple[QuestionSeed, ...] = (
    _q(
        "caching-strategies-q01",
        "caching-strategies",
        MC,
        MEDIUM,
        ("c",),
        ("hit-ratio", "estimation"),
        _t(
            "A service handles 10,000 reads per second and its cache hit ratio is 95%, so the "
            "database sees about 500 reads per second. A deploy flushes part of the cache and "
            "the hit ratio falls to 90%. What happens to the database's read load?",
            "The database only sees misses: load = traffic x miss ratio. Going from a 5% to a "
            "10% miss ratio doubles it, from about 500 to about 1,000 reads per second. That is "
            "why a hit ratio that looks only slightly worse can overload a database that was "
            "sized for the old miss rate.",
            (
                "It rises by about 5%, to roughly 525 reads per second.",
                "It rises by 10%, to roughly 550 reads per second.",
                "It doubles, to roughly 1,000 reads per second.",
                "It stays about the same, because the cache absorbs the difference.",
            ),
        ),
        _t(
            "Um serviço recebe 10.000 leituras por segundo e a taxa de acerto (hit ratio) do "
            "cache é de 95%, então o banco vê cerca de 500 leituras por segundo. Um deploy "
            "esvazia parte do cache e o hit ratio cai para 90%. O que acontece com a carga de "
            "leitura do banco?",
            "O banco só vê os misses: carga = tráfego x taxa de miss. Passar de 5% para 10% de "
            "miss dobra a carga, de cerca de 500 para cerca de 1.000 leituras por segundo. Por "
            "isso um hit ratio que parece só um pouco pior pode sobrecarregar um banco "
            "dimensionado para a taxa de miss anterior.",
            (
                "Sobe cerca de 5%, para aproximadamente 525 leituras por segundo.",
                "Sobe 10%, para aproximadamente 550 leituras por segundo.",
                "Dobra, para aproximadamente 1.000 leituras por segundo.",
                "Fica quase igual, porque o cache absorve a diferença.",
            ),
        ),
    ),
    _q(
        "caching-strategies-q02",
        "caching-strategies",
        MC,
        EASY,
        ("a",),
        ("fundamentals", "staleness"),
        _t(
            "Which of these is the **worst** candidate for caching?",
            "Caching trades staleness for speed, so it fits data that is read far more often "
            "than it changes and can be slightly stale. A stock counter decremented on every "
            "sale and checked at checkout is write-heavy and must be exact; a stale value "
            "means overselling. Product descriptions, display names and static bundles are "
            "read-heavy and tolerate staleness.",
            (
                "A remaining-stock counter that is decremented on every sale and checked at "
                "checkout.",
                "Product descriptions that are edited about once a week.",
                "Users' display names shown next to comments.",
                "Static JavaScript and CSS bundles.",
            ),
        ),
        _t(
            "Qual destes é o **pior** candidato a cache?",
            "Cache troca atualidade por velocidade, então serve para dados lidos muito mais "
            "vezes do que alterados e que toleram um pouco de defasagem. Um contador de estoque "
            "decrementado a cada venda e conferido no checkout tem muita escrita e precisa ser "
            "exato; um valor defasado significa vender o que não existe. Descrições de produto, "
            "nomes de exibição e bundles estáticos são de leitura intensa e toleram defasagem.",
            (
                "Um contador de estoque restante que é decrementado a cada venda e conferido no "
                "checkout.",
                "Descrições de produto editadas cerca de uma vez por semana.",
                "Nomes de exibição de usuários mostrados ao lado de comentários.",
                "Bundles estáticos de JavaScript e CSS.",
            ),
        ),
    ),
    _q(
        "caching-strategies-q03",
        "caching-strategies",
        MC,
        EASY,
        ("b",),
        ("write-behind", "durability"),
        _t(
            "What is the main risk of a write-behind (write-back) cache?",
            "Write-behind acknowledges the write once it is in the cache and flushes it to the "
            "database later, in batches. If the cache node dies before a flush, those "
            "acknowledged writes never reached the source of truth. Writes are in fact faster "
            "than with write-through (A is backwards), and a cold cache and TTL-bounded "
            "staleness are concerns of other patterns.",
            (
                "Writes become slower than writing to the database directly.",
                "If the cache node fails before flushing, acknowledged writes are lost.",
                "Every read is a miss until the cache has been warmed up.",
                "Reads can return data older than any configured TTL.",
            ),
        ),
        _t(
            "Qual é o principal risco de um cache write-behind (write-back)?",
            "O write-behind confirma a escrita assim que ela está no cache e a grava no banco "
            "depois, em lotes. Se o nó do cache cair antes de um flush, essas escritas já "
            "confirmadas nunca chegaram à fonte da verdade. As escritas são, na verdade, mais "
            "rápidas que no write-through (A está invertida), e cache frio e defasagem limitada "
            "por TTL são preocupações de outros padrões.",
            (
                "As escritas ficam mais lentas do que gravar direto no banco.",
                "Se o nó do cache falhar antes do flush, escritas já confirmadas são perdidas.",
                "Toda leitura é um miss até o cache ser aquecido.",
                "As leituras podem devolver dados mais antigos do que qualquer TTL configurado.",
            ),
        ),
    ),
    _q(
        "caching-strategies-q04",
        "caching-strategies",
        MC,
        MEDIUM,
        ("d",),
        ("invalidation", "ttl"),
        _t(
            "Product prices are cached with explicit invalidation: the application deletes "
            "`product:{id}` whenever it changes a price. A nightly admin script then updates "
            "prices directly in SQL. What is the consequence, and what is the standard "
            "safeguard?",
            "The script bypasses the application code that invalidates the cache, and the "
            "database does not notify the cache on its own, so old prices keep being served "
            "until each entry expires or is evicted. That is why explicit invalidation should "
            "never stand alone: keep a TTL on every entry as a backstop that bounds the worst "
            "case, and make bulk jobs invalidate keys or bump a version key.",
            (
                "Nothing: the database notifies the cache automatically when a row changes.",
                "Only the first read after the script is stale; later reads refresh the entry "
                "automatically.",
                "The next read raises an error because the cached value no longer matches the row.",
                "The old prices keep being served until each entry expires or is evicted; "
                "always keep a TTL as a backstop, and make bulk jobs invalidate too.",
            ),
        ),
        _t(
            "Os preços de produtos são mantidos em cache com invalidação explícita: a aplicação "
            "apaga `product:{id}` sempre que altera um preço. Um script administrativo noturno "
            "atualiza preços direto em SQL. Qual é a consequência e qual é a salvaguarda padrão?",
            "O script contorna o código da aplicação que invalida o cache, e o banco não avisa "
            "o cache por conta própria, então os preços antigos continuam sendo servidos até "
            "cada entrada expirar ou ser removida. Por isso a invalidação explícita nunca deve "
            "ficar sozinha: mantenha um TTL em toda entrada como rede de segurança que limita "
            "o pior caso, e faça os jobs em lote invalidarem as chaves ou incrementarem uma "
            "chave de versão.",
            (
                "Nada: o banco avisa o cache automaticamente quando uma linha muda.",
                "Só a primeira leitura após o script fica defasada; as seguintes atualizam a "
                "entrada automaticamente.",
                "A próxima leitura gera um erro, porque o valor em cache não bate mais com a "
                "linha.",
                "Os preços antigos continuam sendo servidos até cada entrada expirar ou ser "
                "removida; mantenha sempre um TTL como rede de segurança e faça os jobs em lote "
                "também invalidarem.",
            ),
        ),
    ),
    _q(
        "caching-strategies-q05",
        "caching-strategies",
        CODE,
        EASY,
        ("b",),
        ("cache-aside", "invalidation"),
        _t(
            "What does this program print, and why?\n\n" + _STALE_READ_CODE,
            "The first read misses, loads 10 from the database and stores it in the cache. "
            "`write_price(20)` updates only the database; nothing removes or refreshes the "
            "cached entry, so the second read is a cache hit that returns the stale 10. "
            "A cache-aside write path must also invalidate the key (and a TTL would bound the "
            "staleness).",
            (
                "`10` then `20`: the second read goes to the database.",
                "`10` then `10`: the write never invalidated the cached entry.",
                "`10` then a `KeyError`, because the write removed the key.",
                "`20` then `20`: the write updates the cache as well.",
            ),
        ),
        _t(
            "O que este programa imprime, e por quê?\n\n" + _STALE_READ_CODE,
            "A primeira leitura dá miss, carrega 10 do banco e guarda no cache. "
            "`write_price(20)` atualiza apenas o banco; nada remove nem atualiza a entrada em "
            "cache, então a segunda leitura é um hit e devolve o 10 defasado. O caminho de "
            "escrita de um cache-aside também precisa invalidar a chave (e um TTL limitaria a "
            "defasagem).",
            (
                "`10` e depois `20`: a segunda leitura vai ao banco.",
                "`10` e depois `10`: a escrita nunca invalidou a entrada em cache.",
                "`10` e depois um `KeyError`, porque a escrita removeu a chave.",
                "`20` e depois `20`: a escrita atualiza o cache também.",
            ),
        ),
    ),
    _q(
        "caching-strategies-q06",
        "caching-strategies",
        MC,
        MEDIUM,
        ("c",),
        ("stampede", "locking"),
        _t(
            "A hot key serving 1,200 requests per second expires. For a moment every request "
            "misses and runs the same expensive query, overloading the database. Which "
            "technique collapses these concurrent misses into a single recomputation?",
            "A short-lived lock taken with SET-if-not-exists lets exactly one request "
            "recompute while the others wait briefly or serve a stale copy. Jitter (A) "
            "desynchronizes the expiry of *many* keys but does nothing for one hot key. A "
            "bigger pool (B) just lets more identical queries hit the database, and a shorter "
            "TTL (D) makes the expiry events more frequent.",
            (
                "Add random jitter to the TTL of every key.",
                "Increase the database connection pool so it can run all 1,200 queries.",
                "Take a short-lived SET-if-not-exists lock so one request recomputes while the "
                "others wait or serve stale data.",
                "Lower the TTL so the key is refreshed more often.",
            ),
        ),
        _t(
            "Uma chave quente que recebe 1.200 requisições por segundo expira. Por um instante "
            "todas as requisições dão miss e executam a mesma consulta cara, sobrecarregando o "
            "banco. Qual técnica reduz esses misses concorrentes a uma única recomputação?",
            "Um lock de curta duração obtido com SET-if-not-exists deixa exatamente uma "
            "requisição recomputar enquanto as outras esperam um pouco ou servem uma cópia "
            "defasada. O jitter (A) dessincroniza a expiração de *muitas* chaves, mas não ajuda "
            "com uma única chave quente. Um pool maior (B) só deixa mais consultas idênticas "
            "chegarem ao banco, e um TTL menor (D) torna as expirações mais frequentes.",
            (
                "Adicionar jitter aleatório ao TTL de todas as chaves.",
                "Aumentar o pool de conexões do banco para que ele execute as 1.200 consultas.",
                "Obter um lock de curta duração com SET-if-not-exists para que uma requisição "
                "recompute enquanto as outras esperam ou servem dados defasados.",
                "Reduzir o TTL para que a chave seja atualizada com mais frequência.",
            ),
        ),
    ),
    _q(
        "caching-strategies-q07",
        "caching-strategies",
        MS,
        MEDIUM,
        ("b", "c", "e"),
        ("stampede", "ttl", "mitigations"),
        _t(
            "Which techniques reduce the risk of a cache stampede? Select all that apply.",
            "Locking or single-flight recomputation collapses concurrent misses, probabilistic "
            "early recomputation refreshes hot keys before they expire, and jittered TTLs stop "
            "bulk-loaded keys from expiring together. Giving a warm-up job's keys exactly the "
            "same TTL creates a synchronized expiry, and a 1-second TTL for everything makes "
            "misses constant and defeats the cache.",
            (
                "Give all keys filled by a warm-up job exactly the same TTL so they stay in sync.",
                "Let only one request recompute a missing hot key (SET-if-not-exists lock or "
                "request coalescing).",
                "Probabilistically recompute a hot key shortly before it expires.",
                "Set a 1-second TTL on every key so entries are always fresh.",
                "Add random jitter to the TTLs of keys that are loaded in bulk.",
            ),
        ),
        _t(
            "Quais técnicas reduzem o risco de um cache stampede? Selecione todas que se aplicam.",
            "Lock ou recomputação single-flight reduz os misses concorrentes, a recomputação "
            "antecipada probabilística atualiza chaves quentes antes de expirarem, e TTLs com "
            "jitter impedem que chaves carregadas em lote expirem juntas. Dar às chaves de um "
            "job de aquecimento exatamente o mesmo TTL cria uma expiração sincronizada, e um "
            "TTL de 1 segundo para tudo torna os misses constantes e anula o cache.",
            (
                "Dar a todas as chaves preenchidas por um job de aquecimento exatamente o mesmo "
                "TTL, para que fiquem sincronizadas.",
                "Deixar apenas uma requisição recomputar uma chave quente ausente (lock com "
                "SET-if-not-exists ou coalescência de requisições).",
                "Recomputar probabilisticamente uma chave quente pouco antes de ela expirar.",
                "Definir TTL de 1 segundo em toda chave para que as entradas estejam sempre "
                "frescas.",
                "Adicionar jitter aleatório aos TTLs de chaves carregadas em lote.",
            ),
        ),
    ),
    _q(
        "caching-strategies-q08",
        "caching-strategies",
        MC,
        MEDIUM,
        ("a",),
        ("versioned-keys", "invalidation"),
        _t(
            "When are versioned cache keys (for example `config:v7:...`, moving to `v8` when "
            "something changes) most useful?",
            "Bumping one version value makes every entry of the old version unreachable at once, "
            "so you invalidate a whole family of related keys without enumerating them. The old "
            "entries are not deleted; they age out through TTL or eviction, so a TTL is still "
            "needed (B). Each access also pays one extra read to resolve the current version "
            "(C), and the approach replaces values rather than updating them in place (D).",
            (
                "When many related entries must be invalidated at once and enumerating every "
                "key would be error-prone.",
                "When you want to drop TTLs entirely, since old versions disappear on their own.",
                "When you need the cheapest possible read path, with no extra cache lookups.",
                "When cached values must be modified in place instead of being replaced.",
            ),
        ),
        _t(
            "Quando chaves de cache versionadas (por exemplo `config:v7:...`, passando para "
            "`v8` quando algo muda) são mais úteis?",
            "Incrementar um único valor de versão torna inalcançáveis, de uma só vez, todas as "
            "entradas da versão antiga, então você invalida uma família inteira de chaves "
            "relacionadas sem enumerá-las. As entradas antigas não são apagadas; elas saem por "
            "TTL ou por eviction, então o TTL continua necessário (B). Cada acesso também paga "
            "uma leitura extra para resolver a versão atual (C), e a abordagem substitui valores "
            "em vez de atualizá-los no lugar (D).",
            (
                "Quando muitas entradas relacionadas precisam ser invalidadas de uma vez e "
                "enumerar cada chave seria propenso a erros.",
                "Quando se quer abandonar os TTLs, já que as versões antigas somem sozinhas.",
                "Quando se precisa do caminho de leitura mais barato possível, sem consultas "
                "extras ao cache.",
                "Quando os valores em cache precisam ser modificados no lugar em vez de "
                "substituídos.",
            ),
        ),
    ),
    _q(
        "caching-strategies-q09",
        "caching-strategies",
        MC,
        HARD,
        ("d",),
        ("cache-aside", "race-conditions"),
        _t(
            "In cache-aside, most implementations update the database first and then delete the "
            "cache key, instead of deleting the key first. Why?",
            "If the delete comes first, a concurrent reader can miss, read the old row and "
            "repopulate the cache with the old value just before the write commits, leaving "
            "stale data until the TTL. Deleting after the commit shrinks that window (a small "
            "race still exists, which is why a TTL stays as a backstop). Delete speed (A) and "
            "blocking (B) are not the issue, and an empty cache after a rolled-back write (C) "
            "is harmless: the next read simply reloads it.",
            (
                "Deleting from the cache is slower than writing to the database, so it "
                "belongs last.",
                "A delete issued before the commit blocks all readers until the commit finishes.",
                "If the write is rolled back after the delete, the cache stays permanently empty.",
                "A concurrent reader could repopulate the cache with the old value between the "
                "delete and the commit, leaving stale data until the TTL.",
            ),
        ),
        _t(
            "No cache-aside, a maioria das implementações atualiza primeiro o banco e depois "
            "apaga a chave do cache, em vez de apagar a chave primeiro. Por quê?",
            "Se o delete vier primeiro, um leitor concorrente pode dar miss, ler a linha antiga "
            "e repopular o cache com o valor antigo pouco antes de a escrita ser confirmada "
            "(commit), deixando dados defasados até o TTL. Apagar depois do commit reduz essa "
            "janela (ainda resta uma pequena race, por isso o TTL continua como rede de "
            "segurança). A velocidade do delete (A) e o bloqueio (B) não são o problema, e um "
            "cache vazio após uma escrita revertida (C) é inofensivo: a próxima leitura o "
            "recarrega.",
            (
                "Apagar do cache é mais lento do que gravar no banco, então deve vir por último.",
                "Um delete emitido antes do commit bloqueia todos os leitores até o commit "
                "terminar.",
                "Se a escrita for revertida depois do delete, o cache fica vazio para sempre.",
                "Um leitor concorrente poderia repopular o cache com o valor antigo entre o "
                "delete e o commit, deixando dados defasados até o TTL.",
            ),
        ),
    ),
    _q(
        "caching-strategies-q10",
        "caching-strategies",
        SHORT,
        HARD,
        None,
        ("design", "invalidation", "stampede"),
        _t(
            "Design the caching layer for a product-catalog service that is read-heavy and "
            "edited by an admin back office. What do you cache, which TTL and invalidation do "
            "you use, and how do you protect against a stampede on a hot product?",
            "Self-check: did you mention (1) cache-aside for product reads, (2) a TTL sized to "
            "how bad stale data is, (3) invalidation on the write path as well as the TTL, and "
            "(4) a stampede defense such as a lock, jitter or early recomputation?",
            model_answer="Use cache-aside for product reads: check the cache, on a miss load "
            "from the database, populate with a TTL and return. Pick the TTL from how costly "
            "staleness is; for descriptions a few minutes is fine, for prices a short TTL (tens "
            "of seconds). Invalidate on the write path by deleting the key after the database "
            "commit, and keep the TTL as a backstop for writes that bypass the application. Use "
            "versioned keys for bulk changes such as a price-list update. Against a stampede on "
            "a hot product, let only one request recompute a missing key (SET-if-not-exists "
            "lock) while others wait or serve stale data, add jitter to TTLs of bulk-loaded "
            "keys, and optionally refresh the hottest keys early.",
        ),
        _t(
            "Projete a camada de cache de um serviço de catálogo de produtos, com muita leitura "
            "e editado por um back office administrativo. O que você coloca em cache, qual TTL "
            "e qual invalidação usa, e como protege contra um stampede em um produto quente?",
            "Autoavaliação: você mencionou (1) cache-aside para as leituras de produto, (2) um "
            "TTL dimensionado conforme o custo de dados defasados, (3) invalidação no caminho de "
            "escrita além do TTL e (4) uma defesa contra stampede, como lock, jitter ou "
            "recomputação antecipada?",
            model_answer="Usar cache-aside nas leituras de produto: consultar o cache, em caso "
            "de miss carregar do banco, popular com um TTL e retornar. Escolher o TTL pelo custo "
            "da defasagem; para descrições alguns minutos bastam, para preços um TTL curto "
            "(dezenas de segundos). Invalidar no caminho de escrita apagando a chave após o "
            "commit no banco, e manter o TTL como rede de segurança para escritas que "
            "contornam a aplicação. Usar chaves versionadas para mudanças em lote, como uma "
            "atualização de tabela de preços. Contra o stampede em um produto quente, deixar "
            "apenas uma requisição recomputar a chave ausente (lock com SET-if-not-exists) "
            "enquanto as outras esperam ou servem dados defasados, adicionar jitter aos TTLs de "
            "chaves carregadas em lote e, opcionalmente, atualizar antecipadamente as chaves "
            "mais quentes.",
        ),
    ),
)
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
    AssessmentSeed(
        code="system-design-caching-strategies-quiz",
        title="Caching Strategies Quiz",
        description="Cache-aside, write-through and write-behind, invalidation, TTLs and "
        "stampedes.",
        kind=AssessmentKind.COMPETENCY,
        competency_slug="caching-strategies",
        translations={
            "pt-BR": {
                "title": "Quiz de Estratégias de Cache",
                "description": "Cache-aside, write-through e write-behind, invalidação, TTLs e "
                "stampedes.",
            }
        },
    ),
)


QUESTION_SET = SubjectQuestionSet(
    subject_slug="system-design",
    questions=QUESTIONS,
    assessments=ASSESSMENTS,
)
