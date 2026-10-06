"""Question bank for the Python subject (pilot set: python-fundamentals and
type-hints, six questions each, English + Brazilian Portuguese).

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


def _options(*pairs: str) -> tuple[OptionSeed, ...]:
    """_options("text a", "text b", ...) -> options with ids a, b, c..."""
    return tuple(OptionSeed(id=chr(ord("a") + i), text=text) for i, text in enumerate(pairs))


_MUTABLE_DEFAULT_CODE = """```python
def collect(items=[]):
    items.append(1)
    return items

print(collect(), collect())
```"""

_WITH_CODE = """```python
class Timer:
    def __enter__(self):
        print("enter")
        return self

    def __exit__(self, exc_type, exc, tb):
        print("exit")
        return False

with Timer():
    raise ValueError("boom")
```"""

_PROTOCOL_CODE = """```python
from typing import Protocol

class Closeable(Protocol):
    def close(self) -> None: ...

class File:
    def close(self) -> None: ...

class Socket:
    def close(self, force: bool) -> None: ...

def shutdown(resource: Closeable) -> None:
    resource.close()

shutdown(File())     # call 1
shutdown(Socket())   # call 2
```"""

_RETURN_CODE = """```python
def first(items: list[int]) -> int:
    return items[0] if items else None
```"""


QUESTIONS: tuple[QuestionSeed, ...] = (
    # ------------------------------------------------------------------
    # python-fundamentals
    # ------------------------------------------------------------------
    QuestionSeed(
        code="python-fundamentals-q01",
        competency_slug="python-fundamentals",
        type=MC,
        difficulty=EASY,
        correct=("c",),
        tags=("comprehensions",),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="Which expression builds a **list** with the squares of the even numbers "
                "from 0 to 9?",
                options=_options(
                    "`[x * x if x % 2 == 0 for x in range(10)]`",
                    "`(x * x for x in range(10) if x % 2 == 0)`",
                    "`[x * x for x in range(10) if x % 2 == 0]`",
                    "`{x * x for x in range(10) if x % 2 == 0}`",
                ),
                explanation="In a comprehension the filter goes at the end (`for ... if ...`). "
                "Option A is a syntax error (a bare `if` before the `for` needs an `else`), "
                "B builds a generator, and D builds a set, not a list.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Qual expressão constrói uma **lista** com os quadrados dos números pares "
                "de 0 a 9?",
                options=_options(
                    "`[x * x if x % 2 == 0 for x in range(10)]`",
                    "`(x * x for x in range(10) if x % 2 == 0)`",
                    "`[x * x for x in range(10) if x % 2 == 0]`",
                    "`{x * x for x in range(10) if x % 2 == 0}`",
                ),
                explanation="Em uma comprehension o filtro vai no final (`for ... if ...`). "
                "A opção A é um erro de sintaxe (um `if` solto antes do `for` exige `else`), "
                "a B cria um generator e a D cria um conjunto (set), não uma lista.",
            ),
        },
    ),
    QuestionSeed(
        code="python-fundamentals-q02",
        competency_slug="python-fundamentals",
        type=MC,
        difficulty=EASY,
        correct=("b",),
        tags=("generators", "memory"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="What is the main difference between `sum([x * x for x in range(10**7)])` "
                "and `sum(x * x for x in range(10**7))`?",
                options=_options(
                    "The second one is a syntax error because `sum` needs a list.",
                    "The second one produces the values lazily, one at a time, instead of "
                    "building a ten-million-element list in memory first.",
                    "The first one is lazy and the second one is eager.",
                    "There is no difference; both build the full list internally.",
                ),
                explanation="A generator expression yields items on demand, so `sum` consumes "
                "them without ever materializing the whole sequence. The list comprehension "
                "builds the full list first (a lot of memory), then sums it.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Qual é a principal diferença entre `sum([x * x for x in range(10**7)])` "
                "e `sum(x * x for x in range(10**7))`?",
                options=_options(
                    "A segunda é um erro de sintaxe, pois `sum` exige uma lista.",
                    "A segunda produz os valores sob demanda, um de cada vez, em vez de "
                    "construir antes uma lista de dez milhões de elementos na memória.",
                    "A primeira é preguiçosa (lazy) e a segunda é ansiosa (eager).",
                    "Não há diferença; ambas constroem a lista completa internamente.",
                ),
                explanation="Uma generator expression entrega os itens sob demanda, então `sum` "
                "os consome sem nunca materializar a sequência inteira. A list comprehension "
                "constrói a lista completa primeiro (muita memória) e só depois soma.",
            ),
        },
    ),
    QuestionSeed(
        code="python-fundamentals-q03",
        competency_slug="python-fundamentals",
        type=MS,
        difficulty=MEDIUM,
        correct=("a", "c", "d"),
        tags=("truthiness",),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="Which of these values are **falsy** (evaluate to `False` in a boolean "
                "context)? Select all that apply.",
                options=_options("`[]`", '`"0"`', "`0.0`", "`{}`", '`" "` (a single space)'),
                explanation="Empty containers and numeric zeros are falsy: `[]`, `{}` and `0.0`. "
                'Any non-empty string is truthy, including `"0"` and `" "`.',
            ),
            Language.PT_BR: QuestionText(
                prompt="Quais destes valores são **falsy** (avaliam como `False` em um contexto "
                "booleano)? Selecione todos que se aplicam.",
                options=_options("`[]`", '`"0"`', "`0.0`", "`{}`", '`" "` (um único espaço)'),
                explanation="Contêineres vazios e zeros numéricos são falsy: `[]`, `{}` e `0.0`. "
                'Qualquer string não vazia é truthy, inclusive `"0"` e `" "`.',
            ),
        },
    ),
    QuestionSeed(
        code="python-fundamentals-q04",
        competency_slug="python-fundamentals",
        type=CODE,
        difficulty=MEDIUM,
        correct=("a",),
        tags=("context-managers", "exceptions"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="What happens when this code runs?\n\n" + _WITH_CODE,
                options=_options(
                    "It prints `enter`, then `exit`, and then the `ValueError` propagates.",
                    "It prints `enter` only; `__exit__` is not called because of the exception.",
                    "It prints `enter` and `exit`, and the `ValueError` is silently swallowed.",
                    "It raises a `SyntaxError` because `__exit__` must not return a value.",
                ),
                explanation="`__exit__` is always called when the block ends, even on an "
                "exception. It receives the exception details, and only a truthy return value "
                "suppresses the exception. This one returns `False`, so the `ValueError` "
                "continues to propagate after `exit` is printed.",
            ),
            Language.PT_BR: QuestionText(
                prompt="O que acontece quando este código é executado?\n\n" + _WITH_CODE,
                options=_options(
                    "Imprime `enter`, depois `exit`, e então o `ValueError` se propaga.",
                    "Imprime só `enter`; `__exit__` não é chamado por causa da exceção.",
                    "Imprime `enter` e `exit`, e o `ValueError` é silenciosamente engolido.",
                    "Lança um `SyntaxError`, pois `__exit__` não pode retornar um valor.",
                ),
                explanation="`__exit__` é sempre chamado quando o bloco termina, mesmo com "
                "exceção. Ele recebe os detalhes da exceção, e somente um retorno verdadeiro "
                "(truthy) a suprime. Este retorna `False`, então o `ValueError` continua se "
                "propagando depois de imprimir `exit`.",
            ),
        },
    ),
    QuestionSeed(
        code="python-fundamentals-q05",
        competency_slug="python-fundamentals",
        type=CODE,
        difficulty=HARD,
        correct=("c",),
        tags=("functions", "mutable-default"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="What does this code print?\n\n" + _MUTABLE_DEFAULT_CODE,
                options=_options(
                    "`[1] [1]`",
                    "`[1] [1, 1]`",
                    "`[1, 1] [1, 1]`",
                    "`[1, 1] [1]`",
                ),
                explanation="The default value `[]` is created once, when the function is "
                "defined, and shared by every call that omits the argument. Both calls "
                "therefore return the very same list object. `print` only runs after both "
                "calls finished, so that single list already holds two items and is printed "
                "twice. Use `items=None` and create the list inside the function.",
            ),
            Language.PT_BR: QuestionText(
                prompt="O que este código imprime?\n\n" + _MUTABLE_DEFAULT_CODE,
                options=_options(
                    "`[1] [1]`",
                    "`[1] [1, 1]`",
                    "`[1, 1] [1, 1]`",
                    "`[1, 1] [1]`",
                ),
                explanation="O valor padrão `[]` é criado uma única vez, quando a função é "
                "definida, e compartilhado por toda chamada que omite o argumento. Assim, as "
                "duas chamadas retornam exatamente o mesmo objeto lista. O `print` só executa "
                "depois que ambas terminaram, então essa lista única já tem dois itens e é "
                "impressa duas vezes. Use `items=None` e crie a lista dentro da função.",
            ),
        },
    ),
    QuestionSeed(
        code="python-fundamentals-q06",
        competency_slug="python-fundamentals",
        type=SHORT,
        difficulty=MEDIUM,
        correct=None,
        tags=("context-managers",),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="In your own words: what problem does the `with` statement solve, and what "
                "does `__exit__` receive and return?",
                model_answer="`with` guarantees that setup/cleanup code runs deterministically: "
                "`__exit__` is called when the block ends, whether it finished normally or "
                "raised, so resources (files, locks, connections) are always released without "
                "scattering try/finally. `__exit__(exc_type, exc, tb)` receives the exception "
                "type, value and traceback (all `None` if there was no exception). If it "
                "returns a truthy value the exception is suppressed; otherwise it propagates.",
                explanation="Self-check against the model answer: did you mention (1) guaranteed "
                "cleanup even on exceptions, (2) the three exception arguments, and (3) that a "
                "truthy return suppresses the exception?",
            ),
            Language.PT_BR: QuestionText(
                prompt="Com suas palavras: que problema a instrução `with` resolve, e o que "
                "`__exit__` recebe e retorna?",
                model_answer="`with` garante que o código de preparação e de limpeza execute de "
                "forma determinística: `__exit__` é chamado quando o bloco termina, tenha ele "
                "acabado normalmente ou lançado uma exceção, então recursos (arquivos, locks, "
                "conexões) são sempre liberados sem espalhar try/finally. "
                "`__exit__(exc_type, exc, tb)` recebe o tipo, o valor e o traceback da exceção "
                "(todos `None` se não houve exceção). Se retornar um valor verdadeiro (truthy) "
                "a exceção é suprimida; caso contrário ela se propaga.",
                explanation="Autoavaliação contra a resposta-modelo: você mencionou (1) a "
                "limpeza garantida mesmo com exceções, (2) os três argumentos da exceção e "
                "(3) que um retorno truthy suprime a exceção?",
            ),
        },
    ),
    # ------------------------------------------------------------------
    # type-hints
    # ------------------------------------------------------------------
    QuestionSeed(
        code="python-type-hints-q01",
        competency_slug="type-hints",
        type=MC,
        difficulty=EASY,
        correct=("b",),
        tags=("basics", "runtime"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="Does a wrong type hint, such as passing a `str` to a parameter annotated "
                "`int`, make the Python interpreter raise an error at runtime?",
                options=_options(
                    "Yes, Python always raises `TypeError` when an annotation is violated.",
                    "No, annotations are not enforced by the interpreter; they are checked by "
                    "external tools such as mypy or pyright.",
                    "Only when Python is run with the `-O` flag.",
                    "Only for function parameters, never for variable annotations.",
                ),
                explanation="Python is still dynamically typed: annotations are metadata. The "
                "interpreter ignores them when running the code (libraries such as pydantic "
                "may read them to validate data, but that is their own logic). Static checkers "
                "verify them before the code runs.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Uma anotação de tipo errada, como passar uma `str` para um parâmetro "
                "anotado como `int`, faz o interpretador Python lançar um erro em tempo de "
                "execução?",
                options=_options(
                    "Sim, o Python sempre lança `TypeError` quando uma anotação é violada.",
                    "Não, as anotações não são impostas pelo interpretador; elas são "
                    "verificadas por ferramentas externas como mypy ou pyright.",
                    "Somente quando o Python roda com a flag `-O`.",
                    "Somente para parâmetros de função, nunca para anotações de variáveis.",
                ),
                explanation="O Python continua sendo dinamicamente tipado: anotações são "
                "metadados. O interpretador as ignora ao executar o código (bibliotecas como "
                "pydantic podem lê-las para validar dados, mas isso é lógica delas). "
                "Verificadores estáticos as conferem antes de o código rodar.",
            ),
        },
    ),
    QuestionSeed(
        code="python-type-hints-q02",
        competency_slug="type-hints",
        type=MC,
        difficulty=EASY,
        correct=("a",),
        tags=("optional", "union"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="In Python 3.10+, which is the modern way to annotate a parameter that may "
                "be a `str` or `None`?",
                options=_options(
                    "`name: str | None`",
                    "`name: str or None`",
                    "`name: Union[str]`",
                    "`name: Nullable[str]`",
                ),
                explanation="Since 3.10 unions are written with `|`, so `str | None` is the "
                "idiomatic spelling (equivalent to `Optional[str]`). `str or None` is an "
                "ordinary expression that evaluates to `str`, `Union[str]` collapses to plain "
                "`str`, and there is no `Nullable` in `typing`.",
            ),
            Language.PT_BR: QuestionText(
                prompt="No Python 3.10+, qual é a forma moderna de anotar um parâmetro que pode "
                "ser `str` ou `None`?",
                options=_options(
                    "`name: str | None`",
                    "`name: str or None`",
                    "`name: Union[str]`",
                    "`name: Nullable[str]`",
                ),
                explanation="Desde a 3.10 as uniões se escrevem com `|`, então `str | None` é a "
                "forma idiomática (equivalente a `Optional[str]`). `str or None` é uma "
                "expressão comum que resulta em `str`, `Union[str]` se reduz a apenas `str`, e "
                "não existe `Nullable` em `typing`.",
            ),
        },
    ),
    QuestionSeed(
        code="python-type-hints-q03",
        competency_slug="type-hints",
        type=MC,
        difficulty=MEDIUM,
        correct=("c",),
        tags=("protocol", "structural-typing"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="When does a class satisfy a `typing.Protocol` for a type checker?",
                options=_options(
                    "Only when it explicitly inherits from the protocol class.",
                    "Only when it is registered with `Protocol.register()`.",
                    "When it provides the attributes and methods the protocol declares, with "
                    "compatible signatures, even without inheriting from it.",
                    "When its name matches the name of the protocol.",
                ),
                explanation="Protocols use structural typing (static duck typing): what matters "
                "is the shape of the class, not its ancestry. Explicit inheritance is optional. "
                "Registration is an `abc.ABC` virtual-subclass concept, and names are irrelevant.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Quando uma classe satisfaz um `typing.Protocol` para um verificador de "
                "tipos?",
                options=_options(
                    "Somente quando herda explicitamente da classe do protocolo.",
                    "Somente quando é registrada com `Protocol.register()`.",
                    "Quando fornece os atributos e métodos que o protocolo declara, com "
                    "assinaturas compatíveis, mesmo sem herdar dele.",
                    "Quando seu nome é igual ao nome do protocolo.",
                ),
                explanation="Protocolos usam tipagem estrutural (duck typing estático): o que "
                "importa é o formato da classe, não sua ancestralidade. A herança explícita é "
                "opcional. Registro é um conceito de subclasse virtual de `abc.ABC`, e nomes "
                "são irrelevantes.",
            ),
        },
    ),
    QuestionSeed(
        code="python-type-hints-q04",
        competency_slug="type-hints",
        type=CODE,
        difficulty=MEDIUM,
        correct=("b",),
        tags=("mypy", "none"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="What does `mypy` report for this function?\n\n" + _RETURN_CODE,
                options=_options(
                    "Nothing: `None` is a valid value for every type.",
                    "An error: incompatible return value type (got `None`, expected `int`).",
                    "An error: `list[int]` is not valid before Python 3.12.",
                    "A warning that `items[0]` may raise `IndexError`.",
                ),
                explanation="The conditional expression returns `None` when `items` is empty, "
                "but the declared return type is `int`, so mypy flags an incompatible return "
                "value. The fix is to annotate `-> int | None` (and handle `None` in callers) "
                "or to raise instead of returning `None`.",
            ),
            Language.PT_BR: QuestionText(
                prompt="O que o `mypy` reporta para esta função?\n\n" + _RETURN_CODE,
                options=_options(
                    "Nada: `None` é um valor válido para qualquer tipo.",
                    "Um erro: tipo de retorno incompatível (recebeu `None`, esperado `int`).",
                    "Um erro: `list[int]` não é válido antes do Python 3.12.",
                    "Um aviso de que `items[0]` pode lançar `IndexError`.",
                ),
                explanation="A expressão condicional retorna `None` quando `items` está vazia, "
                "mas o tipo de retorno declarado é `int`; por isso o mypy aponta um valor de "
                "retorno incompatível. A correção é anotar `-> int | None` (e tratar `None` "
                "nos chamadores) ou lançar uma exceção em vez de retornar `None`.",
            ),
        },
    ),
    QuestionSeed(
        code="python-type-hints-q05",
        competency_slug="type-hints",
        type=CODE,
        difficulty=HARD,
        correct=("b",),
        tags=("protocol", "signatures"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="Which of the two calls does a type checker accept?\n\n" + _PROTOCOL_CODE,
                options=_options(
                    "Both calls.",
                    "Only call 1 (`File`).",
                    "Only call 2 (`Socket`).",
                    "Neither: `File` and `Socket` do not inherit from `Closeable`.",
                ),
                explanation="Protocol matching is structural, so inheritance is not required "
                "(rules out D). `File.close()` matches `close() -> None`. `Socket.close` needs "
                "an extra required argument, so its signature is incompatible and the checker "
                "rejects call 2.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Qual das duas chamadas um verificador de tipos aceita?\n\n"
                + _PROTOCOL_CODE,
                options=_options(
                    "Ambas as chamadas.",
                    "Somente a chamada 1 (`File`).",
                    "Somente a chamada 2 (`Socket`).",
                    "Nenhuma: `File` e `Socket` não herdam de `Closeable`.",
                ),
                explanation="A verificação de protocolos é estrutural, então herança não é "
                "necessária (descarta a D). `File.close()` casa com `close() -> None`. "
                "`Socket.close` exige um argumento extra, logo sua assinatura é incompatível "
                "e o verificador rejeita a chamada 2.",
            ),
        },
    ),
    QuestionSeed(
        code="python-type-hints-q06",
        competency_slug="type-hints",
        type=SHORT,
        difficulty=HARD,
        correct=None,
        tags=("generics", "variance"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="`int` is accepted where `float` is expected, yet mypy rejects passing a "
                "`list[int]` to a parameter typed `list[float]`. Why, and what is the usual fix?",
                model_answer="`list` is mutable, so it is invariant in its element type. If a "
                "`list[int]` were accepted as `list[float]`, the function could append a float "
                "to it and the caller's list of ints would silently hold a float. The usual "
                "fix is to declare the parameter as a read-only, covariant abstraction such as "
                "`Sequence[float]` (or `Iterable[float]`), which a `list[int]` satisfies "
                "safely.",
                explanation="Self-check: did you mention (1) mutability and invariance, (2) the "
                "unsafe append example, and (3) switching to `Sequence`/`Iterable`?",
            ),
            Language.PT_BR: QuestionText(
                prompt="`int` é aceito onde `float` é esperado, mas o mypy rejeita passar uma "
                "`list[int]` para um parâmetro tipado como `list[float]`. Por quê, e qual é a "
                "correção usual?",
                model_answer="`list` é mutável, então é invariante no tipo dos elementos. Se uma "
                "`list[int]` fosse aceita como `list[float]`, a função poderia adicionar um "
                "float a ela e a lista de ints do chamador passaria a guardar um float "
                "silenciosamente. A correção usual é declarar o parâmetro como uma abstração "
                "somente leitura e covariante, como `Sequence[float]` (ou `Iterable[float]`), "
                "que uma `list[int]` satisfaz com segurança.",
                explanation="Autoavaliação: você mencionou (1) mutabilidade e invariância, "
                "(2) o exemplo inseguro de `append` e (3) a troca por `Sequence`/`Iterable`?",
            ),
        },
    ),
)


ASSESSMENTS: tuple[AssessmentSeed, ...] = (
    AssessmentSeed(
        code="python-fundamentals-quiz",
        title="Python Fundamentals Quiz",
        description="Comprehensions, generators, truthiness, context managers and a classic trap.",
        kind=AssessmentKind.COMPETENCY,
        competency_slug="python-fundamentals",
        translations={
            "pt-BR": {
                "title": "Quiz de Fundamentos de Python",
                "description": "Comprehensions, generators, truthiness, context managers e uma "
                "pegadinha clássica.",
            }
        },
    ),
    AssessmentSeed(
        code="python-type-hints-quiz",
        title="Type Hints Quiz",
        description="What annotations do (and do not do), unions, protocols and variance.",
        kind=AssessmentKind.COMPETENCY,
        competency_slug="type-hints",
        translations={
            "pt-BR": {
                "title": "Quiz de Type Hints",
                "description": "O que as anotações fazem (e não fazem), uniões, protocolos e "
                "variância.",
            }
        },
    ),
    AssessmentSeed(
        code="python-core-checkpoint",
        title="Python Core Checkpoint",
        description="A short mixed check across fundamentals and type hints.",
        kind=AssessmentKind.MIXED,
        question_codes=(
            "python-fundamentals-q01",
            "python-fundamentals-q04",
            "python-type-hints-q01",
            "python-type-hints-q02",
            "python-type-hints-q04",
        ),
        translations={
            "pt-BR": {
                "title": "Checkpoint do Núcleo de Python",
                "description": "Uma verificação rápida e mista entre fundamentos e type hints.",
            }
        },
        pass_threshold=80,
        completion_bonus_xp=40,
    ),
)


QUESTION_SET = SubjectQuestionSet(
    subject_slug="python",
    questions=QUESTIONS,
    assessments=ASSESSMENTS,
)
