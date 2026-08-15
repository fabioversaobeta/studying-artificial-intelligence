"""Initial educational content, expressed as plain data structures.

This is the *only* place subject/competency/challenge/achievement content is
authored as Python — `app.seeds.run` upserts it into the database, and every
other part of the application reads it back as rows. Keeping content here
(rather than scattered across migrations or hardcoded in services) is what
lets new subjects be added without touching application logic.
"""

from dataclasses import dataclass, field

from app.models.gamification import AchievementCriterion, QuestCriterion, QuestPeriod
from app.models.learning import DifficultyLevel, ResourceType


@dataclass
class ResourceSeed:
    type: ResourceType
    title: str
    url: str | None = None
    description: str | None = None


@dataclass
class ChallengeSeed:
    title: str
    description: str
    difficulty: DifficultyLevel
    xp_value: int


@dataclass
class CompetencySeed:
    slug: str
    name: str
    description: str
    difficulty: DifficultyLevel
    resources: list[ResourceSeed] = field(default_factory=list)
    challenges: list[ChallengeSeed] = field(default_factory=list)
    requires: list[str] = field(
        default_factory=list
    )  # slugs of prerequisite competencies (same subject)


@dataclass
class SubjectSeed:
    slug: str
    name: str
    description: str
    icon: str
    color: str
    competencies: list[CompetencySeed]


@dataclass
class LearningPathSeed:
    slug: str
    title: str
    description: str
    subject_slug: str | None
    items: list[tuple[str, str]]  # (subject_slug, competency_slug)


@dataclass
class AchievementSeed:
    code: str
    name: str
    description: str
    icon: str
    criteria_type: AchievementCriterion
    criteria_value: int | None
    xp_reward: int


@dataclass
class QuestSeed:
    code: str
    title: str
    description: str
    criteria_type: QuestCriterion
    criteria_value: int
    period: QuestPeriod
    xp_reward: int


