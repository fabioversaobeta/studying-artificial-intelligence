"""Question bank for the Software Engineering subject (solid-principles,
design-patterns, clean-architecture, domain-driven-design, testing-strategy;
ten questions each, English + Brazilian Portuguese).

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
        options=_options(*options) if options else None,
        model_answer=model_answer,
    )


def _q(
    competency: str,
    n: int,
    type_: QuestionType,
    difficulty: QuestionDifficulty,
    correct: str | None,
    tags: tuple[str, ...],
    en: QuestionText,
    pt: QuestionText,
) -> QuestionSeed:
    """`correct` is a string of option ids ("b", "ac") or None for short answers."""
    return QuestionSeed(
        code=f"{competency}-q{n:02d}",
        competency_slug=competency,
        type=type_,
        difficulty=difficulty,
        correct=tuple(correct) if correct else None,
        tags=tags,
        source=AI,
        text={Language.EN: en, Language.PT_BR: pt},
    )


# ----------------------------------------------------------------------
# solid-principles
# ----------------------------------------------------------------------

_LSP_CODE = """```python
class Rectangle:
    def __init__(self, w, h):
        self.w, self.h = w, h

    def set_width(self, w):
        self.w = w

    def area(self):
        return self.w * self.h


class Square(Rectangle):
    def set_width(self, w):
        self.w = self.h = w


def widen_to_five(r):
    r.h = 2
    r.set_width(5)
    return r.area()
```"""

_SOLID = "solid-principles"

SOLID_QUESTIONS: tuple[QuestionSeed, ...] = (
    _q(
        _SOLID,
        1,
        MC,
        EASY,
        "b",
        ("srp",),
        _t(
            "What does the Single Responsibility Principle (SRP) actually say?",
            "SRP is about cohesion: a module should have one reason to change, i.e. it "
            "serves one concern or one stakeholder. A class with a single method can still "
            "mix concerns (A), a one-line class is not the goal (C), and SRP says nothing "
            "about creating new instances (D).",
            (
                "A class should expose only one public method.",
                "A class should have only one reason to change: it serves a single concern.",
                "A class should be split until each class is only a few lines long.",
                "A class should be instantiated only once during the program's lifetime.",
            ),
        ),
        _t(
            "O que o Princípio da Responsabilidade Única (SRP) realmente diz?",
            "O SRP trata de coesão: um módulo deve ter um único motivo para mudar, ou seja, "
            "atender a uma só preocupação ou a um só interessado. Uma classe com um único "
            "método ainda pode misturar preocupações (A), classes de uma linha não são o "
            "objetivo (C) e o SRP não diz nada sobre quantas instâncias são criadas (D).",
            (
                "Uma classe deve expor apenas um método público.",
                "Uma classe deve ter apenas um motivo para mudar, pois atende a uma única "
                "preocupação.",
                "Uma classe deve ser dividida até que cada uma tenha poucas linhas.",
                "Uma classe deve ser instanciada uma única vez durante a vida do programa.",
            ),
        ),
    ),
    _q(
        _SOLID,
        2,
        MC,
        EASY,
        "d",
        ("ocp",),
        _t(
            "Which situation best illustrates the Open/Closed Principle?",
            "OCP means new behavior arrives by adding new code (for example a new "
            "implementation of an existing abstraction) instead of editing code that is "
            "already tested and in use. Editing the existing branches (A), copying code (B) "
            "and making fields public (C) all increase the risk of breaking what works.",
            (
                "Adding a new `elif` branch to a long conditional every time a new case appears.",
                "Copy-pasting a class and tweaking the copy for each new customer.",
                "Making every field public so other code can extend the object freely.",
                "Supporting a new payment method by adding a new class that implements an "
                "existing `PaymentMethod` interface.",
            ),
        ),
        _t(
            "Qual situação ilustra melhor o Princípio Aberto/Fechado (OCP)?",
            "O OCP significa que um novo comportamento chega por código novo (por exemplo, "
            "uma nova implementação de uma abstração existente) em vez de editar código já "
            "testado e em uso. Editar os ramos existentes (A), copiar código (B) e tornar "
            "campos públicos (C) aumentam o risco de quebrar o que já funciona.",
            (
                "Adicionar um novo `elif` a uma condicional longa sempre que surge um caso novo.",
                "Copiar e colar uma classe e ajustar a cópia para cada novo cliente.",
                "Tornar todos os campos públicos para que outro código possa estender o objeto "
                "livremente.",
                "Suportar um novo meio de pagamento criando uma nova classe que implementa a "
                "interface `PaymentMethod` já existente.",
            ),
        ),
    ),
    _q(
        _SOLID,
        3,
        MC,
        EASY,
        "a",
        ("dip",),
        _t(
            "What is the core idea of the Dependency Inversion Principle (DIP)?",
            "DIP says high-level policy should not depend on low-level details; both should "
            "depend on abstractions, and the abstraction is shaped by the needs of the "
            "high-level code. B is the opposite, C describes a tool (a DI container) rather "
            "than the principle, and D reverses the actual rule.",
            (
                "High-level modules and low-level modules should both depend on abstractions.",
                "High-level modules should import concrete low-level classes directly for speed.",
                "Every class must receive its dependencies from a dependency injection container.",
                "Abstractions should be defined in terms of the details of their implementations.",
            ),
        ),
        _t(
            "Qual é a ideia central do Princípio da Inversão de Dependência (DIP)?",
            "O DIP diz que a política de alto nível não deve depender de detalhes de baixo "
            "nível; ambos devem depender de abstrações, e a abstração é moldada pelas "
            "necessidades do código de alto nível. A B é o oposto, a C descreve uma "
            "ferramenta (um contêiner de DI) e não o princípio, e a D inverte a regra real.",
            (
                "Módulos de alto nível e de baixo nível devem depender de abstrações.",
                "Módulos de alto nível devem importar classes concretas de baixo nível "
                "diretamente, por velocidade.",
                "Toda classe deve receber suas dependências de um contêiner de injeção de "
                "dependência.",
                "Abstrações devem ser definidas em termos dos detalhes de suas implementações.",
            ),
        ),
    ),
    _q(
        _SOLID,
        4,
        CODE,
        MEDIUM,
        "c",
        ("lsp", "inheritance"),
        _t(
            "What do `widen_to_five(Rectangle(1, 1))` and `widen_to_five(Square(1, 1))` return, "
            "and what does this show?\n\n" + _LSP_CODE,
            "Rectangle: height is set to 2, width to 5, so the area is 10. Square: setting the "
            "height to 2 and then the width to 5 also resets the height to 5, so the area is "
            "25. Code written against `Rectangle` assumes width and height vary independently; "
            "`Square` breaks that behavioral contract, so it is not safely substitutable (LSP "
            "violation) even though the types look compatible.",
            (
                "`10` and `10`; `Square` is a valid specialization of `Rectangle`.",
                "`10` and `10`; the result is the same because both classes share `area()`.",
                "`10` and `25`; `Square` is not substitutable for `Rectangle`, which violates LSP.",
                "`10` and `25`; this is expected polymorphism and respects LSP.",
            ),
        ),
        _t(
            "O que `widen_to_five(Rectangle(1, 1))` e `widen_to_five(Square(1, 1))` retornam, "
            "e o que isso demonstra?\n\n" + _LSP_CODE,
            "Rectangle: a altura vira 2 e a largura 5, então a área é 10. Square: definir a "
            "altura como 2 e depois a largura como 5 também muda a altura para 5, então a área "
            "é 25. O código escrito para `Rectangle` assume que largura e altura variam de "
            "forma independente; `Square` quebra esse contrato comportamental, logo não é "
            "substituível com segurança (violação do LSP), mesmo que os tipos pareçam "
            "compatíveis.",
            (
                "`10` e `10`; `Square` é uma especialização válida de `Rectangle`.",
                "`10` e `10`; o resultado é o mesmo porque as duas classes compartilham `area()`.",
                "`10` e `25`; `Square` não é substituível por `Rectangle`, o que viola o LSP.",
                "`10` e `25`; isso é polimorfismo esperado e respeita o LSP.",
            ),
        ),
    ),
    _q(
        _SOLID,
        5,
        MC,
        MEDIUM,
        "d",
        ("isp",),
        _t(
            "A `MultiFunctionDevice` interface declares `print()`, `scan()` and `fax()`. A "
            "basic `LaserPrinter` must implement it, so it raises `NotImplementedError` in "
            "`scan()` and `fax()`. Which principle is primarily broken, and what is the remedy?",
            "Clients are forced to depend on methods they do not use, which is exactly what "
            "ISP forbids; the stubs that raise errors are the symptom (and a latent LSP "
            "problem). Splitting into role interfaces such as `Printer`, `Scanner` and `Fax` "
            "lets each class implement only what it supports. SRP (B) concerns reasons to "
            "change of a class, OCP (A) is not about interface width, and DIP (C) would not "
            "remove the unused methods.",
            (
                "OCP; add a subclass for every device type.",
                "SRP; split `LaserPrinter` into several concrete classes.",
                "DIP; make the interface depend on the concrete `LaserPrinter`.",
                "ISP; split the interface into small role interfaces (`Printer`, `Scanner`, "
                "`Fax`) that each class picks from.",
            ),
        ),
        _t(
            "Uma interface `MultiFunctionDevice` declara `print()`, `scan()` e `fax()`. Uma "
            "`LaserPrinter` simples precisa implementá-la, então lança `NotImplementedError` "
            "em `scan()` e `fax()`. Qual princípio é principalmente violado e qual é o "
            "remédio?",
            "Os clientes são forçados a depender de métodos que não usam, exatamente o que o "
            "ISP proíbe; os stubs que lançam erro são o sintoma (e um problema latente de "
            "LSP). Dividir em interfaces de papel como `Printer`, `Scanner` e `Fax` permite "
            "que cada classe implemente apenas o que suporta. O SRP (B) trata dos motivos de "
            "mudança de uma classe, o OCP (A) não é sobre a largura da interface e o DIP (C) "
            "não removeria os métodos sem uso.",
            (
                "OCP; criar uma subclasse para cada tipo de dispositivo.",
                "SRP; dividir `LaserPrinter` em várias classes concretas.",
                "DIP; fazer a interface depender da `LaserPrinter` concreta.",
                "ISP; dividir a interface em interfaces de papel pequenas (`Printer`, "
                "`Scanner`, `Fax`) das quais cada classe escolhe o que precisa.",
            ),
        ),
    ),
    _q(
        _SOLID,
        6,
        MS,
        MEDIUM,
        "ac",
        ("ocp", "polymorphism"),
        _t(
            "`total(order)` computes a price using an `if/elif` chain on `order.customer_type` "
            "(`regular`, `vip`, `staff`), and a new customer type is requested every quarter. "
            "Which TWO changes make the design better follow the Open/Closed Principle?",
            "Both correct options move the varying rule behind an abstraction so that a new "
            "customer type is added as new code (a new policy class or a new registry entry) "
            "without editing `total`. Adding one more `elif` (B) is exactly the modification "
            "OCP wants to avoid, relocating the same chain to another module (D) only moves "
            "the problem, and a single class that knows everything (E) concentrates the "
            "change pressure.",
            (
                "Define a `DiscountPolicy` interface with one implementation per customer type "
                "and have `total` call it.",
                "Add another `elif` for each new customer type and keep the tests green.",
                "Keep a mapping from customer type to policy object so a new type is "
                "registered rather than editing `total`.",
                "Move the same `if/elif` chain into a function in a `utils` module.",
                "Put all pricing rules in one large `PricingManager` class.",
            ),
        ),
        _t(
            "`total(order)` calcula um preço com uma cadeia `if/elif` sobre "
            "`order.customer_type` (`regular`, `vip`, `staff`), e um novo tipo de cliente é "
            "pedido a cada trimestre. Quais DUAS mudanças fazem o design seguir melhor o "
            "Princípio Aberto/Fechado?",
            "As duas opções corretas movem a regra variável para trás de uma abstração, de "
            "modo que um novo tipo de cliente entra como código novo (uma nova classe de "
            "política ou uma nova entrada no registro) sem editar `total`. Acrescentar mais "
            "um `elif` (B) é exatamente a modificação que o OCP quer evitar, mover a mesma "
            "cadeia para outro módulo (D) só desloca o problema, e uma única classe que sabe "
            "de tudo (E) concentra a pressão de mudança.",
            (
                "Definir uma interface `DiscountPolicy` com uma implementação por tipo de "
                "cliente e fazer `total` chamá-la.",
                "Adicionar outro `elif` para cada novo tipo de cliente e manter os testes verdes.",
                "Manter um mapeamento de tipo de cliente para objeto de política, de modo "
                "que um novo tipo seja registrado em vez de editar `total`.",
                "Mover a mesma cadeia `if/elif` para uma função em um módulo `utils`.",
                "Colocar todas as regras de preço em uma única classe grande `PricingManager`.",
            ),
        ),
    ),
    _q(
        _SOLID,
        7,
        MC,
        MEDIUM,
        "b",
        ("dip", "dependency-injection"),
        _t(
            "A team wires `OrderService` with a DI container that injects a "
            "`PostgresOrderRepository` through the constructor parameter "
            "`repo: PostgresOrderRepository`. Does this satisfy the Dependency Inversion "
            "Principle?",
            "No. Injection is a mechanism for supplying dependencies; DIP is about the "
            "direction of the source-code dependency. `OrderService` still names the concrete "
            "Postgres class, so business logic depends on a detail. It should depend on an "
            "abstraction such as `OrderRepository`, owned by the high-level layer, which the "
            "Postgres class implements.",
            (
                "Yes, because the dependency is injected rather than created with `new`.",
                "No, because `OrderService` still depends on a concrete class; it should "
                "depend on an `OrderRepository` abstraction.",
                "Yes, because a container is in use and containers always invert dependencies.",
                "No, because DIP forbids constructor injection and requires setters.",
            ),
        ),
        _t(
            "Uma equipe monta o `OrderService` com um contêiner de DI que injeta um "
            "`PostgresOrderRepository` pelo parâmetro de construtor "
            "`repo: PostgresOrderRepository`. Isso satisfaz o Princípio da Inversão de "
            "Dependência?",
            "Não. Injeção é um mecanismo para fornecer dependências; o DIP trata do sentido "
            "da dependência no código-fonte. O `OrderService` ainda cita a classe concreta "
            "do Postgres, então a lógica de negócio depende de um detalhe. Ele deveria "
            "depender de uma abstração como `OrderRepository`, pertencente à camada de alto "
            "nível, que a classe do Postgres implementa.",
            (
                "Sim, porque a dependência é injetada em vez de criada com `new`.",
                "Não, porque o `OrderService` ainda depende de uma classe concreta; deveria "
                "depender de uma abstração `OrderRepository`.",
                "Sim, porque há um contêiner em uso e contêineres sempre invertem dependências.",
                "Não, porque o DIP proíbe injeção por construtor e exige setters.",
            ),
        ),
    ),
    _q(
        _SOLID,
        8,
        MC,
        MEDIUM,
        "a",
        ("srp", "refactoring"),
        _t(
            "An `Invoice` class has `calculate_total()`, `save_to_database()` and "
            "`send_email_to_customer()`. Which refactoring best applies SRP?",
            "Pricing rules, persistence and notification change for different reasons and "
            "driven by different people, so each gets its own cohesive collaborator while "
            "`Invoice` keeps the domain behavior. Private helpers (B) leave everything in one "
            "class, a manager (C) is the same god class under a new name, and static "
            "utilities (D) still bind the entity to the database and the mail system.",
            (
                "Keep `Invoice` for the domain rules, and add an `InvoiceRepository` for "
                "persistence and an `InvoiceMailer` for notification.",
                "Keep all three methods in `Invoice` but make two of them private.",
                "Create an `InvoiceManager` that contains all three behaviors.",
                "Move the persistence and email code into static methods of an "
                "`InvoiceUtils` class that `Invoice` calls.",
            ),
        ),
        _t(
            "Uma classe `Invoice` tem `calculate_total()`, `save_to_database()` e "
            "`send_email_to_customer()`. Qual refatoração aplica melhor o SRP?",
            "Regras de preço, persistência e notificação mudam por motivos diferentes e "
            "movidas por pessoas diferentes, então cada uma ganha um colaborador coeso "
            "próprio, enquanto `Invoice` mantém o comportamento de domínio. Métodos "
            "privados (B) deixam tudo na mesma classe, um gerenciador (C) é a mesma god "
            "class com outro nome, e utilitários estáticos (D) ainda prendem a entidade ao "
            "banco e ao sistema de e-mail.",
            (
                "Manter `Invoice` para as regras de domínio e adicionar um "
                "`InvoiceRepository` para persistência e um `InvoiceMailer` para "
                "notificação.",
                "Manter os três métodos em `Invoice`, mas tornar dois deles privados.",
                "Criar um `InvoiceManager` que contém os três comportamentos.",
                "Mover o código de persistência e de e-mail para métodos estáticos de uma "
                "classe `InvoiceUtils` chamada por `Invoice`.",
            ),
        ),
    ),
    _q(
        _SOLID,
        9,
        MC,
        HARD,
        "c",
        ("lsp", "design-by-contract"),
        _t(
            "The base class contract is: `withdraw(amount)` raises `InsufficientFunds` if "
            "`amount` exceeds the balance, otherwise reduces the balance by `amount`. Which "
            "override most clearly violates the Liskov Substitution Principle?",
            "A subclass may weaken preconditions and strengthen postconditions, but not the "
            "reverse. Rejecting amounts that are not multiples of 100 strengthens the "
            "precondition: callers valid against the base contract now fail. Writing an audit "
            "entry (A), returning a richer result that keeps the old fields (B) and raising a "
            "subclass of the documented exception (D) all keep the base contract intact.",
            (
                "An override that also writes an audit log entry on each withdrawal.",
                "An override that returns a receipt object extending the original result type.",
                "An override that rejects any amount that is not a multiple of 100.",
                "An override that raises `DailyLimitExceeded`, a subclass of "
                "`InsufficientFunds`, when appropriate.",
            ),
        ),
        _t(
            "O contrato da classe base é: `withdraw(amount)` lança `InsufficientFunds` se "
            "`amount` excede o saldo, caso contrário reduz o saldo em `amount`. Qual "
            "sobrescrita viola mais claramente o Princípio da Substituição de Liskov?",
            "Uma subclasse pode enfraquecer pré-condições e fortalecer pós-condições, mas "
            "não o contrário. Rejeitar valores que não são múltiplos de 100 fortalece a "
            "pré-condição: chamadores válidos segundo o contrato da base passam a falhar. "
            "Gravar uma entrada de auditoria (A), retornar um resultado mais rico que mantém "
            "os campos antigos (B) e lançar uma subclasse da exceção documentada (D) "
            "preservam o contrato da base.",
            (
                "Uma sobrescrita que também grava uma entrada de log de auditoria a cada saque.",
                "Uma sobrescrita que retorna um recibo que estende o tipo de resultado original.",
                "Uma sobrescrita que rejeita qualquer valor que não seja múltiplo de 100.",
                "Uma sobrescrita que lança `DailyLimitExceeded`, subclasse de "
                "`InsufficientFunds`, quando apropriado.",
            ),
        ),
    ),
    _q(
        _SOLID,
        10,
        SHORT,
        HARD,
        None,
        ("ocp", "dip", "tradeoffs"),
        _t(
            "How does the Dependency Inversion Principle help you achieve the Open/Closed "
            "Principle, and what is a cost of applying both too eagerly?",
            "Self-check: did you mention (1) abstractions as the extension point, (2) new "
            "behavior arriving as new implementations without editing the high-level code, "
            "and (3) a cost such as speculative abstractions and indirection?",
            None,
            "When high-level code depends on an abstraction (an interface or port) instead of "
            "concrete classes, new behavior can be added by writing a new implementation of "
            "that abstraction and wiring it in, without modifying the tested high-level code. "
            "The abstraction is the extension point, so DIP is a common mechanism for OCP. The "
            "cost of over-applying both is speculative interfaces for things that never vary, "
            "extra indirection that makes code harder to read and navigate, and more files "
            "to maintain; abstract where change is likely or where a boundary matters, not "
            "everywhere.",
        ),
        _t(
            "Como o Princípio da Inversão de Dependência ajuda a alcançar o Princípio "
            "Aberto/Fechado, e qual é o custo de aplicar ambos com excesso de zelo?",
            "Autoavaliação: você mencionou (1) abstrações como ponto de extensão, (2) novo "
            "comportamento chegando como novas implementações sem editar o código de alto "
            "nível e (3) um custo como abstrações especulativas e indireção?",
            None,
            "Quando o código de alto nível depende de uma abstração (interface ou port) em "
            "vez de classes concretas, um novo comportamento pode ser adicionado escrevendo "
            "uma nova implementação dessa abstração e ligando-a ao sistema, sem modificar o "
            "código de alto nível já testado. A abstração é o ponto de extensão, então o DIP "
            "é um mecanismo comum para o OCP. O custo de aplicar ambos em excesso são "
            "interfaces especulativas para o que nunca varia, indireção extra que dificulta "
            "ler e navegar no código e mais arquivos para manter; abstraia onde a mudança é "
            "provável ou onde há uma fronteira relevante, não em todo lugar.",
        ),
    ),
)

SOLID_ASSESSMENT = AssessmentSeed(
    code="software-engineering-solid-principles-quiz",
    title="SOLID Principles Quiz",
    description="The five SOLID principles: definitions, trade-offs and spotting violations.",
    kind=AssessmentKind.COMPETENCY,
    competency_slug="solid-principles",
    translations={
        "pt-BR": {
            "title": "Quiz de Princípios SOLID",
            "description": "Os cinco princípios SOLID: definições, trade-offs e como "
            "identificar violações.",
        }
    },
)

# ----------------------------------------------------------------------
# design-patterns
# ----------------------------------------------------------------------

_DECORATOR_CODE = """```python
class Source:
    def read(self):
        return "  hello  "


class Upper:
    def __init__(self, inner):
        self.inner = inner

    def read(self):
        return self.inner.read().upper()


class Wrap:
    def __init__(self, inner):
        self.inner = inner

    def read(self):
        return f"[{self.inner.read()}]"


class Strip:
    def __init__(self, inner):
        self.inner = inner

    def read(self):
        return self.inner.read().strip()


pipeline = Strip(Wrap(Upper(Source())))
print(pipeline.read())
```"""

_PAT = "design-patterns"

PATTERNS_QUESTIONS: tuple[QuestionSeed, ...] = (
    _q(
        _PAT,
        1,
        MC,
        EASY,
        "c",
        ("strategy",),
        _t(
            "What is the intent of the Strategy pattern?",
            "Strategy puts each member of a family of algorithms behind a common interface "
            "so they are interchangeable and can be chosen at runtime, without the context "
            "knowing the details. A describes Singleton, B describes Observer, and D "
            "describes Builder.",
            (
                "Guarantee that a class has exactly one instance with a global access point.",
                "Notify many dependents automatically when an object's state changes.",
                "Encapsulate interchangeable algorithms behind a common interface so the "
                "behavior can be swapped at runtime.",
                "Construct a complex object step by step through a readable sequence of calls.",
            ),
        ),
        _t(
            "Qual é a intenção do padrão Strategy?",
            "O Strategy coloca cada algoritmo de uma família atrás de uma interface comum, "
            "para que sejam intercambiáveis e possam ser escolhidos em tempo de execução, "
            "sem que o contexto conheça os detalhes. A descreve o Singleton, a B descreve o "
            "Observer e a D descreve o Builder.",
            (
                "Garantir que uma classe tenha exatamente uma instância com um ponto de "
                "acesso global.",
                "Notificar automaticamente vários dependentes quando o estado de um objeto muda.",
                "Encapsular algoritmos intercambiáveis atrás de uma interface comum, para "
                "trocar o comportamento em tempo de execução.",
                "Construir um objeto complexo passo a passo por uma sequência legível de chamadas.",
            ),
        ),
    ),
    _q(
        _PAT,
        2,
        MC,
        EASY,
        "a",
        ("decorator",),
        _t(
            "Which pattern lets you add responsibilities to an object dynamically by wrapping "
            "it in another object that exposes the same interface?",
            "Decorator wraps a component with an object of the same interface and adds "
            "behavior before or after delegating, so decorators can be combined freely. "
            "Adapter (B) wraps to change the interface, Observer (C) is about notifications, "
            "and Builder (D) is about constructing objects.",
            (
                "Decorator",
                "Adapter",
                "Observer",
                "Builder",
            ),
        ),
        _t(
            "Qual padrão permite adicionar responsabilidades a um objeto dinamicamente, "
            "envolvendo-o em outro objeto que expõe a mesma interface?",
            "O Decorator envolve um componente com um objeto de mesma interface e adiciona "
            "comportamento antes ou depois de delegar, de modo que decorators podem ser "
            "combinados livremente. O Adapter (B) envolve para mudar a interface, o "
            "Observer (C) trata de notificações e o Builder (D) trata da construção de "
            "objetos.",
            (
                "Decorator",
                "Adapter",
                "Observer",
                "Builder",
            ),
        ),
    ),
    _q(
        _PAT,
        3,
        MC,
        EASY,
        "b",
        ("observer",),
        _t(
            "A chart, a table and a summary panel must all refresh whenever a data model "
            "changes, but the model should not know which views exist. Which pattern fits?",
            "Observer lets the subject (the model) keep a list of subscribers and notify "
            "them on change, without depending on their concrete types. Singleton (A) "
            "controls instance count, Factory Method (C) is about creating objects, and "
            "Adapter (D) reconciles incompatible interfaces; none of them provide change "
            "notification.",
            (
                "Singleton",
                "Observer",
                "Factory Method",
                "Adapter",
            ),
        ),
        _t(
            "Um gráfico, uma tabela e um painel de resumo precisam ser atualizados sempre "
            "que um modelo de dados muda, mas o modelo não deve saber quais views existem. "
            "Qual padrão se encaixa?",
            "O Observer permite que o sujeito (o modelo) mantenha uma lista de inscritos e "
            "os notifique quando muda, sem depender dos seus tipos concretos. O Singleton "
            "(A) controla o número de instâncias, o Factory Method (C) trata da criação de "
            "objetos e o Adapter (D) concilia interfaces incompatíveis; nenhum deles "
            "oferece notificação de mudanças.",
            (
                "Singleton",
                "Observer",
                "Factory Method",
                "Adapter",
            ),
        ),
    ),
    _q(
        _PAT,
        4,
        MC,
        MEDIUM,
        "d",
        ("builder",),
        _t(
            "A constructor call such as `HttpRequest(url, True, False, True, None, 30)` is "
            "unreadable, and most of the parameters are optional. Which pattern addresses "
            "this most directly?",
            "Builder assembles an object through named, optional steps "
            "(`.timeout(30).follow_redirects()`) and can validate the combination in a final "
            "`build()` call, which fixes both readability and invalid states. Factory Method "
            "(A) chooses which class to create but does not make the arguments readable, "
            "Observer (B) and Adapter (C) address different problems.",
            (
                "Factory Method, to pick the concrete request class.",
                "Observer, to notify the request about its own parameters.",
                "Adapter, to convert the positional arguments into a dictionary.",
                "Builder, to set each option through named steps and validate in a final "
                "`build()`.",
            ),
        ),
        _t(
            "Uma chamada de construtor como `HttpRequest(url, True, False, True, None, 30)` "
            "é ilegível, e a maioria dos parâmetros é opcional. Qual padrão resolve isso "
            "de forma mais direta?",
            "O Builder monta o objeto por passos nomeados e opcionais "
            "(`.timeout(30).follow_redirects()`) e pode validar a combinação em uma chamada "
            "final `build()`, resolvendo legibilidade e estados inválidos. O Factory Method "
            "(A) escolhe qual classe criar, mas não deixa os argumentos legíveis; o "
            "Observer (B) e o Adapter (C) resolvem outros problemas.",
            (
                "Factory Method, para escolher a classe concreta da requisição.",
                "Observer, para notificar a requisição sobre seus próprios parâmetros.",
                "Adapter, para converter os argumentos posicionais em um dicionário.",
                "Builder, para definir cada opção por passos nomeados e validar em um "
                "`build()` final.",
            ),
        ),
    ),
    _q(
        _PAT,
        5,
        CODE,
        MEDIUM,
        "b",
        ("decorator", "composition-order"),
        _t(
            "What does this program print?\n\n" + _DECORATOR_CODE,
            "Decorators apply from the innermost outwards. `Source` returns `'  hello  '`, "
            "`Upper` makes it `'  HELLO  '`, `Wrap` brackets it as `'[  HELLO  ]'`, and "
            "`Strip` finally removes whitespace only from the ends of that string. The spaces "
            "are inside the brackets, so they remain. The order of wrapping matters: putting "
            "`Strip` innermost would give `[HELLO]`.",
            (
                "`[HELLO]`",
                "`[  HELLO  ]`",
                "`  [HELLO]  `",
                "`HELLO`",
            ),
        ),
        _t(
            "O que este programa imprime?\n\n" + _DECORATOR_CODE,
            "Os decorators são aplicados de dentro para fora. `Source` retorna "
            "`'  hello  '`, `Upper` transforma em `'  HELLO  '`, `Wrap` coloca entre "
            "colchetes: `'[  HELLO  ]'`, e `Strip` remove espaços apenas das pontas dessa "
            "string. Os espaços estão dentro dos colchetes, então permanecem. A ordem do "
            "empilhamento importa: com `Strip` mais interno o resultado seria `[HELLO]`.",
            (
                "`[HELLO]`",
                "`[  HELLO  ]`",
                "`  [HELLO]  `",
                "`HELLO`",
            ),
        ),
    ),
    _q(
        _PAT,
        6,
        MC,
        MEDIUM,
        "a",
        ("observer", "memory-leaks"),
        _t(
            "A long-lived `EventBus` receives a new listener every time a screen opens, and "
            "the listeners are never removed. Memory keeps growing even after screens are "
            "closed. Which known weakness of the Observer pattern is this?",
            "This is the lapsed listener problem: the subject holds strong references to its "
            "observers, so they cannot be garbage-collected until explicitly unsubscribed. "
            "The usual remedies are unsubscribing on teardown (or returning an unsubscribe "
            "handle) and, where available, weak references. Observers do not need to be "
            "singletons (B), and the other options do not describe a leak.",
            (
                "Lapsed listeners: the subject keeps strong references until observers "
                "explicitly unsubscribe.",
                "Observers must be singletons, so every screen shares one listener.",
                "The subject should notify observers in separate processes to free memory.",
                "Observer is limited to a single subscriber per event type.",
            ),
        ),
        _t(
            "Um `EventBus` de longa duração recebe um novo listener toda vez que uma tela "
            "abre, e os listeners nunca são removidos. A memória continua crescendo mesmo "
            "depois que as telas são fechadas. Qual fraqueza conhecida do padrão Observer "
            "é essa?",
            "É o problema do lapsed listener: o sujeito mantém referências fortes aos "
            "observadores, que não podem ser coletados pelo garbage collector até que "
            "cancelem a inscrição explicitamente. Os remédios usuais são cancelar a "
            "inscrição no encerramento (ou devolver um handle de cancelamento) e, quando "
            "disponível, usar referências fracas. Observadores não precisam ser singletons "
            "(B) e as demais opções não descrevem um vazamento.",
            (
                "Lapsed listeners: o sujeito mantém referências fortes até que os "
                "observadores cancelem a inscrição explicitamente.",
                "Os observadores precisam ser singletons, então toda tela compartilha um "
                "único listener.",
                "O sujeito deveria notificar os observadores em processos separados para "
                "liberar memória.",
                "O Observer se limita a um único inscrito por tipo de evento.",
            ),
        ),
    ),
    _q(
        _PAT,
        7,
        MS,
        MEDIUM,
        "ad",
        ("adapter", "decorator"),
        _t(
            "Which TWO statements correctly contrast Adapter and Decorator?",
            "An Adapter exists to make an existing class fit an interface the client expects, "
            "so it changes the interface. A Decorator keeps the interface and adds behavior, "
            "and because each decorator is itself a component, they can be stacked. Decorator "
            "is not tied to inheritance (B), Adapter does not add behavior to every call (C), "
            "and Adapter wraps the adaptee without modifying its source (E).",
            (
                "An Adapter changes the interface the client sees; a Decorator keeps the same "
                "interface.",
                "A Decorator can only be implemented with inheritance, never with composition.",
                "An Adapter adds extra behavior to every method call it forwards.",
                "Decorators can be stacked because each one wraps an object that has the same "
                "interface.",
                "An Adapter requires modifying the source code of the class it adapts.",
            ),
        ),
        _t(
            "Quais DUAS afirmações contrastam corretamente Adapter e Decorator?",
            "Um Adapter existe para fazer uma classe existente se encaixar em uma interface "
            "que o cliente espera, portanto muda a interface. Um Decorator mantém a "
            "interface e adiciona comportamento, e como cada decorator também é um "
            "componente, eles podem ser empilhados. O Decorator não depende de herança (B), "
            "o Adapter não adiciona comportamento a cada chamada (C) e o Adapter envolve o "
            "adaptado sem modificar seu código-fonte (E).",
            (
                "Um Adapter muda a interface que o cliente enxerga; um Decorator mantém a "
                "mesma interface.",
                "Um Decorator só pode ser implementado com herança, nunca com composição.",
                "Um Adapter adiciona comportamento extra a cada chamada que repassa.",
                "Decorators podem ser empilhados porque cada um envolve um objeto que tem a "
                "mesma interface.",
                "Um Adapter exige modificar o código-fonte da classe que ele adapta.",
            ),
        ),
    ),
    _q(
        _PAT,
        8,
        MC,
        MEDIUM,
        "c",
        ("factory-method", "ocp"),
        _t(
            "Twelve places in a codebase contain `if kind == 'email': EmailNotifier(...) "
            "elif kind == 'sms': SmsNotifier(...)`. What is the main benefit of moving "
            "creation into a single factory method that returns a `Notifier`?",
            "Callers now depend only on the `Notifier` abstraction, and supporting a new "
            "kind means changing the one place that creates notifiers instead of twelve. "
            "A factory does not by itself make instances unique (A) or immutable (B), and "
            "the decision logic still exists somewhere, so it does not remove every "
            "conditional (D).",
            (
                "It guarantees that only one `Notifier` instance can ever exist.",
                "It makes every `Notifier` immutable.",
                "Callers depend only on the `Notifier` interface, and adding a kind changes "
                "one place instead of many.",
                "It removes every conditional from the program.",
            ),
        ),
        _t(
            "Doze lugares de uma base de código contêm `if kind == 'email': "
            "EmailNotifier(...) elif kind == 'sms': SmsNotifier(...)`. Qual o principal "
            "benefício de mover a criação para um único factory method que retorna um "
            "`Notifier`?",
            "Os chamadores passam a depender apenas da abstração `Notifier`, e suportar um "
            "novo tipo significa alterar o único lugar que cria notificadores, em vez de "
            "doze. Uma factory, por si só, não torna instâncias únicas (A) nem imutáveis "
            "(B), e a lógica de decisão continua existindo em algum lugar, então ela não "
            "remove todas as condicionais (D).",
            (
                "Garante que só possa existir uma instância de `Notifier`.",
                "Torna todo `Notifier` imutável.",
                "Os chamadores dependem apenas da interface `Notifier`, e adicionar um tipo "
                "altera um lugar em vez de vários.",
                "Remove todas as condicionais do programa.",
            ),
        ),
    ),
    _q(
        _PAT,
        9,
        MC,
        HARD,
        "d",
        ("state", "strategy"),
        _t(
            "State and Strategy have almost the same class structure. Which statement "
            "correctly distinguishes them?",
            "The difference is intent. In State, the object's current behavior object "
            "changes as part of its own lifecycle (for example an order moving from Draft to "
            "Paid to Shipped), and state objects often trigger the transitions. In Strategy, "
            "the client typically picks one interchangeable algorithm and the strategies "
            "know nothing about each other. Both use composition and an interface, and "
            "neither is structural in the GoF sense.",
            (
                "Strategy needs an interface while State does not.",
                "State uses inheritance of the context while Strategy uses composition.",
                "State is a structural pattern and Strategy is a creational pattern.",
                "In State the object's behavior changes as its own state changes, often with "
                "the state objects driving transitions; in Strategy the client chooses an "
                "algorithm and the strategies are independent of each other.",
            ),
        ),
        _t(
            "State e Strategy têm estrutura de classes quase idêntica. Qual afirmação os "
            "distingue corretamente?",
            "A diferença está na intenção. No State, o objeto de comportamento atual muda "
            "como parte do ciclo de vida do próprio objeto (por exemplo, um pedido indo de "
            "Draft para Paid e Shipped), e os objetos de estado costumam disparar as "
            "transições. No Strategy, o cliente tipicamente escolhe um algoritmo "
            "intercambiável e as estratégias não sabem nada umas das outras. Ambos usam "
            "composição e uma interface, e nenhum é estrutural no sentido do GoF.",
            (
                "O Strategy precisa de uma interface, enquanto o State não.",
                "O State usa herança do contexto, enquanto o Strategy usa composição.",
                "O State é um padrão estrutural e o Strategy é um padrão de criação.",
                "No State o comportamento do objeto muda conforme o próprio estado muda, "
                "muitas vezes com os objetos de estado conduzindo as transições; no "
                "Strategy o cliente escolhe um algoritmo e as estratégias são independentes "
                "entre si.",
            ),
        ),
    ),
    _q(
        _PAT,
        10,
        SHORT,
        HARD,
        None,
        ("strategy", "overengineering", "tradeoffs"),
        _t(
            "A colleague proposes replacing a three-branch `if/elif` that has not changed "
            "in two years with the Strategy pattern (an interface, three classes and a "
            "factory). Do you accept the proposal? Justify your answer.",
            "Self-check: did you mention (1) that patterns answer a recurring force such as "
            "frequent variation, (2) the cost of added indirection and files, and (3) an "
            "alternative or trigger such as waiting for the rule of three or using a "
            "function or dictionary?",
            None,
            "Probably not. A pattern is a response to a recurring force, such as a rule that "
            "keeps changing or branches that must be added by different teams. A stable "
            "three-branch conditional has no such force, so Strategy only adds indirection, "
            "more files and more to read (speculative generality). Better to keep the "
            "conditional, and refactor when it actually grows or a fourth case appears. In "
            "languages with first-class functions a dictionary of functions is often enough, "
            "giving the same extensibility without the class hierarchy.",
        ),
        _t(
            "Um colega propõe substituir um `if/elif` de três ramos, que não muda há dois "
            "anos, pelo padrão Strategy (uma interface, três classes e uma factory). Você "
            "aceita a proposta? Justifique.",
            "Autoavaliação: você mencionou (1) que padrões respondem a uma força recorrente, "
            "como variação frequente, (2) o custo de indireção e de arquivos extras e (3) "
            "uma alternativa ou gatilho, como esperar a regra dos três ou usar uma função "
            "ou dicionário?",
            None,
            "Provavelmente não. Um padrão é uma resposta a uma força recorrente, como uma "
            "regra que não para de mudar ou ramos que precisam ser adicionados por times "
            "diferentes. Uma condicional estável de três ramos não tem essa força, então o "
            "Strategy só acrescenta indireção, mais arquivos e mais código para ler "
            "(generalidade especulativa). É melhor manter a condicional e refatorar quando "
            "ela realmente crescer ou surgir um quarto caso. Em linguagens com funções de "
            "primeira classe, um dicionário de funções muitas vezes basta, dando a mesma "
            "extensibilidade sem a hierarquia de classes.",
        ),
    ),
)

PATTERNS_ASSESSMENT = AssessmentSeed(
    code="software-engineering-design-patterns-quiz",
    title="Design Patterns Quiz",
    description="Creational, structural and behavioral patterns: intent, trade-offs and misuse.",
    kind=AssessmentKind.COMPETENCY,
    competency_slug="design-patterns",
    translations={
        "pt-BR": {
            "title": "Quiz de Design Patterns",
            "description": "Padrões de criação, estruturais e comportamentais: intenção, "
            "trade-offs e uso indevido.",
        }
    },
)

# ----------------------------------------------------------------------
# clean-architecture
# ----------------------------------------------------------------------

_LEAKY_USE_CASE_CODE = """```python
from fastapi import HTTPException
from sqlalchemy.orm import Session

from domain.order import Order


class PlaceOrder:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, order_id: str) -> None:
        order = self.session.get(Order, order_id)
        if order is None:
            raise HTTPException(status_code=404, detail="order not found")
        order.confirm()
        self.session.commit()
```"""

_CLEAN = "clean-architecture"

CLEAN_QUESTIONS: tuple[QuestionSeed, ...] = (
    _q(
        _CLEAN,
        1,
        MC,
        EASY,
        "b",
        ("dependency-rule",),
        _t(
            "What does the Dependency Rule of Clean Architecture state?",
            "Source-code dependencies may only point inward, toward higher-level policy "
            "(entities and use cases); inner layers must know nothing about outer ones such "
            "as frameworks, databases or the UI. A is wrong because runtime calls may cross "
            "layers in both directions through interfaces, C describes strict layering that "
            "is not required, and D would break the rule for the innermost layer.",
            (
                "Outer layers must never call inner layers at runtime.",
                "Source-code dependencies must point inward, toward the higher-level "
                "business policy.",
                "Every layer must depend on the layer directly below it and no other.",
                "Entities may depend on frameworks as long as use cases do not.",
            ),
        ),
        _t(
            "O que a Regra de Dependência da Clean Architecture afirma?",
            "As dependências de código-fonte só podem apontar para dentro, em direção à "
            "política de mais alto nível (entidades e casos de uso); camadas internas não "
            "devem saber nada sobre as externas, como frameworks, banco de dados ou a UI. "
            "A está errada porque chamadas em tempo de execução podem cruzar camadas nos "
            "dois sentidos via interfaces, C descreve uma divisão estrita em camadas que "
            "não é exigida e D quebraria a regra para a camada mais interna.",
            (
                "Camadas externas nunca devem chamar camadas internas em tempo de execução.",
                "As dependências de código-fonte devem apontar para dentro, em direção à "
                "política de negócio de mais alto nível.",
                "Toda camada deve depender da camada imediatamente abaixo e de nenhuma outra.",
                "Entidades podem depender de frameworks, desde que os casos de uso não dependam.",
            ),
        ),
    ),
    _q(
        _CLEAN,
        2,
        MC,
        EASY,
        "a",
        ("layers", "business-rules"),
        _t(
            'The rule "an order cannot be shipped until it is paid" is a core business '
            "rule. Where does it belong?",
            "Core business rules live in the innermost layers (entities or use cases), "
            "where they are independent of delivery mechanisms and storage, so they stay "
            "valid and testable whichever UI or database is used. Putting them in a "
            "controller (B), a database trigger (C) or a UI component (D) ties them to a "
            "detail and duplicates them whenever another entry point appears.",
            (
                "In the domain layer (the order entity or a use case), independent of frameworks.",
                "In the HTTP controller that handles the shipping request.",
                "In a database trigger that rejects the update.",
                'In a front-end component that disables the "Ship" button.',
            ),
        ),
        _t(
            'A regra "um pedido não pode ser enviado até ser pago" é uma regra de negócio '
            "central. Onde ela deve ficar?",
            "As regras de negócio centrais ficam nas camadas mais internas (entidades ou "
            "casos de uso), onde são independentes de mecanismos de entrega e de "
            "armazenamento, e continuam válidas e testáveis seja qual for a UI ou o banco. "
            "Colocá-las em um controller (B), em um trigger de banco (C) ou em um "
            "componente de interface (D) as prende a um detalhe e as duplica sempre que "
            "surge outro ponto de entrada.",
            (
                "Na camada de domínio (na entidade pedido ou em um caso de uso), "
                "independente de frameworks.",
                "No controller HTTP que trata a requisição de envio.",
                "Em um trigger de banco de dados que rejeita a atualização.",
                'Em um componente de front-end que desabilita o botão "Enviar".',
            ),
        ),
    ),
    _q(
        _CLEAN,
        3,
        MC,
        EASY,
        "c",
        ("ports-and-adapters",),
        _t(
            "In Ports & Adapters (hexagonal) terminology, what are a port and an adapter?",
            "A port is an interface that belongs to the application core and states what it "
            "needs (an outbound port such as `PaymentGateway`) or what it offers (an inbound "
            "port such as a use case). An adapter is the technology-specific code that "
            "plugs into a port, for example a Stripe client implementing `PaymentGateway`. "
            "The other options swap or blur the roles.",
            (
                "A port is a network port number, and an adapter is a database driver.",
                "A port is a concrete class in the infrastructure layer, and an adapter is an "
                "interface in the domain.",
                "A port is an interface owned by the application core, and an adapter is "
                "technology-specific code that implements or calls it.",
                "A port and an adapter are two names for the same class.",
            ),
        ),
        _t(
            "Na terminologia de Ports & Adapters (hexagonal), o que são uma port e um adapter?",
            "Uma port é uma interface que pertence ao núcleo da aplicação e declara o que "
            "ele precisa (uma port de saída, como `PaymentGateway`) ou o que ele oferece "
            "(uma port de entrada, como um caso de uso). Um adapter é o código específico "
            "de tecnologia que se conecta a uma port, por exemplo um cliente Stripe "
            "implementando `PaymentGateway`. As outras opções trocam ou confundem os "
            "papéis.",
            (
                "Uma port é um número de porta de rede e um adapter é um driver de banco de dados.",
                "Uma port é uma classe concreta da camada de infraestrutura e um adapter é "
                "uma interface do domínio.",
                "Uma port é uma interface pertencente ao núcleo da aplicação e um adapter é "
                "código específico de tecnologia que a implementa ou a chama.",
                "Port e adapter são dois nomes para a mesma classe.",
            ),
        ),
    ),
    _q(
        _CLEAN,
        4,
        CODE,
        MEDIUM,
        "d",
        ("dependency-rule", "frameworks"),
        _t(
            "This use case sits in the application layer. Which imports break the "
            "Dependency Rule?\n\n" + _LEAKY_USE_CASE_CODE,
            "Both `fastapi` and `sqlalchemy` are outer-layer details (web framework and "
            "persistence). The use case raises an HTTP-specific exception and manipulates "
            "an ORM session directly, so it cannot run or be tested without them and must "
            "change when either framework does. The import of `domain.order` points "
            "inward, which is allowed. The fix is a repository port and a domain-level "
            "error that the web layer translates into a 404.",
            (
                "Only `fastapi`; the ORM session is acceptable in a use case.",
                "Only `sqlalchemy`; raising HTTP exceptions is acceptable in a use case.",
                "Only `domain.order`, because use cases must not know about entities.",
                "Both `fastapi` and `sqlalchemy`; the use case depends on outer-layer frameworks.",
            ),
        ),
        _t(
            "Este caso de uso está na camada de aplicação. Quais imports quebram a Regra "
            "de Dependência?\n\n" + _LEAKY_USE_CASE_CODE,
            "Tanto `fastapi` quanto `sqlalchemy` são detalhes de camadas externas "
            "(framework web e persistência). O caso de uso lança uma exceção específica "
            "de HTTP e manipula uma sessão do ORM diretamente, então não roda nem é "
            "testável sem eles e precisa mudar quando qualquer um dos frameworks mudar. O "
            "import de `domain.order` aponta para dentro, o que é permitido. A correção é "
            "uma port de repositório e um erro de domínio que a camada web traduz em 404.",
            (
                "Somente `fastapi`; a sessão do ORM é aceitável em um caso de uso.",
                "Somente `sqlalchemy`; lançar exceções HTTP é aceitável em um caso de uso.",
                "Somente `domain.order`, pois casos de uso não devem conhecer entidades.",
                "Tanto `fastapi` quanto `sqlalchemy`; o caso de uso depende de frameworks "
                "de camadas externas.",
            ),
        ),
    ),
    _q(
        _CLEAN,
        5,
        MC,
        MEDIUM,
        "b",
        ("ports-and-adapters", "dip"),
        _t(
            "Where should the `OrderRepository` interface used by the `PlaceOrder` use case "
            "be defined?",
            "The interface expresses what the use case needs, so it belongs with the "
            "inner layer (domain or application) that owns that need; the Postgres "
            "implementation lives in infrastructure and depends on it. Defining it next to "
            "the Postgres code (A) keeps the use case dependent on infrastructure, and "
            "putting it in the web layer (C) or in a shared package everyone imports (D) "
            "couples unrelated layers.",
            (
                "Next to the Postgres implementation in the infrastructure layer.",
                "In the domain or application layer, with the Postgres class implementing it "
                "from the infrastructure layer.",
                "In the web layer, next to the controllers that call the use case.",
                "In a shared `common` package imported by every layer.",
            ),
        ),
        _t(
            "Onde deve ser definida a interface `OrderRepository` usada pelo caso de uso "
            "`PlaceOrder`?",
            "A interface expressa o que o caso de uso precisa, então pertence à camada "
            "interna (domínio ou aplicação) dona dessa necessidade; a implementação "
            "Postgres fica na infraestrutura e depende dela. Defini-la junto do código "
            "Postgres (A) mantém o caso de uso dependente da infraestrutura, e colocá-la na "
            "camada web (C) ou em um pacote compartilhado que todos importam (D) acopla "
            "camadas que não têm relação.",
            (
                "Ao lado da implementação Postgres, na camada de infraestrutura.",
                "Na camada de domínio ou de aplicação, com a classe Postgres da camada de "
                "infraestrutura implementando-a.",
                "Na camada web, ao lado dos controllers que chamam o caso de uso.",
                "Em um pacote compartilhado `common` importado por todas as camadas.",
            ),
        ),
    ),
    _q(
        _CLEAN,
        6,
        MC,
        MEDIUM,
        "c",
        ("boundaries", "dto"),
        _t(
            "A use case returns ORM model instances directly, and the HTTP layer serializes "
            "them. Why is this a problem for the architecture?",
            "The ORM model is a persistence detail. Returning it across the boundary couples "
            "the API contract to the database schema, so a column rename leaks into clients, "
            "and lazy-loaded relations may hit the database from the outer layer. Passing "
            "simple output data structures keeps both sides free to change. The ORM does not "
            "forbid serialization (A), and speed (B) is not the concern here.",
            (
                "ORM models cannot be serialized to JSON.",
                "It is slower than returning dictionaries in every case.",
                "It couples the API contract to the persistence schema and lets the outer "
                "layer trigger database access.",
                "It violates the rule that use cases must return primitive integers.",
            ),
        ),
        _t(
            "Um caso de uso retorna instâncias de modelos do ORM diretamente, e a camada "
            "HTTP as serializa. Por que isso é um problema para a arquitetura?",
            "O modelo do ORM é um detalhe de persistência. Retorná-lo através da fronteira "
            "acopla o contrato da API ao esquema do banco, então renomear uma coluna vaza "
            "para os clientes, e relações com lazy loading podem acessar o banco a partir "
            "da camada externa. Passar estruturas de dados simples de saída deixa os dois "
            "lados livres para mudar. O ORM não impede a serialização (A) e velocidade (B) "
            "não é a preocupação aqui.",
            (
                "Modelos do ORM não podem ser serializados para JSON.",
                "É mais lento que retornar dicionários em todos os casos.",
                "Acopla o contrato da API ao esquema de persistência e permite que a camada "
                "externa dispare acesso ao banco.",
                "Viola a regra de que casos de uso devem retornar inteiros primitivos.",
            ),
        ),
    ),
    _q(
        _CLEAN,
        7,
        MS,
        MEDIUM,
        "ac",
        ("benefits", "testability"),
        _t(
            "Which TWO benefits does a well-applied Clean Architecture provide?",
            "Because business rules depend on abstractions, they can be tested without a "
            "database or web server, and a persistence technology can be replaced with "
            "changes confined to an adapter. The price is extra mapping between layers "
            "(B), it does not promise better performance (D), and it usually adds files "
            "rather than reducing them (E).",
            (
                "Business rules can be unit-tested without a database or a web server.",
                "No mapping between layers is needed, since all layers share the same models.",
                "Swapping the persistence technology mostly affects the outer adapter code.",
                "Applications always run faster than a plain CRUD design.",
                "The codebase always ends up with fewer files and classes.",
            ),
        ),
        _t(
            "Quais DOIS benefícios uma Clean Architecture bem aplicada oferece?",
            "Como as regras de negócio dependem de abstrações, elas podem ser testadas sem "
            "banco de dados ou servidor web, e uma tecnologia de persistência pode ser "
            "trocada com mudanças restritas a um adapter. O preço é o mapeamento extra "
            "entre camadas (B), ela não promete melhor desempenho (D) e normalmente "
            "adiciona arquivos em vez de reduzi-los (E).",
            (
                "As regras de negócio podem ser testadas unitariamente sem banco de dados "
                "nem servidor web.",
                "Não é preciso mapear entre camadas, pois todas compartilham os mesmos modelos.",
                "Trocar a tecnologia de persistência afeta principalmente o código do "
                "adapter externo.",
                "As aplicações sempre rodam mais rápido que um design CRUD simples.",
                "A base de código sempre termina com menos arquivos e classes.",
            ),
        ),
    ),
    _q(
        _CLEAN,
        8,
        MC,
        MEDIUM,
        "d",
        ("composition-root", "dependency-injection"),
        _t(
            "Where should the concrete adapters (for example `PostgresOrderRepository`) be "
            "instantiated and connected to the use cases?",
            "Wiring is itself a detail, so it belongs in a composition root at the "
            "outermost edge (main or bootstrap code), which is allowed to know every "
            "layer. Instantiating the adapter inside the use case (A) or an entity (B) "
            "reintroduces a dependency on a concrete class, and doing it inside the domain "
            "package (C) makes the innermost layer depend on infrastructure.",
            (
                "Inside the use case's constructor, with `PostgresOrderRepository()`.",
                "Inside the entities, so each entity can load its own data.",
                "In the domain package's `__init__` module, so it is ready everywhere.",
                "In a composition root at the application's entry point, outside the core.",
            ),
        ),
        _t(
            "Onde os adapters concretos (por exemplo, `PostgresOrderRepository`) devem ser "
            "instanciados e ligados aos casos de uso?",
            "A montagem em si é um detalhe, então pertence a uma composition root na borda "
            "mais externa (main ou código de bootstrap), que pode conhecer todas as "
            "camadas. Instanciar o adapter dentro do caso de uso (A) ou de uma entidade "
            "(B) reintroduz a dependência de uma classe concreta, e fazê-lo no pacote de "
            "domínio (C) faz a camada mais interna depender da infraestrutura.",
            (
                "Dentro do construtor do caso de uso, com `PostgresOrderRepository()`.",
                "Dentro das entidades, para que cada uma carregue seus próprios dados.",
                "No módulo `__init__` do pacote de domínio, para estar pronto em todo lugar.",
                "Em uma composition root no ponto de entrada da aplicação, fora do núcleo.",
            ),
        ),
    ),
    _q(
        _CLEAN,
        9,
        MC,
        HARD,
        "b",
        ("tradeoffs", "pragmatism"),
        _t(
            "A team is building an internal admin screen that only lists and edits rows of a "
            "few tables, with no business rules. A new engineer insists on entities, "
            "use-case classes, ports and mappers for every table. What is the best "
            "judgement?",
            "Architectural layering has a cost (indirection, mapping, files) that pays off "
            "when there are rich business rules, several delivery mechanisms, or a long "
            "lifetime with likely technology changes. For plain CRUD with no rules, a thin "
            "design is usually enough, and the team can introduce boundaries later where "
            "complexity appears. Mandating the full structure everywhere (A, C) or letting "
            "the framework decide everything (D) ignores the trade-off.",
            (
                "Agree: Clean Architecture must be applied in full to every feature to be valid.",
                "Use a thin, simple design for this CRUD, and add boundaries where real "
                "business complexity appears; layering cost should match the problem.",
                "Agree, because mappers remove the need for tests.",
                "Reject any architecture and let the web framework's defaults define the "
                "structure of the whole product, including future complex modules.",
            ),
        ),
        _t(
            "Uma equipe está construindo uma tela administrativa interna que apenas lista e "
            "edita linhas de poucas tabelas, sem regras de negócio. Um novo engenheiro "
            "insiste em entidades, classes de casos de uso, ports e mappers para cada "
            "tabela. Qual é o melhor julgamento?",
            "A divisão em camadas tem um custo (indireção, mapeamento, arquivos) que se "
            "justifica quando há regras de negócio ricas, vários mecanismos de entrega ou "
            "vida longa com mudanças de tecnologia prováveis. Para um CRUD simples sem "
            "regras, um design enxuto normalmente basta, e a equipe pode introduzir "
            "fronteiras depois, onde surgir complexidade. Exigir a estrutura completa em "
            "todo lugar (A, C) ou deixar o framework decidir tudo (D) ignora o trade-off.",
            (
                "Concordar: a Clean Architecture precisa ser aplicada por inteiro em toda "
                "funcionalidade para ser válida.",
                "Usar um design enxuto e simples para este CRUD e adicionar fronteiras onde "
                "surgir complexidade de negócio real; o custo das camadas deve corresponder "
                "ao problema.",
                "Concordar, porque mappers eliminam a necessidade de testes.",
                "Rejeitar qualquer arquitetura e deixar os padrões do framework web "
                "definirem a estrutura de todo o produto, inclusive módulos complexos "
                "futuros.",
            ),
        ),
    ),
    _q(
        _CLEAN,
        10,
        SHORT,
        HARD,
        None,
        ("use-cases", "ports", "testing"),
        _t(
            "A `CheckoutOrder` use case must charge a credit card and then send a "
            "confirmation email. Describe how you would structure it following Clean "
            "Architecture: where the interfaces and implementations live, how the use case "
            "gets them, and how you would unit-test it.",
            "Self-check: did you mention (1) outbound ports owned by the application layer, "
            "(2) adapters in infrastructure implementing them, (3) injection from a "
            "composition root, and (4) testing with fakes or mocks and no real network?",
            None,
            "Define two outbound ports in the application layer, for example "
            "`PaymentGateway` and `EmailSender`, expressed in the domain's language "
            "(`charge(order)`, `send_confirmation(order)`), not in the vendor's. "
            "`CheckoutOrder` depends only on those interfaces and receives them through its "
            "constructor. Adapters such as `StripePaymentGateway` and `SmtpEmailSender` live "
            "in infrastructure and implement the ports; a composition root at the app's "
            "entry point wires them together. To unit-test the use case, inject fakes or "
            "stubs for both ports and assert on the outcome (order marked paid, email "
            "requested, behavior on payment failure) with no network or framework. The "
            "adapters get their own integration tests.",
        ),
        _t(
            "Um caso de uso `CheckoutOrder` precisa cobrar um cartão de crédito e depois "
            "enviar um e-mail de confirmação. Descreva como você o estruturaria seguindo a "
            "Clean Architecture: onde ficam as interfaces e as implementações, como o caso "
            "de uso as obtém e como você o testaria unitariamente.",
            "Autoavaliação: você mencionou (1) ports de saída pertencentes à camada de "
            "aplicação, (2) adapters na infraestrutura que as implementam, (3) injeção a "
            "partir de uma composition root e (4) testes com fakes ou mocks, sem rede real?",
            None,
            "Defina duas ports de saída na camada de aplicação, por exemplo "
            "`PaymentGateway` e `EmailSender`, expressas na linguagem do domínio "
            "(`charge(order)`, `send_confirmation(order)`) e não na do fornecedor. O "
            "`CheckoutOrder` depende apenas dessas interfaces e as recebe pelo construtor. "
            "Adapters como `StripePaymentGateway` e `SmtpEmailSender` ficam na "
            "infraestrutura e implementam as ports; uma composition root no ponto de "
            "entrada da aplicação os conecta. Para testar o caso de uso unitariamente, "
            "injete fakes ou stubs das duas ports e verifique o resultado (pedido marcado "
            "como pago, e-mail solicitado, comportamento em caso de falha no pagamento) "
            "sem rede nem framework. Os adapters recebem seus próprios testes de "
            "integração.",
        ),
    ),
)

CLEAN_ASSESSMENT = AssessmentSeed(
    code="software-engineering-clean-architecture-quiz",
    title="Clean Architecture Quiz",
    description="The Dependency Rule, layers, ports and adapters, and when to apply them.",
    kind=AssessmentKind.COMPETENCY,
    competency_slug="clean-architecture",
    translations={
        "pt-BR": {
            "title": "Quiz de Clean Architecture",
            "description": "A Regra de Dependência, camadas, ports e adapters e quando aplicá-los.",
        }
    },
)

# @@NEXT@@

QUESTIONS: tuple[QuestionSeed, ...] = (
    *SOLID_QUESTIONS,
    *PATTERNS_QUESTIONS,
    *CLEAN_QUESTIONS,
)

ASSESSMENTS: tuple[AssessmentSeed, ...] = (
    SOLID_ASSESSMENT,
    PATTERNS_ASSESSMENT,
    CLEAN_ASSESSMENT,
)

QUESTION_SET = SubjectQuestionSet(
    subject_slug="software-engineering",
    questions=QUESTIONS,
    assessments=ASSESSMENTS,
)
