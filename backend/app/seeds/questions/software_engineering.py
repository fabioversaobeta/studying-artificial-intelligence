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

# @@NEXT@@

QUESTIONS: tuple[QuestionSeed, ...] = SOLID_QUESTIONS

ASSESSMENTS: tuple[AssessmentSeed, ...] = (
    AssessmentSeed(
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
    ),
)

QUESTION_SET = SubjectQuestionSet(
    subject_slug="software-engineering",
    questions=QUESTIONS,
    assessments=ASSESSMENTS,
)