SUBJECTS: list[SubjectSeed] = [
    SubjectSeed(
        slug="software-engineering",
        name="Software Engineering",
        description="Architecture, design principles, and practices for building maintainable software.",
        icon="layers",
        color="#6685FF",
        competencies=[
            CompetencySeed(
                slug="solid-principles",
                name="SOLID Principles",
                description="The five design principles for maintainable, extensible object-oriented code.",
                difficulty=DifficultyLevel.BEGINNER,
                resources=[
                    ResourceSeed(
                        type=ResourceType.ARTICLE,
                        title="Refactoring.Guru: Design Patterns & Principles",
                        url="https://refactoring.guru/design-patterns",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Refactor a God Class",
                        description=(
                            "Take a class that violates Single Responsibility (mixing persistence, "
                            "validation, and business logic) and split it into cohesive collaborators. "
                            "Explain which SOLID principle each extraction addresses."
                        ),
                        difficulty=DifficultyLevel.BEGINNER,
                        xp_value=40,
                    )
                ],
            ),
            CompetencySeed(
                slug="design-patterns",
                name="Design Patterns",
                description="Reusable solutions to common object-oriented design problems.",
                difficulty=DifficultyLevel.INTERMEDIATE,
                requires=["solid-principles"],
                resources=[
                    ResourceSeed(
                        type=ResourceType.ARTICLE,
                        title="Refactoring.Guru: Catalog of Design Patterns",
                        url="https://refactoring.guru/design-patterns/catalog",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Replace Conditionals with Strategy",
                        description=(
                            "Find a large if/elif or switch statement selecting behavior and refactor it "
                            "into the Strategy pattern. Justify the tradeoff versus keeping the conditional."
                        ),
                        difficulty=DifficultyLevel.INTERMEDIATE,
                        xp_value=60,
                    )
                ],
            ),
            CompetencySeed(
                slug="clean-architecture",
                name="Clean & Hexagonal Architecture",
                description="Separating domain logic from frameworks, databases, and delivery mechanisms.",
                difficulty=DifficultyLevel.INTERMEDIATE,
                requires=["design-patterns"],
                resources=[
                    ResourceSeed(
                        type=ResourceType.ARTICLE,
                        title="Martin Fowler: Architecture articles",
                        url="https://martinfowler.com/architecture/",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Extract a Port/Adapter",
                        description=(
                            "Take a service with a direct dependency on a concrete database or HTTP client "
                            "and introduce a port (interface) with an adapter implementation, so the domain "
                            "layer no longer imports infrastructure code."
                        ),
                        difficulty=DifficultyLevel.INTERMEDIATE,
                        xp_value=60,
                    )
                ],
            ),
            CompetencySeed(
                slug="domain-driven-design",
                name="Domain-Driven Design",
                description="Modeling software around the business domain: entities, value objects, aggregates, bounded contexts.",
                difficulty=DifficultyLevel.ADVANCED,
                requires=["clean-architecture"],
                resources=[
                    ResourceSeed(
                        type=ResourceType.NOTES,
                        title="Personal notes: aggregates vs. entities vs. value objects",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Define a Bounded Context",
                        description=(
                            "Pick a feature area of a real or hypothetical system and define its bounded "
                            "context: ubiquitous language terms, aggregate roots, and where the context "
                            "boundary sits relative to a neighboring context."
                        ),
                        difficulty=DifficultyLevel.ADVANCED,
                        xp_value=80,
                    )
                ],
            ),
            CompetencySeed(
                slug="testing-strategy",
                name="Testing Strategy",
                description="Unit, integration, and end-to-end tests; the test pyramid; what to mock and what not to.",
                difficulty=DifficultyLevel.INTERMEDIATE,
                requires=["solid-principles"],
                resources=[
                    ResourceSeed(
                        type=ResourceType.ARTICLE,
                        title="Martin Fowler: Test Pyramid",
                        url="https://martinfowler.com/bliki/TestPyramid.html",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Write a Test That Would Have Caught a Real Bug",
                        description=(
                            "Recall a bug you shipped or encountered. Write the test that, had it existed "
                            "beforehand, would have caught it before merge. Explain why that test level "
                            "(unit/integration/e2e) was the right one."
                        ),
                        difficulty=DifficultyLevel.INTERMEDIATE,
                        xp_value=50,
                    )
                ],
            ),
        ],
    ),
    SubjectSeed(
        slug="system-design",
        name="System Design",
        description="Designing systems that scale: APIs, caching, load balancing, and data architecture.",
        icon="network",
        color="#97B2FF",
        competencies=[
            CompetencySeed(
                slug="api-design",
                name="API Design",
                description="REST semantics, versioning, pagination, idempotency, and error contracts.",
                difficulty=DifficultyLevel.BEGINNER,
                resources=[
                    ResourceSeed(
                        type=ResourceType.ARTICLE,
                        title="REST API Tutorial",
                        url="https://restfulapi.net/",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Design an Idempotent POST Endpoint",
                        description=(
                            "Design a payments-style POST /orders endpoint that is safe to retry: define "
                            "the idempotency key mechanism, storage, and the exact response for a retried "
                            "request versus a genuinely new one."
                        ),
                        difficulty=DifficultyLevel.BEGINNER,
                        xp_value=40,
                    )
                ],
            ),
            CompetencySeed(
                slug="caching-strategies",
                name="Caching Strategies",
                description="Cache-aside, write-through, write-behind, invalidation, and TTL tradeoffs.",
                difficulty=DifficultyLevel.INTERMEDIATE,
                requires=["api-design"],
                resources=[
                    ResourceSeed(
                        type=ResourceType.DOCUMENTATION,
                        title="Redis Documentation",
                        url="https://redis.io/docs/latest/",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Design a Cache Invalidation Strategy",
                        description=(
                            "For a product catalog service, design the caching layer: what's cached, TTL, "
                            "invalidation triggers, and how you'd prevent a cache stampede on a hot key."
                        ),
                        difficulty=DifficultyLevel.INTERMEDIATE,
                        xp_value=60,
                    )
                ],
            ),
            CompetencySeed(
                slug="load-balancing",
                name="Load Balancing & Scaling",
                description="Horizontal scaling, load balancer algorithms, health checks, and autoscaling.",
                difficulty=DifficultyLevel.INTERMEDIATE,
                requires=["api-design"],
                resources=[
                    ResourceSeed(
                        type=ResourceType.NOTES,
                        title="Personal notes: L4 vs L7 load balancing",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Design for a 10x Traffic Spike",
                        description=(
                            "A service currently handles 500 req/s on 3 instances. Design how it scales to "
                            "5,000 req/s: what becomes the bottleneck first (DB? cache? downstream API?) "
                            "and how you'd address each in order."
                        ),
                        difficulty=DifficultyLevel.INTERMEDIATE,
                        xp_value=70,
                    )
                ],
            ),
            CompetencySeed(
                slug="database-scaling",
                name="Database Scaling",
                description="Read replicas, connection pooling, sharding, and when to denormalize.",
                difficulty=DifficultyLevel.ADVANCED,
                requires=["caching-strategies", "load-balancing"],
                resources=[
                    ResourceSeed(
                        type=ResourceType.DOCUMENTATION,
                        title="PostgreSQL: Indexes",
                        url="https://www.postgresql.org/docs/current/indexes.html",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Diagnose a Slow Query at Scale",
                        description=(
                            "Given a table with 200M rows and a query that scans it fully, propose an "
                            "indexing strategy, and explain when you'd reach for a read replica versus "
                            "sharding instead of just adding an index."
                        ),
                        difficulty=DifficultyLevel.ADVANCED,
                        xp_value=80,
                    )
                ],
            ),
        ],
    ),
    SubjectSeed(
        slug="distributed-systems",
        name="Distributed Systems",
        description="The theory and tradeoffs behind systems that span multiple machines.",
        icon="git-branch",
        color="#C3CCD9",
        competencies=[
            CompetencySeed(
                slug="cap-theorem",
                name="CAP Theorem",
                description="Consistency, availability, and partition tolerance — and why you can't have all three.",
                difficulty=DifficultyLevel.BEGINNER,
                resources=[
                    ResourceSeed(
                        type=ResourceType.ARTICLE,
                        title="CAP theorem — overview",
                        url="https://en.wikipedia.org/wiki/CAP_theorem",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Classify Three Real Systems",
                        description=(
                            "Pick three systems you've used (e.g. a payments DB, a DNS service, a chat app) "
                            "and classify each as CP or AP under a network partition. Justify each choice."
                        ),
                        difficulty=DifficultyLevel.BEGINNER,
                        xp_value=40,
                    )
                ],
            ),
            CompetencySeed(
                slug="replication",
                name="Replication",
                description="Leader-follower replication, synchronous vs asynchronous, and failover.",
                difficulty=DifficultyLevel.INTERMEDIATE,
                requires=["cap-theorem"],
                resources=[
                    ResourceSeed(
                        type=ResourceType.NOTES,
                        title="Personal notes: replication lag and read-your-writes",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Design a Failover Plan",
                        description=(
                            "Design the failover procedure for a primary-replica Postgres setup: detection, "
                            "promotion, and how clients discover the new primary without manual intervention."
                        ),
                        difficulty=DifficultyLevel.INTERMEDIATE,
                        xp_value=60,
                    )
                ],
            ),
            CompetencySeed(
                slug="partitioning-sharding",
                name="Partitioning & Sharding",
                description="Splitting data across nodes: hash, range, and directory-based sharding.",
                difficulty=DifficultyLevel.ADVANCED,
                requires=["replication"],
                resources=[
                    ResourceSeed(
                        type=ResourceType.NOTES, title="Personal notes: choosing a shard key"
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Choose a Shard Key",
                        description=(
                            "For a multi-tenant SaaS database, propose a shard key, explain how it avoids "
                            "hot shards, and describe what breaks (cross-shard queries, joins) as a result."
                        ),
                        difficulty=DifficultyLevel.ADVANCED,
                        xp_value=80,
                    )
                ],
            ),
            CompetencySeed(
                slug="consensus-algorithms",
                name="Consensus Algorithms",
                description="How distributed nodes agree on a single value: Raft and Paxos at a conceptual level.",
                difficulty=DifficultyLevel.ADVANCED,
                requires=["replication"],
                resources=[
                    ResourceSeed(
                        type=ResourceType.DOCUMENTATION,
                        title="The Raft Consensus Algorithm",
                        url="https://raft.github.io/",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Explain Raft Leader Election",
                        description=(
                            "Explain, in your own words and without notes, how Raft elects a leader after "
                            "a failure, including terms, votes, and the split-vote edge case."
                        ),
                        difficulty=DifficultyLevel.ADVANCED,
                        xp_value=90,
                    )
                ],
            ),
        ],
    ),
    SubjectSeed(
        slug="backend-engineering",
        name="Backend Engineering",
        description="Building production backend services: APIs, data, auth, and messaging.",
        icon="server",
        color="#6685FF",
        competencies=[
            CompetencySeed(
                slug="rest-api-design",
                name="REST API Implementation",
                description="Turning API design into a real, well-tested implementation.",
                difficulty=DifficultyLevel.BEGINNER,
                resources=[
                    ResourceSeed(
                        type=ResourceType.DOCUMENTATION,
                        title="FastAPI Documentation",
                        url="https://fastapi.tiangolo.com/",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Build a Paginated List Endpoint",
                        description=(
                            "Implement a list endpoint with cursor or offset pagination, filtering, and "
                            "sorting, plus a test asserting the response shape and edge cases (empty page, "
                            "last page)."
                        ),
                        difficulty=DifficultyLevel.BEGINNER,
                        xp_value=40,
                    )
                ],
            ),
            CompetencySeed(
                slug="authentication-authorization",
                name="Authentication & Authorization",
                description="Password hashing, sessions, JWTs, and RBAC/ABAC access control.",
                difficulty=DifficultyLevel.INTERMEDIATE,
                requires=["rest-api-design"],
                resources=[
                    ResourceSeed(
                        type=ResourceType.DOCUMENTATION,
                        title="JWT Introduction",
                        url="https://jwt.io/introduction",
                    ),
                    ResourceSeed(
                        type=ResourceType.DOCUMENTATION,
                        title="OWASP Top 10",
                        url="https://owasp.org/www-project-top-ten/",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Threat-Model Your Auth Flow",
                        description=(
                            "Take an access + refresh token flow and threat-model it: token theft, replay, "
                            "and what happens on logout. Propose one concrete mitigation per threat."
                        ),
                        difficulty=DifficultyLevel.INTERMEDIATE,
                        xp_value=65,
                    )
                ],
            ),
            CompetencySeed(
                slug="postgresql-fundamentals",
                name="PostgreSQL Fundamentals",
                description="Schema design, indexes, transactions, and isolation levels.",
                difficulty=DifficultyLevel.INTERMEDIATE,
                requires=["rest-api-design"],
                resources=[
                    ResourceSeed(
                        type=ResourceType.DOCUMENTATION,
                        title="PostgreSQL: Transaction Isolation",
                        url="https://www.postgresql.org/docs/current/transaction-iso.html",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Reproduce a Race Condition",
                        description=(
                            "Design (in pseudocode or SQL) two concurrent transactions that produce a lost "
                            "update under READ COMMITTED, then fix it with either SELECT ... FOR UPDATE or "
                            "SERIALIZABLE isolation."
                        ),
                        difficulty=DifficultyLevel.INTERMEDIATE,
                        xp_value=65,
                    )
                ],
            ),
            CompetencySeed(
                slug="event-driven-architecture",
                name="Event-Driven Architecture",
                description="Message queues, pub/sub, at-least-once delivery, and consumer idempotency.",
                difficulty=DifficultyLevel.ADVANCED,
                requires=["postgresql-fundamentals"],
                resources=[
                    ResourceSeed(
                        type=ResourceType.NOTES,
                        title="Personal notes: outbox pattern for reliable publishing",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Design an Idempotent Consumer",
                        description=(
                            "A message queue guarantees at-least-once delivery. Design a consumer that "
                            "processes a 'charge card' event exactly-once from the caller's perspective."
                        ),
                        difficulty=DifficultyLevel.ADVANCED,
                        xp_value=80,
                    )
                ],
            ),
        ],
    ),
    SubjectSeed(
        slug="python",
        name="Python",
        description="Modern, idiomatic Python: typing, async, testing, and packaging.",
        icon="code",
        color="#97B2FF",
        competencies=[
            CompetencySeed(
                slug="python-fundamentals",
                name="Python Fundamentals",
                description="Data model, comprehensions, context managers, and idiomatic control flow.",
                difficulty=DifficultyLevel.BEGINNER,
                resources=[
                    ResourceSeed(
                        type=ResourceType.DOCUMENTATION,
                        title="The Python Tutorial",
                        url="https://docs.python.org/3/tutorial/",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Write a Context Manager",
                        description="Implement a context manager (class-based or @contextmanager) that times a block of code and logs the duration on exit, including when an exception is raised.",
                        difficulty=DifficultyLevel.BEGINNER,
                        xp_value=35,
                    )
                ],
            ),
            CompetencySeed(
                slug="type-hints",
                name="Type Hints & Static Typing",
                description="Type hints, generics, Protocol, and using mypy effectively.",
                difficulty=DifficultyLevel.INTERMEDIATE,
                requires=["python-fundamentals"],
                resources=[
                    ResourceSeed(
                        type=ResourceType.DOCUMENTATION,
                        title="typing — Support for type hints",
                        url="https://docs.python.org/3/library/typing.html",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Type a Generic Repository",
                        description="Write a generic Repository[T] class with type-safe get/add/list methods, and get it to pass mypy --strict.",
                        difficulty=DifficultyLevel.INTERMEDIATE,
                        xp_value=55,
                    )
                ],
            ),
            CompetencySeed(
                slug="async-python",
                name="Async Python",
                description="asyncio, coroutines, event loops, and when async actually helps.",
                difficulty=DifficultyLevel.ADVANCED,
                requires=["type-hints"],
                resources=[
                    ResourceSeed(
                        type=ResourceType.DOCUMENTATION,
                        title="asyncio — Coroutines and Tasks",
                        url="https://docs.python.org/3/library/asyncio-task.html",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Fan Out Concurrent Requests",
                        description="Write an async function that fetches N URLs concurrently with a bounded concurrency limit (e.g. via a semaphore) and handles individual failures without cancelling the rest.",
                        difficulty=DifficultyLevel.ADVANCED,
                        xp_value=75,
                    )
                ],
            ),
            CompetencySeed(
                slug="testing-with-pytest",
                name="Testing with Pytest",
                description="Fixtures, parametrization, mocking, and structuring a test suite.",
                difficulty=DifficultyLevel.INTERMEDIATE,
                requires=["python-fundamentals"],
                resources=[
                    ResourceSeed(
                        type=ResourceType.DOCUMENTATION,
                        title="pytest documentation",
                        url="https://docs.pytest.org/en/stable/",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Parametrize an Edge-Case Suite",
                        description="Take a function with several boundary conditions and write a single parametrized test covering all of them, with clear test IDs.",
                        difficulty=DifficultyLevel.INTERMEDIATE,
                        xp_value=50,
                    )
                ],
            ),
        ],
    ),
    SubjectSeed(
        slug="ai-engineering",
        name="AI Engineering",
        description="Building production systems with LLMs: prompting, context, agents, RAG, and evaluation.",
        icon="sparkles",
        color="#6685FF",
        competencies=[
            CompetencySeed(
                slug="llm-fundamentals",
                name="LLM Fundamentals",
                description="Tokens, embeddings, context windows, sampling, and why models hallucinate.",
                difficulty=DifficultyLevel.BEGINNER,
                resources=[
                    ResourceSeed(
                        type=ResourceType.NOTES, title="Personal notes: tokens, temperature, top-p"
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Explain Hallucination Without Jargon",
                        description="Write a two-paragraph explanation of why LLMs hallucinate and one concrete architectural mitigation, suitable for a non-technical stakeholder.",
                        difficulty=DifficultyLevel.BEGINNER,
                        xp_value=40,
                    )
                ],
            ),
            CompetencySeed(
                slug="context-engineering",
                name="Context Engineering",
                description="Deciding what information the model sees: selection, compression, and prioritization.",
                difficulty=DifficultyLevel.INTERMEDIATE,
                requires=["llm-fundamentals"],
                resources=[
                    ResourceSeed(
                        type=ResourceType.ARTICLE,
                        title="Anthropic Engineering: Building Effective Agents",
                        url="https://www.anthropic.com/engineering/building-effective-agents",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Design a Context Budget",
                        description="For an agent with a 200K token window operating on a large codebase, design a policy for what goes in context (files, history, tool outputs) and what gets summarized or dropped.",
                        difficulty=DifficultyLevel.INTERMEDIATE,
                        xp_value=65,
                    )
                ],
            ),
            CompetencySeed(
                slug="rag-architecture",
                name="RAG Architecture",
                description="Chunking, embeddings, retrieval, reranking, and grounding answers in retrieved context.",
                difficulty=DifficultyLevel.INTERMEDIATE,
                requires=["context-engineering"],
                resources=[
                    ResourceSeed(
                        type=ResourceType.NOTES, title="Personal notes: chunking strategy tradeoffs"
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Design a RAG Pipeline for Docs",
                        description="Design the ingestion-to-answer pipeline for a RAG system over a 10,000-page documentation set: chunking strategy, metadata, retrieval, and how you'd evaluate answer groundedness.",
                        difficulty=DifficultyLevel.INTERMEDIATE,
                        xp_value=70,
                    )
                ],
            ),
            CompetencySeed(
                slug="ai-agents-tool-use",
                name="AI Agents & Tool Use",
                description="Agent loops, tool calling, planning, and when to use a workflow instead of an agent.",
                difficulty=DifficultyLevel.ADVANCED,
                requires=["rag-architecture"],
                resources=[
                    ResourceSeed(
                        type=ResourceType.ARTICLE,
                        title="Model Context Protocol — official site",
                        url="https://modelcontextprotocol.io/",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Workflow or Agent?",
                        description="Take three tasks (e.g. 'summarize a PR', 'triage a support ticket', 'refactor a module across 20 files') and decide, with justification, whether each is best served by a fixed workflow, a single agent, or a multi-agent setup.",
                        difficulty=DifficultyLevel.ADVANCED,
                        xp_value=85,
                    )
                ],
            ),
            CompetencySeed(
                slug="ai-evaluation",
                name="AI Evaluation",
                description="Golden datasets, LLM-as-judge, regression suites, and measuring tool-call accuracy.",
                difficulty=DifficultyLevel.ADVANCED,
                requires=["ai-agents-tool-use"],
                resources=[
                    ResourceSeed(
                        type=ResourceType.NOTES, title="Personal notes: designing a golden dataset"
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Design a Regression Eval Suite",
                        description="For an agent that answers questions from a payments API's documentation, design 10 golden test cases and the pass/fail criteria for each (exact match, LLM-judge, or tool-call assertion).",
                        difficulty=DifficultyLevel.ADVANCED,
                        xp_value=90,
                    )
                ],
            ),
        ],
    ),
    SubjectSeed(
        slug="interview-preparation",
        name="Interview Preparation",
        description="Coding, system design, and behavioral interview practice for senior/staff roles.",
        icon="target",
        color="#C3CCD9",
        competencies=[
            CompetencySeed(
                slug="coding-interview-patterns",
                name="Coding Interview Patterns",
                description="Arrays, hash maps, trees, graphs, and the patterns that cover most interview problems.",
                difficulty=DifficultyLevel.INTERMEDIATE,
                resources=[
                    ResourceSeed(
                        type=ResourceType.NOTES,
                        title="Personal notes: two-pointer and sliding-window checklist",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Solve and Explain Out Loud",
                        description="Solve one medium-difficulty problem while narrating your reasoning as if in an interview: clarifying questions, brute force, optimization, complexity analysis.",
                        difficulty=DifficultyLevel.INTERMEDIATE,
                        xp_value=50,
                    )
                ],
            ),
            CompetencySeed(
                slug="system-design-interviews",
                name="System Design Interviews",
                description="Structuring a system design answer: requirements, estimation, high-level design, deep dives.",
                difficulty=DifficultyLevel.ADVANCED,
                requires=["coding-interview-patterns"],
                resources=[
                    ResourceSeed(
                        type=ResourceType.NOTES,
                        title="Personal notes: system design interview framework",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Design an AI Coding Assistant (Mock Interview)",
                        description="In 45 minutes, produce a system design for 'design an AI coding assistant': requirements, high-level architecture, data flow, and two deep dives on components you'd expect to be pressed on.",
                        difficulty=DifficultyLevel.ADVANCED,
                        xp_value=90,
                    )
                ],
            ),
            CompetencySeed(
                slug="behavioral-interviews",
                name="Behavioral Interviews (STAR)",
                description="Structuring behavioral answers with Situation-Task-Action-Result, and picking the right stories.",
                difficulty=DifficultyLevel.BEGINNER,
                resources=[
                    ResourceSeed(type=ResourceType.NOTES, title="Personal notes: STAR story bank"),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Write Your Incident Story",
                        description="Write a STAR-format answer to 'tell me about a time production went down' using a real incident, keeping Action focused on what *you* specifically did.",
                        difficulty=DifficultyLevel.BEGINNER,
                        xp_value=40,
                    )
                ],
            ),
            CompetencySeed(
                slug="technical-communication",
                name="Technical Communication in English",
                description="Explaining architecture decisions clearly and concisely, in English, under interview pressure.",
                difficulty=DifficultyLevel.INTERMEDIATE,
                requires=["behavioral-interviews"],
                resources=[
                    ResourceSeed(
                        type=ResourceType.NOTES,
                        title="Personal notes: recording and reviewing mock answers",
                    ),
                ],
                challenges=[
                    ChallengeSeed(
                        title="Record a 2-Minute Architecture Pitch",
                        description="Record yourself explaining a system you built in under 2 minutes, in English, then review for filler words and unclear jumps in logic.",
                        difficulty=DifficultyLevel.INTERMEDIATE,
                        xp_value=55,
                    )
                ],
            ),
        ],
    ),
]


