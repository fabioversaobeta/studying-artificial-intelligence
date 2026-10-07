# Question bank — items flagged for the owner's review

The 300 questions in `backend/app/seeds/questions/` were written by Claude
(`source=ai_generated`, English + pt-BR), every code snippet was executed and
every SQL query run on PostgreSQL 16 before it was committed. The authors also
flagged the questions below as the ones most open to debate: a second look is
recommended before relying on them. To change one, edit its seed file and re-run
`python -m app.seeds.run` (idempotent; it updates in place).

| Question | Why it was flagged |
|---|---|
| `solid-principles-q05` | ISP vs LSP as the "primary" violation is arguable |
| `solid-principles-q09` | assumes the contract-based view of LSP |
| `design-patterns-q09` | State vs Strategy is a distinction of intent |
| `domain-driven-design-q09` | "one aggregate per transaction" is classic guidance some teams break on purpose |
| `domain-driven-design-q10` | whether a bounded context equals a microservice has a gradient of valid answers |
| `clean-architecture-q09` | judgement call about when full layering pays off |
| `api-design-q08` | "adding an optional response field is backward compatible" assumes tolerant clients |
| `caching-strategies-q09` | write-then-invalidate order still leaves a small race; TTL is the backstop |
| `database-scaling-q09` | cross-shard transaction options framed as "options include" |
| `load-balancing-q09` | assumes the app and its connection pool scale together |
| `cap-theorem-q09` | 5-node majority-quorum cluster classified CP by the formal CAP availability definition |
| `cap-theorem-q06` | classifies DNS as AP |
| `replication-q09` | read/write quorum overlap is not enough for linearizability (correct but nuanced) |
| `replication-q05` | only 2 of 5 options correct, with subtle distractors |
| `replication-q10`, `consensus-algorithms-q10` | model answers go beyond the lessons (RPO, fencing tokens) |
| `rest-api-design-q03` | asserts FastAPI's default validation status is 422 |
| `rest-api-design-q06` | ETag / `If-Match` / 412 as the standard lost-update guard |
| `authentication-authorization-q02` | 403 is the answer, though some APIs return 404 to hide existence |
| `authentication-authorization-q09` | XSS / CSRF / token-storage trade-offs |
| `event-driven-architecture-q04` | "exactly-once is not generally achievable end to end" can be argued against (Kafka transactions) |
| `event-driven-architecture-q09` | assumes Kafka-style partition ordering |
| `postgresql-fundamentals-q04` | planner behaviour depends on data and statistics |
| `postgresql-fundamentals-q10` | names the default `deadlock_timeout` (1 s) |
| `async-python-q07` | depends on current `cancel()` / `uncancel()` semantics (checked on Python 3.14) |
| `async-python-q08` | mentions TaskGroup as Python 3.11+ (a version detail) |
| `testing-with-pytest-q06` | the `patch("app.email")` distractor is a bit forced |
| `python-fundamentals-q08` | the TOCTOU argument is a style opinion |
| `llm-fundamentals-q09` | letter counting explained via tokens is a simplification |
| `context-engineering-q07` | quadratic growth assumes no caching (stated in the question) |
| `context-engineering-q09` | "lost in the middle" is empirical, worded as a tendency |
| `ai-evaluation-q05` | stylised position-bias scenario |
| `ai-evaluation-q06` | option D ("temperature 0 removes all biases") deserves a second look |
| `rag-architecture-q09` | "say I don't know" is only a partial mitigation; wording may be ambiguous |
| `system-design-interviews-q04`, `-q09` | the correct option is also the longest (a tell) |
| `system-design-interviews-q05` | "plan for peaks a few times higher" is a rule of thumb |
| `behavioral-interviews-q04`, `-q09`, `-q10` | "best answer" judgements; q10's model answer is one valid example |
| `coding-interview-patterns-q03` | Dijkstra is also valid; the question asks for the simplest correct and optimal approach |
| `technical-communication-q09` | best practice, but somewhat opinionated |

Short-answer questions are self-graded against `model_answer` until the AI judge
(roadmap I5) exists.
