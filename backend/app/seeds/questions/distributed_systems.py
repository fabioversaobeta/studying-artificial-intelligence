"""Question bank for the Distributed Systems subject: cap-theorem, replication,
partitioning-sharding and consensus-algorithms (10 questions each, English +
Brazilian Portuguese).

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


def _text(
    prompt: str,
    explanation: str,
    *options: str,
    model_answer: str | None = None,
) -> QuestionText:
    """_text(prompt, explanation, "opt a", "opt b", ...) -> options get ids a, b, c..."""
    opts = tuple(OptionSeed(id=chr(ord("a") + i), text=t) for i, t in enumerate(options))
    return QuestionText(
        prompt=prompt,
        explanation=explanation,
        options=opts or None,
        model_answer=model_answer,
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


_STALE_READ_CODE = """```python
class Replica:
    def __init__(self):
        self.data = {}


a, b = Replica(), Replica()
partitioned = True


def write(key, value):
    a.data[key] = value
    if not partitioned:
        b.data[key] = value


def read_from_b(key):
    return b.data.get(key)


write("x", 1)
print(read_from_b("x"))
```"""


_CAP: tuple[QuestionSeed, ...] = (
    _q(
        "cap-theorem-q01",
        "cap-theorem",
        MC,
        EASY,
        ("c",),
        ("cap", "partitions"),
        _text(
            "In a system whose data is spread across several machines connected by a network, "
            "what does the CAP theorem really force you to decide?",
            "Network partitions will eventually happen in any multi-node system, so partition "
            "tolerance is not something you can opt out of. The real decision is what to "
            "sacrifice while a partition lasts: consistency or availability. Option A treats "
            "P as optional, B and D are about other trade-offs entirely (throughput/latency, "
            "storage model).",
            "Which one of consistency, availability and partition tolerance to give up for "
            "good; partition tolerance is the usual one to drop when the network is fast.",
            "Whether to optimize for throughput or for latency during normal operation.",
            "Whether to favor consistency or availability while a network partition is happening.",
            "Whether to store the data in a relational or a non-relational database.",
        ),
        _text(
            "Em um sistema cujos dados estão espalhados por várias máquinas conectadas por uma "
            "rede, o que o teorema CAP realmente obriga você a decidir?",
            "Partições de rede vão acabar acontecendo em qualquer sistema com vários nós, então "
            "tolerância a partições não é algo de que se possa abrir mão. A decisão real é o "
            "que sacrificar enquanto a partição dura: consistência ou disponibilidade. A opção "
            "A trata o P como opcional; B e D são sobre outros trade-offs (vazão/latência, "
            "modelo de armazenamento).",
            "Qual das três propriedades (consistência, disponibilidade, tolerância a "
            "partições) abandonar de vez; a tolerância a partições costuma ser a dispensada "
            "quando a rede é rápida.",
            "Se otimizar vazão ou latência durante a operação normal.",
            "Se favorecer consistência ou disponibilidade enquanto uma partição de rede está "
            "ocorrendo.",
            "Se armazenar os dados em um banco relacional ou não relacional.",
        ),
    ),
    _q(
        "cap-theorem-q02",
        "cap-theorem",
        MC,
        EASY,
        ("d",),
        ("cap", "availability"),
        _text(
            "In the formal statement of the CAP theorem, what does **availability** mean?",
            "CAP availability is a per-request guarantee: every request sent to a node that "
            "has not failed must get a non-error response. The answer may be stale. It is not "
            "an uptime percentage (A), it does not promise the latest write (B; that is "
            "consistency), and the theorem sets no latency bound (C).",
            "The service is up a very high percentage of the time, for example 99.99% over a "
            "month.",
            "Every request returns the result of the most recent completed write, as if there "
            "were a single copy of the data.",
            "Every request is answered within the latency target in the service's SLO, for "
            "example 200 ms.",
            "Every request to a non-failing node gets a non-error response, even if it is not "
            "the latest write.",
        ),
        _text(
            "Na formulação formal do teorema CAP, o que significa **disponibilidade** "
            "(availability)?",
            "A disponibilidade do CAP é uma garantia por requisição: toda requisição enviada a "
            "um nó que não falhou deve receber uma resposta sem erro. A resposta pode estar "
            "desatualizada. Não é um percentual de uptime (A), não promete a última escrita "
            "(B; isso é consistência) e o teorema não define limite de latência (C).",
            "O serviço fica no ar uma porcentagem altíssima do tempo, por exemplo 99,99% ao "
            "longo de um mês.",
            "Toda requisição retorna o resultado da última escrita concluída, como se "
            "houvesse uma única cópia dos dados.",
            "Toda requisição é respondida dentro da meta de latência do SLO do serviço, por "
            "exemplo 200 ms.",
            "Toda requisição a um nó que não falhou recebe uma resposta sem erro, mesmo que "
            "não seja a da última escrita.",
        ),
    ),
    _q(
        "cap-theorem-q03",
        "cap-theorem",
        MC,
        EASY,
        ("a",),
        ("cap", "cp-vs-ap"),
        _text(
            "A bank ledger is deployed across three data centers and a network partition "
            "isolates one of them. Which behavior of the isolated data center is "
            "characteristic of a **CP** design?",
            "A CP system protects correctness: a node that cannot confirm its data is current "
            "(for example, it cannot reach a majority) refuses or times out requests. B and C "
            "keep answering and so are AP behaviors, and D accepts writes it cannot "
            "coordinate, so it risks the very divergence a ledger must avoid.",
            "It rejects or times out requests it cannot guarantee are consistent until the "
            "partition heals.",
            "It keeps accepting writes locally and merges them with the other data centers "
            "once the partition heals.",
            "It keeps answering reads from its local, possibly stale, copy of the data until "
            "the partition heals.",
            "It acknowledges writes immediately and replicates them whenever the network "
            "returns to normal.",
        ),
        _text(
            "Um livro-razão bancário está implantado em três data centers e uma partição de "
            "rede isola um deles. Qual comportamento do data center isolado é característico "
            "de um projeto **CP**?",
            "Um sistema CP protege a correção: um nó que não consegue confirmar que seus dados "
            "estão atualizados (por exemplo, não alcança a maioria) recusa as requisições ou "
            "deixa que expirem. B e C continuam respondendo, portanto são comportamentos AP, e "
            "D aceita escritas que não consegue coordenar, correndo o risco da divergência "
            "que um livro-razão precisa evitar.",
            "Rejeita ou deixa expirar as requisições cuja consistência não consegue garantir "
            "até que a partição seja resolvida.",
            "Continua aceitando escritas localmente e as mescla com os outros data centers "
            "quando a partição for resolvida.",
            "Continua respondendo leituras a partir da sua cópia local, possivelmente "
            "desatualizada, até a partição ser resolvida.",
            "Confirma as escritas imediatamente e as replica quando a rede voltar ao normal.",
        ),
    ),
    _q(
        "cap-theorem-q04",
        "cap-theorem",
        MC,
        MEDIUM,
        ("b",),
        ("cap", "consistency", "linearizability", "acid"),
        _text(
            'Which statement best distinguishes the "C" in CAP from the "C" in ACID?',
            "CAP consistency is essentially linearizability: the system behaves as if there "
            "were a single copy of the data and every read sees the latest completed write. "
            "ACID consistency is about a transaction moving the database from one valid state "
            "to another, preserving application-defined invariants such as constraints. They "
            "are unrelated guarantees, and CAP consistency is not eventual consistency.",
            "They are the same guarantee; CAP just applies the ACID definition to several nodes.",
            "CAP consistency means reads see the latest write, as if there were one copy; ACID "
            "consistency means a transaction preserves the invariants.",
            "CAP consistency means replicas eventually converge to the same value; ACID "
            "consistency means every read sees the latest committed write.",
            "CAP consistency is about durability, meaning writes survive a crash on disk; ACID "
            "consistency is about isolation between concurrent transactions.",
        ),
        _text(
            'Qual afirmação distingue melhor o "C" do CAP do "C" do ACID?',
            "A consistência do CAP é essencialmente linearizabilidade: o sistema se comporta "
            "como se houvesse uma única cópia dos dados e toda leitura enxerga a última escrita "
            "concluída. A consistência do ACID diz respeito a uma transação levar o banco de "
            "um estado válido a outro, preservando invariantes definidas pela aplicação, como "
            "constraints. São garantias sem relação, e a consistência do CAP não é consistência "
            "eventual.",
            "São a mesma garantia; o CAP apenas aplica a definição do ACID a vários nós.",
            "No CAP, consistência significa que as leituras veem a última escrita, como se "
            "houvesse uma só cópia; no ACID, que uma transação preserva as invariantes.",
            "No CAP, consistência significa que as réplicas acabam convergindo para o mesmo "
            "valor; no ACID, que toda leitura vê a última escrita confirmada.",
            "No CAP, consistência trata de durabilidade, ou seja, as escritas sobrevivem a "
            "uma queda em disco; no ACID, de isolamento entre transações concorrentes.",
        ),
    ),
    _q(
        "cap-theorem-q05",
        "cap-theorem",
        MS,
        MEDIUM,
        ("a", "c", "d"),
        ("cap", "misconceptions"),
        _text(
            "Which of the following statements about the CAP theorem are **correct**? "
            "Select all that apply.",
            "A, C and D are correct: CAP describes the forced choice during a partition, its "
            '"C" is linearizability (not ACID\'s), and when there is no partition it does not '
            "stop a system from being consistent and available. B is false, since "
            "that is exactly what the theorem rules out during a partition. E is false because "
            "partitions come from network failures, delays and unreachable nodes that no "
            "hardware purchase can eliminate.",
            "During a partition, a system must either answer some requests with possibly stale "
            "data or refuse some requests.",
            "With enough replicas, a system can stay both linearizable and fully available "
            "during a partition.",
            'The "C" in CAP is linearizability, which is a different notion from the "C" in ACID.',
            "When the network is healthy, CAP by itself does not prevent a system from being "
            "both consistent and available.",
            "Partition tolerance can be dropped by buying more reliable network hardware.",
        ),
        _text(
            "Quais das afirmações a seguir sobre o teorema CAP estão **corretas**? "
            "Selecione todas que se aplicam.",
            "A, C e D estão corretas: o CAP descreve a escolha forçada durante uma partição, "
            'seu "C" é linearizabilidade (não a do ACID) e, sem partição, ele não impede que '
            "um sistema seja consistente e disponível. B é falsa, pois é exatamente isso que o "
            "teorema proíbe durante uma partição. E é falsa porque partições vêm de falhas, "
            "atrasos e nós inalcançáveis que nenhuma compra de hardware elimina.",
            "Durante uma partição, o sistema precisa responder a algumas requisições com dados "
            "possivelmente desatualizados ou recusar algumas requisições.",
            "Com réplicas suficientes, um sistema pode continuar linearizável e totalmente "
            "disponível durante uma partição.",
            'O "C" do CAP é linearizabilidade, noção diferente do "C" do ACID.',
            "Quando a rede está saudável, o CAP por si só não impede que um sistema seja "
            "consistente e disponível ao mesmo tempo.",
            "A tolerância a partições pode ser dispensada comprando hardware de rede mais "
            "confiável.",
        ),
    ),
    _q(
        "cap-theorem-q06",
        "cap-theorem",
        MC,
        MEDIUM,
        ("c",),
        ("cap", "dns", "classification"),
        _text(
            "How is DNS best classified under CAP, and why?",
            "DNS leans AP: resolvers and caches keep answering from cached records until their "
            "TTL expires, accepting that a change may take time to propagate. Hierarchical "
            "delegation does not make it CP (A), TTLs bound staleness rather than guarantee "
            'freshness (D), and "CA" would assume the network never partitions, which is not '
            "a property any internet-scale system can have (B).",
            "CP: delegation from the root servers gives every name a single authority, so "
            "answers are always up to date.",
            "CA: DNS runs on a reliable network, so partitions are not a concern.",
            "AP: resolvers keep answering from cached records, accepting temporary staleness.",
            "CP: TTLs guarantee that a record is never older than its expiry time.",
        ),
        _text(
            "Como o DNS é melhor classificado segundo o CAP, e por quê?",
            "O DNS tende a AP: resolvers e caches continuam respondendo com registros em cache "
            "até o TTL expirar, aceitando que uma mudança leve tempo para se propagar. A "
            "delegação hierárquica não o torna CP (A), os TTLs limitam a defasagem em vez de "
            'garantir frescor (D) e "CA" pressuporia uma rede que nunca sofre partições, '
            "propriedade que nenhum sistema em escala de internet tem (B).",
            "CP: a delegação a partir dos root servers dá a cada nome uma autoridade única, "
            "então as respostas estão sempre atualizadas.",
            "CA: o DNS roda em uma rede confiável, então partições não são uma preocupação.",
            "AP: os resolvers continuam respondendo com registros em cache, aceitando "
            "defasagem temporária.",
            "CP: os TTLs garantem que um registro nunca fique mais antigo que seu prazo de "
            "expiração.",
        ),
    ),
    _q(
        "cap-theorem-q07",
        "cap-theorem",
        MC,
        MEDIUM,
        ("a",),
        ("pacelc", "latency"),
        _text(
            'The PACELC formulation adds an "ELC" clause to CAP. What does it describe?',
            "PACELC reads: if there is a Partition, choose Availability or Consistency; Else "
            "(no partition), choose Latency or Consistency. Even on a healthy network, "
            "synchronous replication buys stronger consistency at the cost of latency, while "
            "asynchronous replication does the opposite. B reverses the roles of the clauses, "
            "C is not a PACELC trade-off, and D describes CAP's own clause.",
            "The trade-off between latency and consistency when there is no partition, such as "
            "synchronous replication.",
            "The trade-off between latency and consistency that a system faces while a network "
            "partition is in progress.",
            "The trade-off between storage cost and durability, such as how many replicas to "
            "keep, when there is no partition.",
            "The trade-off between availability and consistency when there is no partition, "
            "that is, the choice CAP already describes.",
        ),
        _text(
            'A formulação PACELC acrescenta uma cláusula "ELC" ao CAP. O que ela descreve?',
            "O PACELC diz: se há Partição, escolha Disponibilidade ou Consistência; Senão (sem "
            "partição), escolha Latência ou Consistência. Mesmo em uma rede saudável, a "
            "replicação síncrona compra mais consistência ao custo de latência, e a assíncrona "
            "faz o oposto. B inverte os papéis das cláusulas, C não é um trade-off do PACELC e "
            "D descreve a própria cláusula do CAP.",
            "O trade-off entre latência e consistência quando não há partição, como a "
            "replicação síncrona.",
            "O trade-off entre latência e consistência que o sistema enfrenta enquanto uma "
            "partição de rede está em curso.",
            "O trade-off entre custo de armazenamento e durabilidade, como quantas réplicas "
            "manter, quando não há partição.",
            "O trade-off entre disponibilidade e consistência quando não há partição, ou "
            "seja, a escolha que o CAP já descreve.",
        ),
    ),
    _q(
        "cap-theorem-q08",
        "cap-theorem",
        CODE,
        MEDIUM,
        ("c",),
        ("cap", "stale-reads", "availability"),
        _text(
            "Two replicas are separated by a network partition (`partitioned = True`). "
            "What does this code print, and which CAP choice does `read_from_b` represent?\n\n"
            + _STALE_READ_CODE,
            "The write only reaches replica `a`, because the partition blocks replication, so "
            '`b.data.get("x")` returns `None`. Replica `b` still answers instead of refusing, '
            "which is the availability choice, but its answer is not the latest write, so the "
            "read is not linearizable. Option A is wrong because the write never reached `b`; "
            "B is wrong because `dict.get` does not raise; D calls it CP although it returns "
            "stale data instead of refusing.",
            "It prints `1`, because the write was acknowledged and so every replica already has "
            "it.",
            "It raises a `KeyError`, which is the CP choice of failing instead of answering.",
            "It prints `None`: the replica stays available but returns a stale answer, an "
            "AP-style choice.",
            "It prints `None`: this is a CP-style choice because the function never returns a "
            "wrong value.",
        ),
        _text(
            "Duas réplicas estão separadas por uma partição de rede (`partitioned = True`). "
            "O que este código imprime, e qual escolha do CAP `read_from_b` representa?\n\n"
            + _STALE_READ_CODE,
            "A escrita só chega à réplica `a`, pois a partição bloqueia a replicação, então "
            '`b.data.get("x")` retorna `None`. A réplica `b` ainda responde em vez de '
            "recusar, o que é a escolha pela disponibilidade, mas a resposta não é a última "
            "escrita, logo a leitura não é linearizável. A opção A erra porque a escrita nunca "
            "chegou a `b`; B erra porque `dict.get` não lança exceção; D chama de CP algo que "
            "devolve dado desatualizado em vez de recusar.",
            "Imprime `1`, pois a escrita foi confirmada e, portanto, todas as réplicas já a têm.",
            "Lança um `KeyError`, que é a escolha CP de falhar em vez de responder.",
            "Imprime `None`: a réplica continua disponível mas devolve uma resposta "
            "desatualizada, uma escolha de estilo AP.",
            "Imprime `None`: é uma escolha de estilo CP porque a função nunca retorna um valor "
            "errado.",
        ),
    ),
    _q(
        "cap-theorem-q09",
        "cap-theorem",
        MC,
        HARD,
        ("b",),
        ("cap", "quorum", "partitions"),
        _text(
            "A 5-node cluster uses majority quorums for all reads and writes. A partition splits "
            "it into a group of 3 nodes and a group of 2 nodes, and clients can reach both "
            "groups. How is this behavior classified under CAP?",
            "The 3-node side holds a majority, so it keeps serving linearizable reads and "
            "writes. The 2-node side cannot form a quorum, so its nodes must refuse requests: "
            "they are non-failing nodes that do not respond, so CAP availability is lost. "
            'That is CP. Option A ignores the refused requests; C confuses "some nodes still '
            'answer" with CAP availability, which requires every non-failing node to answer; '
            "D is false, as CAP applies to any number of nodes.",
            "Neither trade-off applies: the 3-node side still serves everything, so the system "
            "is both consistent and available.",
            "CP: the 3-node side keeps serving linearizable requests, while the 2-node side "
            "must refuse them, so not every non-failing node responds.",
            "AP: part of the cluster keeps answering, so the system has chosen availability "
            "over consistency.",
            "It is outside CAP, which only applies to clusters with two nodes.",
        ),
        _text(
            "Um cluster de 5 nós usa quóruns de maioria para todas as leituras e escritas. Uma "
            "partição o divide em um grupo de 3 nós e um grupo de 2 nós, e os clientes "
            "alcançam ambos os grupos. Como esse comportamento se classifica segundo o CAP?",
            "O lado de 3 nós tem a maioria, então continua servindo leituras e escritas "
            "linearizáveis. O lado de 2 nós não forma quórum, então seus nós precisam recusar "
            "requisições: são nós que não falharam e não respondem, logo a disponibilidade do "
            "CAP se perde. Isso é CP. A opção A ignora as requisições recusadas; C confunde "
            '"alguns nós ainda respondem" com a disponibilidade do CAP, que exige resposta de '
            "todo nó que não falhou; D é falsa, pois o CAP vale para qualquer número de nós.",
            "Nenhum dos dois trade-offs se aplica: o lado de 3 nós ainda serve tudo, então o "
            "sistema é consistente e disponível.",
            "CP: o lado de 3 nós continua servindo requisições linearizáveis, enquanto o lado de "
            "2 nós precisa recusá-las, então nem todo nó que não falhou responde.",
            "AP: parte do cluster continua respondendo, então o sistema escolheu "
            "disponibilidade em vez de consistência.",
            "Está fora do CAP, que só vale para clusters de dois nós.",
        ),
    ),
    _q(
        "cap-theorem-q10",
        "cap-theorem",
        SHORT,
        HARD,
        None,
        ("cap", "pacelc", "interview"),
        _text(
            'In an interview you hear: "CAP says you can only pick two of consistency, '
            'availability and partition tolerance, so our database is CA." Explain what is '
            "wrong with this claim and what extra trade-off PACELC adds.",
            "Self-check: did you mention (1) that partitions cannot be opted out of, so the real "
            "choice is C vs A during a partition, (2) that CAP says nothing about normal "
            "operation, and (3) PACELC's latency vs consistency trade-off in the Else case?",
            model_answer="Partitions are a fact of life in any multi-node system, so partition "
            'tolerance is not optional and "CA" is not a real choice for a distributed '
            "database: it would only describe a system that assumes the network never fails, "
            "such as a single node. The theorem's actual content is that, when a partition "
            "occurs, you must choose between consistency (linearizable reads that see the "
            "latest write, possibly by refusing requests) and availability (every non-failing "
            "node answers, possibly with stale data). CAP says nothing about normal operation. "
            "PACELC fills that gap: Else (no partition), you still trade latency against "
            "consistency, for example synchronous replication gives stronger consistency but "
            "higher write latency, while asynchronous replication is faster but can serve "
            "stale reads. So you describe a system by both choices, such as PA/EL or PC/EC.",
        ),
        _text(
            'Em uma entrevista você ouve: "O CAP diz que só dá para escolher dois entre '
            'consistência, disponibilidade e tolerância a partições, então nosso banco é CA." '
            "Explique o que há de errado nessa afirmação e qual trade-off adicional o PACELC "
            "traz.",
            "Autoavaliação: você mencionou (1) que não se pode abrir mão de tolerar partições, "
            "então a escolha real é C versus A durante uma partição, (2) que o CAP não diz nada "
            "sobre a operação normal e (3) o trade-off latência versus consistência do caso "
            "Else do PACELC?",
            model_answer="Partições são um fato em qualquer sistema com vários nós, então a "
            'tolerância a partições não é opcional e "CA" não é uma escolha real para um '
            "banco distribuído: descreveria apenas um sistema que supõe que a rede nunca "
            "falha, como um nó único. O conteúdo real do teorema é que, quando ocorre uma "
            "partição, é preciso escolher entre consistência (leituras linearizáveis que veem "
            "a última escrita, possivelmente recusando requisições) e disponibilidade (todo nó "
            "que não falhou responde, possivelmente com dados desatualizados). O CAP não diz "
            "nada sobre a operação normal. O PACELC preenche essa lacuna: Else (sem partição), "
            "ainda se troca latência por consistência; por exemplo, a replicação síncrona dá "
            "mais consistência com maior latência de escrita, enquanto a assíncrona é mais "
            "rápida mas pode servir leituras desatualizadas. Assim, descreve-se um sistema "
            "pelas duas escolhas, como PA/EL ou PC/EC.",
        ),
    ),
)


_QUORUM_CODE = """```python
# A key is replicated on N = 5 nodes, identified as 0..4.
def overlaps(w_nodes, r_nodes):
    return bool(set(w_nodes) & set(r_nodes))


print(overlaps({0, 1, 2}, {2, 3, 4}), overlaps({0, 1}, {2, 3, 4}))
```"""


_REPL: tuple[QuestionSeed, ...] = (
    _q(
        "replication-q01",
        "replication",
        MC,
        EASY,
        ("b",),
        ("replication", "async", "durability"),
        _text(
            "What is the main trade-off of **asynchronous** leader-follower replication "
            "compared with synchronous replication?",
            "With asynchronous replication the leader acknowledges a write as soon as it is "
            "committed locally, so write latency does not depend on followers. The price is "
            "that, if the leader crashes before followers receive the write, a write the client "
            "was told succeeded can be lost. A describes the synchronous trade-off, C and D "
            "describe benefits that asynchronous replication does not provide.",
            "It guarantees that acknowledged writes survive a leader crash, but every write "
            "waits for follower acknowledgments and is slower.",
            "It gives lower write latency, but an acknowledged write can be lost if the "
            "leader crashes before followers get it.",
            "It gives followers stronger consistency than the leader, but uses more storage "
            "for the extra copies.",
            "It removes replication lag, because followers apply each write in parallel with "
            "the client's acknowledgment.",
        ),
        _text(
            "Qual é o principal trade-off da replicação líder-seguidor **assíncrona** em "
            "comparação com a síncrona?",
            "Na replicação assíncrona o líder confirma a escrita assim que a persiste "
            "localmente, então a latência de escrita não depende dos seguidores. O preço é que, "
            "se o líder falhar antes de os seguidores receberem a escrita, uma escrita que o "
            "cliente foi informado que deu certo pode ser perdida. A descreve o trade-off da "
            "replicação síncrona; C e D descrevem benefícios que a assíncrona não oferece.",
            "Garante que escritas confirmadas sobrevivem à queda do líder, mas cada escrita "
            "espera a confirmação dos seguidores e fica mais lenta.",
            "Dá menor latência de escrita, mas uma escrita confirmada pode ser perdida se o "
            "líder falhar antes de os seguidores a receberem.",
            "Dá aos seguidores consistência mais forte que a do líder, mas usa mais "
            "armazenamento para as cópias extras.",
            "Elimina o replication lag, porque os seguidores aplicam cada escrita em paralelo "
            "com a confirmação ao cliente.",
        ),
    ),
    _q(
        "replication-q02",
        "replication",
        MC,
        EASY,
        ("c",),
        ("replication", "read-your-writes", "lag"),
        _text(
            "A user posts a comment (the write goes to the leader) and the page reloads. The "
            "comment list is read from an asynchronous follower and the new comment is missing. "
            "Which guarantee was violated?",
            "Read-your-writes (read-after-write) consistency says a user must always see their "
            "own writes. Here the follower had not yet applied the user's write because of "
            "replication lag. Monotonic reads (A) concerns time moving backwards across "
            "successive reads, durability (B) is not at stake since the leader has the write, "
            "and atomicity (D) is about all-or-nothing transactions.",
            "Monotonic reads (no going back in time)",
            "Durability of acknowledged writes",
            "Read-your-writes (seeing own writes)",
            "Atomicity of multi-row transactions",
        ),
        _text(
            "Um usuário publica um comentário (a escrita vai para o líder) e a página recarrega. "
            "A lista de comentários é lida de um seguidor assíncrono e o novo comentário não "
            "aparece. Qual garantia foi violada?",
            "Read-your-writes (consistência de leitura após escrita) diz que o usuário deve "
            "sempre enxergar as próprias escritas. Aqui o seguidor ainda não tinha aplicado a "
            "escrita do usuário devido ao replication lag. Monotonic reads (A) trata do tempo "
            "andar para trás entre leituras sucessivas, durabilidade (B) não está em jogo, pois "
            "o líder tem a escrita, e atomicidade (D) trata de transações tudo-ou-nada.",
            "Monotonic reads (sem voltar no tempo)",
            "Durabilidade das escritas confirmadas",
            "Read-your-writes (ver as próprias escritas)",
            "Atomicidade de transações com várias linhas",
        ),
    ),
    _q(
        "replication-q03",
        "replication",
        MC,
        EASY,
        ("a",),
        ("replication", "leader-follower"),
        _text(
            "Why does single-leader replication avoid write conflicts?",
            "Only the leader accepts writes, and followers apply the leader's replication log in "
            "the order the leader applied it, so there is a single order of truth and nothing "
            "to reconcile. B and C describe mechanisms (locking, timestamps) that this design "
            "does not need, and D is not required: the leader does not wait for all followers.",
            "Only the leader accepts writes, and followers apply its log in the same order.",
            "Followers lock the affected rows on the leader before it applies each write.",
            "Every node accepts writes, and timestamps resolve any conflicts afterwards.",
            "The leader waits for every follower to apply a write before accepting the next one.",
        ),
        _text(
            "Por que a replicação com líder único evita conflitos de escrita?",
            "Só o líder aceita escritas, e os seguidores aplicam o log de replicação do líder "
            "na ordem em que ele o aplicou, então há uma única ordem de verdade e nada a "
            "reconciliar. B e C descrevem mecanismos (locks, timestamps) de que esse projeto "
            "não precisa, e D não é necessário: o líder não espera todos os seguidores.",
            "Só o líder aceita escritas, e os seguidores aplicam o log dele na mesma ordem.",
            "Os seguidores bloqueiam as linhas afetadas no líder antes de ele aplicar cada "
            "escrita.",
            "Todos os nós aceitam escritas, e timestamps resolvem os conflitos depois.",
            "O líder espera todos os seguidores aplicarem uma escrita antes de aceitar a próxima.",
        ),
    ),
    _q(
        "replication-q04",
        "replication",
        MC,
        MEDIUM,
        ("c",),
        ("replication", "monotonic-reads", "routing"),
        _text(
            "Reads are load-balanced across several asynchronous followers. A user refreshes "
            "a page twice and the second response shows older data than the first. What is "
            "this anomaly, and what is a common fix?",
            "This is a monotonic-reads violation: the two requests hit followers with "
            "different lag, so time appears to go backwards. Pinning a user's reads to the same "
            "replica (for example by hashing the session ID) makes the view only move forward. "
            "Reading from the leader after a write (A) addresses read-your-writes, and "
            "more followers (B) would make the lag differences worse, while split-brain (D) "
            "is about two leaders.",
            "A read-your-writes violation; read from the leader after every write the user "
            "makes.",
            "A monotonic-reads violation; add more followers so that each one carries less "
            "read load.",
            "A monotonic-reads violation; pin each user's reads to the same replica.",
            "Split-brain; require a quorum before promoting a follower to leader.",
        ),
        _text(
            "As leituras são distribuídas entre vários seguidores assíncronos. Um usuário "
            "atualiza uma página duas vezes e a segunda resposta mostra dados mais antigos que "
            "a primeira. Que anomalia é essa e qual é uma correção comum?",
            "É uma violação de monotonic reads: as duas requisições caíram em seguidores com "
            "lag diferente, então o tempo parece andar para trás. Fixar as leituras de um "
            "usuário na mesma réplica (por exemplo, por hash do ID de sessão) faz a visão só "
            "avançar. Ler do líder após uma escrita (A) trata de read-your-writes, mais "
            "seguidores (B) aumentariam as diferenças de lag, e split-brain (D) trata de dois "
            "líderes.",
            "Violação de read-your-writes; ler do líder após toda escrita feita pelo usuário.",
            "Violação de monotonic reads; adicionar mais seguidores para que cada um receba "
            "menos carga de leitura.",
            "Violação de monotonic reads; fixar as leituras de cada usuário na mesma réplica.",
            "Split-brain; exigir um quórum antes de promover um seguidor a líder.",
        ),
    ),
    _q(
        "replication-q05",
        "replication",
        MS,
        MEDIUM,
        ("a", "c"),
        ("replication", "read-your-writes", "routing"),
        _text(
            "Which techniques help provide **read-your-writes** for a user when reads are "
            "served by asynchronous followers? Select all that apply.",
            "A and C work: after a write, send that user's reads to the leader for a short "
            "window, or remember the log position of the write and serve the read only from a "
            "replica that has applied at least that position. Adding followers (B) and a "
            "longer heartbeat timeout (D) have no effect on whether a given follower has "
            "applied a specific write, and always choosing the least-lagged follower (E) "
            "reduces staleness but does not guarantee the user's own write is there.",
            "For a short window after a user writes, serve that user's reads from the leader.",
            "Add more followers so that reads are spread over more replicas.",
            "Record the log position of the user's last write and serve the read only from a "
            "replica that has applied at least that position.",
            "Increase the leader's heartbeat timeout.",
            "Always read from the follower with the smallest current lag, without tracking the "
            "user's writes.",
        ),
        _text(
            "Quais técnicas ajudam a oferecer **read-your-writes** a um usuário quando as "
            "leituras são atendidas por seguidores assíncronos? Selecione todas que se "
            "aplicam.",
            "A e C funcionam: após uma escrita, envie as leituras daquele usuário ao líder por "
            "uma janela curta, ou guarde a posição no log da escrita e atenda a leitura só "
            "com uma réplica que já aplicou ao menos essa posição. Adicionar seguidores (B) e "
            "aumentar o timeout de heartbeat (D) não mudam se um seguidor específico já aplicou "
            "determinada escrita, e escolher sempre o seguidor com menor lag (E) reduz a "
            "defasagem mas não garante que a escrita do usuário esteja lá.",
            "Por uma janela curta após o usuário escrever, atender as leituras dele pelo líder.",
            "Adicionar mais seguidores para que as leituras se espalhem por mais réplicas.",
            "Registrar a posição no log da última escrita do usuário e atender a leitura só "
            "com uma réplica que já aplicou ao menos essa posição.",
            "Aumentar o timeout de heartbeat do líder.",
            "Ler sempre do seguidor com menor lag no momento, sem rastrear as escritas do usuário.",
        ),
    ),
    _q(
        "replication-q06",
        "replication",
        MC,
        MEDIUM,
        ("d",),
        ("replication", "failover", "data-loss"),
        _text(
            "A leader using asynchronous replication crashes and a follower is promoted. Some "
            "writes that clients were told had succeeded are gone. Which setup best reduces "
            "this risk?",
            "Keeping at least one synchronous follower guarantees that a copy of every "
            "acknowledged write exists on that follower, and promoting it avoids the loss. "
            "A shorter timeout (A) only changes when failover starts, promoting a random "
            "follower (B) ignores that followers are at different positions, and blind client "
            "retries (C) can duplicate writes and do not recover what was lost.",
            "A shorter heartbeat timeout, so failover starts sooner.",
            "Promote a random follower, since all followers hold identical data.",
            "Have clients retry every write after a failover.",
            "Keep at least one synchronous follower and promote that one.",
        ),
        _text(
            "Um líder com replicação assíncrona cai e um seguidor é promovido. Algumas escritas "
            "que os clientes foram informados que deram certo sumiram. Qual configuração "
            "reduz melhor esse risco?",
            "Manter ao menos um seguidor síncrono garante que existe uma cópia de toda escrita "
            "confirmada nele, e promovê-lo evita a perda. Um timeout menor (A) só muda quando o "
            "failover começa, promover um seguidor aleatório (B) ignora que os seguidores "
            "estão em posições diferentes, e retries cegos dos clientes (C) podem duplicar "
            "escritas e não recuperam o que foi perdido.",
            "Um timeout de heartbeat menor, para o failover começar mais cedo.",
            "Promover um seguidor aleatório, já que todos os seguidores têm dados idênticos.",
            "Fazer os clientes repetirem toda escrita após um failover.",
            "Manter ao menos um seguidor síncrono e promover esse.",
        ),
    ),
    _q(
        "replication-q07",
        "replication",
        MC,
        MEDIUM,
        ("a",),
        ("replication", "failover", "heartbeats"),
        _text(
            "A cluster detects leader failure with heartbeats and a 5-second timeout. The "
            "leader occasionally freezes for 20 seconds because of a long garbage-collection "
            "pause. What is the main risk of this timeout?",
            "A node that is merely slow looks identical to a dead one, so the timeout causes "
            "a false-positive failover; if the old leader wakes up still believing it leads, "
            "the cluster can have two leaders. B is the problem of a timeout that is too long, "
            "and C and D are unrelated to how failure is detected.",
            "A false-positive failover away from a leader that is only paused, possibly "
            "creating two leaders.",
            "A long write-unavailability window after a real crash, since the failure takes "
            "too long to be detected.",
            "Followers fall further behind the leader's replication log during every long "
            "pause.",
            "The replication log grows without bound on the leader until the next full backup.",
        ),
        _text(
            "Um cluster detecta a falha do líder com heartbeats e um timeout de 5 segundos. O "
            "líder às vezes congela por 20 segundos devido a uma longa pausa de garbage "
            "collection. Qual é o principal risco desse timeout?",
            "Um nó apenas lento é indistinguível de um nó morto, então o timeout causa um "
            "failover falso positivo; se o líder antigo acordar ainda acreditando que lidera, "
            "o cluster pode ficar com dois líderes. B é o problema de um timeout longo demais, "
            "e C e D não têm relação com a detecção de falhas.",
            "Um failover falso positivo, afastando um líder que só estava pausado e "
            "possivelmente criando dois líderes.",
            "Uma longa janela de indisponibilidade de escrita após uma queda real, pois a "
            "falha demora demais a ser detectada.",
            "Os seguidores ficam ainda mais atrás no log de replicação do líder a cada pausa "
            "longa.",
            "O log de replicação cresce sem limite no líder até o próximo backup completo.",
        ),
    ),
    _q(
        "replication-q08",
        "replication",
        MC,
        MEDIUM,
        ("c",),
        ("replication", "split-brain", "quorum"),
        _text(
            "A partition isolates the current leader from the rest of the cluster, and the "
            "majority side promotes a new leader. What is the standard defense against the "
            "resulting **split-brain**?",
            "Promotion must be approved by a majority, and a leader that cannot reach a "
            "majority must step down and refuse writes, so at most one side can accept them. "
            "Promoting on a single missed heartbeat (A) creates the problem, wall-clock "
            "last-write-wins (B) silently discards one side's writes, and a short DNS TTL (D) "
            "only helps clients find a leader, it does not stop the old one from accepting "
            "writes.",
            "Promote a new leader as soon as any single follower misses one heartbeat from the "
            "old leader.",
            "Let both leaders keep accepting writes and, afterwards, keep whichever write "
            "carries the later wall-clock timestamp.",
            "Require a majority quorum to authorize promotion, and make a leader that loses "
            "the majority step down.",
            "Use a short DNS TTL so that clients switch to the new leader quickly after a "
            "failover.",
        ),
        _text(
            "Uma partição isola o líder atual do resto do cluster, e o lado majoritário "
            "promove um novo líder. Qual é a defesa padrão contra o **split-brain** resultante?",
            "A promoção precisa ser aprovada por uma maioria, e um líder que não alcança a "
            "maioria deve renunciar e recusar escritas, de modo que no máximo um lado aceite "
            "escritas. Promover após um único heartbeat perdido (A) cria o problema, "
            "last-write-wins por relógio (B) descarta silenciosamente as escritas de um lado, "
            "e um TTL de DNS curto (D) só ajuda os clientes a achar um líder, não impede o "
            "antigo de aceitar escritas.",
            "Promover um novo líder assim que qualquer seguidor perder um heartbeat do líder "
            "antigo.",
            "Deixar ambos os líderes continuarem aceitando escritas e, depois, manter a de "
            "timestamp de relógio mais recente.",
            "Exigir um quórum de maioria para autorizar a promoção e fazer o líder que perde "
            "a maioria renunciar.",
            "Usar um TTL de DNS curto para os clientes migrarem rápido para o novo líder "
            "após o failover.",
        ),
    ),
    _q(
        "replication-q09",
        "replication",
        CODE,
        HARD,
        ("b",),
        ("replication", "quorum", "overlap"),
        _text(
            "A write was acknowledged by the nodes in `w_nodes`, and a later read contacts "
            "`r_nodes`. What does this print, and what does it show about quorum sizes?\n\n"
            + _QUORUM_CODE,
            "It prints `True False`. With N = 5, W = 3 and R = 3 give W + R > N, so any write "
            "set and any read set share at least one node, which means the read reaches a node "
            "holding the acknowledged write. With W = 2 and R = 3, W + R = N, so a read set "
            "can miss the write set entirely, as in the second call. Option A is wrong because "
            "R = 3 is a majority yet still missed the write, C is contradicted by the second "
            "call, and D is wrong because the guarantee comes from the sizes, not from lucky "
            "node ids. Overlap alone does not make a system linearizable; other mechanisms "
            "build on it.",
            "`True False`: reading from a majority of nodes is always enough to see every "
            "acknowledged write.",
            "`True False`: when W + R > N every read set intersects every write set, but with "
            "W = 2 and R = 3 a read can miss the write entirely.",
            "`True True`: any read set overlaps any write set, whatever the quorum sizes.",
            "`False True`: overlap depends on the node ids chosen, not on the quorum sizes.",
        ),
        _text(
            "Uma escrita foi confirmada pelos nós em `w_nodes`, e uma leitura posterior "
            "contata `r_nodes`. O que isto imprime, e o que mostra sobre tamanhos de quórum?\n\n"
            + _QUORUM_CODE,
            "Imprime `True False`. Com N = 5, W = 3 e R = 3 dão W + R > N, então qualquer "
            "conjunto de escrita e qualquer conjunto de leitura compartilham ao menos um nó, "
            "ou seja, a leitura alcança um nó que tem a escrita confirmada. Com W = 2 e R = 3, "
            "W + R = N, então um conjunto de leitura pode não encontrar o de escrita, como na "
            "segunda chamada. A opção A erra porque R = 3 é uma maioria e mesmo assim perdeu a "
            "escrita, C é contradita pela segunda chamada, e D erra porque a garantia vem dos "
            "tamanhos, não de ids de nós com sorte. A interseção sozinha não torna um sistema "
            "linearizável; outros mecanismos se constroem sobre ela.",
            "`True False`: ler de uma maioria de nós sempre basta para ver toda escrita "
            "confirmada.",
            "`True False`: quando W + R > N todo conjunto de leitura intersecta todo conjunto "
            "de escrita, mas com W = 2 e R = 3 uma leitura pode perder a escrita por completo.",
            "`True True`: qualquer conjunto de leitura sobrepõe qualquer de escrita, quaisquer "
            "que sejam os tamanhos de quórum.",
            "`False True`: a sobreposição depende dos ids dos nós escolhidos, não dos tamanhos "
            "de quórum.",
        ),
    ),
    _q(
        "replication-q10",
        "replication",
        SHORT,
        HARD,
        None,
        ("replication", "failover", "interview", "design"),
        _text(
            "Design the automatic failover procedure for a primary with two asynchronous "
            "replicas of a relational database. Cover how you detect the failure, how you "
            "choose and promote a new primary, how you protect against split-brain, and what "
            "you tell the business about possible data loss.",
            "Self-check: did you mention (1) failure detection with a tuned timeout and "
            "multiple observers, (2) quorum or fencing to prevent two primaries, (3) promoting "
            "the most up-to-date replica and redirecting clients, (4) the old primary rejoining "
            "as a follower, and (5) the data-loss window of async replication?",
            model_answer="Detection: health checks or heartbeats from more than one observer "
            "with a timeout tuned between failover speed and false positives. Authorization: "
            "a majority-based coordination service (etcd, ZooKeeper, Consul or a consensus "
            "layer) decides that failover happens, so one isolated observer cannot promote "
            "alone. Fencing: make sure the old primary cannot keep accepting writes, by "
            "making it step down when it loses the majority, cutting it off at the network or "
            "storage level, or shutting it down. Promotion: pick the replica with the most "
            "complete replication log (the highest log position), promote it and reconfigure "
            "the other replica to follow it. Redirection: update the proxy, virtual IP, DNS "
            "or service-discovery entry so clients find the new primary. Recovery: when the "
            "old primary returns, discard or rewind any writes the new primary never saw and "
            "rejoin it as a follower. Data loss: with asynchronous replication, writes "
            "acknowledged but not yet received by the promoted replica are lost, so state this "
            "window (RPO) explicitly, or reduce it with one synchronous standby at a "
            "write-latency cost. Rehearse the whole procedure regularly.",
        ),
        _text(
            "Projete o procedimento de failover automático para um primário com duas réplicas "
            "assíncronas de um banco relacional. Cubra como detectar a falha, como escolher e "
            "promover o novo primário, como se proteger contra split-brain e o que dizer ao "
            "negócio sobre possível perda de dados.",
            "Autoavaliação: você mencionou (1) detecção de falha com timeout ajustado e vários "
            "observadores, (2) quórum ou fencing para evitar dois primários, (3) promover a "
            "réplica mais atualizada e redirecionar os clientes, (4) o primário antigo "
            "voltando como seguidor e (5) a janela de perda de dados da replicação "
            "assíncrona?",
            model_answer="Detecção: health checks ou heartbeats de mais de um observador, com "
            "um timeout ajustado entre velocidade de failover e falsos positivos. Autorização: "
            "um serviço de coordenação baseado em maioria (etcd, ZooKeeper, Consul ou uma "
            "camada de consenso) decide que o failover acontece, de modo que um observador "
            "isolado não promova sozinho. Fencing: garantir que o primário antigo não continue "
            "aceitando escritas, fazendo-o renunciar ao perder a maioria, isolando-o na rede "
            "ou no armazenamento, ou desligando-o. Promoção: escolher a réplica com o log de "
            "replicação mais completo (maior posição no log), promovê-la e reconfigurar a "
            "outra réplica para segui-la. Redirecionamento: atualizar o proxy, o IP virtual, o "
            "DNS ou o service discovery para que os clientes achem o novo primário. "
            "Recuperação: quando o primário antigo voltar, descartar ou reverter as escritas "
            "que o novo primário nunca viu e reintegrá-lo como seguidor. Perda de dados: com "
            "replicação assíncrona, escritas confirmadas mas ainda não recebidas pela réplica "
            "promovida são perdidas, então declare essa janela (RPO) explicitamente, ou "
            "reduza-a com um standby síncrono ao custo de latência de escrita. Ensaie todo o "
            "procedimento regularmente.",
        ),
    ),
)


_RESHARD_CODE = """```python
OLD_SHARDS, NEW_SHARDS = 4, 5

moved = sum(1 for key in range(1000) if key % OLD_SHARDS != key % NEW_SHARDS)
print(moved)
```"""


_SHARD: tuple[QuestionSeed, ...] = (
    _q(
        "partitioning-sharding-q01",
        "partitioning-sharding",
        MC,
        EASY,
        ("d",),
        ("sharding", "hash", "range-scans"),
        _text(
            "A table is sharded by `hash(order_id)`. What is the main drawback of this strategy?",
            "A good hash spreads keys almost uniformly, which is its strength, but it also "
            "destroys ordering: adjacent keys land on unrelated shards, so a range query such "
            'as "orders from March 1 to 15" must be sent to every shard. Hash sharding does '
            "not create hot ranges (A), does not need a lookup service (B) and does not prevent "
            "lookups by key (C).",
            "It concentrates the most recent writes on a single shard, because new ids are "
            "always the largest.",
            "It requires a separate lookup service that maps each key to the shard storing it.",
            "It makes lookups by `order_id` impossible, because the hash cannot be reversed.",
            "Range scans must go to every shard, because hashing destroys key ordering.",
        ),
        _text(
            "Uma tabela é particionada (sharded) por `hash(order_id)`. Qual é a principal "
            "desvantagem dessa estratégia?",
            "Um bom hash espalha as chaves de forma quase uniforme, o que é sua força, mas também "
            "destrói a ordenação: chaves adjacentes caem em shards sem relação, então uma "
            'consulta por faixa como "pedidos de 1 a 15 de março" precisa ser enviada a todos '
            "os shards. O sharding por hash não cria faixas quentes (A), não precisa de um "
            "serviço de lookup (B) e não impede buscas por chave (C).",
            "Concentra as escritas mais recentes em um único shard, pois os novos ids são "
            "sempre os maiores.",
            "Exige um serviço de lookup separado que mapeie cada chave ao shard que a guarda.",
            "Torna impossíveis as buscas por `order_id`, porque o hash não pode ser revertido.",
            "Consultas por faixa precisam ir a todos os shards, pois o hash destrói a "
            "ordenação das chaves.",
        ),
    ),
    _q(
        "partitioning-sharding-q02",
        "partitioning-sharding",
        MC,
        EASY,
        ("b",),
        ("sharding", "replication"),
        _text(
            "What problem does sharding solve that replication alone does not?",
            "Every replica holds the full dataset, so replication adds durability and read "
            "capacity but does not help when the data or the write throughput no longer fits "
            "on one machine. Sharding splits the data so each node holds only a slice, letting "
            "total storage and write capacity grow with the number of shards.",
            "It protects the data against the loss of a single machine or an entire data "
            "center.",
            "It lets the dataset and write load exceed what a single machine can handle.",
            "It makes every read return the latest write, even when replicas are lagging.",
            "It removes the need for backups, because the data is already stored on several "
            "nodes.",
        ),
        _text(
            "Que problema o sharding resolve e a replicação sozinha não resolve?",
            "Toda réplica guarda o conjunto de dados completo, então a replicação agrega "
            "durabilidade e capacidade de leitura, mas não ajuda quando os dados ou a vazão de "
            "escrita não cabem mais em uma máquina. O sharding divide os dados para que cada nó "
            "guarde só uma fatia, permitindo que o armazenamento e a capacidade de escrita "
            "totais cresçam com o número de shards.",
            "Protege os dados contra a perda de uma única máquina ou de um data center "
            "inteiro.",
            "Permite que os dados e a carga de escrita excedam o que uma máquina suporta.",
            "Faz toda leitura retornar a última escrita, mesmo com réplicas atrasadas.",
            "Elimina a necessidade de backups, pois os dados já ficam em vários nós.",
        ),
    ),
    _q(
        "partitioning-sharding-q03",
        "partitioning-sharding",
        MC,
        EASY,
        ("c",),
        ("sharding", "range", "hot-shards"),
        _text(
            "A time-series table is range-sharded by timestamp, with one shard per month. What "
            "problem will show up first?",
            "Almost all current writes carry the current timestamp, so they hit the one shard "
            'that owns "now" while the shards with historical data stay mostly idle: a hot '
            "shard. Option A describes hash sharding (range scans over time stay efficient "
            "here), and neither re-sharding (B) nor cross-shard joins (D) is the first thing "
            "to bite.",
            "Time-range queries must be sent to every shard, because range sharding scatters "
            "adjacent times.",
            "Adding a shard forces nearly all existing data to move to its new owner.",
            "All new writes land on the shard of the current month, creating a hot shard.",
            "Joins between rows of different months become impossible.",
        ),
        _text(
            "Uma tabela de séries temporais é particionada por faixa de timestamp, com um shard "
            "por mês. Que problema aparece primeiro?",
            "Quase todas as escritas atuais carregam o timestamp atual, então atingem o único "
            'shard que detém o "agora" enquanto os shards com dados históricos ficam quase '
            "ociosos: um hot shard. A opção A descreve o sharding por hash (aqui as consultas "
            "por faixa de tempo continuam eficientes), e nem o re-sharding (B) nem os joins "
            "entre shards (D) são o primeiro problema.",
            "Consultas por faixa de tempo precisam ser enviadas a todos os shards, pois o "
            "sharding por faixa espalha tempos adjacentes.",
            "Adicionar um shard força a movimentação de quase todos os dados existentes para "
            "o novo dono.",
            "Todas as novas escritas caem no shard do mês atual, criando um hot shard.",
            "Joins entre linhas de meses diferentes se tornam impossíveis.",
        ),
    ),
    _q(
        "partitioning-sharding-q04",
        "partitioning-sharding",
        MC,
        MEDIUM,
        ("a",),
        ("sharding", "directory"),
        _text(
            "Directory-based sharding lets you move any key (or tenant) to any shard by "
            "updating a lookup table. What is its main cost?",
            "The directory is consulted to route requests, so it adds a lookup to the request "
            "path and becomes a critical dependency that must itself be highly available and "
            "usually cached. It does not prevent range scans (B), it makes moving data easier, "
            "not harder (C), and it does not require uniformly distributed keys (D); that "
            "flexibility is its selling point.",
            "The directory is an extra dependency on the request path and must be highly "
            "available.",
            "Range scans become impossible, because the lookup table has no notion of key "
            "order.",
            "Data can only be rebalanced by taking the whole system offline while the "
            "directory is rebuilt.",
            "Keys must be uniformly distributed for the directory to work, or it overloads.",
        ),
        _text(
            "O sharding baseado em diretório permite mover qualquer chave (ou tenant) para "
            "qualquer shard atualizando uma tabela de lookup. Qual é o seu principal custo?",
            "O diretório é consultado para rotear requisições, então adiciona um lookup ao "
            "caminho da requisição e vira uma dependência crítica que precisa ser altamente "
            "disponível e, em geral, cacheada. Ele não impede consultas por faixa (B), torna "
            "mover dados mais fácil, não mais difícil (C), e não exige chaves uniformemente "
            "distribuídas (D); essa flexibilidade é seu ponto forte.",
            "O diretório é uma dependência extra no caminho da requisição e precisa ser "
            "altamente disponível.",
            "Consultas por faixa se tornam impossíveis, pois a tabela de lookup não tem "
            "noção da ordem das chaves.",
            "Os dados só podem ser rebalanceados desligando o sistema inteiro enquanto o "
            "diretório é reconstruído.",
            "As chaves precisam ser distribuídas uniformemente para o diretório funcionar, "
            "senão ele sobrecarrega.",
        ),
    ),
    _q(
        "partitioning-sharding-q05",
        "partitioning-sharding",
        CODE,
        MEDIUM,
        ("d",),
        ("sharding", "modulo", "resharding"),
        _text(
            "A system routes each key to shard `key % N`. Assuming uniformly distributed "
            "integer keys, what does this print, and what does it tell you about growing the "
            "cluster from 4 to 5 shards?\n\n" + _RESHARD_CODE,
            "It prints `800`: only keys whose remainders modulo 4 and modulo 5 happen to match "
            "(20% of them) stay put, so about 80% of the data moves. A consistent-hashing "
            "scheme would move only about one fifth of the keys (the share the new shard must "
            "own), which is what option B describes. Options A and C do not match the "
            "computation, since the remainders differ for most keys.",
            "`0`: modulo sharding never moves keys when shards are added.",
            "`200`: about 1/N of the keys move, the ideal minimum.",
            "`500`: about half of the keys move.",
            "`800`: about 80% of the keys move, which is why naive modulo resharding is costly.",
        ),
        _text(
            "Um sistema roteia cada chave para o shard `key % N`. Supondo chaves inteiras "
            "uniformemente distribuídas, o que isto imprime e o que revela sobre crescer o "
            "cluster de 4 para 5 shards?\n\n" + _RESHARD_CODE,
            "Imprime `800`: só as chaves cujos restos módulo 4 e módulo 5 coincidem (20% delas) "
            "ficam onde estão, então cerca de 80% dos dados se movem. Um esquema de consistent "
            "hashing moveria apenas cerca de um quinto das chaves (a parte que o novo shard "
            "deve assumir), que é o que a opção B descreve. As opções A e C não batem com o "
            "cálculo, pois os restos diferem para a maioria das chaves.",
            "`0`: o sharding por módulo nunca move chaves quando shards são adicionados.",
            "`200`: cerca de 1/N das chaves se movem, o mínimo ideal.",
            "`500`: cerca de metade das chaves se movem.",
            "`800`: cerca de 80% das chaves se movem, por isso o re-sharding ingênuo por módulo "
            "é caro.",
        ),
    ),
    _q(
        "partitioning-sharding-q06",
        "partitioning-sharding",
        MC,
        MEDIUM,
        ("b",),
        ("sharding", "shard-key", "multi-tenant"),
        _text(
            "For a multi-tenant SaaS database, why is `tenant_id` often a good default shard key?",
            "Nearly every query and transaction in such an app is already scoped to one "
            "tenant, so with `tenant_id` as the shard key each of them is served entirely by a "
            "single shard, avoiding cross-shard joins and distributed transactions. Tenants "
            "are usually very uneven in size (A is false and skew is the main risk), secondary "
            "indexes are still needed (C), and cross-tenant analytics become fan-out queries "
            "(D).",
            "Tenants are normally similar in size, so the load is spread perfectly evenly "
            "across shards.",
            "Most queries and transactions touch one tenant, so they stay in one shard.",
            "It removes the need for secondary indexes, since every lookup is routed by tenant.",
            "It makes queries across all tenants cheap.",
        ),
        _text(
            "Em um banco de SaaS multi-tenant, por que `tenant_id` costuma ser uma boa "
            "shard key padrão?",
            "Quase toda consulta e transação nesse tipo de aplicação já é restrita a um tenant, "
            "então com `tenant_id` como shard key cada uma é atendida inteiramente por um único "
            "shard, evitando joins entre shards e transações distribuídas. Os tenants costumam "
            "ter tamanhos muito desiguais (A é falsa e o desvio é o principal risco), índices "
            "secundários continuam necessários (C) e análises entre tenants viram consultas "
            "em todos os shards (D).",
            "Os tenants normalmente têm tamanho parecido, então a carga fica perfeitamente "
            "uniforme entre os shards.",
            "A maioria das consultas e transações toca um só tenant, então ficam em um único "
            "shard.",
            "Elimina a necessidade de índices secundários, pois toda busca é roteada por "
            "tenant.",
            "Torna baratas as consultas que cruzam todos os tenants.",
        ),
    ),
    _q(
        "partitioning-sharding-q07",
        "partitioning-sharding",
        MC,
        MEDIUM,
        ("c",),
        ("sharding", "secondary-indexes"),
        _text(
            "A table is sharded by `tenant_id` and has a **local** secondary index on "
            "`external_ticket_id` in each shard. A query looks up one ticket by "
            "`external_ticket_id` without knowing its tenant. What happens?",
            "Each local index covers only the rows of its own shard, and the ticket could be on "
            "any of them, so the query has to be sent to every shard and the results gathered. "
            "A global secondary index, partitioned by the indexed column, would allow a "
            "targeted lookup but must be kept in sync with the base data and may lag "
            "behind it. A is wrong because no single shard can be chosen, B because the lookup "
            "is possible, and D because a read needs no distributed transaction.",
            "The query goes to one shard, picked by hashing `external_ticket_id` with the same "
            "function as the table.",
            "The query cannot be answered at all unless the table is re-sharded by "
            "`external_ticket_id`.",
            "The query is sent to every shard (scatter-gather) and the results are merged.",
            "The query needs a distributed transaction across all shards to give a consistent "
            "result.",
        ),
        _text(
            "Uma tabela é particionada por `tenant_id` e tem um índice secundário **local** em "
            "`external_ticket_id` em cada shard. Uma consulta busca um ticket por "
            "`external_ticket_id` sem saber o tenant. O que acontece?",
            "Cada índice local cobre apenas as linhas do seu próprio shard, e o ticket pode "
            "estar em qualquer um, então a consulta precisa ser enviada a todos os shards e os "
            "resultados reunidos. Um índice secundário global, particionado pela coluna "
            "indexada, permitiria uma busca direcionada, mas precisa ser mantido em sincronia "
            "com os dados-base e pode ficar atrasado em relação a eles. A erra porque nenhum "
            "shard único pode ser escolhido, B porque a busca é possível, e D porque uma "
            "leitura não precisa de transação distribuída.",
            "A consulta vai a um shard, escolhido pelo hash de `external_ticket_id` com a "
            "mesma função da tabela.",
            "A consulta não pode ser respondida a menos que a tabela seja re-particionada por "
            "`external_ticket_id`.",
            "A consulta é enviada a todos os shards (scatter-gather) e os resultados são "
            "reunidos.",
            "A consulta exige uma transação distribuída entre todos os shards para dar um "
            "resultado consistente.",
        ),
    ),
    _q(
        "partitioning-sharding-q08",
        "partitioning-sharding",
        MS,
        MEDIUM,
        ("a", "c", "e"),
        ("sharding", "joins", "transactions", "secondary-indexes"),
        _text(
            "A database was sharded by `tenant_id`. Which of these operations become harder "
            "or more expensive because of the sharding? Select all that apply.",
            "Joins across shards, atomic updates spanning shards (which need two-phase commit "
            "or a redesign), and lookups by a non-shard-key column (fan-out or a global index) "
            "all get harder. Fetching one row by its shard key (B) and writing a row whose "
            "shard key is known (D) are routed to a single shard and stay as simple as "
            "before.",
            "A join between tables whose matching rows live on different shards.",
            "Fetching one row when its `tenant_id` is known.",
            "An atomic transaction that updates rows belonging to two different shards.",
            "Inserting a new row whose `tenant_id` is known.",
            "Finding rows by a column other than the shard key.",
        ),
        _text(
            "Um banco foi particionado por `tenant_id`. Quais destas operações ficam mais "
            "difíceis ou mais caras por causa do sharding? Selecione todas que se aplicam.",
            "Joins entre shards, atualizações atômicas que abrangem shards (que exigem "
            "two-phase commit ou redesenho) e buscas por uma coluna que não é a shard key "
            "(fan-out ou índice global) ficam mais difíceis. Buscar uma linha pela shard key "
            "(B) e gravar uma linha cuja shard key é conhecida (D) são roteadas a um único "
            "shard e continuam tão simples quanto antes.",
            "Um join entre tabelas cujas linhas correspondentes estão em shards diferentes.",
            "Buscar uma linha quando seu `tenant_id` é conhecido.",
            "Uma transação atômica que atualiza linhas de dois shards diferentes.",
            "Inserir uma nova linha cujo `tenant_id` é conhecido.",
            "Encontrar linhas por uma coluna diferente da shard key.",
        ),
    ),
    _q(
        "partitioning-sharding-q09",
        "partitioning-sharding",
        MC,
        HARD,
        ("c",),
        ("sharding", "hot-shards", "multi-tenant", "directory"),
        _text(
            "A multi-tenant database is sharded by `hash(tenant_id)`. One enterprise tenant "
            "now generates about 40% of all traffic and overloads its shard. Which change best "
            "fixes this while keeping most queries and transactions single-shard for everyone "
            "else?",
            "A directory (lookup table) lets you override the hash for the large tenant and "
            "give it a dedicated shard while every other tenant keeps hash placement and "
            "tenant locality. A would spread each tenant's rows over all shards, turning "
            "most queries into fan-outs and most transactions into cross-shard ones. B changes "
            "nothing for this tenant, since all of its rows still hash to one shard. D "
            "reintroduces the hot-shard problem on the newest range.",
            "Re-shard by `hash(row_id)` so every tenant's rows spread over all shards.",
            "Add more shards but keep `hash(tenant_id)` as the key.",
            "Add a directory that places the large tenant on a dedicated shard and leaves "
            "other tenants where hashing put them.",
            "Switch to range sharding by creation timestamp.",
        ),
        _text(
            "Um banco multi-tenant é particionado por `hash(tenant_id)`. Um tenant corporativo "
            "passa a gerar cerca de 40% de todo o tráfego e sobrecarrega o seu shard. Qual "
            "mudança resolve isso melhor, mantendo a maioria das consultas e transações dos "
            "demais em um único shard?",
            "Um diretório (tabela de lookup) permite sobrescrever o hash para o tenant grande "
            "e dar a ele um shard dedicado, enquanto os demais tenants mantêm a colocação por "
            "hash e a localidade por tenant. A espalharia as linhas de cada tenant por todos os "
            "shards, transformando a maioria das consultas em fan-outs e a maioria das "
            "transações em transações entre shards. B não muda nada para esse tenant, já que "
            "todas as suas linhas continuam no mesmo shard. D reintroduz o problema de hot "
            "shard na faixa mais recente.",
            "Re-particionar por `hash(row_id)` para que as linhas de cada tenant se espalhem "
            "por todos os shards.",
            "Adicionar mais shards mantendo `hash(tenant_id)` como chave.",
            "Adicionar um diretório que coloque o tenant grande em um shard dedicado e deixe "
            "os demais onde o hash os colocou.",
            "Trocar para sharding por faixa de data de criação.",
        ),
    ),
    _q(
        "partitioning-sharding-q10",
        "partitioning-sharding",
        SHORT,
        HARD,
        None,
        ("sharding", "consistent-hashing", "virtual-nodes", "interview"),
        _text(
            "Explain how consistent hashing works, why it reshards better than `hash(key) % N`, "
            "and what virtual nodes add.",
            "Self-check: did you mention (1) keys and nodes placed on the same hash ring with "
            "clockwise ownership, (2) that adding or removing a node moves only about 1/N of "
            "the keys, and (3) virtual nodes smoothing load and spreading rebalancing?",
            model_answer="Both nodes and keys are hashed onto a fixed ring (for example "
            "0 to 2^32-1). A key belongs to the first node found clockwise from its position. "
            "When a node is added, it takes over only the keys between its predecessor and "
            "itself, so about 1/N of the keys move; when one leaves, only its keys go to its "
            "successor. With hash(key) % N, changing N changes the shard of most keys, forcing "
            "a near-total reshuffle. With a single position per node, load can be uneven and "
            "a departing node dumps everything on one neighbor. Virtual nodes give each "
            "physical node many positions on the ring, which evens out the load, spreads the "
            "keys moved by an addition or removal across many nodes, and allows weighting "
            "bigger machines with more positions. Like plain hash sharding, it gives up "
            "efficient range scans.",
        ),
        _text(
            "Explique como funciona o consistent hashing, por que ele faz re-sharding melhor "
            "que `hash(key) % N` e o que os virtual nodes acrescentam.",
            "Autoavaliação: você mencionou (1) chaves e nós no mesmo anel de hash com "
            "propriedade no sentido horário, (2) que adicionar ou remover um nó move apenas "
            "cerca de 1/N das chaves e (3) virtual nodes suavizando a carga e distribuindo o "
            "rebalanceamento?",
            model_answer="Tanto os nós quanto as chaves recebem hash em um anel fixo (por "
            "exemplo, de 0 a 2^32-1). Uma chave pertence ao primeiro nó encontrado no sentido "
            "horário a partir da sua posição. Quando um nó é adicionado, ele assume apenas as "
            "chaves entre seu antecessor e ele mesmo, então cerca de 1/N das chaves se movem; "
            "quando um nó sai, só as chaves dele vão para o sucessor. Com hash(key) % N, mudar "
            "N muda o shard da maioria das chaves, forçando uma redistribuição quase total. "
            "Com uma única posição por nó, a carga pode ficar desigual e um nó que sai despeja "
            "tudo em um vizinho. Os virtual nodes dão a cada nó físico muitas posições no "
            "anel, o que equilibra a carga, distribui as chaves movidas por uma adição ou "
            "remoção entre muitos nós e permite dar peso maior a máquinas maiores. Como o "
            "sharding por hash simples, abre mão de consultas por faixa eficientes.",
        ),
    ),
)


_MAJORITY_CODE = """```python
def majority(n):
    return n // 2 + 1


# (cluster size, majority, failures tolerated)
print([(n, majority(n), n - majority(n)) for n in (3, 4, 5, 6)])
```"""


_CONSENSUS: tuple[QuestionSeed, ...] = (
    _q(
        "consensus-algorithms-q01",
        "consensus-algorithms",
        MC,
        EASY,
        ("b",),
        ("consensus", "replicated-log", "paxos", "raft"),
        _text(
            "What problem do consensus algorithms such as Paxos and Raft solve?",
            "Consensus lets a group of nodes agree on a single value, and in practice on a "
            "single ordered sequence of values (a replicated log), even when some nodes crash "
            "or messages are lost, as long as a majority can communicate. That is what makes "
            "replicated state machines possible. A is conflict merging after the fact, C is "
            "impossible, and D is partitioning.",
            "Letting any node accept writes and merging conflicting values afterwards using "
            "timestamps.",
            "Getting nodes to agree on one ordered sequence of values despite crashes and "
            "message loss, while a majority stays up.",
            "Guaranteeing that no node in the cluster ever crashes.",
            "Distributing keys evenly across the nodes of a cluster.",
        ),
        _text(
            "Que problema algoritmos de consenso como Paxos e Raft resolvem?",
            "O consenso permite que um grupo de nós concorde com um único valor e, na prática, "
            "com uma única sequência ordenada de valores (um log replicado), mesmo que alguns "
            "nós falhem ou mensagens se percam, desde que uma maioria consiga se comunicar. É o "
            "que torna possíveis as máquinas de estado replicadas. A é mesclagem de conflitos "
            "depois do fato, C é impossível e D é particionamento.",
            "Permitir que qualquer nó aceite escritas e mesclar depois os valores conflitantes "
            "usando timestamps.",
            "Fazer os nós concordarem sobre uma sequência ordenada de valores apesar de falhas "
            "e perda de mensagens, enquanto uma maioria continua ativa.",
            "Garantir que nenhum nó do cluster jamais falhe.",
            "Distribuir as chaves uniformemente entre os nós de um cluster.",
        ),
    ),
    _q(
        "consensus-algorithms-q02",
        "consensus-algorithms",
        MC,
        EASY,
        ("a",),
        ("raft", "leader-election", "terms"),
        _text(
            "In Raft, a follower does not hear from a leader before its election timeout "
            "expires. What does it do?",
            "It assumes the leader is gone, increments its term, becomes a candidate, votes for "
            "itself and requests votes from the other nodes; it becomes leader only if a "
            "majority grants them. It does not declare itself leader outright (B), and it "
            "neither shuts down (C) nor waits indefinitely for the old leader (D).",
            "It increments its term, becomes a candidate and requests votes from the other nodes.",
            "It declares itself the leader of the current term immediately.",
            "It shuts down until an operator restarts it.",
            "It keeps waiting for the old leader, since only the leader may start an election.",
        ),
        _text(
            "No Raft, um seguidor não ouve o líder antes de seu election timeout expirar. "
            "O que ele faz?",
            "Ele presume que o líder sumiu, incrementa seu term, vira candidato, vota em si "
            "mesmo e pede votos aos outros nós; só vira líder se uma maioria os conceder. Não se "
            "declara líder diretamente (B), não se desliga (C) nem espera indefinidamente pelo "
            "líder antigo (D).",
            "Incrementa seu term, vira candidato e pede votos aos outros nós.",
            "Declara-se imediatamente líder do term atual.",
            "Desliga-se até que um operador o reinicie.",
            "Continua esperando o líder antigo, pois só o líder pode iniciar uma eleição.",
        ),
    ),
    _q(
        "consensus-algorithms-q03",
        "consensus-algorithms",
        MC,
        EASY,
        ("c",),
        ("consensus", "quorum", "majority"),
        _text(
            "Why do consensus protocols require a **majority** (rather than just any "
            "particular set of nodes) to commit a decision?",
            "Any two majorities of the same cluster share at least one node. So a decision "
            "stored by one majority is known to at least one member of every later majority, "
            "which is what stops a later leader or decision from ignoring it. Majorities are not "
            "required for speed (A), do not pick the fastest node (B), and the argument does "
            "not depend on odd cluster sizes (D).",
            "A majority is the smallest group that can answer quickly enough.",
            "The majority always includes the fastest node, which then becomes leader.",
            "Any two majorities overlap in at least one node, so a committed decision cannot be "
            "missed by a later majority.",
            "Clusters must have an odd number of nodes for any vote to work.",
        ),
        _text(
            "Por que protocolos de consenso exigem uma **maioria** (e não um conjunto "
            "qualquer de nós) para confirmar uma decisão?",
            "Quaisquer duas maiorias do mesmo cluster compartilham ao menos um nó. Assim, uma "
            "decisão guardada por uma maioria é conhecida por ao menos um membro de toda "
            "maioria posterior, o que impede que um líder ou decisão posterior a ignore. A "
            "maioria não é exigida por velocidade (A), não escolhe o nó mais rápido (B) e o "
            "argumento não depende de o cluster ter tamanho ímpar (D).",
            "A maioria é o menor grupo capaz de responder rápido o bastante.",
            "A maioria sempre inclui o nó mais rápido, que então vira líder.",
            "Quaisquer duas maiorias se sobrepõem em ao menos um nó, então uma decisão "
            "confirmada não pode ser ignorada por uma maioria posterior.",
            "Os clusters precisam ter um número ímpar de nós para qualquer votação funcionar.",
        ),
    ),
    _q(
        "consensus-algorithms-q04",
        "consensus-algorithms",
        MC,
        MEDIUM,
        ("b",),
        ("raft", "availability", "quorum"),
        _text(
            "In a 5-node Raft cluster, 3 nodes crash and stay down. What is the state of the "
            "cluster?",
            "Electing a leader and committing entries both need a majority, which is 3 of 5 "
            "nodes. With only 2 alive, the cluster cannot make progress, but entries "
            "committed earlier are on a majority and so survive on the disk of nodes that "
            "come back. The 2 survivors are not a majority of the cluster (A), letting them "
            "write anyway (C) would risk diverging history, and nothing committed is lost (D).",
            "It continues normally, since the 2 survivors are a majority of the nodes still "
            "running.",
            "It cannot elect a leader or commit new entries until enough nodes return, but "
            "committed data is not lost.",
            "The 2 survivors elect a leader and accept writes, to be reconciled once the other "
            "nodes return.",
            "All data committed so far is lost, because most nodes are gone.",
        ),
        _text(
            "Em um cluster Raft de 5 nós, 3 nós caem e continuam fora. Qual é o estado do cluster?",
            "Eleger um líder e confirmar entradas exigem uma maioria, que é 3 de 5 nós. Com "
            "apenas 2 ativos, o cluster não consegue progredir, mas as entradas confirmadas "
            "antes estão em uma maioria e, portanto, sobrevivem no disco dos nós que "
            "voltarem. Os 2 sobreviventes não são uma maioria do cluster (A), deixá-los "
            "escrever mesmo assim (C) arriscaria divergir o histórico, e nada que foi "
            "confirmado se perde (D).",
            "Continua normalmente, pois os 2 sobreviventes são uma maioria dos nós que ainda "
            "estão rodando.",
            "Não consegue eleger líder nem confirmar novas entradas até que nós suficientes "
            "voltem, mas os dados confirmados não se perdem.",
            "Os 2 sobreviventes elegem um líder e aceitam escritas, a serem reconciliadas "
            "quando os outros nós voltarem.",
            "Todos os dados confirmados até agora se perdem, pois a maioria dos nós sumiu.",
        ),
    ),
    _q(
        "consensus-algorithms-q05",
        "consensus-algorithms",
        CODE,
        MEDIUM,
        ("c",),
        ("quorum", "cluster-size", "fault-tolerance"),
        _text(
            "What does this code print, and what does it suggest about choosing the size of a "
            "consensus cluster?\n\n" + _MAJORITY_CODE,
            "It prints `[(3, 2, 1), (4, 3, 1), (5, 3, 2), (6, 4, 2)]`. A 4-node cluster needs "
            "3 nodes for a majority, so it still tolerates only 1 failure, the same as 3 nodes; "
            "likewise 6 tolerates 2, the same as 5. Even sizes add cost without adding fault "
            "tolerance, so odd sizes are preferred. Option A shows the wrong output, B claims "
            "every extra node helps, and D confuses a majority with half of the nodes.",
            "`[(3, 2, 1), (4, 2, 2), (5, 3, 2), (6, 3, 3)]`: even-sized clusters tolerate more "
            "failures.",
            "`[(3, 2, 1), (4, 3, 1), (5, 3, 2), (6, 4, 2)]`: every extra node always increases "
            "the number of failures tolerated.",
            "`[(3, 2, 1), (4, 3, 1), (5, 3, 2), (6, 4, 2)]`: a 4-node cluster tolerates no more "
            "failures than a 3-node one, so odd sizes are preferred.",
            "`[(3, 2, 1), (4, 3, 1), (5, 3, 2), (6, 4, 2)]`: a majority is just half of the nodes.",
        ),
        _text(
            "O que este código imprime, e o que sugere sobre escolher o tamanho de um cluster "
            "de consenso?\n\n" + _MAJORITY_CODE,
            "Imprime `[(3, 2, 1), (4, 3, 1), (5, 3, 2), (6, 4, 2)]`. Um cluster de 4 nós precisa "
            "de 3 nós para a maioria, então ainda tolera só 1 falha, o mesmo que 3 nós; do mesmo "
            "modo, 6 tolera 2, o mesmo que 5. Tamanhos pares acrescentam custo sem acrescentar "
            "tolerância a falhas, por isso se preferem tamanhos ímpares. A opção A mostra a "
            "saída errada, B afirma que mais nós sempre ajudam, e D confunde maioria com "
            "metade.",
            "`[(3, 2, 1), (4, 2, 2), (5, 3, 2), (6, 3, 3)]`: clusters de tamanho par toleram "
            "mais falhas.",
            "`[(3, 2, 1), (4, 3, 1), (5, 3, 2), (6, 4, 2)]`: todo nó extra sempre aumenta o "
            "número de falhas toleradas.",
            "`[(3, 2, 1), (4, 3, 1), (5, 3, 2), (6, 4, 2)]`: um cluster de 4 nós não tolera mais "
            "falhas que um de 3, por isso se preferem tamanhos ímpares.",
            "`[(3, 2, 1), (4, 3, 1), (5, 3, 2), (6, 4, 2)]`: uma maioria é apenas metade dos nós.",
        ),
    ),
    _q(
        "consensus-algorithms-q06",
        "consensus-algorithms",
        MC,
        MEDIUM,
        ("b",),
        ("raft", "election-timeout", "split-votes"),
        _text(
            "Why does Raft randomize each node's election timeout?",
            "If all followers used the same timeout they would all become candidates at the "
            "same moment and split the votes, again and again. Randomization makes it likely "
            "that one node times out first and wins before the others even start. It does not "
            "guarantee that the most up-to-date node goes first (A); log freshness is enforced "
            "by the voting rule instead. Security (C) and read distribution (D) are not goals "
            "of this mechanism.",
            "To guarantee that the node with the most complete log always times out first.",
            "So one node usually times out first and wins the election, avoiding repeated "
            "split votes.",
            "To make the leader's heartbeats unpredictable to attackers.",
            "To spread read traffic evenly across the followers.",
        ),
        _text(
            "Por que o Raft randomiza o election timeout de cada nó?",
            "Se todos os seguidores usassem o mesmo timeout, todos virariam candidatos no mesmo "
            "instante e dividiriam os votos, repetidamente. A randomização faz com que um nó "
            "provavelmente expire primeiro e vença antes de os demais sequer começarem. Ela "
            "não garante que o nó mais atualizado saia primeiro (A); o frescor do log é "
            "garantido pela regra de votação. Segurança contra atacantes (C) e distribuição de "
            "leituras (D) não são objetivos desse mecanismo.",
            "Para garantir que o nó com o log mais completo sempre expire primeiro.",
            "Para que um nó em geral expire primeiro e vença a eleição, evitando votos "
            "divididos repetidos.",
            "Para tornar os heartbeats do líder imprevisíveis para atacantes.",
            "Para distribuir uniformemente o tráfego de leitura entre os seguidores.",
        ),
    ),
    _q(
        "consensus-algorithms-q07",
        "consensus-algorithms",
        MC,
        MEDIUM,
        ("d",),
        ("raft", "partitions", "leader-election"),
        _text(
            "A 5-node Raft cluster is partitioned into a group of 3 and a group of 2, and the "
            "old leader is in the group of 2. What happens?",
            "The group of 3 has a majority, so it elects a new leader in a higher term and keeps "
            "committing. The old leader cannot get a majority to acknowledge anything, so "
            "nothing it accepts is committed; once the partition heals, it sees the higher "
            "term, steps down and discards its uncommitted entries. A is impossible because the "
            "group of 2 cannot commit, B would let uncommitted data become visible as committed, "
            "and C is too pessimistic because the majority side stays available.",
            "Both groups keep committing writes and reconcile them when the partition heals.",
            "The old leader keeps committing writes in its group of 2 and the other group "
            "copies them later.",
            "The whole cluster halts until the partition heals.",
            "The group of 3 elects a new leader and continues; the old leader cannot commit "
            "anything and steps down after the partition heals.",
        ),
        _text(
            "Um cluster Raft de 5 nós é particionado em um grupo de 3 e um grupo de 2, e o "
            "líder antigo está no grupo de 2. O que acontece?",
            "O grupo de 3 tem maioria, então elege um novo líder em um term maior e continua "
            "confirmando. O líder antigo não consegue que uma maioria reconheça nada, então "
            "nada que ele aceita é confirmado; quando a partição se resolve, ele vê o term "
            "maior, renuncia e descarta suas entradas não confirmadas. A é impossível porque o "
            "grupo de 2 não consegue confirmar, B tornaria dados não confirmados visíveis "
            "como confirmados, e C é pessimista demais, pois o lado majoritário continua "
            "disponível.",
            "Os dois grupos continuam confirmando escritas e as reconciliam quando a partição "
            "se resolve.",
            "O líder antigo continua confirmando escritas em seu grupo de 2 e o outro grupo as "
            "copia depois.",
            "O cluster inteiro para até a partição se resolver.",
            "O grupo de 3 elege um novo líder e continua; o líder antigo não consegue "
            "confirmar nada e renuncia depois que a partição se resolve.",
        ),
    ),
    _q(
        "consensus-algorithms-q08",
        "consensus-algorithms",
        MS,
        MEDIUM,
        ("a", "c", "d"),
        ("raft", "commit", "voting"),
        _text(
            "Which statements about Raft are **correct**? Select all that apply.",
            "A, C and D are correct. An entry is committed once a majority has durably stored "
            "it, a node votes for at most one candidate per term, and it only votes for "
            "candidates whose log is at least as up to date as its own. B is wrong: waiting "
            "for every follower would let one slow node block progress. E is wrong: the "
            "voting rule means a new leader already has every committed entry, so it never "
            "overwrites committed data.",
            "A leader treats an entry as committed once a majority of nodes, including "
            "itself, have durably stored it.",
            "A leader must wait until every follower has stored an entry before committing it.",
            "A node grants at most one vote in any given term.",
            "A node only votes for a candidate whose log is at least as up to date as its own.",
            "A newly elected leader may overwrite committed entries if its term is higher.",
        ),
        _text(
            "Quais afirmações sobre o Raft estão **corretas**? Selecione todas que se aplicam.",
            "A, C e D estão corretas. Uma entrada é confirmada quando uma maioria a guardou de "
            "forma durável, um nó vota em no máximo um candidato por term e só vota em "
            "candidatos cujo log esteja pelo menos tão atualizado quanto o seu. B está errada: "
            "esperar todos os seguidores deixaria um nó lento bloquear o progresso. E está "
            "errada: pela regra de votação, um novo líder já tem todas as entradas "
            "confirmadas, então nunca sobrescreve dados confirmados.",
            "Um líder considera uma entrada confirmada quando uma maioria dos nós, incluindo "
            "ele mesmo, a guardou de forma durável.",
            "Um líder precisa esperar todos os seguidores guardarem uma entrada antes de "
            "confirmá-la.",
            "Um nó concede no máximo um voto em um dado term.",
            "Um nó só vota em um candidato cujo log esteja pelo menos tão atualizado quanto o seu.",
            "Um líder recém-eleito pode sobrescrever entradas confirmadas se seu term for maior.",
        ),
    ),
    _q(
        "consensus-algorithms-q09",
        "consensus-algorithms",
        MC,
        HARD,
        ("c",),
        ("raft", "safety", "election-restriction"),
        _text(
            "In Raft, a node refuses to vote for a candidate whose log is less up to date than "
            "its own. What does this rule guarantee, and why?",
            "A committed entry is stored on a majority, and a candidate needs votes from a "
            "majority, so at least one voter holds every committed entry and would refuse a "
            "candidate that lacks it. Hence every elected leader already has all committed "
            "entries. It does not choose the fastest node (A), cannot prevent split votes (B; "
            "randomized timeouts address those), and uncommitted entries can still be lost (D).",
            "It guarantees the leader is the node with the lowest network latency.",
            "It guarantees that split votes can never happen.",
            "It guarantees that every elected leader already holds all committed entries, "
            "because the voting majority overlaps the majority that stored each one.",
            "It guarantees that no entry, even an uncommitted one, is ever lost.",
        ),
        _text(
            "No Raft, um nó se recusa a votar em um candidato cujo log esteja menos atualizado "
            "que o seu. O que essa regra garante, e por quê?",
            "Uma entrada confirmada está guardada em uma maioria, e um candidato precisa de "
            "votos de uma maioria; logo, ao menos um votante tem todas as entradas confirmadas "
            "e recusaria um candidato que não as tenha. Assim, todo líder eleito já possui "
            "todas as entradas confirmadas. A regra não escolhe o nó mais rápido (A), não "
            "impede votos divididos (B; os timeouts randomizados cuidam disso) e entradas "
            "não confirmadas ainda podem ser perdidas (D).",
            "Garante que o líder é o nó com a menor latência de rede.",
            "Garante que votos divididos nunca aconteçam.",
            "Garante que todo líder eleito já possua todas as entradas confirmadas, pois a "
            "maioria votante se sobrepõe à maioria que guardou cada uma delas.",
            "Garante que nenhuma entrada, mesmo não confirmada, jamais seja perdida.",
        ),
    ),
    _q(
        "consensus-algorithms-q10",
        "consensus-algorithms",
        SHORT,
        HARD,
        None,
        ("consensus", "distributed-lock", "leader-election", "fencing", "interview"),
        _text(
            "Your team needs exactly one instance of a scheduler to be active across five "
            "machines. A colleague proposes a row in the shared database with an owner and a "
            "timestamp that instances check every few seconds. Why is this fragile, what would "
            "you use instead, and what problem remains even then?",
            "Self-check: did you mention (1) races and clock/failure problems of the naive "
            "check, (2) a consensus-backed store (etcd, ZooKeeper, Consul) with leases or "
            "ephemeral nodes, and (3) the paused-holder problem and fencing tokens?",
            model_answer="A check-then-act on a row is fragile: two instances can read the row "
            "as free at nearly the same time, expiry based on timestamps and local clocks can "
            "misfire, and if the database itself is replicated with failover or partitioned, "
            "it has no principled guarantee that only one owner exists. I would use a "
            "consensus-backed coordination service such as etcd, ZooKeeper or Consul: a "
            "lease, ephemeral node or session acquired with an atomic compare-and-set on a "
            "linearizable store, which expires if the holder stops renewing it and which "
            "keeps working correctly through crashes and partitions as long as a majority is "
            "up. What remains is the paused-holder problem: a holder that stalls (for example "
            "a long GC pause) can wake up after its lease expired and still act as the "
            "leader. So the protected resource should also check a fencing token, a "
            "monotonically increasing number issued with each lease, and reject writes from "
            "older tokens; making the work idempotent adds more safety.",
        ),
        _text(
            "Sua equipe precisa que exatamente uma instância de um scheduler esteja ativa entre "
            "cinco máquinas. Um colega propõe uma linha no banco compartilhado com um dono e um "
            "timestamp que as instâncias verificam a cada poucos segundos. Por que isso é "
            "frágil, o que você usaria no lugar e que problema ainda permanece?",
            "Autoavaliação: você mencionou (1) as condições de corrida e os problemas de "
            "relógio/falha da verificação ingênua, (2) um armazenamento com consenso (etcd, "
            "ZooKeeper, Consul) com leases ou nós efêmeros e (3) o problema do detentor pausado "
            "e os fencing tokens?",
            model_answer="Um check-then-act em uma linha é frágil: duas instâncias podem ler a "
            "linha como livre quase ao mesmo tempo, a expiração baseada em timestamps e "
            "relógios locais pode falhar e, se o próprio banco tem replicação com failover ou "
            "sofre uma partição, não há garantia de princípio de que exista um único dono. "
            "Eu usaria um serviço de coordenação baseado em consenso, como etcd, ZooKeeper ou "
            "Consul: um lease, nó efêmero ou sessão obtido com um compare-and-set atômico em um "
            "armazenamento linearizável, que expira se o detentor parar de renová-lo e que "
            "continua correto diante de falhas e partições enquanto uma maioria estiver ativa. "
            "O que resta é o problema do detentor pausado: quem trava (por exemplo, numa longa "
            "pausa de GC) pode acordar depois que o lease expirou e ainda agir como líder. Por "
            "isso o recurso protegido também deve verificar um fencing token, um número "
            "monotonicamente crescente emitido a cada lease, e rejeitar escritas de tokens "
            "mais antigos; tornar o trabalho idempotente acrescenta mais segurança.",
        ),
    ),
)


_QUESTIONS: tuple[QuestionSeed, ...] = (*_CAP, *_REPL, *_SHARD, *_CONSENSUS)

_ASSESSMENTS: tuple[AssessmentSeed, ...] = (
    AssessmentSeed(
        code="distributed-systems-cap-theorem-quiz",
        title="CAP Theorem Quiz",
        description="What CAP really says, consistency and availability defined precisely, "
        "and PACELC.",
        kind=AssessmentKind.COMPETENCY,
        competency_slug="cap-theorem",
        translations={
            "pt-BR": {
                "title": "Quiz do Teorema CAP",
                "description": "O que o CAP realmente diz, consistência e disponibilidade "
                "definidas com precisão, e PACELC.",
            }
        },
    ),
    AssessmentSeed(
        code="distributed-systems-replication-quiz",
        title="Replication Quiz",
        description="Sync vs async, replication lag, failover, split-brain and quorums.",
        kind=AssessmentKind.COMPETENCY,
        competency_slug="replication",
        translations={
            "pt-BR": {
                "title": "Quiz de Replicação",
                "description": "Síncrona vs assíncrona, replication lag, failover, split-brain "
                "e quóruns.",
            }
        },
    ),
    AssessmentSeed(
        code="distributed-systems-partitioning-sharding-quiz",
        title="Partitioning & Sharding Quiz",
        description="Hash, range and directory sharding, shard keys, secondary indexes and "
        "consistent hashing.",
        kind=AssessmentKind.COMPETENCY,
        competency_slug="partitioning-sharding",
        translations={
            "pt-BR": {
                "title": "Quiz de Particionamento e Sharding",
                "description": "Sharding por hash, faixa e diretório, shard keys, índices "
                "secundários e consistent hashing.",
            }
        },
    ),
    AssessmentSeed(
        code="distributed-systems-consensus-algorithms-quiz",
        title="Consensus Algorithms Quiz",
        description="Majorities, Raft elections and log replication, safety and where "
        "consensus is used.",
        kind=AssessmentKind.COMPETENCY,
        competency_slug="consensus-algorithms",
        translations={
            "pt-BR": {
                "title": "Quiz de Algoritmos de Consenso",
                "description": "Maiorias, eleições e replicação de log no Raft, segurança e "
                "onde o consenso é usado.",
            }
        },
    ),
    AssessmentSeed(
        code="distributed-systems-checkpoint",
        title="Distributed Systems Checkpoint",
        description="A mixed check across CAP, replication, sharding and consensus.",
        kind=AssessmentKind.MIXED,
        question_codes=(
            "cap-theorem-q03",
            "cap-theorem-q07",
            "cap-theorem-q09",
            "replication-q04",
            "replication-q06",
            "replication-q08",
            "partitioning-sharding-q06",
            "partitioning-sharding-q09",
            "consensus-algorithms-q07",
            "consensus-algorithms-q09",
        ),
        translations={
            "pt-BR": {
                "title": "Checkpoint de Sistemas Distribuídos",
                "description": "Uma verificação mista entre CAP, replicação, sharding e consenso.",
            }
        },
        pass_threshold=75,
        completion_bonus_xp=40,
    ),
)


QUESTION_SET = SubjectQuestionSet(
    subject_slug="distributed-systems",
    questions=_QUESTIONS,
    assessments=_ASSESSMENTS,
)
