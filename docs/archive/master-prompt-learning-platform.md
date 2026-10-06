# Learning Platform — Autonomous Development Instructions

## 1. Role

You are the primary software engineer responsible for designing, implementing, testing, documenting, and continuously improving this project.

Your objective is to build a robust personal learning platform that I will use to track my professional development, knowledge acquisition, practical skills, and career readiness.

You are expected to operate autonomously.

Do not wait for me for routine decisions.

Do not stop development because something is ambiguous unless the decision would have a significant architectural, security, financial, or product impact.

When ambiguity exists, make the most reasonable assumption, document it, implement it, and continue.

---

# 2. Product Vision

Build a personal Learning Management and Professional Development platform.

The platform should help me:

- define learning goals
- organize subjects and competencies
- create learning paths
- study concepts
- practice through challenges
- review previously learned material
- measure knowledge retention
- track progress
- identify knowledge gaps
- develop practical skills
- prepare for technical interviews
- monitor career readiness
- maintain motivation through gamification
- receive personalized learning recommendations

The long-term vision is an adaptive learning system capable of understanding my current knowledge and recommending what I should learn next.

The first version should already establish the architecture necessary to evolve toward this vision.

---

# 3. Current Learning Focus

The platform must initially support learning related to:

## Software Engineering

- Software Architecture
- Clean Architecture
- Hexagonal Architecture
- SOLID
- Design Patterns
- Domain-Driven Design
- Clean Code
- Testing
- System Design
- Distributed Systems
- Scalability
- Reliability
- Observability
- Performance
- Security

## Backend

- PHP
- Node.js
- Python
- REST APIs
- Databases
- PostgreSQL
- MySQL
- Redis
- Messaging
- Event-driven architecture

## Frontend

- React
- TypeScript
- JavaScript
- Frontend Architecture
- Accessibility
- Performance

## Artificial Intelligence

The platform should be prepared to support subjects such as:

- AI-assisted software development
- Prompt Engineering
- Context Engineering
- Coding Agents
- AI-assisted development workflows
- LLM fundamentals
- AI application architecture
- AI evaluation
- AI agents
- RAG
- Tool use
- AI engineering

## Career Development

- Technical interviews
- System Design interviews
- Coding interviews
- Behavioral interviews
- English communication
- Technical communication

The architecture must make adding new subjects easy.

Do not hard-code the current subjects into application logic.

Subjects, competencies, learning paths, challenges, questions, and other educational content should be represented as data.

---

# 4. Technology Stack

For this first version, use:

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Modern component architecture

The frontend will be deployed to Vercel.

## Backend

Use Python.

Prefer:

- Python 3.13+
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL
- pytest

The backend will be deployed to Railway.

## Infrastructure

- PostgreSQL hosted on Railway
- Backend hosted on Railway
- Frontend hosted on Vercel

The architecture must be suitable for production deployment.

---

# 5. Architectural Principles

Use a modular monolith architecture.

Do NOT create microservices unless there is a compelling reason.

The backend should be organized around clear business modules and boundaries.

Prefer:

- Clean Architecture
- SOLID
- Dependency Inversion
- Separation of concerns
- Domain-oriented organization
- Explicit application services
- Repository abstractions where useful
- DTOs / schemas
- Dependency injection
- Strong typing
- Small cohesive modules

Avoid:

- God classes
- God services
- business logic inside controllers
- business logic inside database models
- duplicated business rules
- unnecessary abstractions
- premature microservices
- unnecessary design patterns
- magic values
- hidden global state

Do not introduce abstractions simply to demonstrate architecture.

Architecture must serve the product.

---

# 6. Backend Structure

Use a structure similar to:

backend/

    app/
        api/
        core/
        domain/
        application/
        infrastructure/
        models/
        schemas/
        repositories/
        services/

    tests/

    alembic/

    pyproject.toml

Adjust the structure when a better architectural decision is justified.

Document significant deviations.

---

# 7. Frontend Structure

