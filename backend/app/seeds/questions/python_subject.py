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

_COROUTINE_OBJECT_CODE = """```python
async def hello():
    print("hi")
    return 1

x = hello()
print(type(x).__name__)
```"""

_GATHER_ORDER_CODE = """```python
import asyncio

async def work(name, delay):
    await asyncio.sleep(delay)
    print(name)
    return name

async def main():
    results = await asyncio.gather(work("a", 0.3), work("b", 0.1), work("c", 0.2))
    print(results)

asyncio.run(main())
```"""

_BLOCKING_SLEEP_CODE = """```python
import asyncio
import time

async def tick():
    for _ in range(3):
        print("tick")
        await asyncio.sleep(0.1)

async def blocker():
    time.sleep(0.5)
    print("done blocking")

async def main():
    await asyncio.gather(tick(), blocker())

asyncio.run(main())
```"""

_ASYNC_COUNTER_CODE = """```python
import asyncio

counter = 0

async def inc():
    global counter
    tmp = counter
    await asyncio.sleep(0)
    counter = tmp + 1

async def main():
    await asyncio.gather(*(inc() for _ in range(100)))
    print(counter)

asyncio.run(main())
```"""

_ASYNC_EXTRA: tuple[QuestionSeed, ...] = (
    _q(
        "async-python-q01",
        "async-python",
        CODE,
        EASY,
        ("b",),
        ("coroutines",),
        _t(
            "What does this script print to standard output?\n\n" + _COROUTINE_OBJECT_CODE,
            "Calling an `async def` function does not run its body: it returns a coroutine "
            "object that must be awaited (or scheduled as a task) to execute. So `hi` is never "
            'printed and the type name is `coroutine`. Python also emits a "coroutine was never '
            'awaited" warning on stderr, which is a classic sign of a missing `await`.',
            "`hi` and then `int`",
            "`coroutine`",
            "`hi` and then `coroutine`",
            "`function`",
        ),
        _t(
            "O que este script imprime na saída padrão?\n\n" + _COROUTINE_OBJECT_CODE,
            "Chamar uma função `async def` não executa o corpo: ela retorna um objeto "
            "coroutine que precisa ser aguardado com `await` (ou agendado como task) para "
            "rodar. Assim, `hi` nunca é impresso e o nome do tipo é `coroutine`. O Python "
            'também emite no stderr um aviso "coroutine was never awaited", sinal clássico '
            "de um `await` esquecido.",
            "`hi` e depois `int`",
            "`coroutine`",
            "`hi` e depois `coroutine`",
            "`function`",
        ),
    ),
    _q(
        "async-python-q02",
        "async-python",
        MC,
        EASY,
        ("c",),
        ("await", "event-loop"),
        _t(
            "What does `await` do inside a coroutine?",
            "`await` runs the awaited coroutine, future or task, and is the point where the "
            "current coroutine may be suspended so the event loop can run something else "
            "while it waits. It does not create a thread, it does not block the whole "
            "program, and it does not change what kind of function the awaited code is.",
            "It starts a new OS thread to run the awaited object.",
            "It blocks the entire program until the awaited object finishes.",
            "It runs the awaited object and, if that has to wait, suspends this coroutine so "
            "the event loop can run other tasks.",
            "It turns the awaited function into a regular synchronous function.",
        ),
        _t(
            "O que o `await` faz dentro de uma coroutine?",
            "`await` executa a coroutine, future ou task aguardada e é o ponto em que a "
            "coroutine atual pode ser suspensa para que o event loop rode outra coisa enquanto "
            "ela espera. Ele não cria uma thread, não bloqueia o programa inteiro e não muda "
            "o tipo de função do código aguardado.",
            "Inicia uma nova thread do SO para executar o objeto aguardado.",
            "Bloqueia o programa inteiro até o objeto aguardado terminar.",
            "Executa o objeto aguardado e, se ele precisar esperar, suspende esta coroutine "
            "para que o event loop rode outras tasks.",
            "Transforma a função aguardada em uma função síncrona comum.",
        ),
    ),
    _q(
        "async-python-q03",
        "async-python",
        MC,
        EASY,
        ("d",),
        ("io-bound", "concurrency"),
        _t(
            "A service must make 200 independent HTTP requests and spends almost all of its "
            "time waiting on the network. Why is `asyncio` a good fit?",
            "With asyncio, one thread runs other coroutines while a request is waiting for "
            "the network, so the total time approaches that of the slowest requests instead "
            "of the sum of all of them. It does not use several CPU cores, it does not remove "
            "the GIL, and it does not make any single request faster.",
            "Coroutines run in parallel on several CPU cores.",
            "`asyncio` removes the GIL, so Python code runs without restrictions.",
            "Each individual request becomes faster because it is a coroutine.",
            "While one request waits for the network, the event loop runs the others on the "
            "same thread, so the waiting time overlaps.",
        ),
        _t(
            "Um serviço precisa fazer 200 requisições HTTP independentes e passa quase todo o "
            "tempo esperando a rede. Por que o `asyncio` é uma boa escolha?",
            "Com asyncio, uma única thread executa outras coroutines enquanto uma requisição "
            "espera a rede, então o tempo total se aproxima do das requisições mais lentas em "
            "vez da soma de todas. Ele não usa vários núcleos de CPU, não remove o GIL e não "
            "torna nenhuma requisição individual mais rápida.",
            "As coroutines rodam em paralelo em vários núcleos de CPU.",
            "O `asyncio` remove o GIL, então o código Python roda sem restrições.",
            "Cada requisição individual fica mais rápida por ser uma coroutine.",
            "Enquanto uma requisição espera a rede, o event loop executa as outras na mesma "
            "thread, então os tempos de espera se sobrepõem.",
        ),
    ),
    _q(
        "async-python-q04",
        "async-python",
        CODE,
        MEDIUM,
        ("c",),
        ("gather", "ordering"),
        _t(
            "What does this program print?\n\n" + _GATHER_ORDER_CODE,
            "The three coroutines run concurrently, so each prints when its own sleep ends: "
            "`b` (0.1 s), `c` (0.2 s), then `a` (0.3 s). `asyncio.gather` however returns the "
            "results in the order the awaitables were passed in, not in completion order, so "
            "the list is `['a', 'b', 'c']`. Running them one after another would print `a`, "
            "`b`, `c`.",
            "`a`, `b`, `c`, then `['a', 'b', 'c']`",
            "`b`, `c`, `a`, then `['b', 'c', 'a']`",
            "`b`, `c`, `a`, then `['a', 'b', 'c']`",
            "`a`, `b`, `c`, then `['b', 'c', 'a']`",
        ),
        _t(
            "O que este programa imprime?\n\n" + _GATHER_ORDER_CODE,
            "As três coroutines rodam de forma concorrente, então cada uma imprime quando o "
            "seu próprio sleep termina: `b` (0,1 s), `c` (0,2 s) e depois `a` (0,3 s). Já o "
            "`asyncio.gather` devolve os resultados na ordem em que os awaitables foram "
            "passados, não na ordem de conclusão, então a lista é `['a', 'b', 'c']`. Rodá-las "
            "uma após a outra imprimiria `a`, `b`, `c`.",
            "`a`, `b`, `c` e depois `['a', 'b', 'c']`",
            "`b`, `c`, `a` e depois `['b', 'c', 'a']`",
            "`b`, `c`, `a` e depois `['a', 'b', 'c']`",
            "`a`, `b`, `c` e depois `['b', 'c', 'a']`",
        ),
    ),
    _q(
        "async-python-q05",
        "async-python",
        CODE,
        MEDIUM,
        ("b",),
        ("blocking", "event-loop"),
        _t(
            "In what order does this program print its lines?\n\n" + _BLOCKING_SLEEP_CODE,
            "`gather` starts `tick` first: it prints `tick` and awaits, handing control to "
            "`blocker`. `blocker` calls the synchronous `time.sleep(0.5)`, which never yields, "
            "so the whole event loop is frozen for half a second and `tick` cannot resume. "
            "Only after `done blocking` does `tick` print its remaining two lines. With "
            "`await asyncio.sleep(0.5)` (or `asyncio.to_thread`) the ticks would interleave "
            "normally.",
            "`tick`, `tick`, `tick`, `done blocking`",
            "`tick`, `done blocking`, `tick`, `tick`",
            "`done blocking`, `tick`, `tick`, `tick`",
            "`tick`, `tick`, `done blocking`, `tick`",
        ),
        _t(
            "Em que ordem este programa imprime suas linhas?\n\n" + _BLOCKING_SLEEP_CODE,
            "O `gather` inicia `tick` primeiro: ela imprime `tick` e faz `await`, passando o "
            "controle a `blocker`. `blocker` chama o `time.sleep(0.5)` síncrono, que nunca "
            "cede o controle, então o event loop inteiro fica congelado por meio segundo e "
            "`tick` não consegue retomar. Só depois de `done blocking` a `tick` imprime as "
            "duas linhas restantes. Com `await asyncio.sleep(0.5)` (ou `asyncio.to_thread`) "
            "os ticks se intercalariam normalmente.",
            "`tick`, `tick`, `tick`, `done blocking`",
            "`tick`, `done blocking`, `tick`, `tick`",
            "`done blocking`, `tick`, `tick`, `tick`",
            "`tick`, `tick`, `done blocking`, `tick`",
        ),
    ),
    _q(
        "async-python-q06",
        "async-python",
        MC,
        MEDIUM,
        ("a",),
        ("blocking", "to-thread"),
        _t(
            "An async request handler must call a legacy synchronous function "
            "`parse_report(path)` that takes about two seconds and cannot be rewritten. What "
            "is the best way to call it without freezing the event loop?",
            "`asyncio.to_thread` (or `loop.run_in_executor`) runs the blocking call in a worker "
            "thread and gives you an awaitable, so the loop keeps serving other tasks. Calling "
            "it directly blocks the loop, a plain function cannot be awaited, and merely "
            "adding `async` to its definition changes nothing about the blocking body.",
            "`await asyncio.to_thread(parse_report, path)`",
            "`await parse_report(path)`",
            "Declare `parse_report` with `async def` and leave its body unchanged.",
            "Call `parse_report(path)` directly; the event loop will preempt it when needed.",
        ),
        _t(
            "Um handler assíncrono precisa chamar uma função síncrona legada "
            "`parse_report(path)` que leva cerca de dois segundos e não pode ser reescrita. "
            "Qual é a melhor forma de chamá-la sem congelar o event loop?",
            "`asyncio.to_thread` (ou `loop.run_in_executor`) executa a chamada bloqueante em "
            "uma thread de trabalho e devolve um awaitable, então o loop continua atendendo "
            "outras tasks. Chamá-la diretamente bloqueia o loop, uma função comum não pode "
            "ser aguardada e apenas adicionar `async` à definição não muda o corpo bloqueante.",
            "`await asyncio.to_thread(parse_report, path)`",
            "`await parse_report(path)`",
            "Declarar `parse_report` com `async def` e manter o corpo inalterado.",
            "Chamar `parse_report(path)` diretamente; o event loop a interrompe quando necessário.",
        ),
    ),
    _q(
        "async-python-q07",
        "async-python",
        MS,
        MEDIUM,
        ("a", "c", "e"),
        ("cancellation",),
        _t(
            "Which statements about cancelling an asyncio task with `task.cancel()` are true? "
            "Select all that apply.",
            "`cancel()` only requests cancellation: the `CancelledError` is raised inside the "
            "task at the `await` where it is suspended, and the task is not done immediately. "
            "`finally` blocks run, so cleanup is possible. In modern Python `CancelledError` is "
            "a `BaseException`, so `except Exception` does not catch it. If the coroutine "
            "catches it and does not re-raise, the cancellation is swallowed and the task "
            "ends normally instead of as cancelled.",
            "It requests cancellation: a `CancelledError` is raised inside the task at the "
            "`await` where it is currently suspended.",
            "It stops the task immediately and synchronously, so `task.done()` is already "
            "`True` right after the call.",
            "`finally` blocks in the cancelled coroutine still run, so it can release resources.",
            "`except Exception:` is enough to catch the `CancelledError` and clean up.",
            "If the coroutine catches `CancelledError` and does not re-raise it, the "
            "cancellation is swallowed and the task does not end as cancelled.",
        ),
        _t(
            "Quais afirmações sobre cancelar uma task do asyncio com `task.cancel()` são "
            "verdadeiras? Selecione todas que se aplicam.",
            "`cancel()` apenas solicita o cancelamento: o `CancelledError` é lançado dentro da "
            "task no `await` em que ela está suspensa, e a task não termina na hora. Os "
            "blocos `finally` executam, então é possível fazer limpeza. No Python moderno "
            "`CancelledError` herda de `BaseException`, então `except Exception` não o "
            "captura. Se a coroutine o captura e não o relança, o cancelamento é engolido e "
            "a task termina normalmente em vez de cancelada.",
            "Solicita o cancelamento: um `CancelledError` é lançado dentro da task no `await` "
            "em que ela está suspensa no momento.",
            "Interrompe a task imediatamente e de forma síncrona, então `task.done()` já é "
            "`True` logo após a chamada.",
            "Blocos `finally` da coroutine cancelada ainda executam, então ela pode liberar "
            "recursos.",
            "`except Exception:` basta para capturar o `CancelledError` e fazer a limpeza.",
            "Se a coroutine captura `CancelledError` e não o relança, o cancelamento é "
            "engolido e a task não termina como cancelada.",
        ),
    ),
    _q(
        "async-python-q08",
        "async-python",
        MC,
        MEDIUM,
        ("c",),
        ("taskgroup", "structured-concurrency"),
        _t(
            "Using `asyncio.TaskGroup` (Python 3.11+), what happens when one task in the group "
            "raises an exception while the others are still running?",
            "A `TaskGroup` implements structured concurrency: the first failure cancels the "
            "sibling tasks, the group waits for all of them to finish, and then the `async "
            "with` block raises an `ExceptionGroup` carrying the errors (handled with "
            "`except*`). The error is therefore never silently dropped and no task is left "
            "running after the block exits.",
            "The other tasks keep running to completion and the exception is ignored.",
            "Only the failing task stops; its exception is stored on it and the group exits "
            "normally.",
            "The remaining tasks are cancelled and, once all have finished, the `async with` "
            "block raises an `ExceptionGroup`.",
            "The interpreter exits immediately, without letting the other tasks clean up.",
        ),
        _t(
            "Usando `asyncio.TaskGroup` (Python 3.11+), o que acontece quando uma task do "
            "grupo lança uma exceção enquanto as outras ainda estão rodando?",
            "Um `TaskGroup` implementa structured concurrency: a primeira falha cancela as "
            "tasks irmãs, o grupo espera todas terminarem e então o bloco `async with` lança "
            "um `ExceptionGroup` com os erros (tratado com `except*`). Assim o erro nunca é "
            "descartado em silêncio e nenhuma task fica rodando depois que o bloco termina.",
            "As outras tasks continuam até o fim e a exceção é ignorada.",
            "Só a task com falha para; a exceção fica guardada nela e o grupo termina normalmente.",
            "As demais tasks são canceladas e, quando todas terminam, o bloco `async with` "
            "lança um `ExceptionGroup`.",
            "O interpretador encerra imediatamente, sem deixar as outras tasks fazerem limpeza.",
        ),
    ),
    _q(
        "async-python-q09",
        "async-python",
        CODE,
        HARD,
        ("d",),
        ("race-condition", "shared-state"),
        _t(
            "What does this program print?\n\n" + _ASYNC_COUNTER_CODE,
            "There is only one thread, but the `await` sits between the read and the write of "
            "`counter`. `gather` starts all 100 coroutines; each reads `counter` (still 0) and "
            "suspends at `await asyncio.sleep(0)`. When they resume, every one writes `0 + 1`, "
            "so the final value is 1, not 100. A read-modify-write that spans an `await` needs "
            "an `asyncio.Lock`, or the update must happen without awaiting in between.",
            "`100`",
            "`0`",
            "A value between 1 and 100 that changes from run to run.",
            "`1`",
        ),
        _t(
            "O que este programa imprime?\n\n" + _ASYNC_COUNTER_CODE,
            "Há uma única thread, mas o `await` fica entre a leitura e a escrita de "
            "`counter`. O `gather` inicia as 100 coroutines; cada uma lê `counter` (ainda 0) e "
            "suspende em `await asyncio.sleep(0)`. Quando retomam, todas escrevem `0 + 1`, "
            "então o valor final é 1, não 100. Um read-modify-write que atravessa um `await` "
            "precisa de um `asyncio.Lock`, ou a atualização deve ocorrer sem `await` no meio.",
            "`100`",
            "`0`",
            "Um valor entre 1 e 100 que muda a cada execução.",
            "`1`",
        ),
    ),
    _q(
        "async-python-q10",
        "async-python",
        SHORT,
        HARD,
        None,
        ("async-vs-threads", "cpu-bound"),
        _t(
            "A team must (1) call 1,000 slow HTTP endpoints, (2) resize 10,000 large images, "
            "and (3) use a legacy blocking database driver from an async web service. Which "
            "concurrency tool fits each job, and why?",
            "Self-check against the model answer: did you pair each job with a tool, explain "
            "the reason (waiting vs computing vs blocking call), and mention the GIL for the "
            "CPU-bound case?",
            model_answer="(1) Many network waits: asyncio, with a semaphore to bound "
            "concurrency; one thread overlaps the waiting, with very low per-task cost. (2) "
            "CPU-bound work: a process pool (`ProcessPoolExecutor`, possibly via "
            "`run_in_executor`) because the GIL prevents threads, and coroutines, from running "
            "Python bytecode in parallel; a CPU loop without `await` would also freeze the "
            "event loop. (3) A blocking driver: run it in a worker thread "
            "(`asyncio.to_thread`) so it does not block the loop; threads are enough because "
            "the driver releases the GIL while waiting on I/O, or move to a native async driver.",
        ),
        _t(
            "Uma equipe precisa (1) chamar 1.000 endpoints HTTP lentos, (2) redimensionar "
            "10.000 imagens grandes e (3) usar um driver de banco de dados bloqueante e legado "
            "em um serviço web assíncrono. Qual ferramenta de concorrência serve para cada "
            "tarefa, e por quê?",
            "Autoavaliação contra a resposta-modelo: você associou cada tarefa a uma "
            "ferramenta, explicou o motivo (espera vs computação vs chamada bloqueante) e "
            "mencionou o GIL no caso limitado por CPU?",
            model_answer="(1) Muitas esperas de rede: asyncio, com um semáforo para limitar a "
            "concorrência; uma thread sobrepõe as esperas, com custo muito baixo por task. "
            "(2) Trabalho limitado por CPU: um pool de processos (`ProcessPoolExecutor`, "
            "possivelmente via `run_in_executor`), pois o GIL impede que threads e coroutines "
            "executem bytecode Python em paralelo; um laço de CPU sem `await` também "
            "congelaria o event loop. (3) Um driver bloqueante: executá-lo em uma thread de "
            "trabalho (`asyncio.to_thread`) para não bloquear o loop; threads bastam porque o "
            "driver libera o GIL enquanto espera por I/O, ou migrar para um driver async "
            "nativo.",
        ),
    ),
)