LEARNING_PATHS: list[LearningPathSeed] = [
    LearningPathSeed(
        slug="ai-native-software-engineer",
        title="AI-Native Software Engineer",
        description="Combine solid software engineering fundamentals with AI engineering to build and reason about AI-assisted systems.",
        subject_slug=None,
        items=[
            ("software-engineering", "solid-principles"),
            ("software-engineering", "clean-architecture"),
            ("system-design", "api-design"),
            ("ai-engineering", "llm-fundamentals"),
            ("ai-engineering", "context-engineering"),
            ("ai-engineering", "rag-architecture"),
            ("ai-engineering", "ai-agents-tool-use"),
            ("ai-engineering", "ai-evaluation"),
        ],
    ),
    LearningPathSeed(
        slug="backend-engineering-fundamentals",
        title="Backend Engineering Fundamentals",
        description="Core backend skills: Python, APIs, databases, and authentication.",
        subject_slug=None,
        items=[
            ("python", "python-fundamentals"),
            ("python", "type-hints"),
            ("backend-engineering", "rest-api-design"),
            ("backend-engineering", "authentication-authorization"),
            ("backend-engineering", "postgresql-fundamentals"),
            ("python", "testing-with-pytest"),
        ],
    ),
    LearningPathSeed(
        slug="senior-interview-readiness",
        title="Senior Engineer Interview Readiness",
        description="Coding, system design, and communication skills for senior/staff technical interviews.",
        subject_slug=None,
        items=[
            ("interview-preparation", "coding-interview-patterns"),
            ("system-design", "api-design"),
            ("system-design", "caching-strategies"),
            ("distributed-systems", "cap-theorem"),
            ("interview-preparation", "system-design-interviews"),
            ("interview-preparation", "behavioral-interviews"),
            ("interview-preparation", "technical-communication"),
        ],
    ),
]