Use a scalable React architecture.

Prefer something similar to:

frontend/

    src/
        app/
        components/
        features/
        pages/
        hooks/
        services/
        lib/
        types/
        routes/
        layouts/

Organize feature-specific code together where appropriate.

Avoid creating enormous generic folders.

---

# 8. Authentication

The platform must support:

- user registration
- login
- logout
- authenticated sessions
- protected routes
- password hashing
- password validation
- secure token/session handling
- authentication error handling

Never store passwords in plain text.

Use industry-standard password hashing.

Do not implement custom cryptography.

The authentication architecture must be extensible for future OAuth providers.

---

# 9. Core Domain

The initial domain should support at least:

## User

Represents the platform user.

## Learning Goal

Represents something the user wants to achieve.

Example:

"Become a high-performance AI Software Engineer."

## Subject

Examples:

- Python
- Distributed Systems
- System Design
- AI Engineering

## Competency

A specific skill inside a subject.

Example:

Distributed Systems

- CAP theorem
- Replication
- Partitioning
- Consensus
- Distributed transactions

## Learning Path

A structured sequence of competencies.

## Learning Resource

A resource used for studying.

Examples:

- article
- book
- video
- documentation
- course
- personal notes

## Study Session

Records an actual study session.

## Challenge

A practical activity designed to test understanding.

## Assessment

Evaluates knowledge or competency.

## Question

Used in quizzes and assessments.

## Progress

Represents progress toward a competency or learning goal.

## Mastery

Represents estimated knowledge level for a competency.

## Achievement

Represents an accomplishment.

## XP

Experience points earned through learning activities.

## Level

Represents gamification progression.

## Streak / Momentum

Represents learning consistency.

## Review

Represents spaced-repetition activities.

## Project

Represents practical application of knowledge.

## Interview Session

Represents technical or behavioral interview practice.

---

# 10. Mastery System

Do not equate completion with mastery.

The system must distinguish between:

- activity
- completion
- knowledge
- retention
- practical ability

Use a Mastery Score between 0 and 100.

Example:

Distributed Systems: 67%

    CAP Theorem           95%
    Consistency           82%
    Replication           71%
    Partitioning          54%
    Consensus              38%
    Distributed TX         42%

The exact algorithm may evolve.

Initially implement a transparent and deterministic scoring model.

Document the algorithm.

Make it possible to improve the algorithm later without rewriting the domain.

---

# 11. Gamification

Implement a meaningful gamification system.

The system should include:

- XP
- levels
- achievements
- quests
- streaks
- learning momentum
- challenges
- milestones

Example XP:

- reading/studying: low XP
- quiz: medium XP
- challenge: high XP
- project: very high XP
- assessment: high XP
- teaching/explaining a concept: high XP
- review: moderate XP

XP measures activity.

Mastery measures knowledge.

Do not mix the two concepts.

---

# 12. Skill Tree

The platform should support a visual competency graph / skill tree.

Competencies may have:

- prerequisites
- related competencies
- dependent competencies
- learning resources
- challenges
- assessments
- projects
- interview questions

Possible states:

- locked
- available
- learning
- mastered

Do not hard-code the tree.

The relationship must be represented in the database.

---

# 13. Spaced Repetition

Implement the architecture for spaced repetition.

The system should eventually determine:

- what should be reviewed
- when it should be reviewed
- how difficult the concept was
- whether the user remembered it
- how mastery changes after review

Start with a simple algorithm.

Keep the implementation isolated so the algorithm can later be replaced by a more sophisticated one.

---

# 14. AI Architecture

The platform should eventually have an AI Mentor.

Do not tightly couple the entire application to a single AI provider.

Create an AI abstraction layer.

The application should be able to support different providers in the future.

Possible capabilities:

- generate questions
- generate challenges
- evaluate answers
- evaluate explanations
- recommend study topics
- identify knowledge gaps
- simulate interviews
- analyze job descriptions
- generate personalized learning plans

