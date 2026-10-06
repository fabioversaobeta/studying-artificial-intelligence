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
# ----------------------------------------------------------------------
# load-balancing
# ----------------------------------------------------------------------
_REMAP_CODE = """```python
keys = range(1000)
before = {k: k % 4 for k in keys}   # 4 cache servers
after = {k: k % 5 for k in keys}    # a 5th server is added
moved = sum(1 for k in keys if before[k] != after[k])
print(moved)
```"""

_LB: tuple[QuestionSeed, ...] = (
    _q(
        "load-balancing-q01",
        "load-balancing",
        MC,
        EASY,
        ("d",),
        ("l4-vs-l7", "routing"),
        _t(
            "You want `/api/v1/*` to go to one pool of servers and `/api/v2/*` to another, and "
            "you also want TLS terminated at the balancer. Which option does this?",
            "Routing by URL path needs something that parses the HTTP request, which is what a "
            "layer 7 balancer does (and it can terminate TLS). A layer 4 balancer only sees "
            "IP addresses and ports, whatever algorithm it uses, and DNS round robin just "
            "hands out different addresses without ever looking at the request path.",
            (
                "An L4 (TCP) balancer, because it is faster and sees every packet.",
                "An L4 balancer configured with consistent hashing.",
                "DNS round robin with one record per pool.",
                "An L7 (HTTP) balancer, which parses requests and can route on path, host or "
                "headers.",
            ),
        ),
        _t(
            "Você quer que `/api/v1/*` vá para um pool de servidores e `/api/v2/*` para outro, "
            "e também quer o TLS terminado no balanceador. Qual opção faz isso?",
            "Rotear por caminho de URL exige algo que interprete a requisição HTTP, que é o que "
            "um balanceador de camada 7 faz (e ele pode terminar o TLS). Um balanceador de "
            "camada 4 enxerga apenas endereços IP e portas, qualquer que seja o algoritmo, e o "
            "DNS round robin só entrega endereços diferentes sem nunca olhar o caminho da "
            "requisição.",
            (
                "Um balanceador L4 (TCP), porque é mais rápido e vê todos os pacotes.",
                "Um balanceador L4 configurado com consistent hashing.",
                "DNS round robin com um registro por pool.",
                "Um balanceador L7 (HTTP), que interpreta requisições e pode rotear por "
                "caminho, host ou headers.",
            ),
        ),
    ),
    _q(
        "load-balancing-q02",
        "load-balancing",
        MC,
        EASY,
        ("a",),
        ("round-robin", "algorithms"),
        _t(
            "A pool of identical servers handles requests whose cost ranges from 5 ms to 10 s. "
            "What is the main weakness of plain round robin here?",
            "Round robin is fair by request count, not by cost. A server that is stuck on "
            "slow requests keeps receiving new work at the same rate as the others and falls "
            "behind. Least connections corrects this by steering new requests toward servers "
            "with fewer in-flight ones. The other options describe behaviors round robin does "
            "not have.",
            (
                "It spreads requests evenly by count, so a server stuck on slow requests keeps "
                "receiving new work at the same rate.",
                "It sends all traffic to the first server until that server fails.",
                "It requires the balancer to parse the HTTP request body.",
                "It cannot be used with more than two servers.",
            ),
        ),
        _t(
            "Um pool de servidores idênticos atende requisições cujo custo vai de 5 ms a 10 s. "
            "Qual é a principal fraqueza do round robin simples nesse cenário?",
            "O round robin é justo por quantidade de requisições, não por custo. Um servidor "
            "preso em requisições lentas continua recebendo trabalho novo no mesmo ritmo dos "
            "outros e fica para trás. O least connections corrige isso direcionando novas "
            "requisições a servidores com menos requisições em andamento. As demais opções "
            "descrevem comportamentos que o round robin não tem.",
            (
                "Ele distribui as requisições igualmente por quantidade, então um servidor "
                "preso em requisições lentas continua recebendo trabalho novo no mesmo ritmo.",
                "Ele envia todo o tráfego ao primeiro servidor até que este falhe.",
                "Ele exige que o balanceador interprete o corpo da requisição HTTP.",
                "Ele não pode ser usado com mais de dois servidores.",
            ),
        ),
    ),
    _q(
        "load-balancing-q03",
        "load-balancing",
        MC,
        EASY,
        ("b",),
        ("health-checks", "readiness"),
        _t(
            "An instance's database connection pool is exhausted, but the process is running "
            "and its liveness endpoint still returns 200. What is the right behavior?",
            "Failing the readiness check makes the load balancer stop sending new requests "
            "while the process stays alive; it may recover in seconds, for example once "
            "connections free up. Failing liveness (A) would get the process restarted, "
            "which is destructive overkill for a temporary condition. Option C is the bug that "
            "an unconditional health check causes, and removing the instance forever (D) "
            "throws away capacity that will come back.",
            (
                "Fail the liveness check so the orchestrator restarts the process immediately.",
                "Fail the readiness check so the balancer stops routing new requests, without "
                "killing the process.",
                "Keep routing traffic, since the process is technically up.",
                "Remove the instance from the pool permanently.",
            ),
        ),
        _t(
            "O pool de conexões com o banco de uma instância está esgotado, mas o processo está "
            "rodando e o endpoint de liveness ainda retorna 200. Qual é o comportamento certo?",
            "Falhar o readiness check faz o balanceador parar de enviar novas requisições "
            "enquanto o processo continua vivo; ele pode se recuperar em segundos, por exemplo "
            "quando conexões forem liberadas. Falhar o liveness (A) faria o processo ser "
            "reiniciado, um exagero destrutivo para uma condição temporária. A opção C é o bug "
            "que um health check incondicional causa, e remover a instância para sempre (D) "
            "joga fora capacidade que voltaria.",
            (
                "Falhar o liveness check para que o orquestrador reinicie o processo "
                "imediatamente.",
                "Falhar o readiness check para que o balanceador pare de rotear novas "
                "requisições, sem matar o processo.",
                "Continuar roteando tráfego, já que o processo tecnicamente está no ar.",
                "Remover a instância do pool permanentemente.",
            ),
        ),
    ),
    _q(
        "load-balancing-q04",
        "load-balancing",
        MC,
        MEDIUM,
        ("c",),
        ("least-connections", "algorithms"),
        _t(
            "A stateless HTTP API serves requests that take anywhere from 10 ms to several "
            "seconds. Which balancing algorithm is generally the better default?",
            "Least connections sends each new request to the backend with the fewest in-flight "
            "ones, so a backend bogged down by slow requests naturally stops receiving new work "
            "until it catches up, without the balancer knowing why it is slow. Plain round "
            "robin ignores cost, hashing by client IP pins clients to servers (useful only "
            "for per-client state) and can skew load, and active/passive wastes the standby.",
            (
                "Plain round robin.",
                "Hashing on the client IP address.",
                "Least connections.",
                "Always the first backend, failing over to the next only when it is down.",
            ),
        ),
        _t(
            "Uma API HTTP stateless atende requisições que levam de 10 ms a vários segundos. "
            "Qual algoritmo de balanceamento costuma ser o melhor padrão?",
            "O least connections envia cada nova requisição ao backend com menos requisições em "
            "andamento, então um backend atolado em requisições lentas naturalmente para de "
            "receber trabalho novo até se recuperar, sem que o balanceador saiba por que ele "
            "está lento. O round robin simples ignora o custo, o hash por IP do cliente fixa "
            "clientes em servidores (útil só para estado por cliente) e pode desbalancear a "
            "carga, e o ativo/passivo desperdiça o servidor reserva.",
            (
                "Round robin simples.",
                "Hash do endereço IP do cliente.",
                "Least connections.",
                "Sempre o primeiro backend, passando ao próximo só se ele cair.",
            ),
        ),
    ),
    _q(
        "load-balancing-q05",
        "load-balancing",
        CODE,
        MEDIUM,
        ("c",),
        ("consistent-hashing", "modulo-hashing"),
        _t(
            "A team routes cache keys with `key % number_of_servers` and adds a fifth server. "
            "Roughly what does this program print?\n\n" + _REMAP_CODE,
            "A key stays on the same server only when `k % 4 == k % 5`, which holds for just "
            "4 of every 20 consecutive keys, so about 200 of 1,000 stay and 800 move. Plain "
            "modulo hashing reshuffles most keys whenever the server count changes, wiping "
            "out most of the cache. Consistent hashing would move only about 1/5 of them, "
            "around 200.",
            (
                "About 200.",
                "About 500.",
                "About 800.",
                "Exactly 1000.",
            ),
        ),
        _t(
            "Uma equipe roteia chaves de cache com `chave % numero_de_servidores` e adiciona um "
            "quinto servidor. Aproximadamente o que este programa imprime?\n\n" + _REMAP_CODE,
            "Uma chave só continua no mesmo servidor quando `k % 4 == k % 5`, o que vale para "
            "apenas 4 de cada 20 chaves consecutivas, então cerca de 200 de 1.000 ficam e 800 "
            "mudam. O hash por módulo simples embaralha a maioria das chaves sempre que o "
            "número de servidores muda, destruindo grande parte do cache. O consistent hashing "
            "moveria só cerca de 1/5 delas, aproximadamente 200.",
            (
                "Cerca de 200.",
                "Cerca de 500.",
                "Cerca de 800.",
                "Exatamente 1000.",
            ),
        ),
    ),
    _q(
        "load-balancing-q06",
        "load-balancing",
        MC,
        MEDIUM,
        ("a",),
        ("stateless", "sessions", "sticky-sessions"),
        _t(
            "A service keeps user sessions in each instance's memory. After autoscaling from 3 "
            "to 6 instances, users are logged out at random. What is the best long-term fix?",
            "Moving the sessions to a shared external store (such as Redis) makes the "
            "instances stateless, so any of them can serve any client and scaling in or out "
            "is safe. Sticky sessions (B) are a stopgap: if the pinned instance dies the "
            "session dies with it, and load gets uneven. A longer cookie lifetime (C) does "
            "not change where the session data lives, and scaling back (D) gives up the "
            "capacity you needed.",
            (
                "Move the session data to a shared store such as Redis, so any instance can "
                "serve any user.",
                "Enable sticky sessions and keep them permanently.",
                "Increase the session cookie's lifetime.",
                "Scale back down to 3 instances.",
            ),
        ),
        _t(
            "Um serviço guarda as sessões dos usuários na memória de cada instância. Depois de "
            "escalar de 3 para 6 instâncias, usuários são deslogados aleatoriamente. Qual é a "
            "melhor correção de longo prazo?",
            "Mover as sessões para um armazenamento externo compartilhado (como o Redis) deixa "
            "as instâncias stateless, então qualquer uma atende qualquer cliente e aumentar ou "
            "reduzir o número de instâncias é seguro. Sticky sessions (B) são um paliativo: se a "
            "instância fixada cair, a sessão cai junto, e a carga fica desigual. Um cookie com "
            "vida mais longa (C) não muda onde os dados da sessão ficam, e voltar para 3 (D) "
            "abre mão da capacidade de que você precisava.",
            (
                "Mover os dados de sessão para um armazenamento compartilhado, como o Redis, "
                "para que qualquer instância atenda qualquer usuário.",
                "Ativar sticky sessions e mantê-las permanentemente.",
                "Aumentar o tempo de vida do cookie de sessão.",
                "Voltar a 3 instâncias.",
            ),
        ),
    ),
    _q(
        "load-balancing-q07",
        "load-balancing",
        MS,
        MEDIUM,
        ("b", "d", "e"),
        ("autoscaling", "metrics"),
        _t(
            "Which are sound autoscaling practices? Select all that apply.",
            "In-flight requests per instance reflect real saturation even for I/O-bound "
            "services, a sustained-window condition with cooldown prevents flapping, and "
            "queue length is the most direct signal for a queue-consumer worker pool. CPU "
            "alone is misleading for an I/O-bound service that waits on slow downstreams, and "
            "scaling in as aggressively as scaling out removes capacity right before the next "
            "spike.",
            (
                "Use CPU utilization as the only signal, even for a service that mostly waits "
                "on I/O.",
                "Scale on in-flight requests per instance.",
                "Scale in as quickly and aggressively as you scale out.",
                "Require a metric to stay above its threshold for a sustained window, with a "
                "cooldown after scaling.",
                "Scale a queue-consumer worker pool on the length of the queue it consumes.",
            ),
        ),
        _t(
            "Quais são boas práticas de autoscaling? Selecione todas que se aplicam.",
            "Requisições em andamento por instância refletem a saturação real mesmo em serviços "
            "limitados por I/O, uma condição sustentada por uma janela, com cooldown, evita o "
            "flapping, e o tamanho da fila é o sinal mais direto para um pool de workers que "
            "consome uma fila. Só a CPU engana em um serviço limitado por I/O que espera "
            "dependências lentas, e reduzir tão agressivamente quanto aumenta tira capacidade "
            "logo antes do próximo pico.",
            (
                "Usar a utilização de CPU como único sinal, mesmo em um serviço que passa a maior "
                "parte do tempo esperando I/O.",
                "Escalar com base nas requisições em andamento por instância.",
                "Reduzir instâncias tão rápida e agressivamente quanto se aumenta.",
                "Exigir que a métrica fique acima do limite por uma janela sustentada, com um "
                "cooldown após escalar.",
                "Escalar um pool de workers consumidores de fila pelo tamanho da fila que "
                "consomem.",
            ),
        ),
    ),
    _q(
        "load-balancing-q08",
        "load-balancing",
        MC,
        MEDIUM,
        ("b",),
        ("graceful-shutdown", "deployments"),
        _t(
            "Every deploy causes a burst of failed requests as old instances are stopped. Which "
            "shutdown sequence avoids this?",
            "The instance should first fail its readiness check so the balancer stops sending "
            "new requests, keep running until the in-flight requests finish (draining), and "
            "only then terminate. Killing it immediately (A) or waiting for health checks to "
            "notice a dead instance (C) guarantees that some requests hit a dead backend, and "
            "a longer idle timeout (D) does not stop new requests from arriving.",
            (
                "Kill the instance immediately and rely on clients to retry.",
                "Fail readiness so no new requests arrive, let in-flight requests finish, then "
                "terminate.",
                "Stop the process and wait for the health checks to notice it is gone.",
                "Raise the balancer's idle timeout.",
            ),
        ),
        _t(
            "Todo deploy causa uma rajada de requisições com falha quando as instâncias antigas "
            "são paradas. Qual sequência de desligamento evita isso?",
            "A instância deve primeiro falhar o readiness check para que o balanceador pare de "
            "enviar novas requisições, continuar rodando até as requisições em andamento "
            "terminarem (draining) e só então encerrar. Matá-la de imediato (A) ou esperar os "
            "health checks perceberem uma instância morta (C) garante que algumas requisições "
            "cheguem a um backend morto, e um idle timeout maior (D) não impede a chegada de "
            "novas requisições.",
            (
                "Matar a instância imediatamente e contar com novas tentativas dos clientes.",
                "Falhar o readiness para não chegarem novas requisições, deixar as em andamento "
                "terminarem e então encerrar.",
                "Parar o processo e esperar os health checks perceberem que ele sumiu.",
                "Aumentar o idle timeout do balanceador.",
            ),
        ),
    ),
    _q(
        "load-balancing-q09",
        "load-balancing",
        MC,
        HARD,
        ("d",),
        ("bottlenecks", "connection-pooling", "estimation"),
        _t(
            "A service runs on 3 stateless instances and handles 500 requests/s. Each instance "
            "keeps a pool of 10 connections to a PostgreSQL server with `max_connections = 100`. "
            "Traffic is about to grow 10x and autoscaling will run roughly 30 instances with "
            "the same pool settings. What is most likely to break first, and what is the "
            "appropriate response?",
            "30 instances x 10 connections = 300 potential connections against a hard limit of "
            "100, so the database connection ceiling is hit long before CPU on the stateless "
            "app tier or the balancer. Cap and shrink the per-instance pools and put an external "
            "pooler (PgBouncer-style, transaction mode) in front of the database, and relieve "
            "read load with caching or replicas. Scaling stateless servers is the easy part, "
            "and a balancer node is rarely the first limit.",
            (
                "The balancer's CPU; add a second balancer in front of it.",
                "The app servers' CPU; move to larger instance types.",
                "DNS resolution of the instances; raise the DNS TTL.",
                "The database connection limit (about 300 potential connections against 100); "
                "cap the pools and add an external pooler, plus caching or replicas for read "
                "load.",
            ),
        ),
        _t(
            "Um serviço roda em 3 instâncias stateless e atende 500 requisições/s. Cada "
            "instância mantém um pool de 10 conexões com um servidor PostgreSQL com "
            "`max_connections = 100`. O tráfego vai crescer 10x e o autoscaling vai rodar cerca "
            "de 30 instâncias com a mesma configuração de pool. O que tem mais chance de "
            "quebrar primeiro e qual é a resposta adequada?",
            "30 instâncias x 10 conexões = 300 conexões potenciais contra um limite rígido de "
            "100, então o teto de conexões do banco é atingido muito antes da CPU da camada de "
            "aplicação stateless ou do balanceador. Limite e reduza os pools por instância e "
            "coloque um pooler externo (estilo PgBouncer, em modo transaction) na frente do "
            "banco, aliviando a leitura com cache ou réplicas. Escalar servidores stateless é "
            "a parte fácil, e um nó de balanceador raramente é o primeiro limite.",
            (
                "A CPU do balanceador; adicionar um segundo balanceador na frente.",
                "A CPU dos servidores de aplicação; migrar para instâncias maiores.",
                "A resolução DNS das instâncias; aumentar o TTL do DNS.",
                "O limite de conexões do banco (cerca de 300 conexões potenciais contra 100); "
                "limitar os pools e adicionar um pooler externo, além de cache ou réplicas para "
                "a carga de leitura.",
            ),
        ),
    ),
    _q(
        "load-balancing-q10",
        "load-balancing",
        SHORT,
        HARD,
        None,
        ("consistent-hashing", "scaling"),
        _t(
            "Explain how consistent hashing works and why it is preferable to "
            "`hash(key) % N` when routing requests to cache servers that scale out and in.",
            "Self-check: did you mention (1) the hash ring with servers and keys, (2) a key "
            "going to the next server clockwise, (3) only about 1/N of the keys moving when a "
            "server is added or removed, versus most of them with modulo, and (4) virtual "
            "nodes to even out the load?",
            model_answer="Servers and keys are hashed onto the same fixed ring, and a key is "
            "served by the first server found going clockwise from the key's position. When a "
            "server is added or removed, only the keys on its arc move to a neighbor, roughly "
            "1/N of all keys, so most cache entries stay valid. With `hash(key) % N`, changing "
            "N changes the target of most keys, effectively flushing the whole cache at every "
            "scaling event. In practice each server is placed on the ring many times (virtual "
            "nodes) so that load spreads evenly and a removed server's keys are shared among "
            "several neighbors.",
        ),
        _t(
            "Explique como funciona o consistent hashing e por que ele é preferível a "
            "`hash(chave) % N` ao rotear requisições para servidores de cache que escalam para "
            "mais e para menos.",
            "Autoavaliação: você mencionou (1) o anel de hash com servidores e chaves, (2) a "
            "chave indo para o próximo servidor no sentido horário, (3) apenas cerca de 1/N das "
            "chaves mudando quando um servidor entra ou sai, contra a maioria delas com módulo, "
            "e (4) nós virtuais para equilibrar a carga?",
            model_answer="Servidores e chaves são mapeados por hash no mesmo anel fixo, e uma "
            "chave é atendida pelo primeiro servidor encontrado no sentido horário a partir da "
            "posição da chave. Quando um servidor entra ou sai, apenas as chaves do seu arco "
            "passam para um vizinho, cerca de 1/N de todas as chaves, então a maior parte das "
            "entradas de cache continua válida. Com `hash(chave) % N`, mudar N muda o destino "
            "da maioria das chaves, esvaziando na prática todo o cache a cada evento de "
            "escalonamento. Na prática cada servidor é colocado no anel várias vezes (nós "
            "virtuais) para que a carga se distribua de forma uniforme e as chaves de um "
            "servidor removido sejam divididas entre vários vizinhos.",
        ),
    ),
)
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
    AssessmentSeed(
        code="system-design-load-balancing-quiz",
        title="Load Balancing & Scaling Quiz",
        description="L4 vs L7, balancing algorithms, health checks, autoscaling and the next "
        "bottleneck.",
        kind=AssessmentKind.COMPETENCY,
        competency_slug="load-balancing",
        translations={
            "pt-BR": {
                "title": "Quiz de Balanceamento de Carga e Escalabilidade",
                "description": "L4 vs L7, algoritmos de balanceamento, health checks, "
                "autoscaling e o próximo gargalo.",
            }
        },
    ),
)


QUESTION_SET = SubjectQuestionSet(
    subject_slug="system-design",
    questions=QUESTIONS,
    assessments=ASSESSMENTS,
)
