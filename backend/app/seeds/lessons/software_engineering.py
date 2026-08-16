"""Lesson content for the Software Engineering subject.

Module count per competency tracks real topic complexity — SOLID gets one
module per principle plus a synthesis module (6 total); simpler topics get
fewer. See app.seeds.lessons.types.LessonModule.
"""

from app.seeds.lessons.types import LessonModule

LESSONS: dict[str, list[LessonModule]] = {
    "solid-principles": [
        LessonModule(
            title="S — Single Responsibility Principle",
            content=r"""
## The idea

> "A class should have only one reason to change." — Robert C. Martin

Notice what this *doesn't* say: it doesn't say "a class should do one thing"
(that's a simplification that misleads people into over-splitting classes
into meaningless fragments). It says one **reason to change** — one axis of
responsibility, one stakeholder or concern whose requirements could force
you to edit this code.

## A violation, concretely

```python
class Invoice:
    def __init__(self, items: list[LineItem]) -> None:
        self.items = items

    def total(self) -> Decimal:
        return sum(item.price * item.quantity for item in self.items)

    def save_to_database(self, db: Connection) -> None:
        db.execute(
            "INSERT INTO invoices (total) VALUES (%s)", (self.total(),)
        )

    def render_as_pdf(self) -> bytes:
        # ... PDF generation logic ...
        ...

    def send_email(self, smtp: SMTPClient, to: str) -> None:
        pdf = self.render_as_pdf()
        smtp.send(to=to, subject="Your invoice", attachment=pdf)
```

This class has *four* reasons to change:

1. The business rule for computing a total changes (e.g. tax handling).
2. The database schema or ORM changes.
3. The PDF layout changes (a design request).
4. The email provider or template changes.

Four different people — a finance analyst, a DBA, a designer, a marketing
lead — could each independently request a change that means editing this
one class. That's the smell: unrelated stakeholders converging on the same
file.

## The fix

Split along those axes:

```python
class Invoice:
    # Owns only the domain calculation.
    def __init__(self, items: list[LineItem]) -> None:
        self.items = items

    def total(self) -> Decimal:
        return sum(item.price * item.quantity for item in self.items)


class InvoiceRepository:
    # Owns persistence.
    def save(self, invoice: Invoice, db: Connection) -> None: ...


class InvoicePdfRenderer:
    # Owns presentation.
    def render(self, invoice: Invoice) -> bytes: ...


class InvoiceMailer:
    # Owns delivery.
    def send(self, invoice: Invoice, to: str) -> None: ...
```

Now each class changes for exactly one reason. `Invoice` itself becomes
pure domain logic with zero infrastructure dependencies — trivially unit
testable without a database, a PDF library, or an SMTP mock.

## The trap: over-splitting

SRP is not "functions should be five lines" or "one class per file no
matter what." A class that reads a config value and uses it in the same
method isn't two responsibilities — it's one responsibility with a
collaborator. Ask: *would these two pieces of logic ever need to change
for different business reasons?* If the honest answer is no, don't split
them just to look "SOLID." Splitting cohesive logic apart adds indirection
that costs more than it buys.

## Key takeaways

- "One reason to change" means one axis of *stakeholder-driven* change, not
  "does one thing" literally.
- The classic tell: a class importing infrastructure (DB, HTTP, file I/O)
  *and* containing business rules in the same place.
- Splitting by responsibility is what makes unit testing domain logic
  possible without mocking half the world.
- Don't over-apply it — cohesive logic that changes together should stay
  together.
""",
        ),
        LessonModule(
            title="O — Open/Closed Principle",
            content=r"""
## The idea

> "Software entities should be open for extension, but closed for
> modification." — Bertrand Meyer (the OCP originator); reframed by Martin

In practice: when a new *variant* of existing behavior shows up, you should
be able to add it without editing the code that already works and is
already tested. You extend by adding new code, not by re-opening old code
and risking what it already does correctly.

## A violation, concretely

```python
class DiscountCalculator:
    def calculate(self, order: Order, customer_type: str) -> Decimal:
        if customer_type == "regular":
            return order.total * Decimal("0.0")
        elif customer_type == "premium":
            return order.total * Decimal("0.10")
        elif customer_type == "vip":
            return order.total * Decimal("0.20")
        else:
            raise ValueError(f"Unknown customer type: {customer_type}")
```

Every time the business adds a new customer tier, you edit this method —
touching code that governs discounts for *every existing* customer type,
with every edit carrying a chance of breaking `premium` while adding
`enterprise`. The method also violates SRP as a side effect: it now knows
about every tier's policy at once.

## The fix: extension via polymorphism

```python
class DiscountPolicy(Protocol):
    def discount_for(self, order: Order) -> Decimal: ...


class RegularDiscount:
    def discount_for(self, order: Order) -> Decimal:
        return Decimal("0.0")


class PremiumDiscount:
    def discount_for(self, order: Order) -> Decimal:
        return order.total * Decimal("0.10")


class VipDiscount:
    def discount_for(self, order: Order) -> Decimal:
        return order.total * Decimal("0.20")


class DiscountCalculator:
    def __init__(self, policy: DiscountPolicy) -> None:
        self.policy = policy

    def calculate(self, order: Order) -> Decimal:
        return self.policy.discount_for(order)
```

Adding `EnterpriseDiscount` is now a new file, with its own unit test, that
never touches `RegularDiscount`'s tested behavior. `DiscountCalculator`
itself never changes again for this reason.

## This is not "never edit code"

OCP is about *behavioral extension points* that you can reasonably predict
will grow — payment methods, discount tiers, export formats, notification
channels. It is not a mandate to wrap every three-line function in an
interface "just in case." Predicting the wrong extension points and
abstracting them prematurely is its own, very real, cost (see: the
`AbstractSingletonProxyFactoryBean` school of over-engineering). Apply OCP
where you've already seen the pattern repeat, or where the domain
explicitly tells you "this will have more kinds."

## Key takeaways

- OCP is achieved through abstraction (interfaces/protocols) + polymorphism
  or composition (strategy pattern, plugin registries), not through
  guessing every possible future requirement.
- The trigger to apply it: a growing `if/elif` chain or `match` statement
  switching on a "kind" or "type" field that keeps getting new cases.
- Don't apply it speculatively — apply it to axes of variation you've
  already observed changing, or that the domain explicitly promises will.
""",
        ),
        LessonModule(
            title="L — Liskov Substitution Principle",
            content=r"""
## The idea

> "Subtypes must be substitutable for their base types." — Barbara Liskov

More precisely: if `S` is a subtype of `T`, you should be able to replace
any `T` with an `S` anywhere in the program without altering the
correctness of that program from the caller's point of view. This isn't
about the type system letting you substitute it (Python and most languages
will happily let you) — it's about *behavioral* compatibility: the subtype
must honor the base type's contract (preconditions, postconditions,
invariants), not just its method signatures.

## The canonical violation: Rectangle/Square

```python
class Rectangle:
    def __init__(self, width: float, height: float) -> None:
        self.width = width
        self.height = height

    def set_width(self, width: float) -> None:
        self.width = width

    def set_height(self, height: float) -> None:
        self.height = height

    def area(self) -> float:
        return self.width * self.height


class Square(Rectangle):
    def set_width(self, width: float) -> None:
        self.width = width
        self.height = width  # keep it a square

    def set_height(self, height: float) -> None:
        self.width = height
        self.height = height
```

`Square` type-checks as a `Rectangle`. But this breaks a caller that relies
on `Rectangle`'s implicit contract — that `set_width` doesn't also change
`height`:

```python
def resize_and_check(rect: Rectangle) -> None:
    rect.set_width(5)
    rect.set_height(4)
    assert rect.area() == 20  # true for Rectangle, FALSE for Square (area=16)
```

The code compiles, the types "match," and it's still wrong. That's exactly
what LSP is warning about: type-checking is necessary but not sufficient.

## Subtler violations: strengthened preconditions, weakened postconditions

Two ways this bites in real backend code:

- **A subclass that raises where the parent didn't.** If `PaymentGateway.
  charge()` never raises for a valid amount, but `StripeGateway.charge()`
  raises `RateLimitError` for amounts processed too quickly, every caller
  written against `PaymentGateway` is now unsafe until it learns about a
  concrete subclass's extra behavior — the abstraction leaked.
- **A subclass that returns a weaker guarantee.** If `Repository.get(id)`
  is documented to return a fully-loaded entity, and `CachedRepository.
  get(id)` sometimes returns a stale, partially-invalidated one, callers
  that trusted the contract get silently wrong data.

## The fix

Model what's actually true. A `Square` and a `Rectangle` are both
"quadrilaterals with an area," but they don't share a mutable
width/height contract — so don't force an inheritance relationship that
implies they do:

```python
class Shape(Protocol):
    def area(self) -> float: ...


@dataclass(frozen=True)
class Rectangle:
    width: float
    height: float
    def area(self) -> float:
        return self.width * self.height


@dataclass(frozen=True)
class Square:
    side: float
    def area(self) -> float:
        return self.side ** 2
```

Making both immutable and modeling them as siblings implementing a shared
`Shape` protocol (not a `Square(Rectangle)` inheritance) sidesteps the
whole problem — there's no mutable contract left to violate.

## Key takeaways

- LSP violations are *behavioral*, not syntactic — the type checker won't
  catch them.
- Watch for: subclasses that raise new exceptions, return weaker
  guarantees, or silently change the meaning of a mutation.
- When inheritance forces you to "turn off" or override behavior to keep a
  subtype sane, that's the signal the hierarchy is modeling the wrong
  relationship — prefer composition or a shared interface over inheritance.
""",
        ),
        LessonModule(
            title="I — Interface Segregation Principle",
            content=r"""
## The idea

> "Clients should not be forced to depend on interfaces they do not use."
> — Robert C. Martin

A fat interface with a dozen methods forces every implementer to provide
all twelve — including the ones that make no sense for it — and forces
every *caller* to depend (and be recompiled/retested, in stricter
languages) on methods it never calls. ISP says: split interfaces along the
lines of what clients actually need, not along the lines of "everything
this kind of thing could theoretically do."

## A violation, concretely

```python
class Worker(Protocol):
    def work(self) -> None: ...
    def eat_lunch(self) -> None: ...
    def get_paid(self) -> None: ...


class HumanWorker:
    def work(self) -> None: ...
    def eat_lunch(self) -> None: ...
    def get_paid(self) -> None: ...


class RobotWorker:
    def work(self) -> None: ...
    def eat_lunch(self) -> None:
        raise NotImplementedError("Robots don't eat lunch")  # 🚩
    def get_paid(self) -> None:
        raise NotImplementedError("Robots don't get paid")  # 🚩
```

`NotImplementedError` in an override is almost always ISP screaming at
you: the interface bundled together things that don't actually belong to
every implementer.

## A backend-flavored violation

```python
class UserRepository(Protocol):
    def get(self, id: UUID) -> User: ...
    def save(self, user: User) -> None: ...
    def delete(self, id: UUID) -> None: ...
    def bulk_export_to_csv(self) -> bytes: ...
    def run_gdpr_erasure(self, id: UUID) -> None: ...
```

A read-only reporting service that only ever calls `.get()` still has to
depend on (and, in a statically-typed language with structural typing
gaps, potentially implement stubs for) `bulk_export_to_csv` and
`run_gdpr_erasure`. Worse: every caller of this interface is coupled to
changes in *any* of these five methods' signatures, even the ones it never
touches.

## The fix: split by client need

```python
class UserReader(Protocol):
    def get(self, id: UUID) -> User: ...


class UserWriter(Protocol):
    def save(self, user: User) -> None: ...
    def delete(self, id: UUID) -> None: ...


class UserComplianceOps(Protocol):
    def bulk_export_to_csv(self) -> bytes: ...
    def run_gdpr_erasure(self, id: UUID) -> None: ...
```

The reporting service now depends only on `UserReader`. A concrete
`PostgresUserRepository` can still implement all three protocols — nothing
stops one class from satisfying several small interfaces — but *callers*
each depend on exactly the slice they use.

## Why this matters more than it looks

Small, role-specific interfaces are also what makes testing pleasant:
mocking `UserReader` for a test means faking one method, not five. And
they document intent — seeing a function accept a `UserReader` tells you,
without reading its body, that it definitely does not delete or export
user data.

## Key takeaways

- Fat interfaces force irrelevant dependencies onto every caller and
  implementer.
- The tell: an implementer that raises `NotImplementedError`, returns a
  dummy value, or has a comment like `# not used for this type`.
- A concrete class can implement multiple small interfaces — segregation
  happens at the interface/protocol level, not by limiting what one class
  can do.
""",
        ),
        LessonModule(
            title="D — Dependency Inversion Principle",
            content=r"""
## The idea

> "High-level modules should not depend on low-level modules. Both should
> depend on abstractions. Abstractions should not depend on details;
> details should depend on abstractions." — Robert C. Martin

This is the principle that makes Clean/Hexagonal Architecture possible
(see the next competency). It's also the most commonly misunderstood
letter in SOLID — people conflate it with "dependency injection," which is
a *technique* for achieving DIP, not the principle itself.

## "High-level" and "low-level" — what they actually mean

High-level modules contain policy: business rules, use cases, what the
application is *for*. Low-level modules contain mechanism: how you talk to
Postgres, how you call Stripe's API, how you format an email. The
principle says the business rules should not know or care which database
driver or payment SDK is underneath — that dependency should point the
other way.

## A violation, concretely

```python
class PostgresOrderRepository:
    def save(self, order: Order) -> None:
        # raw psycopg calls...
        ...

class PlaceOrderUseCase:
    def __init__(self) -> None:
        self.repository = PostgresOrderRepository()  # 🚩 concrete dependency

    def execute(self, order: Order) -> None:
        # business rules: validate stock, apply pricing, ...
        self.repository.save(order)
```

`PlaceOrderUseCase` — the high-level policy — directly instantiates and
depends on `PostgresOrderRepository`, a low-level detail. You cannot test
`PlaceOrderUseCase` without a real (or heavily mocked-at-the-SQL-level)
Postgres connection. You cannot swap storage engines without editing the
use case. The dependency arrow points from policy to mechanism — backwards.

## The fix: invert it with an abstraction

```python
class OrderRepository(Protocol):
    def save(self, order: Order) -> None: ...


class PostgresOrderRepository:
    # implements OrderRepository — a detail, depending on the abstraction
    def save(self, order: Order) -> None: ...


class PlaceOrderUseCase:
    def __init__(self, repository: OrderRepository) -> None:
        self.repository = repository  # depends on the abstraction, injected

    def execute(self, order: Order) -> None:
        self.repository.save(order)
```

Now both `PlaceOrderUseCase` (high-level) and `PostgresOrderRepository`
(low-level) depend on `OrderRepository` (the abstraction) — neither
depends on the other directly. `PlaceOrderUseCase` is testable with an
in-memory fake repository in microseconds. Swapping Postgres for DynamoDB
means writing a new class that satisfies `OrderRepository`; the use case
never changes.

## Where the dependency actually gets constructed

Someone still has to build a `PostgresOrderRepository` and hand it to
`PlaceOrderUseCase` — DIP doesn't eliminate that wiring, it moves it to
one place (a composition root / DI container / a `main()`/app-startup
function) instead of scattering `new ConcreteThing()` calls throughout
business logic. In this project, that's `app/api/deps.py` and the FastAPI
`Depends()` system: routers ask for abstractions via type hints, and the
dependency-injection layer supplies concrete instances.

## Key takeaways

- DIP is about the *direction* of source-code dependency: policy defines
  the interface it needs; mechanism implements that interface. The
  interface belongs to (is defined near) the high-level module, not the
  low-level one.
- Dependency injection (passing collaborators in via constructor/function
  parameters instead of instantiating them inline) is the *mechanism* most
  commonly used to satisfy DIP — but DIP is the principle, DI is the tool.
- This is the principle underneath this project's own layering rule:
  services depend on repository *interfaces* in spirit, never on FastAPI
  or a specific driver directly (see docs/ARCHITECTURE.md).
""",
        ),
        LessonModule(
            title="Bringing SOLID Together",
            content=r"""
## Why five separate letters instead of one rule

Each principle attacks a different failure mode of change over time:

| Principle | Fails when... | Symptom |
|---|---|---|
| SRP | one class serves multiple stakeholders | unrelated changes collide in the same file |
| OCP | new variants require editing tested code | growing `if/elif`/`match` on a "kind" |
| LSP | a subtype breaks the base type's contract | surprising bugs only in some subclasses |
| ISP | interfaces bundle unrelated capabilities | `NotImplementedError` in overrides |
| DIP | policy depends on mechanism directly | business logic untestable without infra |

They compound: a class that violates SRP (does persistence *and* business
logic) is much more likely to also violate DIP (business logic now
directly depends on a database driver). Fixing SRP by extracting a
repository interface often fixes DIP as a side effect.

## SOLID is a diagnostic tool, not a checklist to satisfy upfront

The realistic workflow is not "design five abstractions before writing any
code." It's: write the straightforward version first, notice a smell (a
class doing unrelated things, a growing conditional, a subclass that
doesn't fully honor its parent, a fat interface, a use case tightly
coupled to a driver), and *then* apply the relevant letter to fix that
specific pain. Applying all five preemptively to a small CRUD script
produces an unreadable maze of interfaces for behavior that will never
actually vary — that's the well-known "SOLID taken to the extreme" failure
mode, and it's a real cost, not a hypothetical one.

## How this shows up in this project's own codebase

- **SRP**: `backend/app/services/` (business logic) is separate from
  `backend/app/repositories/` (persistence) is separate from
  `backend/app/api/` (HTTP) — see docs/ARCHITECTURE.md.
- **DIP**: FastAPI's `Depends()` mechanism is dependency injection in
  practice — route handlers declare what they need (a `Session`, the
  current user) without constructing it themselves.
- **OCP/ISP**: less prominent in this codebase today because most
  "variation points" (auth methods, storage backends) haven't needed to
  vary yet — a deliberate choice not to abstract prematurely (see
  docs/DECISIONS.md's "avoid unnecessary abstractions" stance).

## Key takeaways

- SOLID principles reinforce each other — fixing one often improves
  another.
- Use them to *diagnose* a smell you're already feeling, not as a design
  ritual to perform before writing the first line of code.
- The cost of applying a principle where it isn't needed is real:
  unnecessary indirection, harder-to-follow code, and interfaces built for
  variation that never materializes.
""",
        ),
    ],
}