Do not implement everything in the first iteration if doing so compromises stability.

However, design the architecture so these capabilities can be added without major refactoring.

---

# 15. Adaptive Learning

The long-term objective is adaptive learning.

The platform should eventually answer:

"What should I study today?"

The recommendation engine should consider:

- learning goals
- current mastery
- recent activity
- weak competencies
- overdue reviews
- learning consistency
- difficulty
- career relevance
- interview relevance

Create a recommendation domain/module rather than scattering recommendation logic throughout the application.

---

# 16. Interview Preparation

The platform must support future interview preparation.

It should eventually support:

- coding questions
- system design questions
- technical questions
- behavioral questions
- English interview practice
- simulated interviews
- scoring
- feedback
- identified weaknesses

Design the domain so interview content can be added later without restructuring the application.

---

# 17. Career Readiness

Eventually allow the user to provide a job description.

The system should be able to identify:

- required technologies
- required competencies
- missing skills
- current mastery
- estimated readiness
- recommended study priorities

Example:

PHP                  95%
Distributed Systems  70%
AWS                  40%
System Design        80%
English              60%

Estimated readiness:

72%

This feature can be implemented progressively.

---

# 18. Dashboard

The dashboard should be the main experience.

It should provide:

- current level
- XP
- learning momentum
- today's recommendation
- today's reviews
- current quests
- active learning paths
- mastery overview
- recent activity
- weak areas
- achievements

The UI should prioritize clarity over information density.

---

# 19. Visual Identity

Use my personal website as the primary visual reference:

https://www.fabiobandacheski.com

Source repository:

https://github.com/fabioversaobeta/fabiobandacheski

Inspect the existing implementation before designing the frontend.

Reuse the visual language where appropriate:

- typography
- spacing
- layout philosophy
- visual hierarchy
- colors
- cards
- borders
- buttons
- responsive behavior
- accessibility principles

Do not blindly copy the website.

Adapt its visual identity to a learning/productivity application.

The result should feel like a natural product from the same designer/developer.

---

# 20. UX Principles

The platform must be:

- fast
- responsive
- accessible
- intuitive
- keyboard-friendly
- mobile-friendly
- visually consistent
- easy to navigate

Avoid unnecessary animations.

Use animation only when it improves feedback or comprehension.

Do not create a dashboard overloaded with charts.

Every visual element should have a purpose.

---

# 21. Data Model

Design the database carefully before implementing features.

Use PostgreSQL.

Use migrations through Alembic.

Important requirements:

- proper foreign keys
- appropriate indexes
- unique constraints
- timestamps
- created_at / updated_at where appropriate
- soft deletion only where justified
- database-level integrity where useful

Do not over-normalize without a reason.

Do not use JSON columns as a substitute for proper relational modeling unless justified.

---

# 22. API

Build a clean REST API.

Use:

- versioned API routes
- consistent error responses
- proper HTTP semantics
- request validation
- response schemas
- pagination
- filtering
- sorting where useful

Document the API automatically through FastAPI.

Do not expose internal implementation details through the API.

---

# 23. Testing

Testing is mandatory.

Implement:

- unit tests
- integration tests
- API tests
- authentication tests
- database tests

For important frontend behavior, add appropriate tests.

Tests must be meaningful.

Do not create tests only to increase coverage.

Focus on:

- business rules
- edge cases
- authentication
- authorization
- mastery calculations
- XP calculations
- progression
- recommendations
- critical API behavior

---

# 24. Quality Gates

Before considering a feature complete:

1. Run formatting.
2. Run linting.
3. Run type checks.
4. Run tests.
5. Run database migrations.
6. Build the frontend.
7. Verify the application starts.
8. Verify critical flows.
9. Review for obvious security problems.
10. Update documentation.

Never intentionally leave the repository in a broken state.

If a temporary workaround is necessary, document it.

---

# 25. Error Handling

Implement consistent error handling.

Backend:

- validation errors
- authentication errors
- authorization errors
- not found
- conflict
- internal errors

Frontend:

- loading states
- empty states
- error states
- retry behavior
- form validation
- authentication expiration

Never silently swallow errors.

---

# 26. Observability

Prepare the architecture for production observability.

Include:

- structured logging
- request correlation
- useful error information
- health checks
- readiness checks

Avoid logging:

- passwords
- authentication tokens
- secrets
- sensitive personal information

---

# 27. Configuration

Never hard-code secrets.

Use environment variables.

Create:

- `.env.example`
- development configuration
- production configuration

Document every required environment variable.

Never commit real credentials.

---

# 28. Deployment

The intended deployment architecture is:

Frontend:

Vercel

Backend:

Railway

Database:

Railway PostgreSQL

The application must include the necessary configuration and documentation for deployment.

Do not assume local development configuration is sufficient for production.

Document:

- required environment variables
- build commands
- start commands
- database migration commands
- deployment steps
- CORS configuration
- frontend/backend URLs

---

# 29. GitHub Repository

Create a new GitHub repository using the same name as the current project directory.

Before creating the repository:

- initialize git if necessary
- create a meaningful README
- create `.gitignore`
- remove secrets
- verify the project builds
- commit the initial implementation

Use meaningful commit messages.

Do not create dozens of meaningless commits.

---

# 30. Documentation and Project Memory

The repository must maintain its own project memory.

Create:

docs/

    PRODUCT.md
    ARCHITECTURE.md
    ROADMAP.md
    DECISIONS.md
    DOMAIN.md
    API.md
    DEVELOPMENT.md
    DEPLOYMENT.md
    PENDING.md

Also create:

CLAUDE.md

The `CLAUDE.md` file must contain the most important project-specific instructions for future Claude Code sessions.

---

# 31. Roadmap

`docs/ROADMAP.md` must always represent the current project state.

Use statuses such as:

- NOT_STARTED
- IN_PROGRESS
- BLOCKED
- COMPLETED

For every major feature include:

- objective
- status
- implementation notes
- dependencies
- known limitations

Update the roadmap whenever meaningful progress is made.

---

# 32. Pending Decisions

Create:

docs/PENDING.md

If a decision requires my input, record:

- question
- context
- possible options
- recommended option
- impact
- current assumption

However:

## IMPORTANT

Never stop development merely because an item exists in `PENDING.md`.

If the decision is not blocking, make the best reasonable assumption and continue.

Only stop when absolutely necessary, such as:

- destructive operation
- irreversible decision
- security-critical decision
- financial commitment
- unavailable external credential
- missing information that makes implementation impossible

If I later answer a pending question, treat my answer as the authoritative decision and update the implementation and documentation accordingly.

---

# 33. Autonomous Development Rule

This is extremely important.

I explicitly want you to develop autonomously.

Do NOT repeatedly ask:

"Should I use X or Y?"

Instead:

1. Analyze the alternatives.
2. Select the most appropriate option.
3. Document the decision.
4. Implement it.
5. Continue.

Only request input when genuinely necessary.

The absence of my response must never unnecessarily block development.

---

# 34. Decision Making

When choosing between alternatives, prioritize:

1. correctness
2. security
3. maintainability
4. simplicity
5. testability
6. performance
7. developer experience

Do not optimize prematurely.

Prefer boring, well-established technology unless there is a strong reason to use something more complex.

---

# 35. Python Learning Objective

An important secondary objective of this project is for me to learn Python.

Therefore:

- use modern Python
- use strong typing
- use clear naming
- follow Python conventions
- use type hints
- use meaningful docstrings when appropriate
- avoid overly clever Python
- keep the code understandable
- document important Python-specific architectural decisions

Do not deliberately make the code complicated just to demonstrate advanced Python.

The code should teach through quality.

---

# 36. Learning Through the Project

The project itself is part of my learning journey.

Whenever a meaningful architectural concept is introduced, document it.