_STACKED_PARAMETRIZE_CODE = """```python
import pytest

@pytest.mark.parametrize("role", ["admin", "member", "guest"])
@pytest.mark.parametrize("is_active", [True, False])
def test_dashboard(role, is_active):
    assert isinstance(is_active, bool)
```"""

_FIXTURE_ORDER_CODE = """```python
import pytest

@pytest.fixture
def a():
    print("setup a")
    yield "a"
    print("teardown a")

@pytest.fixture
def b(a):
    print("setup b")
    yield "b"
    print("teardown b")

def test_order(b):
    print("test body")
```"""

_AUTOSPEC_CODE = """```python
from unittest.mock import Mock, create_autospec

def charge(amount, currency):
    return True

loose = Mock(return_value=True)
strict = create_autospec(charge, return_value=True)

loose(1, 2, 3)   # call 1
strict(1)        # call 2
```"""

_PYTEST_EXTRA: tuple[QuestionSeed, ...] = (
    _q(
        "testing-with-pytest-q01",
        "testing-with-pytest",
        MC,
        EASY,
        ("b",),
        ("discovery", "basics"),
        _t(
            "With its default configuration, how does pytest decide what to run?",
            "By default pytest collects files named `test_*.py` or `*_test.py`, and inside "
            "them top-level functions (and methods of `Test*` classes) whose names start with "
            "`test`. No registration or decorator is needed, and an `assert` alone does not "
            "make a function a test. A `pytest.ini` can customize these rules but is not "
            "required.",
            "It runs every `.py` file and every function that contains an `assert`.",
            "It collects files named `test_*.py` or `*_test.py` and, inside them, functions "
            "(or methods of `Test*` classes) whose names start with `test`.",
            "It only runs the files explicitly listed in `pytest.ini`.",
            "It only runs functions decorated with `@pytest.mark.test`.",
        ),
        _t(
            "Com a configuração padrão, como o pytest decide o que executar?",
            "Por padrão o pytest coleta arquivos chamados `test_*.py` ou `*_test.py` e, dentro "
            "deles, funções de nível superior (e métodos de classes `Test*`) cujos nomes "
            "começam com `test`. Não é preciso registrar nada nem usar decorator, e um `assert` "
            "sozinho não torna uma função um teste. Um `pytest.ini` pode personalizar essas "
            "regras, mas não é obrigatório.",
            "Executa todo arquivo `.py` e toda função que contenha um `assert`.",
            "Coleta arquivos chamados `test_*.py` ou `*_test.py` e, dentro deles, funções "
            "(ou métodos de classes `Test*`) cujos nomes começam com `test`.",
            "Executa apenas os arquivos listados explicitamente no `pytest.ini`.",
            "Executa apenas funções decoradas com `@pytest.mark.test`.",
        ),
    ),
    _q(
        "testing-with-pytest-q02",
        "testing-with-pytest",
        MC,
        EASY,
        ("c",),
        ("markers", "xfail"),
        _t(
            "A test documents a known bug: it fails today, and you want the suite to stay green "
            "but to be told as soon as the bug is fixed. Which is the best fit?",
            "`xfail` still runs the test: a failure is reported as an expected failure, and "
            "with `strict=True` an unexpected pass fails the run, which tells you the bug is "
            "gone and the marker must be removed. `skip` never runs the test, so you would "
            "never notice the fix; deleting it loses the documentation; and swallowing the "
            "`AssertionError` makes the test pass forever.",
            '`@pytest.mark.skip(reason="known bug")`',
            "Delete the test until the bug is fixed.",
            '`@pytest.mark.xfail(reason="known bug", strict=True)`',
            "Wrap the assertion in `try/except AssertionError: pass`.",
        ),
        _t(
            "Um teste documenta um bug conhecido: ele falha hoje, e você quer que a suíte "
            "continue verde mas seja avisado assim que o bug for corrigido. Qual é a melhor "
            "opção?",
            "O `xfail` ainda executa o teste: uma falha é reportada como falha esperada e, com "
            "`strict=True`, um sucesso inesperado quebra a execução, avisando que o bug "
            "sumiu e que o marker deve ser removido. O `skip` nunca executa o teste, então "
            "você jamais notaria a correção; apagar o teste perde a documentação; e engolir o "
            "`AssertionError` faz o teste passar para sempre.",
            '`@pytest.mark.skip(reason="known bug")`',
            "Apagar o teste até o bug ser corrigido.",
            '`@pytest.mark.xfail(reason="known bug", strict=True)`',
            "Envolver o assert em `try/except AssertionError: pass`.",
        ),
    ),
    _q(
        "testing-with-pytest-q03",
        "testing-with-pytest",
        MC,
        EASY,
        ("a",),
        ("exceptions", "pytest-raises"),
        _t(
            'Which test correctly checks that `int("x")` raises `ValueError`?',
            "`pytest.raises` is a context manager: the test passes only if the block raises the "
            "expected exception, and fails if nothing (or something else) is raised. A bare "
            '`assert int("x") == ...` or `is None` raises `ValueError` before the comparison '
            "happens, which errors the test instead of verifying it. A `try/except ...: pass` "
            "with no further check also passes when no exception occurs, so it proves "
            "nothing.",
            '`with pytest.raises(ValueError): int("x")`',
            '`assert int("x") == ValueError`',
            'A `try` block around `int("x")` with `except ValueError: pass` and nothing else.',
            '`assert int("x") is None`',
        ),
        _t(
            'Qual teste verifica corretamente que `int("x")` lança `ValueError`?',
            "`pytest.raises` é um context manager: o teste só passa se o bloco lançar a exceção "
            'esperada, e falha se nada (ou outra coisa) for lançado. Um `assert int("x") == '
            "...` ou `is None` lança `ValueError` antes da comparação, o que dá erro no teste em "
            "vez de verificá-lo. Um `try/except ...: pass` sem outra checagem também passa "
            "quando nenhuma exceção ocorre, então não prova nada.",
            '`with pytest.raises(ValueError): int("x")`',
            '`assert int("x") == ValueError`',
            'Um bloco `try` em volta de `int("x")` com `except ValueError: pass` e nada mais.',
            '`assert int("x") is None`',
        ),
    ),
    _q(
        "testing-with-pytest-q04",
        "testing-with-pytest",
        CODE,
        MEDIUM,
        ("b",),
        ("parametrize",),
        _t(
            "How many test cases does pytest generate from `test_dashboard`?\n\n"
            + _STACKED_PARAMETRIZE_CODE,
            "Stacked `parametrize` decorators multiply: 3 roles x 2 values of `is_active` = 6 "
            "independent test cases, each with its own id such as `test_dashboard[True-admin]` "
            "and reported separately. Adding (3 + 2 = 5) would be the result of two separate "
            "tests, not of stacking.",
            "5",
            "6",
            "3",
            "2",
        ),
        _t(
            "Quantos casos de teste o pytest gera a partir de `test_dashboard`?\n\n"
            + _STACKED_PARAMETRIZE_CODE,
            "Decorators `parametrize` empilhados se multiplicam: 3 roles x 2 valores de "
            "`is_active` = 6 casos de teste independentes, cada um com seu id, como "
            "`test_dashboard[True-admin]`, reportados separadamente. Somar (3 + 2 = 5) seria o "
            "resultado de dois testes separados, não de decorators empilhados.",
            "5",
            "6",
            "3",
            "2",
        ),
    ),
    _q(
        "testing-with-pytest-q05",
        "testing-with-pytest",
        CODE,
        MEDIUM,
        ("c",),
        ("fixtures", "teardown"),
        _t(
            "Run with `pytest -s` (output not captured), in what order are these lines "
            "printed?\n\n" + _FIXTURE_ORDER_CODE,
            "Fixtures that a test needs are set up dependency-first: `b` requests `a`, so `a` "
            "is set up before `b`. The code after each `yield` runs after the test, in the "
            "reverse order of setup (like nested context managers), so `b` is torn down "
            "before `a`. Teardown never runs before the test body.",
            "`setup a`, `setup b`, `test body`, `teardown a`, `teardown b`",
            "`setup b`, `setup a`, `test body`, `teardown b`, `teardown a`",
            "`setup a`, `setup b`, `test body`, `teardown b`, `teardown a`",
            "`setup a`, `setup b`, `teardown b`, `teardown a`, `test body`",
        ),
        _t(
            "Executando com `pytest -s` (saída não capturada), em que ordem estas linhas são "
            "impressas?\n\n" + _FIXTURE_ORDER_CODE,
            "As fixtures de que um teste precisa são preparadas começando pelas dependências: "
            "`b` pede `a`, então `a` é preparada antes de `b`. O código depois de cada `yield` "
            "roda após o teste, na ordem inversa da preparação (como context managers "
            "aninhados), então `b` é desfeita antes de `a`. O teardown nunca roda antes do "
            "corpo do teste.",
            "`setup a`, `setup b`, `test body`, `teardown a`, `teardown b`",
            "`setup b`, `setup a`, `test body`, `teardown b`, `teardown a`",
            "`setup a`, `setup b`, `test body`, `teardown b`, `teardown a`",
            "`setup a`, `setup b`, `teardown b`, `teardown a`, `test body`",
        ),
    ),
    _q(
        "testing-with-pytest-q06",
        "testing-with-pytest",
        MC,
        MEDIUM,
        ("d",),
        ("mock", "patch"),
        _t(
            "The module `app.services.user_service` does `from app.email import send_email` and "
            "calls `send_email(...)` inside `create_user`. In a test you want to replace "
            "`send_email` with a mock. Which target should you give to `patch`?",
            "`patch` rebinds a *name* in a namespace. Because of the `from ... import`, "
            "`user_service` holds its own reference to the function, and that is the name "
            "`create_user` looks up, so you patch it where it is used: "
            "`app.services.user_service.send_email`. Patching `app.email.send_email` changes a "
            "different binding and the call still reaches the real function. Both names "
            "pointing to the same object does not make them the same name, and patching "
            "the package attribute `app.email` does not touch the already-imported reference.",
            '`patch("app.email.send_email")`, where the function is defined.',
            "Either `app.email.send_email` or `app.services.user_service.send_email`, because "
            "both names refer to the same function object.",
            '`patch("app.email")`, which replaces the whole module everywhere.',
            '`patch("app.services.user_service.send_email")`, where the name is looked up.',
        ),
        _t(
            "O módulo `app.services.user_service` faz `from app.email import send_email` e "
            "chama `send_email(...)` dentro de `create_user`. Em um teste você quer substituir "
            "`send_email` por um mock. Qual alvo você deve passar ao `patch`?",
            "O `patch` religa um *nome* em um namespace. Por causa do `from ... import`, o "
            "`user_service` guarda sua própria referência à função, e é esse o nome que "
            "`create_user` consulta, então você faz o patch onde ela é usada: "
            "`app.services.user_service.send_email`. Aplicar patch em `app.email.send_email` "
            "altera outra ligação e a chamada continua chegando à função real. Dois nomes "
            "apontarem para o mesmo objeto não os torna o mesmo nome, e aplicar patch no "
            "atributo `app.email` do pacote não afeta a referência já importada.",
            '`patch("app.email.send_email")`, onde a função é definida.',
            "Tanto `app.email.send_email` quanto `app.services.user_service.send_email`, pois "
            "os dois nomes se referem ao mesmo objeto função.",
            '`patch("app.email")`, que substitui o módulo inteiro em todo lugar.',
            '`patch("app.services.user_service.send_email")`, onde o nome é consultado.',
        ),
    ),
    _q(
        "testing-with-pytest-q07",
        "testing-with-pytest",
        MS,
        MEDIUM,
        ("a", "b", "d"),
        ("fixtures", "scope", "monkeypatch"),
        _t(
            "Which statements about pytest fixtures and `monkeypatch` are true? Select all "
            "that apply.",
            "`monkeypatch` changes (environment variables, attributes, dict items) are undone "
            'automatically when the test ends. A `scope="session"` fixture is created once per '
            "run. Code after `yield` is the teardown and runs even when the test fails. A "
            "wider-scoped fixture cannot depend on a narrower one (pytest reports a "
            "`ScopeMismatch`), because the wide fixture would outlive what it depends on.",
            "Changes made with `monkeypatch` are undone automatically when the test ends.",
            'A fixture with `scope="session"` is created once per test run.',
            "A session-scoped fixture can safely request a function-scoped fixture.",
            "Code after `yield` in a fixture still runs when the test fails.",
            "Code after `yield` in a fixture runs only when the test passes.",
        ),
        _t(
            "Quais afirmações sobre fixtures do pytest e `monkeypatch` são verdadeiras? "
            "Selecione todas que se aplicam.",
            "As alterações feitas com `monkeypatch` (variáveis de ambiente, atributos, itens "
            "de dict) são desfeitas automaticamente quando o teste termina. Uma fixture com "
            '`scope="session"` é criada uma vez por execução. O código depois do `yield` é o '
            "teardown e roda mesmo quando o teste falha. Uma fixture de escopo maior não pode "
            "depender de uma de escopo menor (o pytest reporta `ScopeMismatch`), pois a "
            "fixture ampla sobreviveria àquilo de que depende.",
            "As alterações feitas com `monkeypatch` são desfeitas automaticamente quando o "
            "teste termina.",
            'Uma fixture com `scope="session"` é criada uma vez por execução de testes.',
            "Uma fixture de escopo session pode pedir com segurança uma fixture de escopo "
            "function.",
            "O código depois do `yield` em uma fixture ainda roda quando o teste falha.",
            "O código depois do `yield` em uma fixture roda apenas quando o teste passa.",
        ),
    ),
    _q(
        "testing-with-pytest-q08",
        "testing-with-pytest",
        MC,
        MEDIUM,
        ("d",),
        ("coverage",),
        _t(
            "A function is just `return a / b`, and a single test asserts `div(4, 2) == 2`. "
            "The coverage report shows 100%. What does that tell you?",
            "Line coverage only says each line was executed at least once during the tests. It "
            "does not say the assertions are meaningful, nor that edge cases such as `b == 0` "
            "were exercised: here the division by zero is untested despite the 100%. Coverage "
            "is useful to find code that is never run, not to prove correctness, and it does "
            "not require a test per input value.",
            "The function is fully tested, including the case `b == 0`.",
            "No bug is possible in this function.",
            "The report is wrong, since 100% requires a test for every possible input value.",
            "Every line ran at least once; it says nothing about edge cases such as `b == 0` "
            "or about the quality of the assertions.",
        ),
        _t(
            "Uma função é apenas `return a / b`, e um único teste verifica `div(4, 2) == 2`. O "
            "relatório de cobertura mostra 100%. O que isso diz a você?",
            "A cobertura de linhas só diz que cada linha foi executada ao menos uma vez nos "
            "testes. Ela não diz se as asserções são significativas, nem se casos extremos como "
            "`b == 0` foram exercitados: aqui a divisão por zero está sem teste apesar dos "
            "100%. Cobertura serve para achar código que nunca roda, não para provar "
            "correção, e não exige um teste por valor de entrada.",
            "A função está totalmente testada, inclusive o caso `b == 0`.",
            "Nenhum bug é possível nesta função.",
            "O relatório está errado, pois 100% exige um teste para cada valor de entrada "
            "possível.",
            "Toda linha rodou ao menos uma vez; isso não diz nada sobre casos extremos como "
            "`b == 0` nem sobre a qualidade das asserções.",
        ),
    ),
    _q(
        "testing-with-pytest-q09",
        "testing-with-pytest",
        CODE,
        HARD,
        ("c",),
        ("mock", "autospec"),
        _t(
            "Which of the two calls raises an exception?\n\n" + _AUTOSPEC_CODE,
            "A plain `Mock` accepts any arguments, so call 1 succeeds even though `charge` "
            "takes two. `create_autospec(charge)` copies the real signature, so call 2, with "
            "a missing `currency`, raises `TypeError`. This is why autospec (or `spec=`) makes "
            "mocks safer: they fail when the real function's signature changes, instead of "
            "silently drifting away from it.",
            "Neither call raises.",
            "Only call 1 (`loose`) raises `TypeError`.",
            "Only call 2 (`strict`) raises `TypeError`.",
            "Both calls raise `TypeError`.",
        ),
        _t(
            "Qual das duas chamadas lança uma exceção?\n\n" + _AUTOSPEC_CODE,
            "Um `Mock` simples aceita quaisquer argumentos, então a chamada 1 funciona mesmo "
            "que `charge` receba dois. `create_autospec(charge)` copia a assinatura real, então "
            "a chamada 2, sem `currency`, lança `TypeError`. Por isso autospec (ou `spec=`) "
            "deixa os mocks mais seguros: eles falham quando a assinatura da função real muda, "
            "em vez de se afastarem dela silenciosamente.",
            "Nenhuma das chamadas lança exceção.",
            "Somente a chamada 1 (`loose`) lança `TypeError`.",
            "Somente a chamada 2 (`strict`) lança `TypeError`.",
            "As duas chamadas lançam `TypeError`.",
        ),
    ),
    _q(
        "testing-with-pytest-q10",
        "testing-with-pytest",
        SHORT,
        HARD,
        None,
        ("mock", "test-design"),
        _t(
            "\"Don't mock what you don't own.\" Explain the risk of patching a third-party "
            "library's internals in unit tests, and what to do instead.",
            "Self-check against the model answer: did you mention (1) assumptions about the "
            "library's behavior baked into the test, (2) tests that pass while reality "
            "differs, and (3) a wrapper you own plus a few real integration tests?",
            model_answer="Patching, for example, an SDK call encodes your guess of its "
            "internals and return shape into the test. When the library changes, or behaves "
            "differently from your guess (errors, rate limits, edge cases), the test stays "
            "green while production breaks, and the test is coupled to implementation details. "
            "Instead, wrap the third-party call in a small interface you own (a gateway or "
            "adapter), mock that boundary in unit tests (ideally with `spec`/autospec), and "
            "cover the real integration with a few separate integration tests against the real "
            "service or its sandbox.",
        ),
        _t(
            '"Não faça mock do que você não possui." Explique o risco de aplicar patch nos '
            "internos de uma biblioteca de terceiros em testes unitários e o que fazer em vez "
            "disso.",
            "Autoavaliação contra a resposta-modelo: você mencionou (1) suposições sobre o "
            "comportamento da biblioteca embutidas no teste, (2) testes que passam enquanto a "
            "realidade é outra e (3) um wrapper próprio mais alguns testes de integração "
            "reais?",
            model_answer="Fazer patch, por exemplo, de uma chamada de SDK embute no teste o seu "
            "palpite sobre os internos e o formato de retorno. Quando a biblioteca muda, ou "
            "se comporta diferente do palpite (erros, rate limits, casos extremos), o teste "
            "continua verde enquanto a produção quebra, e o teste fica acoplado a detalhes de "
            "implementação. Em vez disso, encapsule a chamada de terceiros em uma interface "
            "pequena que você controla (um gateway ou adapter), faça mock dessa fronteira nos "
            "testes unitários (de preferência com `spec`/autospec) e cubra a integração real "
            "com poucos testes de integração separados, contra o serviço real ou seu sandbox.",
        ),
    ),
)