ACHIEVEMENTS: list[AchievementSeed] = [
    AchievementSeed(
        code="first_steps",
        name="First Steps",
        description="Log your first study session.",
        icon="footprints",
        criteria_type=AchievementCriterion.FIRST_STUDY_SESSION,
        criteria_value=None,
        xp_reward=20,
    ),
    AchievementSeed(
        code="consistent_learner",
        name="Consistent Learner",
        description="Reach a 7-day learning streak.",
        icon="flame",
        criteria_type=AchievementCriterion.STREAK_DAYS,
        criteria_value=7,
        xp_reward=100,
    ),
    AchievementSeed(
        code="dedicated_learner",
        name="Dedicated Learner",
        description="Reach a 30-day learning streak.",
        icon="flame",
        criteria_type=AchievementCriterion.STREAK_DAYS,
        criteria_value=30,
        xp_reward=300,
    ),
    AchievementSeed(
        code="problem_solver",
        name="Problem Solver",
        description="Pass 5 challenges.",
        icon="check-circle",
        criteria_type=AchievementCriterion.CHALLENGES_PASSED_COUNT,
        criteria_value=5,
        xp_reward=75,
    ),
    AchievementSeed(
        code="challenge_master",
        name="Challenge Master",
        description="Pass 20 challenges.",
        icon="award",
        criteria_type=AchievementCriterion.CHALLENGES_PASSED_COUNT,
        criteria_value=20,
        xp_reward=250,
    ),
    AchievementSeed(
        code="first_mastery",
        name="First Mastery",
        description="Reach mastery (80%+) in a competency.",
        icon="star",
        criteria_type=AchievementCriterion.COMPETENCY_MASTERED_COUNT,
        criteria_value=1,
        xp_reward=50,
    ),
    AchievementSeed(
        code="subject_expert",
        name="Subject Expert",
        description="Reach mastery in 5 competencies.",
        icon="star",
        criteria_type=AchievementCriterion.COMPETENCY_MASTERED_COUNT,
        criteria_value=5,
        xp_reward=200,
    ),
    AchievementSeed(
        code="xp_milestone_1000",
        name="1,000 XP Club",
        description="Earn a total of 1,000 XP.",
        icon="trending-up",
        criteria_type=AchievementCriterion.XP_MILESTONE,
        criteria_value=1000,
        xp_reward=100,
    ),
    AchievementSeed(
        code="xp_milestone_5000",
        name="5,000 XP Club",
        description="Earn a total of 5,000 XP.",
        icon="trending-up",
        criteria_type=AchievementCriterion.XP_MILESTONE,
        criteria_value=5000,
        xp_reward=300,
    ),
]