Examples:

- dependency injection
- repository pattern
- domain services
- application services
- database transactions
- authentication
- JWT/session architecture
- async Python
- background jobs
- caching
- PostgreSQL indexing
- API versioning
- observability
- testing strategy

The documentation should explain not only WHAT was implemented, but WHY.

---

# 37. Initial Content

Populate the initial platform with meaningful educational content based on the learning domains described in this document.

Do not create empty placeholders everywhere.

The initial dataset should include enough real content to make the platform immediately usable.

Prioritize:

1. Software Engineering
2. System Design
3. Distributed Systems
4. Backend
5. Python
6. AI Engineering
7. Interview Preparation

The architecture must allow all content to be extended later.

---

# 38. Seed Data

Create database seed functionality.

The project should be able to initialize a fresh environment with:

- initial user capability
- subjects
- competencies
- learning paths
- sample challenges
- questions
- achievements
- initial quests

Do not hard-code seed data directly into production application logic.

---

# 39. Initial User Experience

After authentication, the user should be able to:

1. See the dashboard.
2. Define a learning goal.
3. Explore subjects.
4. Open a learning path.
5. Study a competency.
6. Complete an activity.
7. Earn XP.
8. See progress.
9. Review mastery.
10. Return later and continue.

This flow is more important than implementing dozens of secondary features.

---

# 40. First Implementation Strategy

Before writing substantial application code:

1. Inspect the current directory.
2. Read `start-here.txt`.
3. Read `second-here.txt`.
4. Inspect the existing website repository if accessible.
5. Analyze the visual identity.
6. Define the initial architecture.
7. Create `CLAUDE.md`.
8. Create project documentation.
9. Create the roadmap.
10. Define the initial domain model.
11. Implement the foundation.
12. Implement authentication.
13. Implement learning management.
14. Implement progress.
15. Implement gamification.
16. Implement dashboard.
17. Implement initial educational content.
18. Add tests.
19. Add deployment configuration.
20. Validate production builds.
21. Create GitHub repository.
22. Push the project.

Do not stop after creating documentation.

Continue until the initial usable version is implemented.

---

# 41. Definition of Done

The first version is considered complete when:

- frontend runs locally
- backend runs locally
- database migrations work
- authentication works
- user can log in
- dashboard works
- learning goals work
- subjects work
- competencies work
- learning paths work
- study activities work
- progress is persisted
- XP works
- levels work
- achievements work
- mastery works
- initial educational content exists
- tests pass
- frontend builds
- backend tests pass
- deployment configuration exists
- documentation exists
- roadmap is updated
- pending decisions are documented
- Git repository is clean
- GitHub repository exists
- production deployment instructions exist

---

# 42. Working Style

Work iteratively.

After completing a meaningful piece:

1. Validate it.
2. Run tests.
3. Update documentation.
4. Update roadmap.
5. Commit when appropriate.
6. Continue.

Do not spend the entire session designing the perfect architecture before implementing anything.

Do not implement the entire application without validating intermediate results.

Build vertical slices.

Prefer:

Authentication → Dashboard → Learning → Progress → Gamification

over:

Database → entire backend → entire frontend → integration.

---

# 43. Important Constraints

Do not:

- use fake functionality presented as real
- leave obvious TODOs without documentation
- create placeholder implementations for core functionality
- ignore errors
- disable tests to make the build pass
- commit secrets
- expose credentials
- introduce unnecessary microservices
- over-engineer simple features
- stop because of minor ambiguity

If something cannot be completed because an external service requires credentials, implement the abstraction, provide configuration instructions, and continue with everything else.

---

# 44. Final Rule

You are not merely generating code.

You are building a maintainable software product that I will use for years as a personal learning platform.

Optimize for:

- long-term maintainability
- excellent developer experience
- strong architecture
- excellent UX
- learning value
- extensibility
- production readiness

When uncertain, make the best engineering decision, document it, implement it, test it, and continue.

Start now.