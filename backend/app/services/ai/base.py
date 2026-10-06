"""Provider-agnostic contract of the AI layer.

Deliberately narrow: one method, ``complete``, taking an ``AIRequest`` and
returning an ``AIResponse``. No provider SDK type appears here, so providers
are interchangeable and the rest of the app never depends on one.
"""

from dataclasses import dataclass, field
from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel

Role = Literal["user", "assistant"]


@dataclass(frozen=True)
class AIMessage:
    role: Role
    content: str


@dataclass(frozen=True)
class AIRequest:
    """A single completion request.

    ``system`` holds trusted instructions only; anything user-controlled must
    go in ``messages`` wrapped with ``app.services.ai.prompts.delimit``.
    ``temperature`` is optional: some current models reject non-default
    sampling parameters, so providers only send it when set.
    """

    messages: list[AIMessage]
    system: str = ""
    max_tokens: int = 1024
    temperature: float | None = None
    output_schema: type[BaseModel] | None = None
    language: str = "en"
    purpose: str = "generic"
    # Mark the system prompt as cacheable (worthwhile only for long, reused prompts).
    cache_system: bool = False


@dataclass(frozen=True)
class AIUsageInfo:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(frozen=True)
class AIResponse:
    """Raw provider answer. With ``output_schema`` set, ``text`` is JSON that
    still has to be validated by the caller (``ai_service`` does it)."""

    text: str
    provider: str
    model: str
    usage: AIUsageInfo = field(default_factory=AIUsageInfo)
    latency_ms: int = 0


@runtime_checkable
class AIProvider(Protocol):
    name: str
    model: str

    def complete(self, request: AIRequest) -> AIResponse:
        """Run one completion. Must raise only ``AIError`` subclasses."""
        ...