QUESTIONS: tuple[QuestionSeed, ...] = tuple(
    sorted(
        _PILOT_QUESTIONS + _FUNDAMENTALS_EXTRA + _TYPE_HINTS_EXTRA + _ASYNC_EXTRA + _PYTEST_EXTRA,
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
        code="async-python-quiz",
        title="Async Python Quiz",
        description="Coroutines, the event loop, gather and TaskGroup, cancellation, blocking "
        "calls and when async is the wrong tool.",
        kind=AssessmentKind.COMPETENCY,
        competency_slug="async-python",
        translations={
            "pt-BR": {
                "title": "Quiz de Python Assíncrono",
                "description": "Coroutines, o event loop, gather e TaskGroup, cancelamento, "
                "chamadas bloqueantes e quando async é a ferramenta errada.",
            }
        },
    ),
    AssessmentSeed(
        code="testing-with-pytest-quiz",
        title="Testing with Pytest Quiz",
        description="Fixtures and scopes, parametrization, markers, mocking and patching, "
        "exception tests and what coverage really tells you.",
        kind=AssessmentKind.COMPETENCY,
        competency_slug="testing-with-pytest",
        translations={
            "pt-BR": {
                "title": "Quiz de Testes com Pytest",
                "description": "Fixtures e escopos, parametrização, markers, mocks e patching, "
                "testes de exceção e o que a cobertura realmente diz.",
            }
        },
    ),
    AssessmentSeed(
        code="python-core-checkpoint",
        title="Python Core Checkpoint",
        description="A mixed check across fundamentals, type hints, async and testing.",
        kind=AssessmentKind.MIXED,
        question_codes=(
            "python-fundamentals-q01",
            "python-fundamentals-q04",
            "python-fundamentals-q08",
            "python-fundamentals-q10",
            "python-type-hints-q01",
            "python-type-hints-q02",
            "python-type-hints-q04",
            "python-type-hints-q09",
            "async-python-q02",
            "async-python-q05",
            "async-python-q09",
            "testing-with-pytest-q03",
            "testing-with-pytest-q05",
            "testing-with-pytest-q08",
        ),
        translations={
            "pt-BR": {
                "title": "Checkpoint do Núcleo de Python",
                "description": "Uma verificação mista entre fundamentos, type hints, código "
                "assíncrono e testes.",
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
