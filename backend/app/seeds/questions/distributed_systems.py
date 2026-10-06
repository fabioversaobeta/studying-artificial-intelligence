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
            "The service is up a very high percentage of the time (for example 99.99%).",
            "Every request returns the result of the most recent write.",
            "Every request is answered within the latency target of the service.",
            "Every request to a non-failing node receives a non-error response, though not "
            "necessarily one reflecting the latest write.",
        ),
        _text(
            "Na formulação formal do teorema CAP, o que significa **disponibilidade** "
            "(availability)?",
            "A disponibilidade do CAP é uma garantia por requisição: toda requisição enviada a "
            "um nó que não falhou deve receber uma resposta sem erro. A resposta pode estar "
            "desatualizada. Não é um percentual de uptime (A), não promete a última escrita "
            "(B; isso é consistência) e o teorema não define limite de latência (C).",
            "O serviço fica no ar uma porcentagem altíssima do tempo (por exemplo, 99,99%).",
            "Toda requisição retorna o resultado da escrita mais recente.",
            "Toda requisição é respondida dentro da meta de latência do serviço.",
            "Toda requisição a um nó que não falhou recebe uma resposta sem erro, embora "
            "não necessariamente refletindo a última escrita.",
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
            "It rejects or times out requests that it cannot guarantee are consistent until the "
            "partition heals.",
            "It keeps accepting writes and merges them with the other data centers afterwards.",
            "It keeps answering reads from its local, possibly stale, copy of the data.",
            "It acknowledges writes immediately and replicates them whenever the network returns.",
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
            "Continua aceitando escritas e as mescla com os outros data centers depois.",
            "Continua respondendo leituras a partir da sua cópia local, possivelmente "
            "desatualizada.",
            "Confirma as escritas imediatamente e as replica quando a rede voltar.",
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
            "CAP consistency means reads see the latest write as if there were one copy of the "
            "data; ACID consistency means a transaction preserves the database's invariants.",
            "CAP consistency means replicas converge eventually; ACID consistency means reads "
            "see the latest write.",
            "CAP consistency is about durability on disk; ACID consistency is about isolation "
            "between transactions.",
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
            "No CAP, consistência significa que as leituras veem a última escrita como se "
            "houvesse uma só cópia dos dados; no ACID, que uma transação preserva as "
            "invariantes do banco.",
            "No CAP, consistência significa que as réplicas convergem com o tempo; no ACID, "
            "que as leituras veem a última escrita.",
            "No CAP, consistência trata de durabilidade em disco; no ACID, de isolamento entre "
            "transações.",
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
            "synchronous versus asynchronous replication.",
            "The trade-off between latency and consistency while a partition is happening.",
            "The trade-off between storage cost and durability when there is no partition.",
            "The trade-off between availability and consistency when there is no partition.",
        ),
        _text(
            'A formulação PACELC acrescenta uma cláusula "ELC" ao CAP. O que ela descreve?',
            "O PACELC diz: se há Partição, escolha Disponibilidade ou Consistência; Senão (sem "
            "partição), escolha Latência ou Consistência. Mesmo em uma rede saudável, a "
            "replicação síncrona compra mais consistência ao custo de latência, e a assíncrona "
            "faz o oposto. B inverte os papéis das cláusulas, C não é um trade-off do PACELC e "
            "D descreve a própria cláusula do CAP.",
            "O trade-off entre latência e consistência quando não há partição, como replicação "
            "síncrona versus assíncrona.",
            "O trade-off entre latência e consistência enquanto uma partição está ocorrendo.",
            "O trade-off entre custo de armazenamento e durabilidade quando não há partição.",
            "O trade-off entre disponibilidade e consistência quando não há partição.",
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


_QUESTIONS: tuple[QuestionSeed, ...] = (*_CAP,)

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
)


QUESTION_SET = SubjectQuestionSet(
    subject_slug="distributed-systems",
    questions=_QUESTIONS,
    assessments=_ASSESSMENTS,
)