QUESTS: list[QuestSeed] = [
    QuestSeed(
        code="onboarding_first_session",
        title="Get Started",
        description="Log your first study session.",
        criteria_type=QuestCriterion.STUDY_SESSIONS_COUNT,
        criteria_value=1,
        period=QuestPeriod.ONE_TIME,
        xp_reward=25,
    ),
    QuestSeed(
        code="weekly_study_3",
        title="Show Up This Week",
        description="Log 3 study sessions this week.",
        criteria_type=QuestCriterion.STUDY_SESSIONS_COUNT,
        criteria_value=3,
        period=QuestPeriod.WEEKLY,
        xp_reward=50,
    ),
    QuestSeed(
        code="weekly_challenge_1",
        title="Prove It",
        description="Pass at least 1 challenge this week.",
        criteria_type=QuestCriterion.CHALLENGES_PASSED_COUNT,
        criteria_value=1,
        period=QuestPeriod.WEEKLY,
        xp_reward=40,
    ),
    QuestSeed(
        code="weekly_review_5",
        title="Keep It Fresh",
        description="Complete 5 spaced-repetition reviews this week.",
        criteria_type=QuestCriterion.REVIEWS_COMPLETED_COUNT,
        criteria_value=5,
        period=QuestPeriod.WEEKLY,
        xp_reward=60,
    ),
]
