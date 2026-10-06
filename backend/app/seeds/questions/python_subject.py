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


_COMPETENCY_ORDER = ("python-fundamentals", "type-hints", "async-python", "testing-with-pytest")


def _t(
    prompt: str, explanation: str, *options: str, model_answer: str | None = None
) -> QuestionText:
    """Compact QuestionText: options (if any) get the ids a, b, c..."""
    return QuestionText(
        prompt=prompt,
        explanation=explanation,
        options=_options(*options) if options else None,
        model_answer=model_answer,
    )


def _q(
    code: str,
    slug: str,
    qtype: QuestionType,
    difficulty: QuestionDifficulty,
    correct: tuple[str, ...] | None,
    tags: tuple[str, ...],
    en: QuestionText,
    pt: QuestionText,
) -> QuestionSeed:
    return QuestionSeed(
        code=code,
        competency_slug=slug,
        type=qtype,
        difficulty=difficulty,
        correct=correct,
        tags=tags,
        source=AI,
        text={Language.EN: en, Language.PT_BR: pt},
    )


_PILOT_QUESTIONS: tuple[QuestionSeed, ...] = (
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


_IDENTITY_CODE = """```python
a = [1, 2]
b = [1, 2]
c = a
print(a == b, a is b, a is c)
```"""

_EXHAUSTED_GEN_CODE = """```python
nums = (n for n in range(3))
total = sum(nums)
print(total, list(nums))
```"""

_LATE_BINDING_CODE = """```python
funcs = [lambda: i for i in range(3)]
print([f() for f in funcs])
```"""

_NARROWING_CODE = """```python
def classify(x: int | str | None) -> str:
    if x is None:
        return "none"
    if isinstance(x, int):
        return "int"
    reveal_type(x)
    return x
```"""

_FUNDAMENTALS_EXTRA: tuple[QuestionSeed, ...] = (
    _q(
        "python-fundamentals-q07",
        "python-fundamentals",
        CODE,
        EASY,
        ("d",),
        ("identity", "equality"),
        _t(
            "What does this code print?\n\n" + _IDENTITY_CODE,
            "`==` compares values, `is` compares object identity. `a` and `b` are two separate "
            "lists that happen to hold equal items, so `a == b` is `True` but `a is b` is "
            "`False`. `c = a` creates a second name for the same object, so `a is c` is `True`. "
            "The other options confuse equality with identity or treat `c` as a copy.",
            "`True True True`",
            "`False False True`",
            "`True True False`",
            "`True False True`",
        ),
        _t(
            "O que este código imprime?\n\n" + _IDENTITY_CODE,
            "`==` compara valores e `is` compara a identidade do objeto. `a` e `b` são duas "
            "listas distintas que têm itens iguais, então `a == b` é `True`, mas `a is b` é "
            "`False`. `c = a` cria só outro nome para o mesmo objeto, logo `a is c` é `True`. "
            "As outras opções confundem igualdade com identidade ou tratam `c` como uma cópia.",
            "`True True True`",
            "`False False True`",
            "`True True False`",
            "`True False True`",
        ),
    ),
    _q(
        "python-fundamentals-q08",
        "python-fundamentals",
        MC,
        MEDIUM,
        ("b",),
        ("eafp", "exceptions"),
        _t(
            "Why do Python programmers often prefer `try: open(path) ... except "
            "FileNotFoundError` over `if os.path.exists(path): open(path)`?",
            "The `if` check only describes the filesystem at one instant: the file can be "
            "deleted (or created) before `open` runs, so you must handle the exception anyway. "
            "EAFP (easier to ask forgiveness than permission) avoids that race and the extra "
            "lookup. `os.path.exists` is not deprecated, `open` does raise for a missing file, "
            "and a raised exception is actually slower than a failed `if`, so speed is not "
            "the argument.",
            "Because `os.path.exists` is deprecated and emits a warning.",
            "Because the file may disappear or appear between the check and the `open` call, so "
            "the check does not make `open` safe; handling the exception covers that race.",
            "Because `try/except` is always faster than an `if` check.",
            "Because `open` never raises an error when the file does not exist.",
        ),
        _t(
            "Por que programadores Python costumam preferir `try: open(path) ... except "
            "FileNotFoundError` a `if os.path.exists(path): open(path)`?",
            "O `if` só descreve o sistema de arquivos em um instante: o arquivo pode ser "
            "apagado (ou criado) antes de o `open` executar, então você precisa tratar a "
            "exceção de qualquer forma. EAFP (easier to ask forgiveness than permission) evita "
            "essa race condition e a consulta extra. `os.path.exists` não está obsoleta, o "
            "`open` lança erro para arquivo ausente, e lançar uma exceção é na verdade mais "
            "lento que um `if` que falha, então velocidade não é o argumento.",
            "Porque `os.path.exists` está obsoleta e emite um aviso.",
            "Porque o arquivo pode sumir ou aparecer entre a verificação e a chamada a `open`, "
            "então a verificação não torna o `open` seguro; tratar a exceção cobre essa corrida.",
            "Porque `try/except` é sempre mais rápido que um `if`.",
            "Porque `open` nunca lança erro quando o arquivo não existe.",
        ),
    ),
    _q(
        "python-fundamentals-q09",
        "python-fundamentals",
        CODE,
        MEDIUM,
        ("a",),
        ("generators", "iterators"),
        _t(
            "What does this code print?\n\n" + _EXHAUSTED_GEN_CODE,
            "A generator is a one-shot iterator. `sum(nums)` consumes it entirely (0 + 1 + 2 = "
            "3), leaving it exhausted, so `list(nums)` is `[]`. Iterating an exhausted "
            "generator does not raise: `list()` handles the `StopIteration` internally. To "
            "reuse the values, store them in a list or build a new generator.",
            "`3 []`",
            "`3 [0, 1, 2]`",
            "A `TypeError`, because a generator cannot be passed to `sum`.",
            "A `StopIteration` propagates out of `list(nums)`.",
        ),
        _t(
            "O que este código imprime?\n\n" + _EXHAUSTED_GEN_CODE,
            "Um generator é um iterador de uso único. `sum(nums)` o consome por inteiro "
            "(0 + 1 + 2 = 3) e o deixa esgotado, então `list(nums)` é `[]`. Iterar um "
            "generator esgotado não lança erro: `list()` trata o `StopIteration` internamente. "
            "Para reutilizar os valores, guarde-os em uma lista ou crie um novo generator.",
            "`3 []`",
            "`3 [0, 1, 2]`",
            "Um `TypeError`, pois um generator não pode ser passado para `sum`.",
            "Um `StopIteration` se propaga para fora de `list(nums)`.",
        ),
    ),
    _q(
        "python-fundamentals-q10",
        "python-fundamentals",
        CODE,
        HARD,
        ("b",),
        ("closures", "late-binding"),
        _t(
            "What does this code print?\n\n" + _LATE_BINDING_CODE,
            "Each lambda closes over the *variable* `i`, not its value at creation time. The "
            "lambdas run after the comprehension has finished, when `i` holds its last value, "
            "2 (the loop variable is never 3, since `range(3)` stops at 2). All three "
            "therefore return 2. Bind the value at definition time with a default argument "
            "(`lambda i=i: i`) or `functools.partial`.",
            "`[0, 1, 2]`",
            "`[2, 2, 2]`",
            "`[3, 3, 3]`",
            "`[0, 0, 0]`",
        ),
        _t(
            "O que este código imprime?\n\n" + _LATE_BINDING_CODE,
            "Cada lambda captura a *variável* `i`, não o valor que ela tinha na criação. As "
            "lambdas executam depois que a comprehension terminou, quando `i` guarda o último "
            "valor, 2 (a variável do laço nunca chega a 3, pois `range(3)` para em 2). As três "
            "retornam, portanto, 2. Fixe o valor na definição com um argumento padrão "
            "(`lambda i=i: i`) ou com `functools.partial`.",
            "`[0, 1, 2]`",
            "`[2, 2, 2]`",
            "`[3, 3, 3]`",
            "`[0, 0, 0]`",
        ),
    ),
)

_TYPE_HINTS_EXTRA: tuple[QuestionSeed, ...] = (
    _q(
        "python-type-hints-q07",
        "type-hints",
        MC,
        EASY,
        ("d",),
        ("callable", "basics"),
        _t(
            "What does the annotation `Callable[[int, str], bool]` describe?",
            "The first item is the list of parameter types and the second is the return type, "
            "so this is any callable that takes an `int` and a `str`, in that order, and "
            "returns a `bool`. The other options misread the parameter list as a single list "
            "argument, swap parameters and return type, or treat the return type as a "
            "parameter.",
            "A function with one argument, a list holding an `int` and a `str`, returning a "
            "`bool`.",
            "A function that returns a collection with an `int`, a `str` and a `bool`.",
            "A function that takes an `int` and a `bool` and returns a `str`.",
            "A callable taking an `int` and a `str`, in that order, and returning a `bool`.",
        ),
        _t(
            "O que a anotação `Callable[[int, str], bool]` descreve?",
            "O primeiro item é a lista de tipos dos parâmetros e o segundo é o tipo de "
            "retorno, então isto é qualquer callable que recebe um `int` e uma `str`, nessa "
            "ordem, e retorna um `bool`. As outras opções leem a lista de parâmetros como um "
            "único argumento do tipo lista, trocam parâmetros e retorno, ou tratam o tipo de "
            "retorno como parâmetro.",
            "Uma função com um argumento, uma lista contendo um `int` e uma `str`, que retorna "
            "um `bool`.",
            "Uma função que retorna uma coleção com um `int`, uma `str` e um `bool`.",
            "Uma função que recebe um `int` e um `bool` e retorna uma `str`.",
            "Um callable que recebe um `int` e uma `str`, nessa ordem, e retorna um `bool`.",
        ),
    ),
    _q(
        "python-type-hints-q08",
        "type-hints",
        MC,
        MEDIUM,
        ("c",),
        ("any", "object"),
        _t(
            "What is the key difference between annotating a parameter as `Any` and as `object`?",
            "`Any` is an escape hatch: the checker allows any operation on the value and "
            "accepts it anywhere. `object` also accepts every value, but you may only do what "
            "is valid for all objects, so `x.upper()` is flagged until you narrow the type "
            "(for example with `isinstance`). Neither one is enforced at runtime, and `object` "
            "is not limited to user-defined classes.",
            "None: they are aliases for the same type.",
            "`object` accepts only instances of user-defined classes, while `Any` also accepts "
            "built-in types.",
            "`Any` disables type checking for that value, while `object` accepts any value but "
            "still lets the checker reject operations that not every object supports.",
            "`Any` is verified by the interpreter at runtime, while `object` is only checked "
            "statically.",
        ),
        _t(
            "Qual é a diferença essencial entre anotar um parâmetro como `Any` e como `object`?",
            "`Any` é uma válvula de escape: o verificador permite qualquer operação sobre o "
            "valor e o aceita em qualquer lugar. `object` também aceita todo valor, mas você "
            "só pode fazer o que vale para qualquer objeto, então `x.upper()` é apontado até "
            "você restringir o tipo (por exemplo com `isinstance`). Nenhum dos dois é imposto "
            "em tempo de execução, e `object` não se limita a classes definidas pelo usuário.",
            "Nenhuma: são apelidos para o mesmo tipo.",
            "`object` aceita apenas instâncias de classes definidas pelo usuário, enquanto "
            "`Any` aceita também tipos embutidos.",
            "`Any` desliga a checagem de tipos para aquele valor, enquanto `object` aceita "
            "qualquer valor mas ainda deixa o verificador rejeitar operações que nem todo "
            "objeto suporta.",
            "`Any` é verificado pelo interpretador em tempo de execução, enquanto `object` só "
            "é checado estaticamente.",
        ),
    ),
    _q(
        "python-type-hints-q09",
        "type-hints",
        MS,
        MEDIUM,
        ("a", "c", "e"),
        ("optional", "none"),
        _t(
            "Which statements about `Optional[int]` are true? Select all that apply.",
            "`Optional[int]` is just another spelling of `int | None`, and a checker makes you "
            "rule out `None` (for example with `is not None`) before using the value as an "
            "`int`. Typing a parameter that way and giving it `= None` is the usual signature. "
            "Two common misconceptions: `Optional` says nothing about whether the argument may "
            "be omitted (that is decided by having a default), and nothing is enforced at "
            "runtime, so passing `None` raises no `TypeError` by itself.",
            "It means the same as `int | None`.",
            "A parameter annotated this way may be omitted by the caller even without a "
            "default value.",
            "Before using such a value in an `int`-only operation, the checker requires you to "
            "rule out `None`, for example with `if x is not None`.",
            "At runtime, passing `None` to such a parameter raises `TypeError`.",
            "`def f(x: Optional[int] = None)` is a valid signature.",
        ),
        _t(
            "Quais afirmações sobre `Optional[int]` são verdadeiras? Selecione todas que se "
            "aplicam.",
            "`Optional[int]` é só outra grafia de `int | None`, e o verificador obriga você a "
            "descartar `None` (por exemplo com `is not None`) antes de usar o valor como "
            "`int`. Tipar um parâmetro assim e dar a ele `= None` é a assinatura habitual. Dois "
            "equívocos comuns: `Optional` não diz nada sobre o argumento poder ser omitido "
            "(isso é decidido por haver um valor padrão), e nada é imposto em tempo de "
            "execução, então passar `None` não gera `TypeError` por si só.",
            "Significa o mesmo que `int | None`.",
            "Um parâmetro anotado assim pode ser omitido pelo chamador mesmo sem valor padrão.",
            "Antes de usar o valor em uma operação exclusiva de `int`, o verificador exige "
            "descartar `None`, por exemplo com `if x is not None`.",
            "Em tempo de execução, passar `None` a esse parâmetro lança `TypeError`.",
            "`def f(x: Optional[int] = None)` é uma assinatura válida.",
        ),
    ),
    _q(
        "python-type-hints-q10",
        "type-hints",
        CODE,
        MEDIUM,
        ("a",),
        ("narrowing", "mypy"),
        _t(
            "What type does `mypy` reveal for `x` at the `reveal_type` line?\n\n" + _NARROWING_CODE,
            "Type checkers narrow a union along each branch. The early `return` removes `None` "
            "(after the `is None` check) and then `int` (after the `isinstance` check), so only "
            "`str` is left, which is also what makes `return x` valid. `Never` would mean the "
            "line is unreachable, and the other unions ignore the narrowing.",
            "`str`",
            "`int | str`",
            "`int | str | None`",
            "`Never`",
        ),
        _t(
            "Qual tipo o `mypy` revela para `x` na linha do `reveal_type`?\n\n" + _NARROWING_CODE,
            "Verificadores de tipos restringem (narrow) uma união a cada ramo. O `return` "
            "antecipado remove `None` (depois do teste `is None`) e depois `int` (depois do "
            "`isinstance`), sobrando apenas `str`, o que também torna `return x` válido. "
            "`Never` significaria que a linha é inalcançável, e as outras uniões ignoram o "
            "narrowing.",
            "`str`",
            "`int | str`",
            "`int | str | None`",
            "`Never`",
        ),
    ),
)

QUESTIONS: tuple[QuestionSeed, ...] = tuple(
    sorted(
        _PILOT_QUESTIONS + _FUNDAMENTALS_EXTRA + _TYPE_HINTS_EXTRA,
        key=lambda q: (_COMPETENCY_ORDER.index(q.competency_slug), q.code),
    )
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
